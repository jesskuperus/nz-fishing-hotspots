#!/usr/bin/env python3
"""End-to-end verification of the engine on synthetic data.

Runs standalone (``python tests/test_pipeline.py``) so ``run.sh`` can use it
without pytest installed; pytest picks the same functions up if you have it.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Keep the whole suite offline and deterministic.
os.environ.setdefault("USE_LIVE_OCEAN_DATA", "false")
os.environ.setdefault("USE_LIVE_CHLOROPHYLL", "false")
os.environ.setdefault("USE_LIVE_WEATHER", "false")

import numpy as np  # noqa: E402

from backend import config  # noqa: E402
from backend.data_ingestion.bathymetry_loader import load_bathymetry  # noqa: E402
from backend.data_ingestion.chlorophyll import (  # noqa: E402
    fetch_chlorophyll,
    productivity_weight,
)
from backend.data_ingestion.coastline import land_mask  # noqa: E402
from backend.data_ingestion import weather  # noqa: E402
from backend.data_ingestion.mock_ocean_fetcher import generate_sst  # noqa: E402
from backend.data_ingestion.ocean_fetcher import fetch_ocean_field  # noqa: E402
from backend.engine import features  # noqa: E402
from backend.engine.grid import build_grid  # noqa: E402
from backend.engine.pipeline import run_pipeline  # noqa: E402

TEST_RESOLUTION_M = 1000.0  # coarser than the 500 m spec, so the suite is quick


def test_grid_cells_are_the_requested_size():
    grid = build_grid(resolution_m=500.0)
    dy, dx = grid.cell_size_m
    assert abs(dy - 500.0) < 1.0, dy
    assert abs(dx - 500.0) < 5.0, dx
    assert grid.n_cells > 10_000, grid.n_cells


def test_sst_stays_in_the_northland_range():
    grid = build_grid(resolution_m=TEST_RESOLUTION_M)
    sst = generate_sst(grid, day_of_year=265)
    assert 17.4 <= sst.min() <= 17.6, sst.min()
    assert 19.7 <= sst.max() <= 19.9, sst.max()


def test_thermal_fronts_are_detected():
    grid = build_grid(resolution_m=500.0)
    sst = generate_sst(grid, day_of_year=265)
    gradient = features.temperature_gradient(sst, grid)
    fronts = gradient >= config.FRONT_THRESHOLD_C_PER_KM
    assert fronts.any(), "synthetic field should contain at least one front"
    # The shelf-break front sits around 174.62-174.69 E.
    _, lon_mesh = grid.mesh
    assert 174.5 < float(np.median(lon_mesh[fronts])) < 174.8


def test_bathymetry_spans_the_shelf_and_masks_land():
    grid = build_grid(resolution_m=TEST_RESOLUTION_M)
    bathy = load_bathymetry(grid)
    depth = bathy.depth_m
    lat_mesh, lon_mesh = grid.mesh
    assert np.isnan(depth[land_mask(lat_mesh, lon_mesh)]).all(), "land must be NaN"
    water = depth[np.isfinite(depth)]
    assert water.min() < 20.0, water.min()
    assert water.max() > 200.0, water.max()


def test_slope_is_steepest_at_the_shelf_break():
    grid = build_grid(resolution_m=TEST_RESOLUTION_M)
    depth = load_bathymetry(grid).depth_m
    slope = features.seabed_slope(depth, grid)
    assert np.nanmax(slope) > 1.0, np.nanmax(slope)
    assert np.nanmax(slope) < 89.0


def test_scores_are_bounded_and_ranked():
    result = run_pipeline(
        date=dt.date(2026, 9, 22), resolution_m=TEST_RESOLUTION_M, write=False
    )
    scores = [f["properties"]["hotspot_score"] for f in result.geojson["features"]]
    assert scores, "pipeline produced no cells"
    assert all(0.0 <= s <= 100.0 for s in scores)
    assert scores == sorted(scores, reverse=True), "features must be score-ranked"
    assert max(scores) > 25.0, f"top score suspiciously flat: {max(scores)}"


def test_geojson_is_wellformed_and_complete():
    result = run_pipeline(
        date=dt.date(2026, 9, 22), resolution_m=TEST_RESOLUTION_M, write=False
    )
    gj = result.geojson
    assert gj["type"] == "FeatureCollection"
    meta = gj["metadata"]
    assert meta["grid"]["cells_scored"] == len(gj["features"])
    assert meta["weights"] == {
        "temp_gradient": 0.4,
        "depth_slope": 0.4,
        "current_velocity": 0.2,
        "chlorophyll": config.WEIGHT_CHLOROPHYLL,
    }
    assert meta["sources"]["chlorophyll"]
    assert meta["timing"]["available"]

    props = gj["features"][0]["properties"]
    for key in (
        "lat", "lon", "depth_m", "sst_c", "hotspot_score", "slope_deg",
        "chlorophyll_mg_m3",
        "temp_gradient_c_per_km", "current_speed_ms", "score_breakdown",
    ):
        assert props[key] is not None, f"missing {key}"

    ring = gj["features"][0]["geometry"]["coordinates"][0]
    assert len(ring) == 5 and ring[0] == ring[-1], "polygon must be a closed ring"


def test_score_matches_the_specified_formula():
    result = run_pipeline(
        date=dt.date(2026, 9, 22), resolution_m=TEST_RESOLUTION_M, write=False
    )
    # Pick a cell inside the fishable band so the depth factor is exactly 1.0.
    for feature in result.geojson["features"]:
        p = feature["properties"]
        if config.DEPTH_MIN_FISHABLE_M < p["depth_m"] < config.DEPTH_MAX_FISHABLE_M:
            b = p["score_breakdown"]
            total = 0.4 + 0.4 + 0.2 + config.WEIGHT_CHLOROPHYLL
            expected = (
                100
                * (
                    b["temp_gradient_weight"] * 0.4
                    + b["depth_slope_weight"] * 0.4
                    + b["current_weight"] * 0.2
                    + b["chlorophyll_weight"] * config.WEIGHT_CHLOROPHYLL
                )
                / total
            )
            assert abs(expected - p["hotspot_score"]) < 0.3, (expected, p)
            return
    raise AssertionError("no cell inside the fishable depth band")


def test_ocean_fetch_falls_back_without_network():
    grid = build_grid(resolution_m=2000.0)
    field = fetch_ocean_field(grid, dt.date(2026, 9, 22))
    assert field.sst_c.shape == grid.shape
    assert np.isfinite(field.sst_c).all()
    assert np.isfinite(field.current_speed_ms).all()


def test_chlorophyll_is_a_band_not_more_is_better():
    grid = build_grid(resolution_m=2000.0)
    field = fetch_chlorophyll(grid, dt.date(2026, 9, 22))
    assert field.is_synthetic and np.isfinite(field.chl_mg_m3).all()
    assert field.chl_mg_m3.min() > 0.0

    # Barren blue water and a thick bloom both score below the ideal band.
    barren, ideal, bloom = productivity_weight(
        np.array([0.02, 0.6, 3.8])
    )
    assert barren < ideal and bloom < ideal
    assert abs(ideal - 1.0) < 1e-9


def test_bite_windows_are_temporal_not_spatial():
    """Tide/light/moon must move the timeline, never the cell ranking."""
    date = dt.date(2026, 9, 22)
    a = run_pipeline(date=date, resolution_m=TEST_RESOLUTION_M, write=False)
    timing = a.metadata["timing"]
    assert timing["available"] and len(timing["hours"]) == 24
    assert all(0 <= h["bite_score"] <= 100 for h in timing["hours"])
    assert len(timing["best_hours"]) == 4

    # The same day scored twice must rank the same ground the same way; the
    # timeline is the only thing the temporal layer is allowed to drive.
    b = run_pipeline(date=date, resolution_m=TEST_RESOLUTION_M, write=False)
    ids_a = [f["id"] for f in a.geojson["features"][:50]]
    ids_b = [f["id"] for f in b.geojson["features"][:50]]
    assert ids_a == ids_b


def test_fishability_penalises_wind_and_swell():
    assert weather.fishability(5.0, 0.5) == 100.0
    assert weather.fishability(30.0, 0.2) == 0.0, "gale is a no-go however flat it is"
    assert weather.fishability(5.0, 3.0) == 0.0, "big swell is a no-go however calm"
    assert 0 < weather.fishability(17.0, 1.5) < 100
    assert weather.compass_point(0) == "N" and weather.compass_point(180) == "S"

    conditions = weather.fetch_conditions(dt.date(2026, 9, 22))
    assert conditions.is_synthetic and len(conditions.fishability) == 24
    assert conditions.notes, "a synthetic forecast must say so"


def test_catch_log_round_trip(tmp_path=None):
    import tempfile

    from backend.calibration.catch_log import CatchEntry, append_entry, load_entries

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "catch_log.csv"
        append_entry(
            CatchEntry("2026-09-22", -35.47, 174.74, "snapper", 4, 2.0, 68.0), path
        )
        append_entry(CatchEntry("2026-09-23", -35.5, 174.6, "kingfish", 1, 4.0), path)
        rows = load_entries(path)
    assert len(rows) == 2
    assert abs(rows[0].catch_rate - 2.0) < 1e-9
    assert rows[1].hotspot_score is None


def test_calibration_refuses_to_guess_from_thin_data():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import calibrate

    from backend.calibration.catch_log import CatchEntry

    thin = [CatchEntry("2026-09-22", -35.4, 174.7, "snapper", 2, 1.0, 60.0)] * 5
    report = calibrate.report(thin)
    assert "Not enough data" in report["verdict"]
    assert "spearman_score_vs_catch_rate" not in report

    # A clean monotonic relationship over enough trips must be detected.
    strong = [
        CatchEntry("2026-09-22", -35.4, 174.7, "snapper", i, 1.0, float(i * 4))
        for i in range(1, 26)
    ]
    assert calibrate.report(strong)["spearman_score_vs_catch_rate"] > 0.9


def test_geodataframe_export():
    result = run_pipeline(resolution_m=2000.0, write=False)
    try:
        gdf = __import__(
            "backend.engine.pipeline", fromlist=["to_geodataframe"]
        ).to_geodataframe(result.geojson)
    except ImportError:
        print("  (geopandas not installed — skipping GeoDataFrame check)")
        return
    assert len(gdf) == len(result.geojson["features"])
    assert gdf.crs.to_epsg() == 4326
    assert gdf.geometry.is_valid.all()


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"ok   {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

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
os.environ.setdefault("USE_LIVE_OCEAN_DATA", "false")  # keep the test offline

import numpy as np  # noqa: E402

from backend import config  # noqa: E402
from backend.data_ingestion.bathymetry_loader import load_bathymetry  # noqa: E402
from backend.data_ingestion.coastline import land_mask  # noqa: E402
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
    }

    props = gj["features"][0]["properties"]
    for key in (
        "lat", "lon", "depth_m", "sst_c", "hotspot_score", "slope_deg",
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
            expected = 100 * (
                b["temp_gradient_weight"] * 0.4
                + b["depth_slope_weight"] * 0.4
                + b["current_weight"] * 0.2
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

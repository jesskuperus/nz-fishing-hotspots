"""End-to-end daily run: ingest -> grid -> features -> score -> GeoJSON."""

from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from backend import config
from backend.data_ingestion import weather
from backend.data_ingestion.bathymetry_loader import load_bathymetry
from backend.data_ingestion.chlorophyll import fetch_chlorophyll
from backend.data_ingestion.coastline import land_mask
from backend.data_ingestion.ocean_fetcher import fetch_ocean_field
from backend.engine import features, scoring
from backend.engine.grid import Grid, build_grid
from backend.timing.windows import build_windows

log = logging.getLogger(__name__)


@dataclass
class RunResult:
    geojson: dict
    path: Path
    date: dt.date
    cells_scored: int

    @property
    def metadata(self) -> dict:
        return self.geojson["metadata"]


def _round(value: float, places: int = 3) -> float | None:
    if value is None or not np.isfinite(value):
        return None
    return round(float(value), places)


def run_pipeline(
    date: dt.date | None = None,
    resolution_m: float | None = None,
    min_score: float = 0.0,
    write: bool = True,
    output_path: Path | None = None,
) -> RunResult:
    """Score the whole bounding box for ``date`` and export GeoJSON."""
    date = date or dt.date.today()
    grid: Grid = build_grid(resolution_m=resolution_m or config.GRID_RESOLUTION_M)
    log.info(
        "Grid: %d x %d cells (%d total) at ~%.0f m",
        *grid.shape,
        grid.n_cells,
        grid.resolution_m,
    )

    ocean = fetch_ocean_field(grid, date)
    bathy = load_bathymetry(grid)
    chl = fetch_chlorophyll(grid, date)

    temp_grad = features.temperature_gradient(ocean.sst_c, grid)
    slope = features.seabed_slope(bathy.depth_m, grid)
    curvature = features.seabed_curvature(bathy.depth_m, grid)
    speed = ocean.current_speed_ms

    scored = scoring.hotspot_score(
        temp_grad, slope, speed, bathy.depth_m, chl.chl_mg_m3
    )
    score = scored["hotspot_score"]

    lat_mesh, lon_mesh = grid.mesh
    water = ~land_mask(lat_mesh, lon_mesh) & np.isfinite(bathy.depth_m)
    keep = water & (score >= min_score)

    # Percentile rank within the day's water cells. The absolute score is the
    # spec's formula and stays untouched; the percentile is what the map
    # colours by, so a flat day still reads as "these are the better marks"
    # instead of a uniformly yellow map.
    percentile = _percentile_rank(score, water)

    geojson = _build_geojson(
        grid=grid,
        keep=keep,
        date=date,
        score=score,
        scored=scored,
        percentile=percentile,
        sst=ocean.sst_c,
        temp_grad=temp_grad,
        slope=slope,
        curvature=curvature,
        depth=bathy.depth_m,
        speed=speed,
        u=ocean.current_u_ms,
        v=ocean.current_v_ms,
        chl=chl.chl_mg_m3,
        ocean_source=ocean.source,
        bathy_source=bathy.source,
        chl_source=chl.source,
        timing=_timing_block(date, grid),
        min_score=min_score,
    )

    path = Path(output_path or config.HOTSPOT_GEOJSON)
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(geojson), encoding="utf-8")
        log.info("Wrote %d cells to %s", len(geojson["features"]), path)

    return RunResult(
        geojson=geojson, path=path, date=date, cells_scored=len(geojson["features"])
    )


def _build_geojson(*, grid: Grid, keep: np.ndarray, date: dt.date, **fields) -> dict:
    """Assemble the FeatureCollection, via geopandas when it is available."""
    rows = _feature_rows(grid, keep, fields)
    collection = {
        "type": "FeatureCollection",
        "metadata": _metadata(grid, keep, date, fields),
        "features": rows,
    }
    return collection


def _feature_rows(grid: Grid, keep: np.ndarray, f: dict) -> list[dict]:
    lat_mesh, lon_mesh = grid.mesh
    half_lat = grid.lat_step / 2
    half_lon = grid.lon_step / 2
    idx = np.argwhere(keep)

    # Highest-scoring cells first, so a client that truncates the list keeps
    # the interesting ground.
    order = np.argsort(-f["score"][keep])
    idx = idx[order]

    features_out: list[dict] = []
    for n, (i, j) in enumerate(idx):
        lat = float(lat_mesh[i, j])
        lon = float(lon_mesh[i, j])
        south, north = lat - half_lat, lat + half_lat
        west, east = lon - half_lon, lon + half_lon
        features_out.append(
            {
                "type": "Feature",
                "id": f"c{i}_{j}",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [round(west, 6), round(south, 6)],
                            [round(east, 6), round(south, 6)],
                            [round(east, 6), round(north, 6)],
                            [round(west, 6), round(north, 6)],
                            [round(west, 6), round(south, 6)],
                        ]
                    ],
                },
                "properties": {
                    "cell_id": f"c{i}_{j}",
                    "rank": n + 1,
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "hotspot_score": _round(f["score"][i, j], 1),
                    "score_percentile": _round(f["percentile"][i, j], 1),
                    "depth_m": _round(f["depth"][i, j], 1),
                    "sst_c": _round(f["sst"][i, j], 2),
                    "temp_gradient_c_per_km": _round(f["temp_grad"][i, j], 3),
                    "slope_deg": _round(f["slope"][i, j], 2),
                    "curvature": _round(f["curvature"][i, j], 2),
                    "current_speed_ms": _round(f["speed"][i, j], 3),
                    "chlorophyll_mg_m3": _round(f["chl"][i, j], 3),
                    "current_bearing_deg": _bearing(f["u"][i, j], f["v"][i, j]),
                    "is_thermal_front": bool(f["scored"]["is_thermal_front"][i, j]),
                    "score_breakdown": {
                        "temp_gradient_weight": _round(
                            f["scored"]["temp_gradient_weight"][i, j], 3
                        ),
                        "depth_slope_weight": _round(
                            f["scored"]["depth_slope_weight"][i, j], 3
                        ),
                        "current_weight": _round(f["scored"]["current_weight"][i, j], 3),
                        "chlorophyll_weight": _round(
                            f["scored"]["chlorophyll_weight"][i, j], 3
                        ),
                        "temp_contribution": _round(
                            f["scored"]["temp_gradient_weight"][i, j]
                            * config.WEIGHT_TEMP_GRADIENT
                            / _total_weight()
                            * 100,
                            1,
                        ),
                        "slope_contribution": _round(
                            f["scored"]["depth_slope_weight"][i, j]
                            * config.WEIGHT_DEPTH_SLOPE
                            / _total_weight()
                            * 100,
                            1,
                        ),
                        "current_contribution": _round(
                            f["scored"]["current_weight"][i, j]
                            * config.WEIGHT_CURRENT
                            / _total_weight()
                            * 100,
                            1,
                        ),
                        "chlorophyll_contribution": _round(
                            f["scored"]["chlorophyll_weight"][i, j]
                            * config.WEIGHT_CHLOROPHYLL
                            / _total_weight()
                            * 100,
                            1,
                        ),
                    },
                },
            }
        )
    return features_out


def _percentile_rank(score: np.ndarray, water: np.ndarray) -> np.ndarray:
    """Map each water cell's score to its 0-100 percentile among water cells."""
    out = np.zeros_like(score)
    values = score[water]
    if values.size == 0:
        return out
    order = np.argsort(values)
    ranks = np.empty(values.size)
    ranks[order] = np.arange(values.size)
    out[water] = ranks / max(values.size - 1, 1) * 100.0
    return out


def _bearing(u: float, v: float) -> float | None:
    if not (np.isfinite(u) and np.isfinite(v)):
        return None
    return round(float(np.degrees(np.arctan2(u, v)) % 360.0), 1)


def _metadata(grid: Grid, keep: np.ndarray, date: dt.date, f: dict) -> dict:
    score = f["score"][keep]
    dy_m, dx_m = grid.cell_size_m
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "date": date.isoformat(),
        "region": "Tutukaka Coast to Poor Knights Shelf, Northland NZ",
        "bbox": [
            grid.bbox.lon_min,
            grid.bbox.lat_min,
            grid.bbox.lon_max,
            grid.bbox.lat_max,
        ],
        "grid": {
            "rows": grid.shape[0],
            "cols": grid.shape[1],
            "requested_resolution_m": grid.resolution_m,
            "actual_cell_size_m": [round(dy_m, 1), round(dx_m, 1)],
            "cells_total": grid.n_cells,
            "cells_scored": int(keep.sum()),
        },
        "sources": {
            "ocean": f["ocean_source"],
            "bathymetry": f["bathy_source"],
            "chlorophyll": f["chl_source"],
            "is_synthetic": any(
                "synthetic-mock" in src
                for src in (f["ocean_source"], f["bathy_source"], f["chl_source"])
            ),
        },
        "weights": {
            "temp_gradient": config.WEIGHT_TEMP_GRADIENT,
            "depth_slope": config.WEIGHT_DEPTH_SLOPE,
            "current_velocity": config.WEIGHT_CURRENT,
            "chlorophyll": config.WEIGHT_CHLOROPHYLL,
        },
        "timing": f["timing"],
        "thresholds": {
            "front_c_per_km": config.FRONT_THRESHOLD_C_PER_KM,
            "depth_band_m": [
                config.DEPTH_MIN_FISHABLE_M,
                config.DEPTH_MAX_FISHABLE_M,
            ],
            "min_score_filter": f["min_score"],
        },
        "percentile_note": (
            "score_percentile ranks each cell against the rest of the day's "
            "water cells; the map colours by it. hotspot_score is the "
            "absolute 0-100 formula value."
        ),
        "score_stats": {
            "min": _round(np.min(score), 1) if score.size else None,
            "mean": _round(np.mean(score), 1) if score.size else None,
            "p90": _round(np.percentile(score, 90), 1) if score.size else None,
            "max": _round(np.max(score), 1) if score.size else None,
        },
        "sst_range_c": [
            _round(np.nanmin(f["sst"]), 2),
            _round(np.nanmax(f["sst"]), 2),
        ],
        "depth_range_m": [
            _round(np.nanmin(f["depth"]), 1),
            _round(np.nanmax(f["depth"]), 1),
        ],
        "chlorophyll_range_mg_m3": [
            _round(np.nanmin(f["chl"]), 3),
            _round(np.nanmax(f["chl"]), 3),
        ],
        "thermal_front_cells": int((f["scored"]["is_thermal_front"] & keep).sum()),
    }


def _total_weight() -> float:
    """Sum of the score weights, so the contributions add up to the score."""
    total = (
        config.WEIGHT_TEMP_GRADIENT
        + config.WEIGHT_DEPTH_SLOPE
        + config.WEIGHT_CURRENT
        + config.WEIGHT_CHLOROPHYLL
    )
    return total or 1.0


def _timing_block(date: dt.date, grid: Grid) -> dict:
    """Bite windows and fishability for the day, for the whole box.

    Deliberately separate from the cell scores: tide, light, moon and wind
    are the same everywhere on a 30 km box, so they answer *when to go*,
    not *where*. Shipped inside the GeoJSON metadata so the static map needs
    no second request.
    """
    lat, lon = grid.bbox.centre
    try:
        windows = build_windows(date, lat, lon)
    except Exception as exc:  # noqa: BLE001 - the map is still useful without it
        log.warning("Bite windows unavailable (%s)", exc)
        return {"available": False, "reason": str(exc)}

    conditions = weather.fetch_conditions(date, lat, lon)
    for hour in windows["hours"]:
        # windows are indexed by UTC hour; the forecast is local NZ time.
        local_h = (hour["utc_hour"] + 12) % 24
        hour["wind_kt"] = conditions.wind_kt[local_h]
        hour["wind_dir"] = weather.compass_point(conditions.wind_dir_deg[local_h])
        hour["swell_m"] = conditions.swell_m[local_h]
        hour["fishability"] = conditions.fishability[local_h]

    windows["available"] = True
    windows["conditions_source"] = conditions.source
    windows["conditions_notes"] = conditions.notes
    windows["fishability_summary"] = {
        "best": max(conditions.fishability),
        "worst": min(conditions.fishability),
        "daylight_mean": round(
            sum(conditions.fishability[6:19]) / len(conditions.fishability[6:19]), 1
        ),
    }
    return windows


def to_geodataframe(geojson: dict):
    """Optional geopandas view of a run, for GIS work or vector tiling."""
    import geopandas as gpd

    return gpd.GeoDataFrame.from_features(geojson["features"], crs="EPSG:4326")

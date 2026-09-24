"""FastAPI app: serves the hotspot GeoJSON and the single-page map UI."""

from __future__ import annotations

import datetime as dt
import json
import logging
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import config
from backend.engine.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

FRONTEND_DIR = config.PROJECT_ROOT / "frontend"

app = FastAPI(
    title="NZ Marine Hotspot Predictor",
    description=(
        "Daily spatial hotspot scoring for the Tutukaka Coast and Poor "
        "Knights Shelf, Northland NZ."
    ),
    version="0.1.0",
)

# One run at a time: the pipeline is CPU-bound and writes a shared file.
_run_lock = threading.Lock()


def _cache_path(date: dt.date, resolution_m: float) -> Path:
    if date == dt.date.today() and resolution_m == config.GRID_RESOLUTION_M:
        return config.HOTSPOT_GEOJSON
    return config.OUTPUT_DIR / f"hotspots_{date.isoformat()}_{int(resolution_m)}m.geojson"


@app.get("/api/v1/health")
def health() -> dict:
    exists = config.HOTSPOT_GEOJSON.is_file()
    return {
        "status": "ok",
        "today_geojson_present": exists,
        "output_dir": str(config.OUTPUT_DIR),
        "mapbox_token_configured": bool(config.MAPBOX_TOKEN),
        "live_ocean_data_enabled": config.USE_LIVE_OCEAN_DATA,
    }


@app.get("/api/v1/config")
def get_config() -> dict:
    """Everything the frontend needs to render without hardcoding it."""
    return {
        "bbox": {
            "lat_min": config.BBOX.lat_min,
            "lat_max": config.BBOX.lat_max,
            "lon_min": config.BBOX.lon_min,
            "lon_max": config.BBOX.lon_max,
        },
        "centre": config.BBOX.centre,
        "grid_resolution_m": config.GRID_RESOLUTION_M,
        "weights": {
            "temp_gradient": config.WEIGHT_TEMP_GRADIENT,
            "depth_slope": config.WEIGHT_DEPTH_SLOPE,
            "current_velocity": config.WEIGHT_CURRENT,
        },
        "front_threshold_c_per_km": config.FRONT_THRESHOLD_C_PER_KM,
        "mapbox_token": config.MAPBOX_TOKEN,
    }


@app.get("/api/v1/hotspots")
def hotspots(
    date: str | None = Query(
        None, description="ISO date (YYYY-MM-DD). Defaults to today."
    ),
    min_score: float = Query(0.0, ge=0, le=100, description="Drop cells scoring below this."),
    min_percentile: float = Query(
        0.0,
        ge=0,
        le=100,
        description=(
            "Keep only cells at or above this percentile of the day's scores. "
            "Resolution-independent, unlike min_score."
        ),
    ),
    resolution_m: float | None = Query(
        None, ge=100, le=5000, description="Grid cell size in metres."
    ),
    limit: int | None = Query(
        None, ge=1, description="Keep only the top N cells by score."
    ),
    refresh: bool = Query(False, description="Force a recalculation."),
) -> JSONResponse:
    """Scored 500 m grid as GeoJSON, computing it on demand if needed."""
    run_date = _parse_date(date)
    resolution = resolution_m or config.GRID_RESOLUTION_M
    path = _cache_path(run_date, resolution)

    if not refresh and path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["metadata"]["served_from_cache"] = True
    else:
        with _run_lock:
            result = run_pipeline(
                date=run_date, resolution_m=resolution, output_path=path
            )
        payload = result.geojson
        payload["metadata"]["served_from_cache"] = False

    if min_score > 0:
        payload = _filter_features(
            payload, lambda p: (p.get("hotspot_score") or 0) >= min_score
        )
        payload["metadata"]["thresholds"]["min_score_filter"] = min_score
    if min_percentile > 0:
        payload = _filter_features(
            payload, lambda p: (p.get("score_percentile") or 0) >= min_percentile
        )
        payload["metadata"]["thresholds"]["min_percentile_filter"] = min_percentile
    if limit:
        payload["features"] = payload["features"][:limit]
    payload["metadata"]["features_returned"] = len(payload["features"])
    return JSONResponse(payload)


@app.post("/api/v1/regenerate")
def regenerate(date: str | None = None, resolution_m: float | None = None) -> dict:
    """Recompute a day's grid and overwrite its cached GeoJSON."""
    run_date = _parse_date(date)
    resolution = resolution_m or config.GRID_RESOLUTION_M
    with _run_lock:
        result = run_pipeline(
            date=run_date,
            resolution_m=resolution,
            output_path=_cache_path(run_date, resolution),
        )
    return {
        "status": "regenerated",
        "date": result.date.isoformat(),
        "cells_scored": result.cells_scored,
        "path": str(result.path),
        "metadata": result.metadata,
    }


@app.get("/api/v1/top")
def top_spots(
    n: int = Query(20, ge=1, le=200), date: str | None = None
) -> dict:
    """The day's best marks as a plain list — handy for a phone or a chart."""
    response = hotspots(
        date=date,
        min_score=0.0,
        min_percentile=0.0,
        resolution_m=None,
        limit=n,
        refresh=False,
    )
    payload = json.loads(bytes(response.body).decode("utf-8"))
    return {
        "date": payload["metadata"]["date"],
        "sources": payload["metadata"]["sources"],
        "spots": [feat["properties"] for feat in payload["features"]],
    }


def _parse_date(raw: str | None) -> dt.date:
    if not raw:
        return dt.date.today()
    try:
        return dt.date.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(400, f"Invalid date {raw!r}; expected YYYY-MM-DD") from exc


def _filter_features(payload: dict, predicate) -> dict:
    kept = [f for f in payload["features"] if predicate(f["properties"])]
    return {**payload, "features": kept}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

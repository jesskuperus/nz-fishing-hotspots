"""Central configuration for the Northland marine hotspot engine.

Everything here is overridable through environment variables (see
``.env.example``) so the pipeline can be pointed at real data sources
without touching code. Absent credentials are not an error: each ingestion
module falls back to a synthetic generator.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # optional, only used to read a local .env during development
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is a convenience, not a need
    def load_dotenv(*_args, **_kwargs):
        return False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", DATA_DIR / "output"))
BATHYMETRY_DIR = Path(os.getenv("BATHYMETRY_DIR", DATA_DIR / "bathymetry"))
HOTSPOT_GEOJSON = OUTPUT_DIR / "hotspots_today.geojson"


@dataclass(frozen=True)
class BoundingBox:
    """Tutukaka Coast to Poor Knights Shelf, Northland NZ."""

    lat_min: float = -35.80
    lat_max: float = -35.30
    lon_min: float = 174.30
    lon_max: float = 174.90

    @property
    def centre(self) -> tuple[float, float]:
        return ((self.lat_min + self.lat_max) / 2, (self.lon_min + self.lon_max) / 2)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    try:
        return float(raw) if raw not in (None, "") else default
    except ValueError:
        return default


BBOX = BoundingBox(
    lat_min=_env_float("BBOX_LAT_MIN", -35.80),
    lat_max=_env_float("BBOX_LAT_MAX", -35.30),
    lon_min=_env_float("BBOX_LON_MIN", 174.30),
    lon_max=_env_float("BBOX_LON_MAX", 174.90),
)

# Grid resolution in metres. 500 m is the MVP spec; raise it for a faster,
# coarser run (useful on a laptop or when serving the whole bbox to a phone).
GRID_RESOLUTION_M = _env_float("GRID_RESOLUTION_M", 500.0)

# Hotspot score weights. They should sum to 1.0.
WEIGHT_TEMP_GRADIENT = _env_float("WEIGHT_TEMP_GRADIENT", 0.4)
WEIGHT_DEPTH_SLOPE = _env_float("WEIGHT_DEPTH_SLOPE", 0.4)
WEIGHT_CURRENT = _env_float("WEIGHT_CURRENT", 0.2)

# A thermal front worth fishing: the spec's 0.5 degC per km threshold.
FRONT_THRESHOLD_C_PER_KM = _env_float("FRONT_THRESHOLD_C_PER_KM", 0.5)

# Gradient/slope values at or above these are treated as "as good as it gets"
# and normalise to 1.0. Without a ceiling a single freak cell would flatten
# every other cell's score.
# Calibrated against what these fields actually reach on a 500 m grid:
# a 0.8 degC/km front is a hard edge, and seabed slope on the Tutukaka
# shelf tops out around 6 degrees even across the shelf break.
TEMP_GRADIENT_CEILING_C_PER_KM = _env_float("TEMP_GRADIENT_CEILING_C_PER_KM", 0.8)
SLOPE_CEILING_DEG = _env_float("SLOPE_CEILING_DEG", 6.0)
CURRENT_CEILING_MS = _env_float("CURRENT_CEILING_MS", 0.7)

# Fishable depth band. Cells shallower/deeper than this are scored down —
# a 900 m abyssal slope is steep but not where you drop a jig.
DEPTH_MIN_FISHABLE_M = _env_float("DEPTH_MIN_FISHABLE_M", 12.0)
DEPTH_MAX_FISHABLE_M = _env_float("DEPTH_MAX_FISHABLE_M", 250.0)

# Data sources. Blank credentials => synthetic fallback, by design.
OPEN_METEO_MARINE_URL = os.getenv(
    "OPEN_METEO_MARINE_URL", "https://marine-api.open-meteo.com/v1/marine"
)
USE_LIVE_OCEAN_DATA = os.getenv("USE_LIVE_OCEAN_DATA", "true").lower() not in (
    "false",
    "0",
    "no",
)
OCEAN_FETCH_TIMEOUT_S = _env_float("OCEAN_FETCH_TIMEOUT_S", 20.0)
# Coarse sampling grid used for live API calls (one request per point, so keep
# it small). The SST field is interpolated up to the 500 m grid afterwards.
LIVE_SAMPLE_POINTS = int(_env_float("LIVE_SAMPLE_POINTS", 5))

COPERNICUS_USERNAME = os.getenv("COPERNICUS_USERNAME", "")
COPERNICUS_PASSWORD = os.getenv("COPERNICUS_PASSWORD", "")
COPERNICUS_DATASET_ID = os.getenv("COPERNICUS_DATASET_ID", "")

LINZ_BATHYMETRY_FILE = os.getenv("LINZ_BATHYMETRY_FILE", "")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

RANDOM_SEED = int(_env_float("RANDOM_SEED", 20260922))

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

# --- Chlorophyll-a (spatial: where the food chain starts) -------------------
# Productive water is a band, not "more is better": a blue desert holds no
# bait, and a thick bloom is murky, oxygen-poor water gamefish avoid. These
# are the edges of the band that scores 1.0, in mg/m^3.
CHL_IDEAL_MIN_MG_M3 = _env_float("CHL_IDEAL_MIN_MG_M3", 0.25)
CHL_IDEAL_MAX_MG_M3 = _env_float("CHL_IDEAL_MAX_MG_M3", 1.20)
CHL_CEILING_MG_M3 = _env_float("CHL_CEILING_MG_M3", 4.0)
USE_LIVE_CHLOROPHYLL = os.getenv("USE_LIVE_CHLOROPHYLL", "true").lower() not in (
    "false",
    "0",
    "no",
)

# Hotspot score weights (spatial terms only). They are renormalised in
# scoring, so changing one does not silently rescale the rest.
# The brief's formula was 0.4 / 0.4 / 0.2 with no chlorophyll term; adding
# productivity takes a slice off each of the three rather than inflating the
# total. Set WEIGHT_CHLOROPHYLL=0 to get the original formula back exactly.
WEIGHT_CHLOROPHYLL = _env_float("WEIGHT_CHLOROPHYLL", 0.15)

# --- Bite window (temporal: when to go, same for every cell) ---------------
# Deliberately NOT part of the per-cell score: tide, light and moon shift
# every cell by the same factor, so folding them in would change the numbers
# without changing the ranking. They drive the hourly timeline instead.
WEIGHT_TIDE_MOVEMENT = _env_float("WEIGHT_TIDE_MOVEMENT", 0.50)
WEIGHT_LIGHT = _env_float("WEIGHT_LIGHT", 0.35)
WEIGHT_MOON = _env_float("WEIGHT_MOON", 0.15)

# --- Fishability (wind and swell: whether you can get out at all) ----------
# Small-trailer-boat limits off Tutukaka. Above the max it is a no-go day.
WIND_COMFORTABLE_KT = _env_float("WIND_COMFORTABLE_KT", 10.0)
WIND_MAX_KT = _env_float("WIND_MAX_KT", 25.0)
SWELL_COMFORTABLE_M = _env_float("SWELL_COMFORTABLE_M", 1.0)
SWELL_MAX_M = _env_float("SWELL_MAX_M", 2.5)
USE_LIVE_WEATHER = os.getenv("USE_LIVE_WEATHER", "true").lower() not in (
    "false",
    "0",
    "no",
)

# --- Catch log / calibration ------------------------------------------------
CATCH_LOG_PATH = Path(os.getenv("CATCH_LOG_PATH", DATA_DIR / "catch_log.csv"))

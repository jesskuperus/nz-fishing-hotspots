"""No-take marine reserves: never score them as fishing water.

Boundaries are the Department of Conservation "DOC Marine Reserves" layer
(Marine Reserves Act 1971), clipped to the Tutukaka bounding box and stored in
``data/marine_reserves.geojson`` (copied to ``public/`` for the phone map).
Refresh from the DOC ArcGIS FeatureServer:
https://services1.arcgis.com/3JjYDyG3oajxU6HO/arcgis/rest/services/DOC_Marine_Reserves/FeatureServer/0

Fishing, taking or disturbing marine life is prohibited inside these areas, so
a cell that touches one is removed from the output instead of being ranked.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from shapely import contains_xy
from shapely.geometry import shape
from shapely.ops import unary_union

from backend import config

RESERVES_PATH = Path(config.DATA_DIR) / "marine_reserves.geojson"
# Extra margin around each reserve, in degrees (~110 m), so GPS error and the
# 500 m cell centre never put a mark on the line.
MARGIN_DEG = 0.001


@lru_cache(maxsize=1)
def reserve_geometry():
    data = json.loads(RESERVES_PATH.read_text(encoding="utf-8"))
    geoms = [shape(f["geometry"]) for f in data["features"]]
    return unary_union(geoms).buffer(MARGIN_DEG)


def reserve_names() -> list[str]:
    data = json.loads(RESERVES_PATH.read_text(encoding="utf-8"))
    return [f["properties"]["name"] for f in data["features"]]


def reserve_mask(lat_mesh: np.ndarray, lon_mesh: np.ndarray, half_cell_deg: float) -> np.ndarray:
    """True where a cell centre, or any part of its footprint, is in a reserve."""
    geom = reserve_geometry().buffer(half_cell_deg)
    return contains_xy(geom, lon_mesh, lat_mesh)

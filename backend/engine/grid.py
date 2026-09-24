"""500 m x 500 m spatial grid over the Northland bounding box.

The grid is held as 2D numpy arrays of cell-centre coordinates so the
feature maths (``numpy.gradient``) stays vectorised, and is only converted
to ``geopandas`` polygons at export time.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backend.config import BBOX, GRID_RESOLUTION_M, BoundingBox

EARTH_M_PER_DEG_LAT = 111_320.0


def metres_per_degree_lon(lat: float) -> float:
    return EARTH_M_PER_DEG_LAT * float(np.cos(np.radians(lat)))


@dataclass(frozen=True)
class Grid:
    """Regular lat/lon grid whose cells are ~``resolution_m`` on a side."""

    lats: np.ndarray  # 1D, ascending
    lons: np.ndarray  # 1D, ascending
    resolution_m: float
    bbox: BoundingBox

    @property
    def shape(self) -> tuple[int, int]:
        return (self.lats.size, self.lons.size)

    @property
    def n_cells(self) -> int:
        return self.lats.size * self.lons.size

    @property
    def lat_step(self) -> float:
        return float(self.lats[1] - self.lats[0])

    @property
    def lon_step(self) -> float:
        return float(self.lons[1] - self.lons[0])

    @property
    def mesh(self) -> tuple[np.ndarray, np.ndarray]:
        """2D (lat, lon) arrays of cell centres, indexed [row, col]."""
        lon_mesh, lat_mesh = np.meshgrid(self.lons, self.lats)
        return lat_mesh, lon_mesh

    @property
    def cell_size_m(self) -> tuple[float, float]:
        """North-south and east-west cell size in metres at the grid centre."""
        mid_lat = float(np.mean(self.lats))
        return (
            self.lat_step * EARTH_M_PER_DEG_LAT,
            self.lon_step * metres_per_degree_lon(mid_lat),
        )


def build_grid(
    bbox: BoundingBox = BBOX, resolution_m: float = GRID_RESOLUTION_M
) -> Grid:
    """Divide ``bbox`` into cells of roughly ``resolution_m`` per side.

    Cell centres are offset half a step in from the bbox edges so every cell
    polygon sits fully inside the requested area.
    """
    lat_step = resolution_m / EARTH_M_PER_DEG_LAT
    mid_lat = (bbox.lat_min + bbox.lat_max) / 2
    lon_step = resolution_m / metres_per_degree_lon(mid_lat)

    n_rows = max(int(np.floor((bbox.lat_max - bbox.lat_min) / lat_step)), 2)
    n_cols = max(int(np.floor((bbox.lon_max - bbox.lon_min) / lon_step)), 2)

    lats = bbox.lat_min + (np.arange(n_rows) + 0.5) * lat_step
    lons = bbox.lon_min + (np.arange(n_cols) + 0.5) * lon_step
    return Grid(lats=lats, lons=lons, resolution_m=resolution_m, bbox=bbox)

"""Spatial feature extraction: thermal fronts and seabed slope.

All derivatives are taken with ``numpy.gradient`` in metres, using the
grid's real cell size, so the outputs are in physical units (degC/km,
degrees of slope) rather than per-pixel values.
"""

from __future__ import annotations

import numpy as np

from backend.engine.grid import Grid


def _gradient_per_metre(field: np.ndarray, grid: Grid) -> tuple[np.ndarray, np.ndarray]:
    """d/dy (north) and d/dx (east) of ``field``, per metre."""
    dy_m, dx_m = grid.cell_size_m
    filled = np.where(np.isfinite(field), field, np.nan)
    # numpy.gradient propagates NaN into neighbours; interpolate the holes
    # first so coastal cells still get a usable derivative.
    filled = _fill_holes(filled)
    d_dy, d_dx = np.gradient(filled, dy_m, dx_m)
    return d_dy, d_dx


def _fill_holes(field: np.ndarray) -> np.ndarray:
    """Replace NaNs with the nearest finite value (nearest-neighbour fill)."""
    mask = ~np.isfinite(field)
    if not mask.any():
        return field
    out = field.copy()
    try:
        from scipy.ndimage import distance_transform_edt

        idx = distance_transform_edt(mask, return_distances=False, return_indices=True)
        out = field[tuple(idx)]
    except ImportError:  # pragma: no cover
        out[mask] = np.nanmean(field)
    return out


def temperature_gradient(sst_c: np.ndarray, grid: Grid) -> np.ndarray:
    """Thermal front strength in degC per kilometre."""
    d_dy, d_dx = _gradient_per_metre(sst_c, grid)
    return np.hypot(d_dy, d_dx) * 1000.0


def seabed_slope(depth_m: np.ndarray, grid: Grid) -> np.ndarray:
    """Seabed slope in degrees. Steep = drop-off, pinnacle or canyon wall."""
    d_dy, d_dx = _gradient_per_metre(depth_m, grid)
    rise_over_run = np.hypot(d_dy, d_dx)
    return np.degrees(np.arctan(rise_over_run))


def seabed_curvature(depth_m: np.ndarray, grid: Grid) -> np.ndarray:
    """Laplacian of depth — negative where the seabed rises into a pinnacle.

    Not part of the scoring formula, but exported per cell because it is how
    you tell a pinnacle apart from a plain sloping shelf.
    """
    dy_m, dx_m = grid.cell_size_m
    filled = _fill_holes(depth_m)
    d_dy, d_dx = np.gradient(filled, dy_m, dx_m)
    d2_dy2 = np.gradient(d_dy, dy_m, axis=0)
    d2_dx2 = np.gradient(d_dx, dx_m, axis=1)
    return (d2_dy2 + d2_dx2) * 1e6  # per km^2, keeps the numbers readable

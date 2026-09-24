"""Synthetic sea-surface temperature and current fields.

Used whenever the live marine API is unreachable or switched off, so the
pipeline always produces a complete run. The field is deliberately
*structured*, not noise: an offshore warm tongue (East Auckland Current),
a cool coastal band, and two sharp thermal fronts in the 17.5-19.8 degC
range so front detection has something real to find.
"""

from __future__ import annotations

import numpy as np

from backend.config import RANDOM_SEED
from backend.data_ingestion.coastline import distance_offshore_km
from backend.engine.grid import Grid

SST_MIN_C = 17.5
SST_MAX_C = 19.8


def _smooth(field: np.ndarray, sigma_cells: float) -> np.ndarray:
    """Gaussian blur, using scipy when present and a box blur otherwise."""
    try:
        from scipy.ndimage import gaussian_filter

        return gaussian_filter(field, sigma=sigma_cells, mode="nearest")
    except ImportError:  # pragma: no cover
        kernel = max(int(sigma_cells), 1)
        padded = np.pad(field, kernel, mode="edge")
        out = np.zeros_like(field)
        count = 0
        for dy in range(-kernel, kernel + 1):
            for dx in range(-kernel, kernel + 1):
                out += padded[
                    kernel + dy : kernel + dy + field.shape[0],
                    kernel + dx : kernel + dx + field.shape[1],
                ]
                count += 1
        return out / count


def generate_sst(grid: Grid, day_of_year: int, seed: int = RANDOM_SEED) -> np.ndarray:
    """Synthetic SST in degrees Celsius, shaped like the grid."""
    lat, lon = grid.mesh
    offshore = distance_offshore_km(lat, lon)
    rng = np.random.default_rng(seed + day_of_year)

    # Base: warmer offshore (East Auckland Current) and warmer to the north.
    # Kept deliberately gentle: the broad-scale trend has to stay small
    # relative to the front steps, or rescaling into the 17.5-19.8 degC band
    # squashes the fronts below the detection threshold.
    base = 18.4 + 0.012 * np.clip(offshore, 0, 40) + 0.5 * (lat + 35.80)

    # Seasonal swing, so successive dates are not identical.
    base += 0.15 * np.sin(2 * np.pi * (day_of_year - 20) / 365.0)

    # Front 1: the shelf-break front, a tanh step that meanders with latitude.
    # The 0.007 deg width is ~0.7 km, which is what makes it a *front* rather
    # than a gradient: it clears the 0.5 degC/km detection threshold.
    front1_lon = 174.655 + 0.028 * np.sin((lat + 35.6) * 24.0)
    base += 0.70 * np.tanh((lon - front1_lon) / 0.007)

    # Front 2: a weaker convergence pushing in behind the Poor Knights.
    front2_lon = 174.545 + 0.02 * np.cos((lat + 35.5) * 31.0)
    base += 0.30 * np.tanh((lon - front2_lon) / 0.010)

    # An eddy sitting off the Poor Knights, and a cool upwelling pocket.
    base += 0.30 * np.exp(-(((lat + 35.47) / 0.055) ** 2 + ((lon - 174.76) / 0.05) ** 2))
    base -= 0.25 * np.exp(-(((lat + 35.70) / 0.05) ** 2 + ((lon - 174.60) / 0.045) ** 2))

    # Mesoscale texture: correlated, not per-pixel noise.
    base += _smooth(rng.normal(0.0, 0.25, size=grid.shape), sigma_cells=5.0)

    # Light smoothing only — a 2-cell blur at 500 m would erase the fronts.
    sst = _smooth(base, sigma_cells=0.8)

    # Rescale into the target range rather than clipping it: clipping would
    # flatten the very front faces the engine is looking for.
    lo, hi = float(np.min(sst)), float(np.max(sst))
    if hi - lo < 1e-6:
        return np.full_like(sst, (SST_MIN_C + SST_MAX_C) / 2)
    return SST_MIN_C + (sst - lo) * (SST_MAX_C - SST_MIN_C) / (hi - lo)


def generate_currents(
    grid: Grid, day_of_year: int, seed: int = RANDOM_SEED
) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic current velocity components (u east, v north) in m/s."""
    lat, lon = grid.mesh
    offshore = distance_offshore_km(lat, lon)
    rng = np.random.default_rng(seed + 7 * day_of_year)

    # The East Auckland Current runs broadly south-east, strengthening
    # offshore and accelerating around the Poor Knights pinnacles.
    strength = 0.15 + 0.010 * np.clip(offshore, 0, 45)
    u = strength * 0.35
    v = -strength

    # Tidal acceleration around the islands and headlands.
    boost = 0.55 * np.exp(
        -(((lat + 35.465) / 0.045) ** 2 + ((lon - 174.728) / 0.038) ** 2)
    ) + 0.30 * np.exp(-(((lat + 35.615) / 0.030) ** 2 + ((lon - 174.560) / 0.030) ** 2))
    u = u + boost * 0.6
    v = v - boost * 0.5

    u = _smooth(u + rng.normal(0, 0.05, grid.shape), 4.0)
    v = _smooth(v + rng.normal(0, 0.05, grid.shape), 4.0)
    return u, v

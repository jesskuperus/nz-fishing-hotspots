"""Synthetic bathymetry for the Tutukaka shelf.

Models the features that matter for the score: a gently shoaling inshore
zone, the shelf break dropping from ~60 m to 200 m+, and the Poor Knights
pinnacles rising steeply out of it. Depths are positive metres below chart
datum. Used when no LINZ raster is supplied.
"""

from __future__ import annotations

import numpy as np

from backend.config import RANDOM_SEED
from backend.data_ingestion.coastline import distance_offshore_km, land_mask
from backend.engine.grid import Grid
from backend.data_ingestion.mock_ocean_fetcher import _smooth

# (lat, lon, crest depth m, radius deg) — the Poor Knights group plus the
# well-known pinnacles and reefs fished off Tutukaka.
PINNACLES = [
    (-35.465, 174.728, 8.0, 0.030),   # Poor Knights (Tawhiti Rahi / Aorangi)
    (-35.428, 174.744, 22.0, 0.012),  # Sugarloaf / Pinnacles, north end
    (-35.510, 174.745, 35.0, 0.014),  # High Peak Rocks area
    (-35.595, 174.640, 40.0, 0.013),  # Tutukaka offshore reef
    (-35.700, 174.680, 55.0, 0.015),  # Southern shelf knoll
    (-35.375, 174.640, 30.0, 0.013),  # Mimiwhangata outer reef
]


def generate_bathymetry(grid: Grid, seed: int = RANDOM_SEED) -> np.ndarray:
    """Depth in positive metres; ``numpy.nan`` on land."""
    lat, lon = grid.mesh
    offshore = np.clip(distance_offshore_km(lat, lon), 0.0, None)
    rng = np.random.default_rng(seed + 991)

    # Inshore ramp: 10 m at the shore to roughly 60 m by 12 km out.
    depth = 10.0 + 4.2 * offshore

    # Shelf break: a tanh step centred ~16 km offshore taking it to 200 m+.
    depth += 150.0 * (1 + np.tanh((offshore - 16.5) / 2.2)) / 2

    # Continental slope beyond the break keeps falling away.
    depth += 22.0 * np.clip(offshore - 22.0, 0.0, None)

    # Pinnacles and reefs: subtract a Gaussian bump down to the crest depth.
    for p_lat, p_lon, crest, radius in PINNACLES:
        bump = np.exp(-(((lat - p_lat) / radius) ** 2 + ((lon - p_lon) / radius) ** 2))
        target = np.maximum(depth - crest, 0.0)
        depth = depth - target * bump

    # A canyon cutting the shelf edge — reliable current-concentrating ground.
    canyon = np.exp(-(((lat + 35.555) / 0.020) ** 2)) * np.clip(offshore - 12.0, 0, 14)
    depth += 5.5 * canyon

    depth = _smooth(depth + rng.normal(0, 1.6, grid.shape), sigma_cells=1.5)
    depth = np.clip(depth, 3.0, None)
    depth[land_mask(lat, lon)] = np.nan
    return depth

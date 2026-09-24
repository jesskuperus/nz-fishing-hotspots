"""Synthetic Tutukaka coastline used to mask land cells.

The real thing would be a LINZ coastline polygon; for the MVP a smooth
analytic curve through the known headlands is enough to keep the grid off
the paddocks. ``land_mask`` is shared by the bathymetry generator and the
exporter so both agree on where the water stops.
"""

from __future__ import annotations

import numpy as np

# Longitude of the shoreline as a function of latitude, anchored on real
# points: Whangarei Heads (-35.83, 174.50), Tutukaka (-35.61, 174.53),
# Ngunguru (-35.62, 174.50), Whananaki (-35.51, 174.45), Mimiwhangata
# (-35.44, 174.44), Cape Brett approach (-35.32, 174.35).
_COAST_LATS = np.array([-35.90, -35.80, -35.70, -35.61, -35.52, -35.44, -35.36, -35.28])
_COAST_LONS = np.array([174.54, 174.51, 174.485, 174.535, 174.455, 174.445, 174.40, 174.34])


def coast_longitude(lats: np.ndarray) -> np.ndarray:
    """Shoreline longitude for each latitude (land is west of this)."""
    order = np.argsort(_COAST_LATS)
    return np.interp(lats, _COAST_LATS[order], _COAST_LONS[order])


def distance_offshore_km(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Rough east-west distance from the shoreline, negative on land."""
    deg = lon - coast_longitude(lat)
    return deg * 111.320 * np.cos(np.radians(lat))


def land_mask(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """True where a cell centre falls on land."""
    return distance_offshore_km(lat, lon) <= 0.0

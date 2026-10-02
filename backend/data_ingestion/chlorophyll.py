"""Chlorophyll-a ingestion: the missing *spatial* layer.

Temperature fronts tell you where water masses meet; chlorophyll tells you
whether that meeting point has any food in it. A front through two barren
water masses is a nice line on a map and nothing else, which is why this
term belongs in the per-cell score rather than in the bite-window timeline.

Order of preference:
1. Copernicus Marine ocean colour (4 km, gap-free daily, needs the free
   account). Open-Meteo has no chlorophyll variable, so it is not used.
2. ``_synthetic_chlorophyll``, which always succeeds.

Like every other fetcher here, a network or credential failure is logged
and downgraded to synthetic; it never raises.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

import numpy as np

from backend import config
from backend.data_ingestion.coastline import distance_offshore_km
from backend.engine.grid import Grid

log = logging.getLogger(__name__)


@dataclass
class ChlorophyllField:
    chl_mg_m3: np.ndarray
    source: str
    date: dt.date

    @property
    def is_synthetic(self) -> bool:
        return "synthetic" in self.source


def _synthetic_chlorophyll(grid: Grid, date: dt.date) -> np.ndarray:
    """Plausible chlorophyll-a in mg/m^3, shaped like the grid.

    Structured the way Northland water actually behaves: rich and murky in
    close, oligotrophic blue water out past the shelf, with a productive
    band lifting over the Poor Knights ridge.
    """
    lat, lon = grid.mesh
    offshore = distance_offshore_km(lat, lon)
    rng = np.random.default_rng(config.RANDOM_SEED + date.toordinal())

    # Exponential decay offshore: ~2.2 at the beach down to ~0.1 in blue water.
    chl = 0.10 + 2.1 * np.exp(-offshore / 9.0)

    # Upwelling/eddy band lifting productivity over the Poor Knights shelf.
    chl += 0.45 * np.exp(
        -(((lat + 35.47) / 0.07) ** 2 + ((lon - 174.73) / 0.06) ** 2)
    )
    # A second patch behind the shelf break, offset from the SST eddy so the
    # two layers do not simply duplicate each other.
    chl += 0.30 * np.exp(
        -(((lat + 35.68) / 0.06) ** 2 + ((lon - 174.63) / 0.05) ** 2)
    )

    # Spring bloom seasonality (Sep-Nov in NZ waters).
    doy = date.timetuple().tm_yday
    chl *= 1.0 + 0.25 * np.sin(2 * np.pi * (doy - 230) / 365.0)

    chl += rng.normal(0.0, 0.03, size=grid.shape)
    return np.clip(chl, 0.02, config.CHL_CEILING_MG_M3)


def fetch_chlorophyll(grid: Grid, date: dt.date | None = None) -> ChlorophyllField:
    """Chlorophyll-a for ``date``, live if reachable and synthetic otherwise."""
    date = date or dt.date.today()
    if config.USE_LIVE_CHLOROPHYLL:
        from backend.data_ingestion import copernicus

        got = copernicus.fetch_on_grid(
            copernicus.CHL_DATASET_ID, copernicus.CHL_VARIABLE, grid, date, lookback_days=8
        )
        if got is not None:
            chl = np.clip(got[0], 0.0, config.CHL_CEILING_MG_M3)
            return ChlorophyllField(chl, f"copernicus-chl({got[1].isoformat()})", date)
        log.info("No Copernicus chlorophyll; using synthetic")
    return ChlorophyllField(
        _synthetic_chlorophyll(grid, date), "synthetic-mock-chlorophyll", date
    )


def productivity_weight(chl_mg_m3: np.ndarray) -> np.ndarray:
    """Normalise chlorophyll to 0-1 as a *band*, not "more is better".

    1.0 across the ideal band, ramping up from barren blue water below it and
    falling away again through murky bloom water above it.
    """
    lo = config.CHL_IDEAL_MIN_MG_M3
    hi = config.CHL_IDEAL_MAX_MG_M3
    chl = np.nan_to_num(chl_mg_m3, nan=lo)
    out = np.ones_like(chl)

    below = chl < lo
    out[below] = np.clip(chl[below] / max(lo, 1e-6), 0.0, 1.0)

    above = chl > hi
    span = max(config.CHL_CEILING_MG_M3 - hi, 1e-6)
    out[above] = np.clip(1.0 - (chl[above] - hi) / span, 0.15, 1.0)
    return out

"""Chlorophyll-a ingestion: the missing *spatial* layer.

Temperature fronts tell you where water masses meet; chlorophyll tells you
whether that meeting point has any food in it. A front through two barren
water masses is a nice line on a map and nothing else, which is why this
term belongs in the per-cell score rather than in the bite-window timeline.

Order of preference:
1. Open-Meteo Marine ``chlorophyll`` (free, no key), sampled coarsely and
   interpolated onto the grid.
2. Copernicus / NASA OceanColor L3 (needs credentials -- see
   ``TODO_USER_SETUP.md``).
3. ``_synthetic_chlorophyll``, which always succeeds.

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


def _fetch_live(grid: Grid, date: dt.date) -> np.ndarray | None:
    """Coarse sample of Open-Meteo's chlorophyll field, or None on failure."""
    import httpx
    from scipy.interpolate import RegularGridInterpolator

    n = max(config.LIVE_SAMPLE_POINTS, 2)
    lats = np.linspace(grid.bbox.lat_min, grid.bbox.lat_max, n)
    lons = np.linspace(grid.bbox.lon_min, grid.bbox.lon_max, n)
    values = np.full((n, n), np.nan)

    with httpx.Client(timeout=config.OCEAN_FETCH_TIMEOUT_S) as client:
        for i, la in enumerate(lats):
            for j, lo in enumerate(lons):
                resp = client.get(
                    config.OPEN_METEO_MARINE_URL,
                    params={
                        "latitude": round(float(la), 4),
                        "longitude": round(float(lo), 4),
                        "daily": "chlorophyll",
                        "start_date": date.isoformat(),
                        "end_date": date.isoformat(),
                        "timezone": "Pacific/Auckland",
                    },
                )
                resp.raise_for_status()
                series = resp.json().get("daily", {}).get("chlorophyll") or []
                if series and series[0] is not None:
                    values[i, j] = float(series[0])

    if not np.isfinite(values).any():
        return None
    # Land-adjacent sample points come back null; fill them from the mean so
    # the interpolator has a complete corner set.
    values = np.where(np.isfinite(values), values, np.nanmean(values))

    interp = RegularGridInterpolator(
        (lats, lons), values, method="linear", bounds_error=False, fill_value=None
    )
    lat_mesh, lon_mesh = grid.mesh
    points = np.stack([lat_mesh.ravel(), lon_mesh.ravel()], axis=-1)
    return np.clip(interp(points).reshape(grid.shape), 0.0, config.CHL_CEILING_MG_M3)


def fetch_chlorophyll(grid: Grid, date: dt.date | None = None) -> ChlorophyllField:
    """Chlorophyll-a for ``date``, live if reachable and synthetic otherwise."""
    date = date or dt.date.today()
    if config.USE_LIVE_CHLOROPHYLL:
        try:
            live = _fetch_live(grid, date)
            if live is not None:
                return ChlorophyllField(live, "open-meteo-marine-chlorophyll", date)
            log.warning("Chlorophyll fetch returned no usable values; using synthetic")
        except Exception as exc:  # noqa: BLE001 - never fail the daily run
            log.warning("Chlorophyll fetch failed (%s); using synthetic", exc)
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

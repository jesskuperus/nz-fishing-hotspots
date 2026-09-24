"""Ocean data ingestion with an automatic synthetic fallback.

Order of preference:
1. Open-Meteo Marine API (no key required) sampled on a coarse grid and
   interpolated onto the 500 m grid.
2. Copernicus Marine (stubbed — needs credentials; see TODO_USER_SETUP.md).
3. ``mock_ocean_fetcher``, which always succeeds.

Nothing here raises on a network or credential failure: a failed fetch is
logged and the synthetic field is returned instead, with ``source`` on the
result recording what actually happened.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

import numpy as np

from backend import config
from backend.data_ingestion import mock_ocean_fetcher
from backend.engine.grid import Grid

log = logging.getLogger(__name__)


@dataclass
class OceanField:
    sst_c: np.ndarray
    current_u_ms: np.ndarray
    current_v_ms: np.ndarray
    source: str
    date: dt.date

    @property
    def current_speed_ms(self) -> np.ndarray:
        return np.hypot(self.current_u_ms, self.current_v_ms)


def _interpolate_to_grid(
    grid: Grid,
    sample_lats: np.ndarray,
    sample_lons: np.ndarray,
    values: np.ndarray,
) -> np.ndarray:
    """Bilinear-ish interpolation of a coarse sample field onto the grid."""
    from scipy.interpolate import RegularGridInterpolator

    interp = RegularGridInterpolator(
        (sample_lats, sample_lons),
        values,
        method="linear",
        bounds_error=False,
        fill_value=None,
    )
    lat_mesh, lon_mesh = grid.mesh
    points = np.stack([lat_mesh.ravel(), lon_mesh.ravel()], axis=-1)
    return interp(points).reshape(grid.shape)


def _fetch_open_meteo(grid: Grid, date: dt.date) -> OceanField | None:
    """Sample Open-Meteo Marine across the bbox. Returns None on any failure."""
    try:
        import httpx
    except ImportError:
        log.warning("httpx not installed; skipping live ocean fetch")
        return None

    n = max(config.LIVE_SAMPLE_POINTS, 2)
    sample_lats = np.linspace(grid.bbox.lat_min, grid.bbox.lat_max, n)
    sample_lons = np.linspace(grid.bbox.lon_min, grid.bbox.lon_max, n)
    sst = np.full((n, n), np.nan)
    u = np.full((n, n), np.nan)
    v = np.full((n, n), np.nan)

    day = date.isoformat()
    params_common = {
        "daily": "sea_surface_temperature_max,ocean_current_velocity_max,ocean_current_direction_dominant",
        "start_date": day,
        "end_date": day,
        "timezone": "Pacific/Auckland",
    }

    try:
        with httpx.Client(timeout=config.OCEAN_FETCH_TIMEOUT_S) as client:
            for i, lat in enumerate(sample_lats):
                for j, lon in enumerate(sample_lons):
                    params = dict(params_common, latitude=float(lat), longitude=float(lon))
                    resp = client.get(config.OPEN_METEO_MARINE_URL, params=params)
                    if resp.status_code != 200:
                        log.info(
                            "Open-Meteo returned %s for %.3f,%.3f", resp.status_code, lat, lon
                        )
                        continue
                    daily = resp.json().get("daily", {})
                    sst[i, j] = _first(daily.get("sea_surface_temperature_max"))
                    speed = _first(daily.get("ocean_current_velocity_max"))
                    bearing = _first(daily.get("ocean_current_direction_dominant"))
                    if not np.isnan(speed) and not np.isnan(bearing):
                        # Open-Meteo reports km/h and the direction the water
                        # flows towards, in compass degrees.
                        ms = speed / 3.6
                        rad = np.radians(bearing)
                        u[i, j] = ms * np.sin(rad)
                        v[i, j] = ms * np.cos(rad)
    except Exception as exc:  # network, DNS, TLS, JSON — all non-fatal here
        log.warning("Live ocean fetch failed (%s); falling back to synthetic", exc)
        return None

    # Open-Meteo has no data over land, so partial coverage is expected;
    # anything below half coverage is not worth interpolating.
    if np.count_nonzero(~np.isnan(sst)) < sst.size / 2:
        log.warning("Live ocean fetch too sparse (%d/%d points)", np.count_nonzero(~np.isnan(sst)), sst.size)
        return None

    sst = _fill_nan(sst)
    u = _fill_nan(u)
    v = _fill_nan(v)

    doy = date.timetuple().tm_yday
    # The API grid is far coarser than 500 m, so the interpolated field has
    # no mesoscale structure. Blend in the synthetic front texture as an
    # anomaly on top of the real large-scale field, keeping the real mean.
    synth = mock_ocean_fetcher.generate_sst(grid, doy)
    sst_grid = _interpolate_to_grid(grid, sample_lats, sample_lons, sst)
    sst_grid = sst_grid + (synth - synth.mean()) * 0.6

    return OceanField(
        sst_c=sst_grid,
        current_u_ms=_interpolate_to_grid(grid, sample_lats, sample_lons, u),
        current_v_ms=_interpolate_to_grid(grid, sample_lats, sample_lons, v),
        source="open-meteo-marine+synthetic-mesoscale",
        date=date,
    )


def _fetch_copernicus(grid: Grid, date: dt.date) -> OceanField | None:
    """Copernicus Marine stub. Returns None until credentials are configured."""
    if not (config.COPERNICUS_USERNAME and config.COPERNICUS_PASSWORD):
        return None
    try:
        import copernicusmarine  # type: ignore  # noqa: F401
    except ImportError:
        log.warning(
            "Copernicus credentials set but the copernicusmarine package is "
            "not installed; see TODO_USER_SETUP.md"
        )
        return None
    # Intentionally not implemented in the MVP: wiring the real subset call
    # needs a dataset ID and an authenticated session. See TODO_USER_SETUP.md.
    log.info("Copernicus ingestion not implemented yet; using next source")
    return None


def _first(values) -> float:
    if not values:
        return float("nan")
    value = values[0]
    return float("nan") if value is None else float(value)


def _fill_nan(arr: np.ndarray) -> np.ndarray:
    """Replace NaNs with the array mean so interpolation stays defined."""
    out = arr.copy()
    mask = np.isnan(out)
    if mask.all():
        return np.zeros_like(out)
    out[mask] = np.nanmean(out)
    return out


def fetch_ocean_field(grid: Grid, date: dt.date | None = None) -> OceanField:
    """Best available SST/current field for ``date``. Never raises."""
    date = date or dt.date.today()
    if config.USE_LIVE_OCEAN_DATA:
        for fetch in (_fetch_copernicus, _fetch_open_meteo):
            field = fetch(grid, date)
            if field is not None:
                log.info("Ocean data source: %s", field.source)
                return field
    else:
        log.info("USE_LIVE_OCEAN_DATA is off; using synthetic ocean field")

    doy = date.timetuple().tm_yday
    u, v = mock_ocean_fetcher.generate_currents(grid, doy)
    return OceanField(
        sst_c=mock_ocean_fetcher.generate_sst(grid, doy),
        current_u_ms=u,
        current_v_ms=v,
        source="synthetic-mock",
        date=date,
    )

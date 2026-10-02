"""Ocean data ingestion with an automatic synthetic fallback.

Order of preference:
1. Open-Meteo Marine API (no key required) sampled on a coarse grid and
   interpolated onto the 500 m grid.
2. Copernicus Marine satellite SST replaces the temperature field when
   credentials are set (see copernicus.py).
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
    # The marine API has no daily current variables, so ask for hourly values
    # and average them over the NZ day.
    params_common = {
        "hourly": "sea_surface_temperature,ocean_current_velocity,ocean_current_direction",
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
                    hourly = resp.json().get("hourly", {})
                    sst[i, j] = _mean(hourly.get("sea_surface_temperature"))
                    speeds = _series(hourly.get("ocean_current_velocity"))
                    bearings = _series(hourly.get("ocean_current_direction"))
                    ok = ~np.isnan(speeds) & ~np.isnan(bearings)
                    if ok.any():
                        # Open-Meteo reports km/h and the direction the water
                        # flows towards, in compass degrees. Average the
                        # hourly vectors, not the angles.
                        ms = speeds[ok] / 3.6
                        rad = np.radians(bearings[ok])
                        u[i, j] = float(np.mean(ms * np.sin(rad)))
                        v[i, j] = float(np.mean(ms * np.cos(rad)))
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

    # The API grid is far coarser than 500 m, so the interpolated field is
    # smooth and will show few real fronts. That is left as is: no invented
    # texture is blended in. Copernicus (finer satellite SST) is the fix.
    sst_grid = _interpolate_to_grid(grid, sample_lats, sample_lons, sst)

    return OceanField(
        sst_c=sst_grid,
        current_u_ms=_interpolate_to_grid(grid, sample_lats, sample_lons, u),
        current_v_ms=_interpolate_to_grid(grid, sample_lats, sample_lons, v),
        source="open-meteo-marine",
        date=date,
    )


def _fetch_copernicus_sst(grid: Grid, date: dt.date):
    """Satellite SST (OSTIA, ~5 km) from Copernicus Marine, or None."""
    from backend.data_ingestion import copernicus

    got = copernicus.fetch_on_grid(
        copernicus.SST_DATASET_ID, copernicus.SST_VARIABLE, grid, date
    )
    if got is None:
        return None
    kelvin, data_date = got
    return kelvin - 273.15, data_date


def _series(values) -> np.ndarray:
    if not values:
        return np.array([np.nan])
    return np.array([np.nan if v is None else float(v) for v in values], dtype="float64")


def _mean(values) -> float:
    arr = _series(values)
    return float("nan") if np.isnan(arr).all() else float(np.nanmean(arr))


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
        field = _fetch_open_meteo(grid, date)
        if field is not None:
            sst = _fetch_copernicus_sst(grid, date)
            if sst is not None:
                # Satellite SST is the better temperature field; Open-Meteo
                # still supplies currents (Copernicus SST has none).
                field.sst_c = sst[0]
                field.source = f"copernicus-sst({sst[1].isoformat()})+open-meteo-currents"
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

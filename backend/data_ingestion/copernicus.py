"""Copernicus Marine subsets, resampled onto the scoring grid.

Needs COPERNICUS_USERNAME and COPERNICUS_PASSWORD (free account) and the
``copernicusmarine`` package. Every failure returns None so callers can fall
back; nothing here raises.
"""

from __future__ import annotations

import datetime as dt
import logging
import tempfile
from pathlib import Path

import numpy as np

from backend import config
from backend.engine.grid import Grid

log = logging.getLogger(__name__)

SST_DATASET_ID = "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2"  # OSTIA, ~5 km, daily
SST_VARIABLE = "analysed_sst"  # kelvin
CHL_DATASET_ID = "cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D"
CHL_VARIABLE = "CHL"  # mg/m3


def available() -> bool:
    return bool(config.COPERNICUS_USERNAME and config.COPERNICUS_PASSWORD)


def fetch_on_grid(
    dataset_id: str,
    variable: str,
    grid: Grid,
    date: dt.date,
    lookback_days: int = 5,
) -> tuple[np.ndarray, dt.date] | None:
    """Latest available day at or before ``date``, interpolated to ``grid``.

    Returns (values, data_date) or None. Near-real-time products lag by one
    to a few days, so the newest time step in the window is used.
    """
    if not available():
        return None
    try:
        import copernicusmarine  # type: ignore
        import xarray as xr
        from scipy.interpolate import RegularGridInterpolator
    except ImportError:
        log.warning("copernicusmarine/xarray not installed; skipping %s", dataset_id)
        return None

    pad = 0.25
    try:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "subset.nc"
            copernicusmarine.subset(
                dataset_id=dataset_id,
                variables=[variable],
                minimum_longitude=grid.bbox.lon_min - pad,
                maximum_longitude=grid.bbox.lon_max + pad,
                minimum_latitude=grid.bbox.lat_min - pad,
                maximum_latitude=grid.bbox.lat_max + pad,
                start_datetime=(date - dt.timedelta(days=lookback_days)).isoformat() + "T00:00:00",
                end_datetime=date.isoformat() + "T23:59:59",
                username=config.COPERNICUS_USERNAME,
                password=config.COPERNICUS_PASSWORD,
                output_filename=str(out),
                overwrite=True,
                disable_progress_bar=True,
            )
            ds = xr.open_dataset(out).load()
    except Exception as exc:  # noqa: BLE001 - never fail the daily run
        log.warning("Copernicus subset %s failed (%s)", dataset_id, exc)
        return None

    # Newest time step that actually has water values.
    for k in range(ds.sizes["time"] - 1, -1, -1):
        frame = ds[variable].isel(time=k)
        if int(frame.notnull().sum()) >= 4:
            break
    else:
        log.warning("Copernicus %s returned no usable values", dataset_id)
        return None

    data_date = np.datetime_as_string(ds.time.values[k], unit="D")
    lats = frame["latitude"].values
    lons = frame["longitude"].values
    vals = frame.values.astype("float64")
    # Land / cloud gaps: fill with the mean so interpolation stays defined.
    vals = np.where(np.isfinite(vals), vals, np.nanmean(vals))
    interp = RegularGridInterpolator(
        (lats, lons), vals, method="linear", bounds_error=False, fill_value=None
    )
    lat_mesh, lon_mesh = grid.mesh
    pts = np.stack([lat_mesh.ravel(), lon_mesh.ravel()], axis=-1)
    return interp(pts).reshape(grid.shape), dt.date.fromisoformat(data_date)

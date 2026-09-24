"""Bathymetry ingestion: local LINZ raster if present, synthetic otherwise.

Supply a depth raster (GeoTIFF) via ``LINZ_BATHYMETRY_FILE`` or drop one in
``data/bathymetry/``. Anything unreadable falls back to
``mock_bathymetry`` rather than failing the run.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from backend import config
from backend.data_ingestion import mock_bathymetry
from backend.data_ingestion.coastline import land_mask
from backend.engine.grid import Grid

log = logging.getLogger(__name__)

RASTER_SUFFIXES = (".tif", ".tiff", ".nc", ".asc", ".vrt")


@dataclass
class BathymetryField:
    depth_m: np.ndarray  # positive metres below datum, NaN on land
    source: str


def _find_local_raster() -> Path | None:
    if config.LINZ_BATHYMETRY_FILE:
        candidate = Path(config.LINZ_BATHYMETRY_FILE).expanduser()
        if candidate.is_file():
            return candidate
        log.warning("LINZ_BATHYMETRY_FILE=%s not found", candidate)
    if config.BATHYMETRY_DIR.is_dir():
        for path in sorted(config.BATHYMETRY_DIR.iterdir()):
            if path.suffix.lower() in RASTER_SUFFIXES:
                return path
    return None


def _sample_raster(path: Path, grid: Grid) -> np.ndarray | None:
    """Sample a depth raster at every cell centre. None if unreadable."""
    try:
        import rasterio
        from rasterio.warp import transform as warp_transform
    except ImportError:
        log.warning("rasterio not installed; cannot read %s", path.name)
        return None

    try:
        with rasterio.open(path) as src:
            lat_mesh, lon_mesh = grid.mesh
            xs, ys = lon_mesh.ravel(), lat_mesh.ravel()
            if src.crs and src.crs.to_epsg() != 4326:
                xs, ys = warp_transform("EPSG:4326", src.crs, list(xs), list(ys))
            samples = np.array(
                [v[0] for v in src.sample(zip(xs, ys))], dtype="float64"
            ).reshape(grid.shape)
            if src.nodata is not None:
                samples[samples == src.nodata] = np.nan
    except Exception as exc:
        log.warning("Failed to read bathymetry raster %s (%s)", path, exc)
        return None

    # LINZ and GEBCO publish elevation (negative below sea level); flip to
    # positive depth when that is clearly the convention in use.
    finite = samples[np.isfinite(samples)]
    if finite.size and np.nanmedian(finite) < 0:
        samples = -samples
    samples[samples <= 0] = np.nan

    coverage = np.count_nonzero(np.isfinite(samples)) / samples.size
    if coverage < 0.25:
        log.warning(
            "Raster %s covers only %.0f%% of the bbox; using synthetic instead",
            path.name,
            coverage * 100,
        )
        return None
    return samples


def load_bathymetry(grid: Grid) -> BathymetryField:
    """Best available depth field. Never raises."""
    path = _find_local_raster()
    if path is not None:
        samples = _sample_raster(path, grid)
        if samples is not None:
            synthetic = mock_bathymetry.generate_bathymetry(grid)
            # Patch any raster holes with the synthetic surface so the slope
            # calculation does not produce NaN islands mid-shelf.
            holes = ~np.isfinite(samples)
            lat_mesh, lon_mesh = grid.mesh
            holes &= ~land_mask(lat_mesh, lon_mesh)
            samples[holes] = synthetic[holes]
            return BathymetryField(depth_m=samples, source=f"raster:{path.name}")

    log.info("No usable bathymetry raster; using synthetic Tutukaka shelf model")
    return BathymetryField(
        depth_m=mock_bathymetry.generate_bathymetry(grid),
        source="synthetic-mock",
    )

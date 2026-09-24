#!/usr/bin/env python3
"""Download a real depth grid, so the seabed stops being a guess.

The synthetic seabed is the weakest layer in the whole engine: it is a
plausible-looking shelf, not a survey, and half the score depends on its
slope. This fetches a real one into ``data/bathymetry/``, where
``bathymetry_loader`` picks it up automatically on the next run.

    python scripts/fetch_bathymetry.py                # GEBCO, no account
    python scripts/fetch_bathymetry.py --source gebco --out data/bathymetry

GEBCO 2024 is a global 15-arc-second grid (~450 m at this latitude), which
is about the resolution of the map. For anything finer, NIWA and LINZ
publish multibeam surveys of the Northland shelf -- those need an account,
so they stay a manual step documented in TODO_USER_SETUP.md.

NEITHER IS A NAVIGATION CHART. Depths here are for deciding where to fish,
never for deciding where it is safe to drive a boat.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend import config  # noqa: E402

# GEBCO's WCS endpoint returns a GeoTIFF subset for a bounding box with no
# account and no key.
GEBCO_WCS = "https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/mapserv"
GEBCO_WCS_PARAMS = {
    "request": "getmap",
    "service": "wms",
    "version": "1.3.0",
    "layers": "GEBCO_LATEST",
    "format": "image/geotiff",
    "crs": "EPSG:4326",
    "width": "1200",
    "height": "1000",
}


def fetch_gebco(out_dir: Path, timeout: float = 120.0) -> Path:
    import httpx

    bbox = config.BBOX
    params = dict(GEBCO_WCS_PARAMS)
    # WMS 1.3.0 with EPSG:4326 takes bbox as lat,lon order.
    params["bbox"] = f"{bbox.lat_min},{bbox.lon_min},{bbox.lat_max},{bbox.lon_max}"

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "gebco_northland.tif"
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(GEBCO_WCS, params=params)
        resp.raise_for_status()
        if len(resp.content) < 10_000:
            raise ValueError(
                f"response was only {len(resp.content)} bytes - that is an error "
                "page, not a raster"
            )
        target.write_bytes(resp.content)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch real bathymetry")
    parser.add_argument("--source", choices=["gebco"], default="gebco")
    parser.add_argument("--out", default=str(config.BATHYMETRY_DIR))
    args = parser.parse_args(argv)

    try:
        path = fetch_gebco(Path(args.out))
    except Exception as exc:  # noqa: BLE001 - this is an optional upgrade
        print(f"Bathymetry download failed: {exc}")
        print(
            "The pipeline still runs on the synthetic seabed. Retry later, or "
            "drop a GeoTIFF into data/bathymetry/ by hand."
        )
        return 1

    size_mb = path.stat().st_size / 1e6
    print(f"Saved {path} ({size_mb:.1f} MB)")
    print("Next run picks it up automatically. Needs: pip install rasterio")
    return 0


if __name__ == "__main__":
    sys.exit(main())

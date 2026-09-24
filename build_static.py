#!/usr/bin/env python3
"""Generate the static payload the phone-friendly map reads.

Writes public/hotspots_today.geojson, which Vercel serves from the same
origin as public/index.html, so the map needs no API server.

    python build_static.py                  # 1 km grid, whole bbox
    python build_static.py --resolution 500 # finer, ~4x the file size
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from pathlib import Path

from backend.engine.pipeline import run_pipeline

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = REPO_ROOT / "public" / "hotspots_today.geojson"

# 500 m, the spec resolution: ~6 MB on disk but ~640 KB gzipped over the
# wire, which is fine on mobile data. A 1 km grid would be a quarter the
# size but smears the thermal fronts out below the 0.5 degC/km threshold,
# which loses the single most useful layer on the map.
DEFAULT_RESOLUTION_M = 500.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the static hotspot map data")
    parser.add_argument("--date", help="ISO date (YYYY-MM-DD), default today NZ")
    parser.add_argument("--resolution", type=float, default=DEFAULT_RESOLUTION_M)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    date = dt.date.fromisoformat(args.date) if args.date else _today_nz()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    result = run_pipeline(date=date, resolution_m=args.resolution, output_path=output)

    meta = result.metadata
    size_mb = output.stat().st_size / 1e6
    print(json.dumps(
        {
            "date": meta["date"],
            "cells": result.cells_scored,
            "sources": meta["sources"],
            "score_max": meta["score_stats"]["max"],
            "thermal_front_cells": meta["thermal_front_cells"],
            "output": str(output),
            "size_mb": round(size_mb, 2),
        },
        indent=2,
    ))
    return 0


def _today_nz() -> dt.date:
    """Today in NZ, so a run just after UTC midnight isn't a day behind."""
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=12)).date()


if __name__ == "__main__":
    sys.exit(main())

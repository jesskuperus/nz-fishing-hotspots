#!/usr/bin/env python3
"""CLI entry point: run the hotspot engine once and write the GeoJSON.

    python run_engine.py                    # today, 500 m grid
    python run_engine.py --date 2026-10-01 --resolution 1000 --min-score 40
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys

from backend.engine.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NZ marine hotspot engine")
    parser.add_argument("--date", help="ISO date (YYYY-MM-DD), default today")
    parser.add_argument(
        "--resolution", type=float, help="Grid cell size in metres (default 500)"
    )
    parser.add_argument(
        "--min-score", type=float, default=0.0, help="Drop cells below this score"
    )
    parser.add_argument("--output", help="Output GeoJSON path")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    result = run_pipeline(
        date=date,
        resolution_m=args.resolution,
        min_score=args.min_score,
        output_path=args.output,
    )

    meta = result.metadata
    print(json.dumps(
        {
            "date": meta["date"],
            "cells_scored": result.cells_scored,
            "grid": meta["grid"],
            "sources": meta["sources"],
            "score_stats": meta["score_stats"],
            "sst_range_c": meta["sst_range_c"],
            "depth_range_m": meta["depth_range_m"],
            "thermal_front_cells": meta["thermal_front_cells"],
            "output": str(result.path),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())

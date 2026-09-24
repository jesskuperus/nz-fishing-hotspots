#!/usr/bin/env python3
"""Log a trip against the score the engine gave that spot.

    python scripts/log_catch.py --lat -35.47 --lon 174.74 \
        --species snapper --fish 4 --hours 3 --notes "incoming tide, 40m"

The score is looked up from the day's run so you never have to read it off
the map yourself -- which matters, because a score you typed in from memory
is exactly the kind of data that would make the calibration worse.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend import config  # noqa: E402
from backend.calibration.catch_log import CatchEntry, append_entry  # noqa: E402


def score_at(lat: float, lon: float, geojson_path: Path) -> float | None:
    """Nearest scored cell to a position, or None if the run is missing."""
    if not geojson_path.exists():
        return None
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    best, best_d2 = None, float("inf")
    for feature in data.get("features", []):
        props = feature["properties"]
        d2 = (props["lat"] - lat) ** 2 + (props["lon"] - lon) ** 2
        if d2 < best_d2:
            best, best_d2 = props.get("hotspot_score"), d2
    # ~0.02 deg is about 2 km; further than that and the "nearest cell" is
    # not describing where you fished.
    return best if best_d2 <= 0.02**2 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Log a fishing trip")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--date", help="ISO date, default today NZ")
    parser.add_argument("--species", default="")
    parser.add_argument("--fish", type=int, default=0)
    parser.add_argument("--hours", type=float, default=0.0)
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--geojson",
        default=str(REPO_ROOT / "public" / "hotspots_today.geojson"),
        help="Run to read the cell score from",
    )
    args = parser.parse_args(argv)

    date = (
        dt.date.fromisoformat(args.date)
        if args.date
        else (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=12)).date()
    )
    score = score_at(args.lat, args.lon, Path(args.geojson))
    entry = CatchEntry(
        date=date.isoformat(),
        lat=args.lat,
        lon=args.lon,
        species=args.species,
        fish_count=args.fish,
        hours_fished=args.hours,
        hotspot_score=score,
        notes=args.notes,
    )
    path = append_entry(entry, config.CATCH_LOG_PATH)
    print(
        json.dumps(
            {
                "logged": entry.date,
                "position": [entry.lat, entry.lon],
                "hotspot_score": score,
                "catch_rate_per_hour": round(entry.catch_rate, 2),
                "log": str(path),
            },
            indent=2,
        )
    )
    if score is None:
        print("note: no scored cell within ~2 km, so this row has no score to fit against")
    return 0


if __name__ == "__main__":
    sys.exit(main())

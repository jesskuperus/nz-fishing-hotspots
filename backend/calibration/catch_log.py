"""A plain CSV catch log -- the one input that could make this tool accurate.

Everything else in this repo is a physical model with weights someone
guessed (including me). A row per trip is what turns those guesses into
something testable: score the mark you fished, record what you caught, and
``scripts/calibrate.py`` can eventually fit the weights to your water
instead of to the brief.

CSV, not a database, on purpose: it opens in Numbers on a phone and syncs
through any folder.
"""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from backend import config

FIELDNAMES = [
    "date",
    "lat",
    "lon",
    "species",
    "fish_count",
    "hours_fished",
    "hotspot_score",
    "notes",
]


@dataclass
class CatchEntry:
    date: str
    lat: float
    lon: float
    species: str = ""
    fish_count: int = 0
    hours_fished: float = 0.0
    hotspot_score: float | None = None
    notes: str = ""

    @property
    def catch_rate(self) -> float:
        """Fish per hour -- the number worth regressing the score against."""
        return self.fish_count / self.hours_fished if self.hours_fished > 0 else 0.0


def _path(path: Path | None = None) -> Path:
    return Path(path or config.CATCH_LOG_PATH)


def append_entry(entry: CatchEntry, path: Path | None = None) -> Path:
    """Add one trip to the log, creating the file with a header if needed."""
    target = _path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    is_new = not target.exists()
    with target.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow(asdict(entry))
    return target


def load_entries(path: Path | None = None) -> list[CatchEntry]:
    """Read the log back, skipping rows that are too broken to use."""
    target = _path(path)
    if not target.exists():
        return []

    known = {f.name for f in fields(CatchEntry)}
    out: list[CatchEntry] = []
    with target.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row = {k: v for k, v in row.items() if k in known}
            try:
                out.append(
                    CatchEntry(
                        date=row["date"],
                        lat=float(row["lat"]),
                        lon=float(row["lon"]),
                        species=row.get("species", ""),
                        fish_count=int(float(row.get("fish_count") or 0)),
                        hours_fished=float(row.get("hours_fished") or 0.0),
                        hotspot_score=(
                            float(row["hotspot_score"])
                            if row.get("hotspot_score")
                            else None
                        ),
                        notes=row.get("notes", ""),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
    return out


def entry_from_args(
    date: dt.date, lat: float, lon: float, **kwargs
) -> CatchEntry:
    return CatchEntry(date=date.isoformat(), lat=lat, lon=lon, **kwargs)

#!/usr/bin/env python3
"""No cell inside a no-take marine reserve may ever be scored."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("USE_LIVE_OCEAN_DATA", "false")
os.environ.setdefault("USE_LIVE_CHLOROPHYLL", "false")
os.environ.setdefault("USE_LIVE_WEATHER", "false")

from shapely.geometry import Point, shape  # noqa: E402

from backend.engine import reserves  # noqa: E402
from backend.engine.pipeline import run_pipeline  # noqa: E402


def test_poor_knights_is_listed():
    assert "Poor Knights Islands Marine Reserve" in reserves.reserve_names()


def test_no_scored_cell_inside_a_reserve():
    result = run_pipeline(write=False)
    geom = reserves.reserve_geometry()
    inside = [
        f["properties"]["cell_id"]
        for f in result.geojson["features"]
        if geom.intersects(shape(f["geometry"]))
    ]
    assert not inside, f"{len(inside)} cells inside a no-take reserve: {inside[:5]}"


if __name__ == "__main__":
    test_poor_knights_is_listed()
    test_no_scored_cell_inside_a_reserve()
    print("reserve checks passed")

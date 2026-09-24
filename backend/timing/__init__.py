"""Temporal layer: when to go, as opposed to where.

Tide, moon and daylight shift every cell on the map by the same factor, so
they are kept out of the per-cell hotspot score and surfaced as an hourly
bite-window timeline instead.
"""

from backend.timing.astronomy import light_factor, moon_phase, sun_times
from backend.timing.tide import fetch_tide
from backend.timing.windows import build_windows

__all__ = ["build_windows", "fetch_tide", "light_factor", "moon_phase", "sun_times"]

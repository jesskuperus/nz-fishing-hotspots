"""Hourly tide height and, more usefully, how fast the tide is moving.

Fish on structure feed on run, not on slack water, so the signal that
matters is |d(height)/dt| rather than the height itself.

Source: Open-Meteo Marine's `sea_level_height_msl` (free, no key). If that
is unreachable, a synthetic semi-diurnal harmonic keeps the timeline
populated — it has the right ~12.42 h rhythm but NOT the right phase for
your coast, so it is badged as synthetic and must not be used to plan a
real trip.
"""

from __future__ import annotations

import datetime as dt
import logging
import math

from backend import config

log = logging.getLogger(__name__)

M2_PERIOD_HOURS = 12.4206  # the principal lunar semi-diurnal constituent


def _synthetic_tide(date: dt.date, hours: int = 24) -> list[float]:
    """A plain M2 harmonic. Right rhythm, arbitrary phase."""
    # Anchor the phase to the date so successive days advance realistically
    # (each day's tide runs ~50 minutes later).
    day_number = date.toordinal()
    phase = (day_number * 24 / M2_PERIOD_HOURS) % 1.0
    return [
        round(1.0 * math.sin(2 * math.pi * ((h / M2_PERIOD_HOURS) + phase)), 3)
        for h in range(hours)
    ]


def fetch_tide(date: dt.date, lat: float, lon: float) -> dict:
    """24 hourly sea levels (m) plus movement rate. Never raises."""
    heights: list[float] | None = None
    source = "synthetic-harmonic"

    if config.USE_LIVE_OCEAN_DATA:
        try:
            import httpx

            with httpx.Client(timeout=config.OCEAN_FETCH_TIMEOUT_S) as client:
                resp = client.get(
                    config.OPEN_METEO_MARINE_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "hourly": "sea_level_height_msl",
                        "start_date": date.isoformat(),
                        "end_date": date.isoformat(),
                        "timezone": "UTC",
                    },
                )
                if resp.status_code == 200:
                    values = resp.json().get("hourly", {}).get("sea_level_height_msl")
                    if values and any(v is not None for v in values):
                        heights = [float(v) if v is not None else 0.0 for v in values]
                        source = "open-meteo-marine"
                else:
                    log.info("Tide fetch returned %s", resp.status_code)
        except Exception as exc:
            log.warning("Tide fetch failed (%s); using synthetic harmonic", exc)

    if heights is None:
        heights = _synthetic_tide(date)

    # Movement rate: central difference in metres per hour, normalised so
    # the day's strongest run is 1.0.
    rates = []
    for i in range(len(heights)):
        lo = heights[max(i - 1, 0)]
        hi = heights[min(i + 1, len(heights) - 1)]
        span = min(i + 1, len(heights) - 1) - max(i - 1, 0)
        rates.append(abs(hi - lo) / max(span, 1))
    peak = max(rates) or 1.0
    movement = [round(r / peak, 3) for r in rates]

    return {
        "source": source,
        "is_synthetic": source == "synthetic-harmonic",
        "heights_m": [round(h, 3) for h in heights],
        "movement": movement,
        "range_m": round(max(heights) - min(heights), 2),
    }

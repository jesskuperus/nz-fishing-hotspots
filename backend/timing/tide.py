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


def fetch_tide_extremes(date: dt.date, lat: float, lon: float, days: int = 3) -> dict:
    """High and low water times (NZ local) for ``days`` days from ``date``.

    Built from the same Open-Meteo modelled sea level as the hourly series,
    requested in NZ time. Heights are metres relative to mean sea level, from
    a coarse global model, so this is a guide and not a tide table.
    Returns {"source", "days": [[{type,time,height_m}, ...], ...]} and an
    empty ``days`` list if the live request fails (nothing is invented).
    """
    out = {"source": "open-meteo-marine", "days": []}
    if not config.USE_LIVE_OCEAN_DATA:
        return {"source": "unavailable", "days": []}
    try:
        import httpx

        end = date + dt.timedelta(days=days)  # one extra day so day-end peaks resolve
        with httpx.Client(timeout=config.OCEAN_FETCH_TIMEOUT_S) as client:
            resp = client.get(
                config.OPEN_METEO_MARINE_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "sea_level_height_msl",
                    "start_date": date.isoformat(),
                    "end_date": end.isoformat(),
                    "timezone": "Pacific/Auckland",
                },
            )
        if resp.status_code != 200:
            log.info("Tide extremes fetch returned %s", resp.status_code)
            return {"source": "unavailable", "days": []}
        hourly = resp.json().get("hourly", {})
        times = hourly.get("time") or []
        vals = hourly.get("sea_level_height_msl") or []
        series = [
            (dt.datetime.fromisoformat(t), float(v))
            for t, v in zip(times, vals)
            if v is not None
        ]
    except Exception as exc:
        log.warning("Tide extremes fetch failed (%s)", exc)
        return {"source": "unavailable", "days": []}

    per_day: dict[dt.date, list[dict]] = {date + dt.timedelta(days=i): [] for i in range(days)}
    for i in range(1, len(series) - 1):
        t, h = series[i]
        prev_h, next_h = series[i - 1][1], series[i + 1][1]
        kind = None
        if h > prev_h and h >= next_h:
            kind = "High"
        elif h < prev_h and h <= next_h:
            kind = "Low"
        if kind is None:
            continue
        # Parabolic refinement of the peak time and height.
        denom = prev_h - 2 * h + next_h
        shift = 0.0 if abs(denom) < 1e-9 else 0.5 * (prev_h - next_h) / denom
        shift = max(-0.5, min(0.5, shift))
        peak_t = t + dt.timedelta(hours=shift)
        peak_h = h - 0.25 * (prev_h - next_h) * shift
        if peak_t.date() in per_day:
            per_day[peak_t.date()].append(
                {
                    "type": kind,
                    "time": peak_t.strftime("%H:%M"),
                    "height_m": round(peak_h, 2),
                }
            )
    out["days"] = [per_day[d] for d in sorted(per_day)]
    return out

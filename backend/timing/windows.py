"""Bite windows: when to go, as opposed to where.

Tide movement, moon phase and the light at dawn and dusk shift every cell
on the map by the same amount, so folding them into the per-cell score
would not change which ground ranks highest — it would only inflate the
numbers. They belong on a timeline instead.

    Bite score = (tide movement x 0.5) + (light x 0.35) + (moon x 0.15)
"""

from __future__ import annotations

import datetime as dt

from backend import config
from backend.timing import astronomy, tide as tide_mod

NZ = dt.timezone(dt.timedelta(hours=12))  # NZST; NZDT shifts labels by an hour


def build_windows(date: dt.date, lat: float, lon: float) -> dict:
    """Hour-by-hour bite score for the day, plus the day's best windows."""
    tide = tide_mod.fetch_tide(date, lat, lon)
    moon = astronomy.moon_phase(
        dt.datetime(date.year, date.month, date.day, 12, tzinfo=dt.timezone.utc)
    )
    sun = astronomy.sun_times(date, lat, lon)

    # Spring tides move more water, so the moon enters as a day-level
    # multiplier rather than an hourly one.
    moon_factor = 1.0 if moon["is_spring_tide"] else 0.55

    hours = []
    for hour in range(24):
        when = dt.datetime(
            date.year, date.month, date.day, hour, tzinfo=dt.timezone.utc
        )
        light = astronomy.light_factor(when, sun["sunrise"], sun["sunset"])
        movement = tide["movement"][hour] if hour < len(tide["movement"]) else 0.0
        score = (
            movement * config.WEIGHT_TIDE_MOVEMENT
            + light * config.WEIGHT_LIGHT
            + moon_factor * config.WEIGHT_MOON
        ) * 100
        hours.append(
            {
                "utc_hour": hour,
                "local": when.astimezone(NZ).strftime("%H:%M"),
                "bite_score": round(score, 1),
                "tide_movement": movement,
                "light": light,
            }
        )

    ranked = sorted(hours, key=lambda h: -h["bite_score"])
    return {
        "date": date.isoformat(),
        "tide": {k: v for k, v in tide.items() if k != "heights_m"},
        "tide_heights_m": tide["heights_m"],
        "moon": moon,
        "sunrise_local": sun["sunrise"].astimezone(NZ).strftime("%H:%M") if sun["sunrise"] else None,
        "sunset_local": sun["sunset"].astimezone(NZ).strftime("%H:%M") if sun["sunset"] else None,
        "hours": hours,
        "best_hours": [
            {"local": h["local"], "bite_score": h["bite_score"]} for h in ranked[:4]
        ],
        "weights": {
            "tide_movement": config.WEIGHT_TIDE_MOVEMENT,
            "light": config.WEIGHT_LIGHT,
            "moon": config.WEIGHT_MOON,
        },
    }

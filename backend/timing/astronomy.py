"""Sun and moon positions, computed offline.

No API, no key, no network: these are deterministic astronomical formulae,
so the bite-window layer works on a boat with no signal. Accuracy is about
a minute for sunrise/sunset and a few hours of phase age for the moon,
which is far finer than the fishing decisions built on top of them.

Formulae follow the standard low-precision solar position algorithm
(NOAA) and a simple mean-phase lunar model.
"""

from __future__ import annotations

import datetime as dt
import math

SYNODIC_MONTH_DAYS = 29.530588853
# A known new moon: 2000-01-06 18:14 UTC.
_KNOWN_NEW_MOON = dt.datetime(2000, 1, 6, 18, 14, tzinfo=dt.timezone.utc)


def _julian_day(when: dt.datetime) -> float:
    when = when.astimezone(dt.timezone.utc)
    y, m = when.year, when.month
    d = (
        when.day
        + (when.hour + when.minute / 60 + when.second / 3600) / 24
    )
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def moon_phase(when: dt.datetime) -> dict:
    """Illuminated fraction, phase age in days, and a readable name."""
    age_days = (
        (when.astimezone(dt.timezone.utc) - _KNOWN_NEW_MOON).total_seconds()
        / 86400.0
    ) % SYNODIC_MONTH_DAYS
    # Illumination follows the phase angle; 0 at new, 1 at full.
    illumination = (1 - math.cos(2 * math.pi * age_days / SYNODIC_MONTH_DAYS)) / 2

    names = [
        (1.85, "new"), (5.54, "waxing crescent"), (9.23, "first quarter"),
        (12.92, "waxing gibbous"), (16.61, "full"), (20.31, "waning gibbous"),
        (24.00, "last quarter"), (27.69, "waning crescent"),
    ]
    name = "new"
    for edge, label in names:
        if age_days <= edge:
            name = label
            break

    return {
        "age_days": round(age_days, 2),
        "illumination": round(illumination, 3),
        "phase": name,
        # New and full moons bring the biggest tidal range (spring tides),
        # which is the part fishers actually plan around.
        "is_spring_tide": bool(age_days < 2.5 or abs(age_days - 14.77) < 2.5),
    }


def _solar_declination_and_eot(jd: float) -> tuple[float, float]:
    """Solar declination (radians) and the equation of time (minutes)."""
    n = jd - 2451545.0
    mean_long = math.radians((280.460 + 0.9856474 * n) % 360)
    mean_anom = math.radians((357.528 + 0.9856003 * n) % 360)
    ecliptic_long = mean_long + math.radians(
        1.915 * math.sin(mean_anom) + 0.020 * math.sin(2 * mean_anom)
    )
    obliquity = math.radians(23.439 - 0.0000004 * n)
    declination = math.asin(math.sin(obliquity) * math.sin(ecliptic_long))

    y = math.tan(obliquity / 2) ** 2
    eot = 4 * math.degrees(
        y * math.sin(2 * mean_long)
        - 2 * 0.0167 * math.sin(mean_anom)
        + 4 * 0.0167 * y * math.sin(mean_anom) * math.cos(2 * mean_long)
        - 0.5 * y * y * math.sin(4 * mean_long)
        - 1.25 * 0.0167**2 * math.sin(2 * mean_anom)
    )
    return declination, eot


def sun_times(date: dt.date, lat: float, lon: float) -> dict:
    """Sunrise and sunset as UTC datetimes. None inside a polar day/night."""
    noon_utc = dt.datetime(date.year, date.month, date.day, 12, tzinfo=dt.timezone.utc)
    declination, eot = _solar_declination_and_eot(_julian_day(noon_utc))

    lat_rad = math.radians(lat)
    # -0.833 deg accounts for refraction and the sun's disc.
    cos_hour_angle = (
        math.sin(math.radians(-0.833)) - math.sin(lat_rad) * math.sin(declination)
    ) / (math.cos(lat_rad) * math.cos(declination))
    if not -1 <= cos_hour_angle <= 1:
        return {"sunrise": None, "sunset": None, "polar": True}

    hour_angle = math.degrees(math.acos(cos_hour_angle))
    solar_noon_min = 720 - 4 * lon - eot
    rise = solar_noon_min - 4 * hour_angle
    set_ = solar_noon_min + 4 * hour_angle

    midnight = dt.datetime(date.year, date.month, date.day, tzinfo=dt.timezone.utc)
    return {
        "sunrise": midnight + dt.timedelta(minutes=rise),
        "sunset": midnight + dt.timedelta(minutes=set_),
        "polar": False,
    }


def light_factor(when: dt.datetime, sunrise: dt.datetime | None,
                 sunset: dt.datetime | None) -> float:
    """0-1 bite weighting from time of day: peaks at dawn and dusk.

    The change of light is what triggers feeding, so this is a bump either
    side of sunrise and sunset rather than a day/night step.
    """
    if sunrise is None or sunset is None:
        return 0.5
    best = 0.25
    for edge in (sunrise, sunset):
        hours_off = abs((when - edge).total_seconds()) / 3600.0
        # A ~1.5 h window around each edge, tapering smoothly.
        best = max(best, math.exp(-((hours_off / 1.5) ** 2)))
    return round(min(best, 1.0), 3)

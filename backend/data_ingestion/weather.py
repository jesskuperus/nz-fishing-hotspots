"""Wind and swell: the fishability layer.

This is not part of the hotspot score and never should be. A 25 kt
south-easterly does not move the fish -- it stops you reaching them. So it
comes out as a separate hourly "can I get out" number that sits alongside
the map instead of inside it.

Falls back to a synthetic forecast when the API is unreachable, and says so
loudly in ``source`` -- an invented wind forecast is the one number here that
could actually put someone in trouble, so it is labelled, not hidden.
"""

from __future__ import annotations

import datetime as dt
import logging
import math
from dataclasses import dataclass, field

from backend import config

log = logging.getLogger(__name__)

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


@dataclass
class MarineConditions:
    hours: list[str]
    wind_kt: list[float]
    wind_dir_deg: list[float]
    swell_m: list[float]
    fishability: list[float]
    source: str
    notes: list[str] = field(default_factory=list)

    @property
    def is_synthetic(self) -> bool:
        return "synthetic" in self.source


def compass_point(bearing_deg: float) -> str:
    return COMPASS[int((bearing_deg % 360) / 22.5 + 0.5) % 16]


def fishability(wind_kt: float, swell_m: float) -> float:
    """0-100: how comfortable a trailer boat would be in this hour.

    Each of wind and swell scores 1.0 up to its comfortable limit and falls
    linearly to 0 at its maximum; the pair is combined by taking the *worse*
    of the two, because a flat sea does not rescue a 30 kt day.
    """
    def ramp(value: float, comfortable: float, maximum: float) -> float:
        if value <= comfortable:
            return 1.0
        if value >= maximum:
            return 0.0
        return 1.0 - (value - comfortable) / max(maximum - comfortable, 1e-6)

    w = ramp(wind_kt, config.WIND_COMFORTABLE_KT, config.WIND_MAX_KT)
    s = ramp(swell_m, config.SWELL_COMFORTABLE_M, config.SWELL_MAX_M)
    return round(min(w, s) * 100.0, 1)


def _synthetic_forecast(date: dt.date) -> tuple[list[float], list[float], list[float]]:
    """A plausible, gently varying day. Deterministic per date."""
    seed = date.toordinal()
    base_wind = 8.0 + 7.0 * (0.5 + 0.5 * math.sin(seed / 3.3))
    base_dir = (seed * 37) % 360
    base_swell = 0.7 + 0.9 * (0.5 + 0.5 * math.sin(seed / 5.1))

    wind, direction, swell = [], [], []
    for h in range(24):
        # Afternoon sea breeze: wind builds through the day and drops at dusk.
        diurnal = 1.0 + 0.35 * math.sin(2 * math.pi * (h - 8) / 24.0)
        wind.append(round(base_wind * diurnal, 1))
        direction.append(round((base_dir + 8 * math.sin(h / 6.0)) % 360, 1))
        swell.append(round(base_swell + 0.15 * math.sin(2 * math.pi * (h - 3) / 24.0), 2))
    return wind, direction, swell


def fetch_conditions(
    date: dt.date | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> MarineConditions:
    """Hourly wind and swell for ``date``, live if reachable else synthetic."""
    date = date or dt.date.today()
    centre_lat, centre_lon = config.BBOX.centre
    lat = centre_lat if lat is None else lat
    lon = centre_lon if lon is None else lon

    hours = [f"{h:02d}:00" for h in range(24)]
    notes: list[str] = []

    if config.USE_LIVE_WEATHER:
        try:
            wind, direction, swell = _fetch_live(date, lat, lon)
            return MarineConditions(
                hours=hours,
                wind_kt=wind,
                wind_dir_deg=direction,
                swell_m=swell,
                fishability=[fishability(w, s) for w, s in zip(wind, swell)],
                source="open-meteo-forecast+marine",
            )
        except Exception as exc:  # noqa: BLE001 - never fail the daily run
            log.warning("Weather fetch failed (%s); using synthetic", exc)
            notes.append(f"live forecast unavailable: {exc}")

    wind, direction, swell = _synthetic_forecast(date)
    notes.append(
        "SYNTHETIC forecast - a shaped guess, not a marine forecast. "
        "Check MetService or Predictwind before you leave the ramp."
    )
    return MarineConditions(
        hours=hours,
        wind_kt=wind,
        wind_dir_deg=direction,
        swell_m=swell,
        fishability=[fishability(w, s) for w, s in zip(wind, swell)],
        source="synthetic-mock-weather",
        notes=notes,
    )


def _fetch_live(
    date: dt.date, lat: float, lon: float
) -> tuple[list[float], list[float], list[float]]:
    import httpx

    params = {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "hourly": "wind_speed_10m,wind_direction_10m",
        "wind_speed_unit": "kn",
        "start_date": date.isoformat(),
        "end_date": date.isoformat(),
        "timezone": "Pacific/Auckland",
    }
    marine_params = {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "hourly": "wave_height",
        "start_date": date.isoformat(),
        "end_date": date.isoformat(),
        "timezone": "Pacific/Auckland",
    }
    with httpx.Client(timeout=config.OCEAN_FETCH_TIMEOUT_S) as client:
        wx = client.get(OPEN_METEO_FORECAST_URL, params=params)
        wx.raise_for_status()
        hourly = wx.json()["hourly"]
        wind = [float(v or 0.0) for v in hourly["wind_speed_10m"][:24]]
        direction = [float(v or 0.0) for v in hourly["wind_direction_10m"][:24]]

        sea = client.get(config.OPEN_METEO_MARINE_URL, params=marine_params)
        sea.raise_for_status()
        swell = [float(v or 0.0) for v in sea.json()["hourly"]["wave_height"][:24]]

    if len(wind) < 24 or len(swell) < 24:
        raise ValueError("incomplete hourly forecast")
    return wind, direction, swell

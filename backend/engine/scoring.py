"""Hotspot scoring.

    Hotspot Score = (temp gradient weight * 0.4)
                  + (depth slope weight  * 0.4)
                  + (current velocity weight * 0.2)

Each weight input is a 0-1 normalised feature. The weighted sum is scaled to
0-100 and then multiplied by a depth-band factor, so steep ground far outside
fishable depth does not score as a hotspot.
"""

from __future__ import annotations

import numpy as np

from backend import config


def normalise(field: np.ndarray, ceiling: float) -> np.ndarray:
    """Clip to [0, ceiling] and rescale to 0-1."""
    if ceiling <= 0:
        return np.zeros_like(field)
    return np.clip(np.nan_to_num(field, nan=0.0), 0.0, ceiling) / ceiling


def depth_band_factor(depth_m: np.ndarray) -> np.ndarray:
    """1.0 inside the fishable depth band, tapering off outside it."""
    lo = config.DEPTH_MIN_FISHABLE_M
    hi = config.DEPTH_MAX_FISHABLE_M
    depth = np.nan_to_num(depth_m, nan=0.0)
    factor = np.ones_like(depth)
    # Taper over the 40 m either side of the band rather than a hard cut,
    # so the map does not grow an artificial edge at exactly 250 m.
    too_shallow = depth < lo
    factor[too_shallow] = np.clip(depth[too_shallow] / max(lo, 1e-6), 0.0, 1.0)
    too_deep = depth > hi
    factor[too_deep] = np.clip(1.0 - (depth[too_deep] - hi) / 150.0, 0.15, 1.0)
    return factor


def hotspot_score(
    temp_gradient_c_per_km: np.ndarray,
    slope_deg: np.ndarray,
    current_speed_ms: np.ndarray,
    depth_m: np.ndarray,
) -> dict[str, np.ndarray]:
    """Per-cell score plus the normalised components that produced it."""
    w_temp = normalise(temp_gradient_c_per_km, config.TEMP_GRADIENT_CEILING_C_PER_KM)
    w_slope = normalise(slope_deg, config.SLOPE_CEILING_DEG)
    w_current = normalise(current_speed_ms, config.CURRENT_CEILING_MS)

    raw = (
        w_temp * config.WEIGHT_TEMP_GRADIENT
        + w_slope * config.WEIGHT_DEPTH_SLOPE
        + w_current * config.WEIGHT_CURRENT
    )
    total_weight = (
        config.WEIGHT_TEMP_GRADIENT
        + config.WEIGHT_DEPTH_SLOPE
        + config.WEIGHT_CURRENT
    ) or 1.0
    score = (raw / total_weight) * 100.0 * depth_band_factor(depth_m)

    return {
        "temp_gradient_weight": w_temp,
        "depth_slope_weight": w_slope,
        "current_weight": w_current,
        "hotspot_score": np.clip(score, 0.0, 100.0),
        "is_thermal_front": temp_gradient_c_per_km >= config.FRONT_THRESHOLD_C_PER_KM,
    }

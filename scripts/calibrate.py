#!/usr/bin/env python3
"""Check the score against the catch log -- and say when it cannot.

The honest state of this tool: the 0.4 / 0.4 / 0.2 weights came from the
brief, the ceilings are estimates, and none of it has been validated
against a single fish. This script is how that changes.

    python scripts/calibrate.py

With enough logged trips it reports the rank correlation between score and
catch rate, and how catch rate varies across score bands. Below the minimum
it refuses to report a number rather than dressing up noise as a finding.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend import config  # noqa: E402
from backend.calibration.catch_log import CatchEntry, load_entries  # noqa: E402

# Below this, a correlation is noise. It is a low bar and still a real one.
MIN_TRIPS = 20


def spearman(xs: list[float], ys: list[float]) -> float:
    """Rank correlation, without pulling in scipy for eight lines of maths."""
    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            mean_rank = (i + j) / 2
            for k in range(i, j + 1):
                out[order[k]] = mean_rank
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else 0.0


def band(score: float) -> str:
    if score >= 70:
        return "70-100"
    if score >= 50:
        return "50-69"
    if score >= 30:
        return "30-49"
    return "0-29"


def report(entries: list[CatchEntry]) -> dict:
    usable = [e for e in entries if e.hotspot_score is not None and e.hours_fished > 0]
    out: dict = {
        "trips_logged": len(entries),
        "trips_usable": len(usable),
        "minimum_for_a_verdict": MIN_TRIPS,
    }
    if len(usable) < MIN_TRIPS:
        out["verdict"] = (
            f"Not enough data. {len(usable)} usable trips against a minimum of "
            f"{MIN_TRIPS}. The weights stay uncalibrated -- treat the map as a "
            "hypothesis, not a forecast."
        )
        return out

    scores = [float(e.hotspot_score) for e in usable]
    rates = [e.catch_rate for e in usable]
    rho = spearman(scores, rates)

    bands: dict[str, list[float]] = {}
    for entry in usable:
        bands.setdefault(band(float(entry.hotspot_score)), []).append(entry.catch_rate)

    out["spearman_score_vs_catch_rate"] = round(rho, 3)
    out["catch_rate_by_score_band"] = {
        key: {"trips": len(vals), "mean_fish_per_hour": round(sum(vals) / len(vals), 2)}
        for key, vals in sorted(bands.items(), reverse=True)
    }
    if rho >= 0.3:
        out["verdict"] = "Score tracks catch rate. Worth trusting the ranking."
    elif rho > 0.0:
        out["verdict"] = "Weak positive signal. Keep logging before changing anything."
    else:
        out["verdict"] = (
            "No signal, or the wrong sign. The weights are wrong for this water -- "
            "try WEIGHT_* overrides in .env and re-run against the same log."
        )
    out["current_weights"] = {
        "temp_gradient": config.WEIGHT_TEMP_GRADIENT,
        "depth_slope": config.WEIGHT_DEPTH_SLOPE,
        "current_velocity": config.WEIGHT_CURRENT,
        "chlorophyll": config.WEIGHT_CHLOROPHYLL,
    }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate the score against catches")
    parser.add_argument("--log", default=str(config.CATCH_LOG_PATH))
    args = parser.parse_args(argv)
    print(json.dumps(report(load_entries(Path(args.log))), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

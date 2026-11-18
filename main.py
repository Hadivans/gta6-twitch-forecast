"""GTA VI launch-day Twitch viewers, hour by hour — light forecaster.

One case in, one forecast out: for hours 2..24 of the release day,
five quantiles (5%, 25%, 50%, 75%, 95%) of that hour's Twitch
concurrent viewers, anchored on hour 1's print.

Method (everything is computed at runtime from the case file itself,
no outside data, no model calls):
  * Each comparable launch in the case carries 17 days of hourly
    Twitch counts. Its release day (24 hours from `day_start`)
    gives one log-ratio curve: log(viewers_h / viewers_1).
  * Keep only comparables whose hour-1 print is >= 5000 viewers:
    a category that is barely alive at midnight UTC has absurd
    ratios (up to 2000x) and poisons the estimate. GTA VI's own
    hour 1 will be large (UK + Europe already unlocked at 00:00 UTC),
    so this is the relevant regime. If fewer than 8 pass the
    filter, fall back to all comparables.
  * Per hour h: m_h = median log-ratio, s_h = pstdev log-ratio
    (floor 0.20, so early hours are never overconfident).
    q_tau = p1 * exp(m_h + z_tau * s_h), z = normal quantiles.
  * p1 is hour 1's print from `known` (min 1). Quantiles are
    rounded to 2 decimals like the house starter, clamped to
    [1, 1e9] and non-decreasing.

Backtest (leave-one-out over the 37 comparable release days in
the kit; pinball loss on the log scale, lower is better):
  baseline house (median = hour 1):  ALL 0.9297 / h1>=5k 0.3595
  this forecaster:                    ALL 0.8479 / h1>=5k 0.3105
  i.e. -8.8% / -13.6% vs baseline. On big launches (h1>=50k,
  the GTA VI regime): 0.2302 vs baseline 0.2509 (-8.2%).
  Beating the baseline does not guarantee beating the house AI
  model — that one cannot be backtested from the kit.
"""

import json
import math
import os
import statistics
from pathlib import Path

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]
MIN_H1 = 5000
MIN_N = 8
SD_FLOOR = 0.20


def round2(x: float):
    """x rounded to 2 decimals, half up, as the starter rounds it."""
    scaled = x * 100
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 100
    return int(value) if value.is_integer() else value


def release_day(comparable: dict):
    """The comparable's 24 release-day viewer counts, or None."""
    hourly = comparable.get("hourly") or []
    start = comparable.get("day_start")
    idx = next((i for i, p in enumerate(hourly) if p.get("from") == start), None)
    if idx is None:
        return None
    day = hourly[idx:idx + 24]
    if len(day) < 24:
        return None
    viewers = [p.get("viewers") for p in day]
    if any(v is None or v < 1 for v in viewers):
        return None
    return viewers


def hour_quantiles(p1: float, median_log: float, sd_log: float):
    return [round2(max(1.0, p1 * math.exp(median_log + z * sd_log))) for z in Z]


def forecast_case(case: dict) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"levels {case['levels']} != {LEVELS}")
    known1 = next((k for k in case["known"] if k["hour"] == 1), None)
    if known1 is None:
        raise ValueError("no hour-1 print in known")
    p1 = max(1, known1["viewers"])

    days = []
    for comp in case.get("comparables") or []:
        day = release_day(comp)
        if day is not None:
            days.append(day)
    big = [d for d in days if d[0] >= MIN_H1]
    use = big if len(big) >= MIN_N else days

    hours = []
    for row in case["forecast"]:
        h = row["hour"]
        if use:
            ratios = [math.log(d[h - 1] / d[0]) for d in use]
            med = statistics.median(ratios)
            sd = max(SD_FLOOR, statistics.pstdev(ratios))
        else:
            # No usable comparable at all: fall back to persistence,
            # the house baseline's shape, rather than crashing the case.
            med = 0.0
            sd = 0.15 * math.sqrt(h - 1)
        hours.append({"hour": h, "q": hour_quantiles(p1, med, sd)})
    return {"hours": hours}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()

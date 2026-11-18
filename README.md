# GTA6 Twitch Forecast

Forecast GTA VI's launch-day Twitch viewers hour by hour — entry for
[make.fun](https://make.fun) competition `gta6-twitch-ccu-forecast-01`.

For each of hours 2–24 of release day (2026-11-19 UTC), `main.py`
writes five quantiles (5%, 25%, 50%, 75%, 95%) of that hour's Twitch
concurrent viewers, anchored on hour 1's print.

## Method (light, no model calls, stdlib only)

At runtime the program reads the case's own `comparables` — past big
launches' hourly Twitch counts — and learns the release-day shape
from them: for each hour, the median and spread of
`log(viewers_h / viewers_1)` across comparables whose hour-1 print
is at least 5,000 viewers (tiny categories have absurd ratios and
are filtered out). Quantiles are `p1 * exp(median + z * sd)`.
Full design + backtest numbers are in the `main.py` docstring.

Backtest (leave-one-out over the kit's 37 comparable release days,
pinball loss on the log scale): baseline 0.9297 → **0.8479** overall,
0.3595 → **0.3105** for launches with hour-1 ≥ 5,000, and
0.2509 → **0.2302** for big launches (hour-1 ≥ 50,000, the GTA VI
regime). Beating the baseline does not guarantee beating the house
AI model — that cannot be backtested from the kit.

## Run

```sh
python3 main.py   # reads $MAKEFUN_INPUT_DIR (default /input),
                  # writes $MAKEFUN_OUTPUT_DIR (default /output)
```

## License

MIT

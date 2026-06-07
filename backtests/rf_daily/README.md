# backtests/rf_daily/ — Random Forest daily sector-ETF strategy

This folder contains the results of backtesting a new daily-cadence Random Forest model (ported from `Refinement_revised/New_Strategy/`) inside the existing ETF-QUANT-LAB engine.

The model and supporting code live in [`/new_strategy/`](../../new_strategy/README.md) — start there if you want to understand what was added to the repo. The signal adapters that make these backtests run live in [`/src/QuantLab/backtest/signal/`](../../src/QuantLab/backtest/signal/) (files prefixed `rf_` or `ml_daily_`).

## Read in this order

1. **[SUMMARY.md](SUMMARY.md)** — the 5 original backtest configurations (baseline ± transaction costs, dual_signal, dual_signal_blended, signal_optimization grid). Numbers are full-window (2023-07 → 2026-03) for the RF model.
2. **[MODEL_COMPARISON.md](MODEL_COMPARISON.md)** — same baseline 3L-2S strategy run on each of the 4 ML models (RF, RF tuned, ElasticNet, LightGBM) plus an SPY buy-and-hold benchmark, split into IS (2023-07 → 2025-06) and OOS (2025-07 → 2026-03). This is the most decision-useful comparison.
3. `model_comparison.csv` — raw data for the comparison.

## What's in each per-config sub-folder

Every backtest configuration writes a folder of artifacts:

| File | What it is |
|---|---|
| `metrics.json` | Sharpe, ann. return / vol, max DD, turnover, CAPM alpha vs SPY, beta, win rate |
| `<name>_metrics.md` | Same as above, human-readable |
| `<name>_all_in_one_panel.png` | 10-panel performance dashboard (equity, drawdown, rolling stats, holding heatmap) |
| `<name>_value_history.csv` | Daily NAV |
| `<name>_holding_history.csv` | Daily position list (long + short) |

`_comparison/` contains the by-model runs from the IS/OOS comparison script.

## How to re-run

```bash
# from repo root, on branch feat/rf-daily-strategy
pip install -e .                                       # one-time
python new_strategy/setup_db.py                        # copies DB + computes alpha_110
python new_strategy/ingest_predictions.py              # RF predictions -> daily_signal (signal_id=6)
python new_strategy/ingest_all_model_predictions.py    # other 3 models -> signal_id=10, 11, 12

# Original 5 configs (full window)
python scripts/run_rf_daily_all_configs.py

# IS vs OOS comparison across all 4 models + SPY
python scripts/compare_all_models_is_oos.py
```

## Headline finding

Best OOS configuration: `RF (fixed) + BaselineStrategy(n_long=3, n_short=2, stickiness_threshold=2)` —
OOS Sharpe **+2.38**, ann. return **+41.8%**, alpha vs SPY **+21.6%**, max DD **−7.1%**, with transaction costs ON.

Same configuration on the IS window: Sharpe +0.48, ann. return +6.1%, **excess vs SPY −19.3%**. The regime sensitivity is large — see [MODEL_COMPARISON.md](MODEL_COMPARISON.md) "Why does the strategy underperform SPY in-sample?" for the explanation.

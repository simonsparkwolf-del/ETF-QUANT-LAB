# Signal 06 — RF_tuned (Daily Panel, frs_4 Proxy)

**Date integrated**: 2026-05-26 | **signal_id**: 6 | **Category**: ML

---

## Overview

| Field | Value |
|-------|-------|
| Model | RandomForest (quarterly walk-forward refit, inner-CV tuned) |
| Target | `y_5d_excess` — 5-trading-day forward excess return over SPY |
| Features | 57 (45 price/vol/macro + 12 FRED macro features) |
| OOS period | 2023-07-03 → 2026-03-12 (138 Wednesday periods) |
| OOS IC (weekly) | 0.033 (IC-IR 0.077, hit rate 54.6%) |
| IC 95% CI | [−0.042, +0.096] |
| Daily R² | −0.029 (negative — model is weaker than predicting the mean) |

---

## Research Location

```
research/20260526_David_RF model/
├── config.py                          # Hyperparameter grids, seeds, INITIAL_TRAIN_END
├── daily_features.py                  # 57-feature panel builder
├── daily_model.py                     # walk_forward_daily, PurgedTimeSeriesSplit, fit_rf_cv
├── run_daily.py                       # Entry point: build → fit → evaluate
├── evaluation.py                      # IC, NDCG, hit rate, block bootstrap
├── data/fred/                         # Raw FRED CSVs (T10Y2Y, BAMLH0A0HYM2, …)
└── outputs/daily/rf_tuned/
    ├── walk_forward_predictions.csv   # 7 392 daily rows (date, ticker, y_true, y_pred, fold_id, …)
    └── metrics_summary.json           # Headline IC/NDCG/hit-rate metrics
```

---

## Walk-Forward Methodology

- **Initial train end**: `2023-06-30` (hard-coded in `config.py`)
- **Outer loop**: quarterly expanding-window refit; each quarter's daily rows are the prediction set
- **Inner CV**: `PurgedTimeSeriesSplit(n_splits=3, gap=5)` scored by weekly Spearman IC
- **Hyperparameter grid**: `max_depth ∈ {4, 6, 8}` × `min_samples_leaf ∈ {100, 200, 400}` (9 candidates)
- **Sector fixed effects**: per-ticker mean of `y_5d_excess` subtracted before fitting; added back at predict time

---

## Integration into QuantLab

**Source file**: [`src/QuantLab/signal/ml/signal_6.py`](../../src/QuantLab/signal/ml/signal_6.py)

The signal reads `walk_forward_predictions.csv`, pivots to wide format, and forward-fills onto the Wednesday calendar from `weekly_bar` (via `load_ml_panel` with empty `required`). Output: `(ticker, date, pred)` long DataFrame injected into `weekly_signal` via `@series_signal(signal_id=6)`.

**FRED Macro data pipeline** (prerequisite): `scripts/trivial/merge_fred_to_csv.py` appends 5 FRED columns to `data/processed/data.csv` (`T10Y2Y`, `BAMLH0A0HYM2`, `DTWEXBGS`, `DCOILWTICO`, `T10YIE`). The RF model itself reads FRED CSVs directly from `research/20260526_David_RF model/data/fred/`; the infra script is only needed to make Macro tickers available in `datapool.db`.

**Entry point**: `scripts/dataset_builder.ipynb` → Cell 7 `save_signal_results(conn)`. Signal 6 is auto-imported via `_auto_import_signals()` and written incrementally (only missing `(date, ticker)` pairs inserted).

---

## Known Methodological Issues

| Issue | Severity | Detail |
|-------|----------|--------|
| Inner CV purge gap too small | High | `gap=5` rows ≈ 0.45 trading days at 11 tickers/day; 5-day overlapping labels require `gap ≥ 55` rows |
| Sector FE leakage into inner CV | Medium | `ticker_mean` computed on full outer train set before inner CV splits — validation fold y values carry a mild look-ahead |
| IC statistically insignificant | Medium | CI [−0.042, +0.096] includes zero; 138 periods insufficient to reject H₀ |
| Daily sanity check negative | High | `corr(pred, y_true) = −0.069` and `R² = −0.029` on daily cadence — model predicts direction inversely |
| No portfolio-level evaluation | Note | IC/NDCG only; actual Sharpe/drawdown requires running through `BaselineStrategy` in `backtests/` |

The gap issue means the inner-CV selected hyperparameters (`max_depth`, `min_samples_leaf`) may be overfitted to the training distribution. The weekly IC lift over the daily IC suggests forward-fill aggregation smooths out daily noise, but the statistical power is too low to confirm a reliable signal.

---

## Signal Performance (OOS, weekly-on-frs4)

| Metric | Value |
|--------|-------|
| Spearman IC mean | 0.033 |
| IC std | 0.425 |
| IC-IR | 0.077 |
| IC 95% CI | [−0.042, +0.096] |
| NDCG@3 mean | 0.143 |
| Top-3 precision | 32.9% |
| Hit rate | 54.6% |
| Global R² | −0.028 |

Baseline portfolio backtest (Sharpe, NAV) pending — run `backtests/baseline/no_trans_cost/[in|out]_sample/ml_signal/run.py` with `signal_id=6`.

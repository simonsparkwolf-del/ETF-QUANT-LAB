# Signal Pool

All signals are stored in `weekly_signal` (ETF-only, long format). Each signal outputs a cross-sectional score per ETF per week, consumed by the backtest engine via `QuoteTerminal.signals()`.

---

## Signal Types

| Type | Implementation class | Registered in |
|------|---------------------|---------------|
| ML model output | `MLBacktestSignal(signal_id)` | `signal/ml/*.py` |
| Alpha factor | `AlphaBacktestSignal(alpha_id)` | `alpha/alpha_metrics.py` |
| Composite / non-ML | `signal/signal_metrics.py` | `signal/signal_metrics.py` |

All signal classes implement `Signal.analyze()` → `OrderedDict[ticker, score]`.

---

## ML Signals (signal_id 1–6)

| signal_id | Name | Model | Label | OOS IC (weekly) | Status |
|-----------|------|-------|-------|-----------------|--------|
| 1 | LightGBM_frs3 | LightGBM | FRS3 | — | ✓ Trained |
| 2 | Ensemble_RankAvg_frs1 | Rank-average ensemble | FRS1 | — | ✓ Trained |
| 3 | XGBoost_frs3 | XGBoost | FRS3 | — | ✓ Trained |
| 4 | PCA_Ridge_frs3 | PCA + Ridge | FRS3 | — | ✓ Trained |
| 5 | MLP_frs2 | MLP | FRS2 | — | ✓ Trained |
| 6 | RF_tuned | RandomForest (quarterly refit, inner-CV tuned) | frs_4 proxy (5d excess) | 0.033 (IC-IR 0.077, hit 54.6%, 138 periods) | ✓ Integrated |

**OOS screening winner (signals 1–5):** Signal 2 (Ensemble_RankAvg_frs1) — most consistent across both baseline L/S and LP signal-opt frameworks. See `02_work/02_trading_opt/01_warmup_test.md` and `02_work/01_signal_opt/00_screening.md` for full results.

**Signal 6 notes:** Daily-cadence RF predictions aligned to Wednesday dates via forward-fill (`reindex(method="ffill")`). Research and walk-forward predictions live in `research/20260526_David_RF model/`. See `02_work/01_signal_mining/01_Signal06_RF.md` for methodology and known issues.

---

## Alpha Signals

82 alpha factors (WQ101 groups A/B) + custom alphas (alpha_id 108–136) stored in `weekly_alpha` and accessible as `AlphaBacktestSignal(alpha_id)`.

Key screening results → `02_work/01_signal_opt/00_screening.md` §6–8 and `03_datapool/02_alpha.md`.

---

## Risk-Control Alpha (special use)

`alpha_110` (12-week cumulative return) is used exclusively inside `BaselineRisk` as a short-entry filter and HEAVY→LIGHT recovery gate. It does **not** participate in ranking signals. Access only via `terminal.alphas(alpha_ids=(110,))`.

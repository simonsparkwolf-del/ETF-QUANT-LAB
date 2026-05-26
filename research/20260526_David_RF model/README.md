# New_Strategy — weekly sector ETF prediction

Theory-first ML redesign of the sector rotation strategy.

## Scope (what this folder does and does NOT do)

- **Does:** load weekly OHLCV from the existing SQLite DB, build a small,
  economically motivated feature panel, train a single penalised linear
  model (ElasticNet) with quarterly walk-forward refits, and report ML
  metrics on the stitched out-of-sample predictions.
- **Does NOT:** construct a portfolio, compute weights, simulate turnover,
  apply transaction costs, or report P&L. A separate downstream script
  handles trading.

## Inputs

`config.DB` points to `../Refinement_revised-old/ML001_data/datapool.db`.
The redesign uses only the `weekly_bar` table; it does not depend on the
pre-computed `weekly_alpha`, `weekly_frs`, or `daily_*` tables.

## Target

Only `frs_4` = 1-week forward excess return over SPY,
`(P_i[t+1w]/P_i[t] - 1) - (P_SPY[t+1w]/P_SPY[t] - 1)`. Adjacent labels are
disjoint (0% overlap). Forward-vol-penalised variants are explicitly out
of scope.

## Features (14 columns)

Ten time-series features per sector:

| Feature | Definition |
|---|---|
| `f_ret_1w` | 1w return (short-term reversal channel) |
| `f_ret_4w` | 4w return |
| `f_ret_12w` | 12w return |
| `f_mom_12_1` | close[t-1w] / close[t-12w] − 1 (Jegadeesh–Titman) |
| `f_vol_12w` | 12w std of weekly returns |
| `f_dd_52w` | close / rolling 52w high − 1 |
| `f_rs_spy_12w` | sector 12w return − SPY 12w return |
| `f_beta_spy_26w` | 26w cov(r_i, r_SPY) / var(r_SPY) |
| `f_dvol_log_z12w` | 12w mean of log(close·volume), z-scored cross-sectionally |
| `f_ma_dist_12w` | close / 12w mean − 1 |

Per-date cross-sectional preprocessing (winsorise 5/95, fill median, z-score)
is applied to the 10 base features only.

Four macro-bucket interaction features (kept raw — no per-date z-score —
because their information is the macro state, not the cross-section):

| Feature | Definition |
|---|---|
| `m_defensive_x_VIXz` | 1{ticker ∈ XLP, XLU, XLV} · VIX_z (12w rolling z) |
| `m_cyclical_x_VIXz` | 1{ticker ∈ XLY, XLI, XLB} · VIX_z |
| `m_ratesens_x_dUS10Yz` | 1{ticker ∈ XLF, XLRE, XLU} · ΔUST10Y_z |
| `m_techgrowth_x_dUS10Yz` | 1{ticker ∈ XLK, XLC} · ΔUST10Y_z |

No statistical feature selection. ElasticNet regularisation handles
correlation among features.

## Model

Single `ElasticNet` from `sklearn`, pooled across the 11 sectors. Inner
hyperparameter tuning via `TimeSeriesSplit(5)` on each training window,
scored by mean weekly Spearman IC. Grid: `alpha ∈ {0.001, 0.003, 0.01, 0.03, 0.1}`,
`l1_ratio ∈ {0.1, 0.5, 0.9}`. 15 candidates × 5 inner folds per refit.

## Walk-forward

- Initial train: panel start → 2023-06-30.
- Quarterly refit; predict that quarter; expand training window each step.
- All predictions stitched into one OOS series stored in
  `outputs/walk_forward_predictions.csv` with columns
  `date, ticker, y_true, y_pred, fold_id, fold_quarter, en_alpha, en_l1_ratio, val_ic_inner`.

## Evaluation (ML metrics only)

Written to `outputs/metrics_summary.{csv,json}`:

- Weekly Spearman IC (mean, std, IR) with 95% block-bootstrap CIs
  (block length = 6 weeks, 1,000 iterations).
- NDCG@3 with a 200-iteration permutation null (`p_value`).
- Top-3 precision vs a 3/11 random baseline.
- Hit rate, R² on the stitched OOS panel.
- Decay curve `outputs/decay_curve.csv`: IC at h ∈ {1, 2, 4, 8} weeks.
- Sub-period IC `outputs/subperiod_ic_yearly.csv` and
  `outputs/subperiod_ic_regime.csv` (high/low VIX, rising/falling rates).
- Vol-vs-return sanity check: `corr(pred, y_true)` vs `corr(pred, |y_true|)`.

## Run it

```bash
cd New_Strategy
python run.py
```

## Realistic expectation

OOS weekly Spearman IC in the 0.03–0.08 band, IC-IR 0.3–0.7. Anything
materially above this on ~140 OOS weeks warrants a leakage audit before
acting on the result.

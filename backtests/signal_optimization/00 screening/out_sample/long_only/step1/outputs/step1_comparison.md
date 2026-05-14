# Step 1 — Signal Screening Report

Date range: 2025-01-01 → 2026-03-01  |  Initial NAV: 10,000

## Comparison Table

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. | Δ Sharpe vs §0 |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|:--------------:|
| EqualWeight (baseline) | 1.537 | 16.40% | 10.23% | -10.64% | 27.95% | +0.000 |
| LightGBM_frs3 | 1.534 | 16.37% | 10.24% | -10.64% | 41.59% | -0.003 |
| Ensemble_RankAvg_frs1 ★ | 1.730 | 19.12% | 10.44% | -10.27% | 648.57% | +0.193 |
| XGBoost_frs3 | 1.538 | 16.41% | 10.23% | -10.62% | 41.58% | +0.001 |
| PCA_Ridge_frs3 | 1.538 | 16.39% | 10.22% | -10.61% | 34.82% | +0.001 |
| MLP_frs2 | 1.598 | 16.93% | 10.12% | -10.26% | 585.54% | +0.061 |

> ★ best ML signal by Sharpe

## Verdict

Best ML signal: **Ensemble_RankAvg_frs1** (Signal 2)
- Sharpe: 1.730

Full artifacts saved in `outputs/best_signal_2/`.
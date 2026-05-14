# Step 1 — Signal Screening Report (Short-Only)

Date range: 2025-01-01 → 2026-03-01  |  Initial NAV: 10,000

## Comparison Table

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. | Δ Sharpe vs §0 |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|:--------------:|
| EqualWeight (baseline) | -1.537 | -15.01% | 10.23% | -21.31% | 28.04% | +0.000 |
| LightGBM_frs3 | -1.540 | -15.03% | 10.23% | -21.33% | 41.73% | -0.003 |
| Ensemble_RankAvg_frs1 ★ | -1.330 | -13.06% | 10.13% | -19.26% | 657.61% | +0.207 |
| XGBoost_frs3 | -1.535 | -14.99% | 10.23% | -21.32% | 41.77% | +0.001 |
| PCA_Ridge_frs3 | -1.536 | -15.02% | 10.25% | -21.33% | 34.98% | +0.001 |
| MLP_frs2 | -1.438 | -14.46% | 10.48% | -20.75% | 591.47% | +0.099 |

> ★ best ML signal by Sharpe

## Verdict

Best ML signal: **Ensemble_RankAvg_frs1** (Signal 2)
- Sharpe: -1.330

Full artifacts saved in `outputs/best_signal_2/`.
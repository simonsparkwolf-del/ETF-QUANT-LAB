# Step 1 — Signal Screening Report (Short-Only)

Date range: 2021-03-03 → 2024-12-31  |  Initial NAV: 10,000

## Comparison Table

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. | Δ Sharpe vs §0 |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|:--------------:|
| EqualWeight (baseline) | -0.690 | -10.94% | 15.13% | -38.42% | 41.72% | +0.000 |
| LightGBM_frs3 | -0.689 | -10.94% | 15.15% | -38.42% | 51.08% | +0.001 |
| Ensemble_RankAvg_frs1 | -0.692 | -10.83% | 14.95% | -38.20% | 607.16% | -0.002 |
| XGBoost_frs3 | -0.689 | -10.93% | 15.14% | -38.40% | 51.35% | +0.001 |
| PCA_Ridge_frs3 | -0.690 | -10.96% | 15.15% | -38.48% | 46.13% | -0.000 |
| MLP_frs2 ★ | -0.673 | -10.75% | 15.18% | -37.98% | 597.25% | +0.017 |

> ★ best ML signal by Sharpe

## Verdict

Best ML signal: **MLP_frs2** (Signal 5)
- Sharpe: -0.673

Full artifacts saved in `outputs/best_signal_5/`.
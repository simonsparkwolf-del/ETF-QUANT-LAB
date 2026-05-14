# Baseline Long-Short — ML Signal Comparison (Out-of-Sample)

Date range: 2025-01-01 → 2026-03-01  |  Initial NAV: 10,000

## Comparison

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| LightGBM_frs3 | -1.571 | -8.54% | 5.58% | -11.76% | 2486.74% |
| Ensemble_RankAvg_frs1 ★ | 0.862 | 10.24% | 12.16% | -4.59% | 4633.34% |
| XGBoost_frs3 | -0.731 | -4.79% | 6.44% | -10.33% | 2643.86% |
| PCA_Ridge_frs3 | 0.267 | 2.47% | 11.57% | -7.98% | 3951.28% |
| MLP_frs2 | -0.087 | -1.27% | 9.59% | -10.40% | 4758.05% |

> ★ best by Sharpe: **Ensemble_RankAvg_frs1** (0.862)

Artifacts: `outputs/best_signal_2/`
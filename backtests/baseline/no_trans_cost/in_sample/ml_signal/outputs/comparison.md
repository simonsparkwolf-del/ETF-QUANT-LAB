# Baseline Long-Short — ML Signal Comparison (In-Sample)

Date range: 2021-03-03 → 2024-12-31  |  Initial NAV: 10,000

## Comparison

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| LightGBM_frs3 | 0.532 | 4.13% | 8.26% | -14.62% | 1544.07% |
| Ensemble_RankAvg_frs1 ★ | 0.730 | 6.57% | 9.30% | -10.74% | 2559.53% |
| XGBoost_frs3 | 0.709 | 5.82% | 8.49% | -13.94% | 1751.83% |
| PCA_Ridge_frs3 | 0.461 | 4.34% | 10.39% | -18.11% | 1807.81% |
| MLP_frs2 | 0.402 | 2.76% | 7.46% | -15.09% | 1739.99% |
| RF_frs4 | 0.696 | 5.86% | 8.74% | -9.21% | 463.12% |

> ★ best by Sharpe: **Ensemble_RankAvg_frs1** (0.730)

Artifacts: `outputs/best_signal_2/`
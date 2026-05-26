# Baseline Long-Short — ML Signal Comparison (In-Sample)

Date range: 2021-03-03 → 2024-12-31  |  Initial NAV: 10,000

## Comparison

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| LightGBM_frs3 | 0.532 | 4.13% | 8.26% | -14.62% | 1544.07% |
| Ensemble_RankAvg_frs1 | 0.454 | 3.37% | 8.02% | -13.07% | 1789.14% |
| XGBoost_frs3 | 0.673 | 5.55% | 8.58% | -14.77% | 1777.81% |
| PCA_Ridge_frs3 | 0.469 | 4.43% | 10.40% | -18.11% | 1799.10% |
| MLP_frs2 | 0.390 | 2.70% | 7.56% | -16.17% | 1902.17% |
| RF_frs4 ★ | 0.696 | 5.86% | 8.74% | -9.21% | 463.12% |

> ★ best by Sharpe: **RF_frs4** (0.696)

Artifacts: `outputs/best_signal_6/`
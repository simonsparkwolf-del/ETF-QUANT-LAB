# Baseline Long-Short — ML Signal Comparison (In-Sample)

Date range: 2021-03-03 → 2024-12-31  |  Initial NAV: 10,000

## Comparison

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| LightGBM_frs3 ★ | 0.601 | 5.09% | 8.94% | -13.71% | 1570.79% |
| Ensemble_RankAvg_frs1 | 0.330 | 2.17% | 7.31% | -16.72% | 1815.20% |
| XGBoost_frs3 | 0.560 | 4.65% | 8.81% | -16.47% | 1830.34% |
| PCA_Ridge_frs3 | 0.442 | 3.89% | 9.71% | -18.05% | 1675.31% |
| MLP_frs2 | 0.247 | 1.61% | 7.66% | -14.06% | 1745.38% |

> ★ best by Sharpe: **LightGBM_frs3** (0.601)

Artifacts: `outputs/best_signal_1/`
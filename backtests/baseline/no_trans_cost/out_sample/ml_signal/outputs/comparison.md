# Baseline Long-Short — ML Signal Comparison (Out-of-Sample)

Date range: 2025-01-01 → 2026-03-01  |  Initial NAV: 10,000

## Comparison

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| LightGBM_frs3 | 0.449 | 4.44% | 11.01% | -8.28% | 3892.47% |
| Ensemble_RankAvg_frs1 ★ | 1.629 | 19.56% | 11.37% | -2.97% | 5025.20% |
| XGBoost_frs3 | 0.801 | 9.00% | 11.60% | -8.45% | 4013.90% |
| PCA_Ridge_frs3 | 0.575 | 6.22% | 11.64% | -7.80% | 4068.66% |
| MLP_frs2 | 0.431 | 4.36% | 11.36% | -9.30% | 5150.25% |
| RF_frs4 | 0.323 | 3.64% | 14.10% | -12.76% | 2485.00% |

> ★ best by Sharpe: **Ensemble_RankAvg_frs1** (1.629)

Artifacts: `outputs/best_signal_2/`
# Step 1 — Signal Screening Report

Date range: 2021-03-03 → 2024-12-31  |  Initial NAV: 10,000

## Comparison Table

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. | Δ Sharpe vs §0 |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|:--------------:|
| EqualWeight (baseline) | 0.690 | 9.73% | 15.13% | -19.87% | 41.88% | +0.000 |
| LightGBM_frs3 | 0.691 | 9.73% | 15.11% | -19.91% | 51.11% | +0.001 |
| Ensemble_RankAvg_frs1 | 0.698 | 10.00% | 15.37% | -20.83% | 614.09% | +0.008 |
| XGBoost_frs3 | 0.691 | 9.74% | 15.11% | -19.87% | 51.39% | +0.001 |
| PCA_Ridge_frs3 | 0.690 | 9.71% | 15.10% | -19.89% | 46.19% | -0.000 |
| MLP_frs2 ★ | 0.705 | 9.98% | 15.14% | -21.19% | 582.52% | +0.015 |

> ★ best ML signal by Sharpe

## Verdict

Best ML signal: **MLP_frs2** (Signal 5)
- Sharpe: 0.705

Full artifacts saved in `outputs/best_signal_5/`.
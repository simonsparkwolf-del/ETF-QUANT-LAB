# Step 1 — Signal Screening Report

Date range: 2025-01-01 → 2026-01-31  |  Initial NAV: 10,000  |  λ (turnover penalty): 0.1

## Comparison Table

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. | L=Sharpe−λ·TO | Δ Sharpe vs §0 |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|:-------------:|:--------------:|
| EqualWeight (baseline) | 1.305 | 13.98% | 10.46% | -10.64% | 28.24% | 1.305 | +0.000 |
| LightGBM_frs3 | 1.300 | 13.92% | 10.46% | -10.64% | 41.53% | 1.300 | -0.005 |
| Ensemble_RankAvg_frs1 ★ | 1.506 | 16.76% | 10.68% | -10.27% | 652.67% | 1.506 | +0.201 |
| XGBoost_frs3 | 1.304 | 13.97% | 10.46% | -10.62% | 41.62% | 1.304 | -0.001 |
| PCA_Ridge_frs3 | 1.304 | 13.96% | 10.44% | -10.61% | 35.20% | 1.304 | -0.001 |
| MLP_frs2 | 1.329 | 14.06% | 10.31% | -10.26% | 577.08% | 1.329 | +0.024 |

> ★ best ML signal by objective L = Sharpe − 0.1 × Turnover_ann

## Verdict

Best ML signal: **Ensemble_RankAvg_frs1** (Signal 2)
- Sharpe: 1.506
- Objective L: 1.506

Full artifacts saved in `outputs/best_signal_2/`.
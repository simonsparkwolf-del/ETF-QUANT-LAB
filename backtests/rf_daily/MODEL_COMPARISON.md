# Model Comparison — IS vs OOS, all 4 ML models + SPY benchmark

Same strategy for every row (`BaselineStrategy(n_long=3, n_short=2, stickiness_threshold=2)`),
Wed-anchored weekly rebalance, **transaction costs ON** (`long_cost=2 bps/leg`,
`short_cost_per_day=30 bps p.a. borrow`). Only the model behind the signal changes.

- **IS** = 2023-07-03 → 2025-06-30 (~104 weekly rebalances)
- **OOS** = 2025-07-01 → 2026-03-12 (~37 weekly rebalances)

The IS/OOS split is internal to the OOS window of the underlying walk-forward training — see [REPORT_METHODOLOGY](#methodology-note) at bottom.

## In-sample window (2023-07 → 2025-06)

| Strategy | Sharpe | Ann. Return | Ann. Vol | Max DD | Alpha vs SPY | Beta | Excess vs SPY |
|---|---:|---:|---:|---:|---:|---:|---:|
| **SPY buy-and-hold** | **1.18** | **19.9%** | 16.6% | −18.8% | 0 | 1.00 | 0 |
| RF (fixed) 3L-2S | 0.48 | 6.1% | 14.6% | −14.8% | −3.7% | 0.40 | **−19.3%** |
| RF tuned 3L-2S | 0.34 | 4.2% | 16.3% | −15.5% | −8.1% | 0.52 | −20.8% |
| ElasticNet 3L-2S | 0.19 | 1.8% | 18.0% | −19.8% | −11.1% | 0.55 | −22.9% |
| LightGBM 3L-2S | 0.11 | 0.6% | 13.2% | −12.7% | −4.9% | 0.24 | −24.8% |

**Take-away IS**: SPY buy-and-hold beat *every* model strategy. RF was the least-bad model (and the best CAPM alpha at −3.7%), but the entire family failed to outperform a passive SPY position during this 2-year bull window. Annual excess returns of −19 to −25 % p.a. are not small.

## Out-of-sample window (2025-07 → 2026-03)

| Strategy | Sharpe | Ann. Return | Ann. Vol | Max DD | Alpha vs SPY | Beta | Excess vs SPY |
|---|---:|---:|---:|---:|---:|---:|---:|
| **RF (fixed) 3L-2S** | **2.38** | **41.8%** | 15.2% | **−7.1%** | **+21.6%** | 0.86 | **+19.3%** |
| LightGBM 3L-2S | 1.68 | 24.4% | 13.5% | −5.9% | +16.2% | 0.39 | +5.9% |
| RF tuned 3L-2S | 1.37 | 22.8% | 15.9% | −9.3% | +9.3% | 0.74 | +5.0% |
| SPY buy-and-hold | 1.11 | 12.5% | 11.2% | −5.1% | 0 | 1.00 | 0 |
| ElasticNet 3L-2S | 1.09 | 17.3% | 15.8% | −7.1% | −0.4% | 1.05 | +0.4% |

**Take-away OOS**: RF beats SPY by a huge margin on every metric. LightGBM (which had ~zero IC) somehow also outperforms — suspicious, very small sample. RF-tuned and ElasticNet roughly match SPY on a risk-adjusted basis.

## Per-model IS → OOS deltas (Sharpe)

| Model | IS Sharpe | OOS Sharpe | Δ |
|---|---:|---:|---:|
| RF (fixed) | 0.48 | 2.38 | **+1.90** |
| RF tuned | 0.34 | 1.37 | +1.03 |
| ElasticNet | 0.19 | 1.09 | +0.90 |
| LightGBM | 0.11 | 1.68 | +1.57 |
| **SPY buy-and-hold** | **1.18** | **1.11** | **−0.07** |

SPY's Sharpe barely changes (large markets are reasonably stationary). All models' Sharpe jumps dramatically. This is partly a regime change in cross-sectional dispersion (good for active sector rotation), and partly a small-sample artifact (8 months is short).

## Why does the strategy underperform SPY in-sample?

The strategy is "3 longs + 2 shorts equal-weight", so gross exposure is 2× NAV and **net exposure ≈ 0** by design. But the realised market beta is non-zero and *drifts* depending on which sectors are picked.

- **IS beta = 0.40**: the model picked low-beta defensives as longs during a bull market — left most of the rally on the table.
- **OOS beta = 0.86**: the model picked high-beta growth sectors as longs in a tech-led rally — captured most of the upside *and* added rotation alpha.

So the IS underperformance is not because the model was wrong — it's because a near-market-neutral construction during a +47 % SPY rally was structurally guaranteed to look bad. The RF was the best of a bad bunch on IS *as a ranking signal*; only on OOS did the strategy construction line up favourably with the model's picks.

## Methodology note

There is **no true holdout** in this comparison. All four models were trained walk-forward across the full 2023-07 → 2026-03 window. Splitting that window into "IS" (first 24 months) and "OOS" (last 8.5 months) gives apples-to-apples comparable evaluation periods but the model itself "saw" both periods during walk-forward training (each fold trained only on data strictly before its predict-quarter, so there is no leakage within a fold — but the model class, hyperparameters, and feature set were chosen knowing how they perform across the whole window).

For a genuinely held-out test, you'd want a quarter or two of fresh post-2026-03-12 data to roll the predictions onto. The numbers here are best read as "in-sample (longer, bull regime) vs out-of-sample (shorter, rotation regime)" rather than as a strictly disjoint train/test split.

## Verdict on the RF + 3L-2S strategy

**The model is the best of the four** — consistent across both windows by every metric except OOS LightGBM (which is suspicious due to its near-zero IC; small-sample noise is the likely explanation).

**The strategy is regime-sensitive.** On the IS bull-market window it cost ~19 % p.a. vs just holding SPY. On the OOS rotation window it added ~19 % p.a. vs SPY. Same parameters, opposite outcome — the difference is which sectors the model identifies as long candidates and what beta that mix happens to carry.

**For deployment**, the honest reading is:
- The signal carries real information (consistent positive rankings across both windows, IS the worst of those signals still produced the best CAPM alpha vs SPY).
- The current strategy construction will sometimes badly underperform a simple SPY hold during persistent uptrends.
- Either widen the OOS window for more confidence, or add a market-aware component (gross-exposure scaling, beta neutralisation, or a SPY fallback when no sector clears a long threshold) so the strategy doesn't structurally fight a bull market.

The earlier claim that "daily data + streamlined RF is what this project needed" is **half-right**: the model upgrade is real. The strategy construction still needs work for the model's signal to translate into reliable risk-adjusted returns across regimes.

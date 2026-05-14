# Signal Optimization — Step 3: Joint L/S Blend

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-14  
**Framework**: `architecture.md` §4 Step 3

---

## 1. Motivation

Step 2 LP/SP blend optimisation produced side-specific weight vectors that each
beat their single-signal counterparts in isolation (LP OOS 2.130, SP OOS −0.496).
However, wiring those weights into the full L/S strategy (Design 02) caused a
catastrophic collapse: OOS Sharpe 0.650 vs the Design 01 baseline of 2.190.

**Root cause:** LP/SP blend weights were optimised on single-side, IS-train
objectives. The L/S strategy introduces interactions — conflict resolution,
stickiness, the alpha_110 short filter — that are invisible to side-specific
optimisers. Weights optimal for LP-only or SP-only backtests are not optimal for
the joint L/S objective.

Step 3 fix: **optimise LP and SP weights jointly, directly on the full L/S Sharpe**.
No differentiability is required — optuna TPE is a black-box sampler.

---

## 2. Search Space

Ten raw weights, two independent simplices:

$$u^{\text{LP}}_k,\; u^{\text{SP}}_k \;\sim\; \text{Uniform}[0,\,1]$$

$$w^{\text{LP}}_k = \frac{u^{\text{LP}}_k}{\sum_j u^{\text{LP}}_j}, \qquad
  w^{\text{SP}}_k = \frac{u^{\text{SP}}_k}{\sum_j u^{\text{SP}}_j}$$

**Candidate pools (IS-correct, from Step 1 IS ranking):**

| Side | Pool |
|------|------|
| LP | #24, #66, #101, #64, #136 (top 5 IS LP Sharpe) |
| SP | #24, #57, #19, #51, #66 (top 5 IS SP Sharpe) |

---

## 3. Objective

Maximise the **full L/S Sharpe** on IS-train:

$$\mathcal{L}(w^{\text{LP}}, w^{\text{SP}}) = \text{Sharpe}\!\Bigl(\text{L/S backtest}\bigl(\text{LongShortBlendSignal}(w^{\text{LP}}, w^{\text{SP}}),\; t \in \text{IS-train}\bigr)\Bigr)$$

The backtest uses `DualSignalStrategy` + `BaselineRisk`, `long_enabled=True`,
`short_enabled=True`, zero transaction costs.

---

## 4. Walk-Forward Windows

| Window | Dates | Bars | Role |
|--------|-------|:----:|------|
| IS train | 2021-03-03 → 2023-12-31 | ~150 | Joint optimisation target |
| IS val | 2024-01-01 → 2024-12-31 | ~52 | Overfitting check |
| OOS test | 2025-01-01 → 2026-03-01 | 61 | Final out-of-sample result |

---

## 5. Bayesian Optimiser

| Setting | Value | Note |
|---------|-------|------|
| Library | `optuna` | |
| Sampler | `TPESampler` (seed=42) | |
| Direction | maximise | full L/S Sharpe |
| Trials | 300 | doubled vs Step 2 (10 params vs 5) |
| Pruner | `MedianPruner` (n_startup_trials=30) | |

---

## 6. Baselines

| Reference | IS-val Sharpe | OOS Sharpe |
|-----------|:-------------:|:----------:|
| `l24_s24` — IS-best single (LP=SP=#24) | TBD | TBD |
| Equal-weight blend (all 1.0) | TBD | TBD |
| **Jointly optimised L/S blend** | TBD | TBD |

Target: beat IS-selected `l24_s24` on IS-val Sharpe; OOS result reported as validation.

---

## 7. Run Script

```
backtests/signal_optimization/02 ls_blend/run.py
```

Outputs:
```
backtests/signal_optimization/02 ls_blend/outputs/
  study.pkl
  best_weights.json    {lp: {alpha_id: weight, …}, sp: {…}}
  summary.json
  best_ls_blend/       full artifacts (OOS window)
  equal_weight_blend/  full artifacts (OOS window)
  l24_s24/             full artifacts (OOS window) — IS-best baseline
```

---

## 8. Results

### 8.1 Optimised Weights

**LP side** — lower IS LP ranks dominate:

| Alpha | Weight | IS LP rank |
|-------|:------:|:----------:|
| #136 | **38.53%** | #5 |
| #101 | **36.96%** | #3 |
| #24 | 13.94% | #1 IS best |
| #64 | 6.97% | #4 |
| #66 | 3.61% | #2 |

**SP side** — #66 dominates (same pattern as Step 2 SP blend):

| Alpha | Weight | IS SP rank |
|-------|:------:|:----------:|
| #66 | **58.78%** | #5 |
| #24 | 30.04% | #1 IS best |
| #19 | 5.98% | #3 |
| #51 | 4.23% | #4 |
| #57 | 0.98% | #2 |

### 8.2 Performance Summary

| Configuration | IS-train Sharpe | IS-val Sharpe | OOS Sharpe | OOS Ann. Return | OOS Vol | OOS Max DD |
|---------------|:---------------:|:-------------:|:----------:|:---------------:|:-------:|:----------:|
| **`l24_s24` (IS-selected ★)** | — | **2.602** | 0.118 | 0.71% | 10.82% | −9.92% |
| EW blend (all 1.0) | — | 1.447 | 0.154 | 1.09% | 10.72% | −8.59% |
| Jointly optimised blend | **1.851** | 1.206 | 0.474 | 4.44% | 10.25% | −12.35% |

> ★ **IS-selected: `l24_s24`** (IS-val 2.602 >> blend 1.206). OOS of IS-selected: 0.118 — severe IS/OOS divergence.

### 8.3 Key Findings

1. **IS selection: `l24_s24` wins IS-val by a wide margin (2.602 vs 1.206).** The single IS-best alpha pair is unambiguously IS-selected. Blending adds no IS-val benefit.

2. **Severe IS/OOS divergence across all three configurations.** All OOS Sharpes are near-zero (0.118–0.474) despite IS-val Sharpes of 1.2–2.6. The 2021–2024 IS regime does not predict 2025–2026 OOS for the L/S combination.

3. **IS-train overfitting is extreme.** Blend IS-train 1.851 → IS-val 1.206 → OOS 0.474. The 300-trial optimiser locks onto IS-train 2021–2023 regime features that do not generalise.

4. **LP weights: lower IS ranks dominate.** #136 (38.5%) and #101 (37.0%) are IS LP #5 and #3; IS LP best #24 gets only 14%. Same pattern as Step 2: the IS-train 2021–2023 sub-period favours different alphas than the full IS period.

5. **SP weight structure mirrors Step 2 SP blend.** #66 again dominates at 59%; #24 (IS SP best) at 30%. The IS-train regime consistently down-weights the IS-period best signals.

6. **Conclusion: Step 3 is also negative.** `l24_s24` is IS-selected but has near-zero OOS Sharpe (0.118). The joint blend improves OOS over `l24_s24` (0.474 vs 0.118) but both are far below any useful threshold. Signal blending in this 11-ETF universe does not produce a viable L/S strategy.

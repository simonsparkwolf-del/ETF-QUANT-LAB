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

**Candidate pools (unchanged from Step 2):**

| Side | Pool |
|------|------|
| LP | #57, #24, #19, #31, #23 |
| SP | #23, #53, #31, #19, #57 |

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
| `l57_s23` — Design 01/02 best | TBD | 2.190 |
| Equal-weight blend (all 1.0) | TBD | TBD |
| **Jointly optimised L/S blend** | TBD | TBD |

Target: OOS Sharpe > **2.190** (`l57_s23` from Design 02 ablation).

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
  l57_s23/             full artifacts (OOS window)
```

---

## 8. Results

### 8.1 Optimised Weights

**LP side** — more balanced than Step 2 LP blend:

| Alpha | Weight | Note |
|-------|:------:|------|
| #24 | 28.65% | L-only in Step 1; joint opt assigns modest weight (vs 61% in Step 2) |
| #57 | 28.39% | Step 1 best LP; recovers weight when optimised in L/S context |
| #23 | 20.64% | Step 1 best SP; LP contribution acknowledged |
| #31 | 17.64% | Strong all-round; significant LP weight |
| #19 | 4.68% | Minor contributor |

**SP side** — #31 emerges as dominant (invisible in Step 2 SP-only):

| Alpha | Weight | Note |
|-------|:------:|------|
| #31 | 49.12% | Near-zero in Step 2 SP-only (2.37%); dominant in joint L/S context |
| #23 | 32.76% | Step 1 best SP; retains significant weight |
| #57 | 7.39% | Minor |
| #19 | 7.17% | Minor |
| #53 | 3.56% | Near-zero — Step 2 SP dominant signal is marginalised here |

### 8.2 Performance Summary

| Configuration | IS-train Sharpe | IS-val Sharpe | OOS Sharpe | OOS Ann. Return | OOS Vol | OOS Max DD |
|---------------|:---------------:|:-------------:|:----------:|:---------------:|:-------:|:----------:|
| `l57_s23` (baseline) | — | 1.830 | **2.152** | 26.74% | 11.33% | −4.54% |
| EW blend (all 1.0) | — | 1.771 | 0.909 | 9.21% | 10.27% | −6.81% |
| **Jointly optimised** | **1.631** | **2.248** | **1.156** | 13.17% | 11.24% | −5.35% |

### 8.3 Key Findings

1. **Design 03 also fails to beat `l57_s23`.** Jointly optimised blend OOS Sharpe 1.156 << baseline 2.152. The blend approach does not improve L/S performance regardless of optimisation context (isolated Step 2 or joint Step 3).

2. **Classic IS→OOS degradation.** IS-train 1.631 → IS-val 2.248 → OOS 1.156. The optimizer overfits to the 2021–2023 regime; the 2025–2026 OOS window is structurally different and the learnt weights fail to generalise.

3. **Joint optimisation changes the weight structure significantly.** LP side is far more balanced (vs #24 dominating at 61% in Step 2). SP side elevates #31 (49%, virtually absent in Step 2 SP-only at 2.4%) and reduces #53 (3.6%, dominant in Step 2 at 39%). The full L/S objective sees the interaction between the two sides and produces qualitatively different weights.

4. **`l57_s23` (Sharpe 2.152) is robust across all blend experiments.** This is the third consecutive experiment — Design 01 pair grid, Design 02 side-blend, Design 03 joint-blend — where the single-pair signal outperforms all blending strategies on OOS.

5. **Signal blending does not improve L/S performance in this universe.** With only 11 ETFs and weekly rebalancing, the cross-signal information gain from blending is insufficient to offset the overfitting cost of additional parameters. Single-signal `l57_s23` is the production configuration.

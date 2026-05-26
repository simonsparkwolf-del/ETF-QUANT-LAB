# Signal Optimization — Step 2: LP Signal Blend

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-14  
**Framework**: `architecture.md` §4 Step 2

---

## 1. Motivation

Step 1 IS LP screening identified the top five alpha candidates by IS LP Sharpe.
Each individually beats the equal-weight baseline on IS, but a **linear blend** may capture
complementary cross-sectional information and produce a more stable composite score.

Step 2 goal: find weights $w_k \geq 0$, $\sum_k w_k = 1$ such that

$$s_i = \sum_k w_k \cdot \alpha^{(k)}_i$$

maximises the LP Sharpe on a held-out validation window, verified on OOS.

---

## 2. Candidate Pool

Five alphas selected from Step 1 **IS LP ranking** (see `00_step1_screening.md`).
IS ranking is the selection criterion — OOS is a held-out result, never used to select candidates.

| Alpha | IS LP Sharpe | IS LP Δ vs EW | L/S status (IS SP) |
|-------|:------------:|:-------------:|:------------------:|
| #24 | 1.122 | +0.432 | IS SP best (−0.420) |
| #66 | 0.744 | +0.054 | IS SP −0.630 |
| #101 | 0.732 | +0.042 | IS SP −0.638 |
| #64 | 0.726 | +0.036 | IS SP −0.668 |
| #136 | 0.709 | +0.019 | IS SP −0.675 |

Equal-weight blend baseline (all $w_k = 0.2$) is included as the null hypothesis
for the optimised weights.

---

## 3. Signal Architecture — `AlphaBlendSignal`

```python
from QuantLab.backtest.signal.signal_blend import AlphaBlendSignal

signal = AlphaBlendSignal(weights={57: 0.4, 24: 0.2, 19: 0.2, 31: 0.1, 23: 0.1})
# signal.analyze() returns:
# symmetric(OrderedDict[ticker, blend_score])   ← higher = stronger long candidate
#
# blend_score_i = Σ_k  w_k * alpha_k_i
# weights are normalised internally: Σ w_k = 1
```

`AlphaBlendSignal` fetches all candidate alpha scores from `terminal.alphas()` in
a single call, computes the weighted sum per ticker, and wraps the result with
`symmetric()` (single-head signal for use with `SiganlOptimizationStrategy`).

---

## 4. Optimisation Design

### 4.1 Search Space

Five raw weights $u_k \in [0, 1]$, normalised to the probability simplex:

$$w_k = \frac{u_k}{\sum_j u_j}$$

This encodes the constraint $w_k \geq 0$, $\sum_k w_k = 1$ without requiring
explicit constraint handling in the sampler.

### 4.2 Objective

Maximise the LP Sharpe on the **optimise window** (IS train):

$$\mathcal{L}(w) = \text{Sharpe}\!\left(\text{LP backtest}(w,\; t \in [\text{IS\_TRAIN\_START},\; \text{IS\_TRAIN\_END}])\right)$$

The LP backtest uses `SiganlOptimizationStrategy(mode="long")` + `BaselineRisk`
under zero transaction costs (consistent with Step 1).

### 4.3 Walk-Forward Windows

| Window | Dates | Bars | Role |
|--------|-------|:----:|------|
| IS train | 2021-03-03 → 2023-12-31 | ~150 | Bayesian optimisation target |
| IS val | 2024-01-01 → 2024-12-31 | ~52 | Overfitting check (unseen during search) |
| OOS test | 2025-01-01 → 2026-03-01 | 61 | Final out-of-sample result |

Optimal weights are selected on IS-train Sharpe.
IS-val and OOS results are computed after optimisation is complete — they are
**never used to select or adjust weights**.

### 4.4 Bayesian Optimiser

| Setting | Value |
|---------|-------|
| Library | `optuna` |
| Sampler | `TPESampler` (Tree-structured Parzen Estimator) |
| Direction | maximise |
| Trials | 150 |
| Pruner | `MedianPruner` (prune trials below median at mid-point) |
| Seed | 42 |

### 4.5 Regularisation

No explicit L1/L2 penalty on weights — the simplex constraint (non-negativity +
sum-to-one) already limits the effective complexity. Post-hoc: if IS-val Sharpe
degrades > 0.3 vs IS-train Sharpe, the result is flagged as overfitted and
the equal-weight blend is preferred instead.

---

## 5. Baselines to Beat

| Reference | LP Sharpe (IS-val window) | LP Sharpe (OOS) |
|-----------|:-------------------------:|:---------------:|
| Equal-weight ETFs (Step 0) | TBD | 1.537 |
| Best single alpha IS — #24 (Step 1) | TBD | TBD |
| Equal-weight blend (all $w_k=0.2$) | TBD | TBD |
| **Optimised blend (Step 2)** | TBD | TBD |

The optimised blend must beat **both** Step 0 (EW ETFs) and Step 1 (#24 single, IS best)
on IS-val LP Sharpe to be considered a genuine improvement.

---

## 6. Run Script

```
backtests/signal_optimization/01 blend/long power/run.py
```

Outputs:
```
backtests/signal_optimization/01 blend/long power/outputs/
  study.pkl              — optuna study object (all 150 trials)
  best_weights.json      — {alpha_id: weight} for the best trial
  summary.json           — IS-train / IS-val / OOS metrics for key configs
  best_blend/            — full artifacts for the optimised blend (OOS window)
  single_alpha_24/       — reference run: single #24 (IS best) on OOS (comparison)
  equal_weight_blend/    — reference run: equal-weight blend on OOS
```

---

## 7. Results

### 7.1 Optimised Weights

| Alpha | Weight | Note |
|-------|:------:|------|
| #24 | **55.07%** | IS LP best; dominant contributor |
| #66 | **29.76%** | IS LP #2; strong second contributor |
| #101 | 7.98% | Minor contribution |
| #136 | 7.12% | Minor contribution |
| #64 | 0.08% | Near-zero — effectively excluded |

Optimiser concentrates weight on IS LP top-2 (#24 + #66 = 84.8%). The bottom three candidates contribute little.

### 7.2 Performance Summary

| Configuration | IS-train Sharpe | IS-val Sharpe | OOS Sharpe | OOS Ann. Return | OOS Vol | OOS Max DD |
|---------------|:---------------:|:-------------:|:----------:|:---------------:|:-------:|:----------:|
| EW ETFs (Step 0) | — | — | 1.537 | — | — | — |
| **Single #24 (IS best) ★** | — | **2.176** | **1.935** | **27.19%** | **12.88%** | **−12.21%** |
| EW blend (all 0.2) | — | 1.707 | 1.611 | 17.23% | 10.21% | −10.48% |
| Optimised blend | 0.871 | 2.006 | 1.877 | 23.59% | 11.66% | −11.63% |

> ★ **IS-selected configuration: Single #24** (IS-val 2.176 > blend 2.006 > EW 1.707).

### 7.3 Key Findings

1. **Blend fails to beat single #24 on IS-val.** IS-val: single #24 (2.176) > optimised blend (2.006) > EW blend (1.707). IS-selection criterion favours single #24 — no blending improvement.

2. **OOS consistent with IS selection.** Single #24 OOS (1.935) > blend (1.877) > EW blend (1.611). IS/OOS rank order preserved — no divergence on LP side with IS-correct pool.

3. **Blend overfits IS-train.** IS-train Sharpe 0.871 vs IS-val 2.006 — large gap indicates the optimiser fits the 2021–2023 regime. Despite this, the blend still loses to single #24 on IS-val.

4. **#64 effectively excluded (0.08%).** Despite being IS LP #4, the optimiser assigns near-zero weight. IS LP top-2 (#24, #66) capture most of the useful signal in this blend context.

5. **Conclusion: single #24 is the IS-selected LP configuration.** Blending within the IS-correct pool does not improve over the IS-best single alpha. Simple IS-based selection dominates.
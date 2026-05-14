# Signal Optimization — Step 2: SP Signal Blend

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-14  
**Framework**: `architecture.md` §4 Step 2

---

## 1. Motivation

Step 1 IS SP screening identified the top five alpha candidates by IS SP Sharpe.
A **linear blend** may capture complementary cross-sectional information on the short
side and produce a more stable composite short-ranking signal.

Step 2 goal: find weights $w_k \geq 0$, $\sum_k w_k = 1$ such that

$$s_i = \sum_k w_k \cdot \alpha^{(k)}_i$$

maximises the SP Sharpe on a held-out validation window, verified on OOS.

---

## 2. Candidate Pool

Five alphas selected from Step 1 **IS SP ranking** (see `00_step1_screening.md`).
IS ranking is the selection criterion — OOS is a held-out result, never used to select candidates.

| Alpha | IS SP Sharpe | IS SP Δ vs EW | L/S status (IS LP) |
|-------|:------------:|:-------------:|:------------------:|
| #24 | −0.420 | +0.270 | IS LP best (1.122) |
| #57 | −0.559 | +0.131 | IS LP 0.691 |
| #19 | −0.593 | +0.097 | IS LP 0.564 |
| #51 | −0.621 | +0.069 | IS LP 0.618 |
| #66 | −0.630 | +0.060 | IS LP 0.744 |

Equal-weight blend baseline (all $w_k = 0.2$) is included as the null hypothesis
for the optimised weights.

---

## 3. Signal Architecture — `AlphaBlendSignal`

```python
from QuantLab.backtest.signal.signal_blend import AlphaBlendSignal

signal = AlphaBlendSignal(weights={23: 0.4, 53: 0.2, 31: 0.2, 19: 0.1, 57: 0.1})
# signal.analyze() returns:
# symmetric(OrderedDict[ticker, blend_score])
#
# blend_score_i = Σ_k  w_k * alpha_k_i
# SiganlOptimizationStrategy(mode="short") shorts the bottom-ranked tickers
# weights are normalised internally: Σ w_k = 1
```

Reuses `AlphaBlendSignal` — no new class needed. The strategy in `mode="short"`
consumes `scores["short"]` and shorts the bottom-ranked ETFs by blend score.

---

## 4. Optimisation Design

### 4.1 Search Space

Five raw weights $u_k \in [0, 1]$, normalised to the probability simplex:

$$w_k = \frac{u_k}{\sum_j u_j}$$

### 4.2 Objective

Maximise the SP Sharpe on the **optimise window** (IS train):

$$\mathcal{L}(w) = \text{Sharpe}\!\left(\text{SP backtest}(w,\; t \in [\text{IS\_TRAIN\_START},\; \text{IS\_TRAIN\_END}])\right)$$

The SP backtest uses `SiganlOptimizationStrategy(mode="short")` + `BaselineRisk`
under zero transaction costs (consistent with Step 1). SP Sharpe is negative for
a poor signal and improves toward zero / positive for a good short signal.

### 4.3 Walk-Forward Windows

| Window | Dates | Bars | Role |
|--------|-------|:----:|------|
| IS train | 2021-03-03 → 2023-12-31 | ~150 | Bayesian optimisation target |
| IS val | 2024-01-01 → 2024-12-31 | ~52 | Overfitting check (unseen during search) |
| OOS test | 2025-01-01 → 2026-03-01 | 61 | Final out-of-sample result |

### 4.4 Bayesian Optimiser

| Setting | Value |
|---------|-------|
| Library | `optuna` |
| Sampler | `TPESampler` (seed=42) |
| Direction | maximise |
| Trials | 150 |
| Pruner | `MedianPruner` (n_startup_trials=20) |
| Seed | 42 |

### 4.5 Regularisation

Same as LP blend: simplex constraint provides implicit regularisation. Overfitting
flag: IS-val SP Sharpe degrades > 0.3 vs IS-train SP Sharpe → prefer EW blend.

---

## 5. Baselines to Beat

| Reference | SP Sharpe (IS-val) | SP Sharpe (OOS) |
|-----------|--------------------|:---------------:|
| Equal-weight ETFs (Step 0) | TBD | −1.537 |
| Best single alpha IS — #24 (Step 1) | TBD | TBD |
| Equal-weight blend (all $w_k=0.2$) | TBD | TBD |
| **Optimised blend (Step 2)** | TBD | TBD |

The optimised blend must beat **both** Step 0 (EW ETFs) and Step 1 (#24 single, IS best)
on IS-val SP Sharpe to be considered a genuine improvement.

---

## 6. Run Script

```
backtests/signal_optimization/01 blend/short power/run.py
```

Outputs:
```
backtests/signal_optimization/01 blend/short power/outputs/
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
| #66 | **50.52%** | IS SP #5; dominant contributor despite lower IS SP rank |
| #19 | **24.13%** | IS SP #3; solid contribution |
| #51 | 14.58% | IS SP #4 |
| #57 | 10.62% | IS SP #2 |
| #24 | 0.15% | IS SP best — near-zero, effectively excluded |

Optimiser concentrates weight on #66 + #19 + #51 (89.2%). #24 (IS SP best) is almost entirely ignored — the 2021–2023 regime favours different signals than IS overall ranking suggests.

### 7.2 Performance Summary

| Configuration | IS-train Sharpe | IS-val Sharpe | OOS Sharpe | OOS Ann. Return | OOS Vol | OOS Max DD |
|---------------|:---------------:|:-------------:|:----------:|:---------------:|:-------:|:----------:|
| EW ETFs (Step 0) | — | — | −1.537 | — | — | — |
| **Single #24 (IS best) ★** | — | **−0.647** | **−0.704** | **−8.32%** | **11.41%** | **−15.81%** |
| EW blend (all 0.2) | — | −1.611 | −0.760 | −8.68% | 11.13% | −15.83% |
| Optimised blend | −1.307 | −1.605 | −0.886 | −8.61% | 9.64% | −15.12% |

> ★ **IS-selected configuration: Single #24** (IS-val −0.647 >> blend −1.605 >> EW −1.611). Higher = better for SP Sharpe.

### 7.3 Key Findings

1. **Blend fails dramatically on IS-val.** Single #24 IS-val (−0.647) >> optimised blend (−1.605) ≈ EW blend (−1.611). IS selection is unambiguously single #24 — the blend adds no value.

2. **OOS consistent with IS selection.** Single #24 OOS (−0.704) beats blend (−0.886) and EW blend (−0.760). IS/OOS rank preserved on SP side.

3. **#24 (IS SP best) gets near-zero blend weight (0.15%).** The IS-train optimiser (2021–2023) essentially ignores the IS-period-wide best signal, instead promoting #66 (IS SP #5) to 50.5%. This is regime-specific overfitting: #24's IS SP advantage is concentrated outside 2021–2023.

4. **Blend overfits IS-train (−1.307) to IS-val (−1.605).** Degradation of 0.298 — right at the overfitting flag threshold (0.3). The optimised blend is worse than both alternatives on every evaluation window.

5. **Conclusion: single #24 is the IS-selected SP configuration.** Blending adds complexity without any benefit. The SP side is better served by the IS-best single signal directly.

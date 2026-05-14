# Signal Optimization — Step 2: SP Signal Blend

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-14  
**Framework**: `architecture.md` §4 Step 2

---

## 1. Motivation

Step 1 OOS SP screening identified five alpha candidates with SP Δ vs EW > 0.40.
A **linear blend** may capture complementary cross-sectional information on the short
side and produce a more stable composite short-ranking signal.

Step 2 goal: find weights $w_k \geq 0$, $\sum_k w_k = 1$ such that

$$s_i = \sum_k w_k \cdot \alpha^{(k)}_i$$

maximises the SP Sharpe on a held-out validation window, verified on OOS.

---

## 2. Candidate Pool

Five alphas selected from Step 1 OOS SP ranking (see `00_step1_screening.md`).
#53 is included despite being S-only in the L/S framework — in SP-only
optimisation there is no LP constraint.

| Alpha | OOS SP Sharpe | OOS SP Δ vs EW | L/S status |
|-------|:-------------:|:--------------:|:----------:|
| #23 | −0.522 | +1.015 | ✓ L/S |
| #53 | −0.530 | +1.007 | S only |
| #31 | −0.895 | +0.642 | ✓ L/S |
| #19 | −1.104 | +0.433 | ✓ L/S |
| #57 | −1.136 | +0.401 | ✓ L/S |

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
| Best single alpha — #23 (Step 1) | TBD | −0.522 |
| Equal-weight blend (all $w_k=0.2$) | TBD | TBD |
| **Optimised blend (Step 2)** | TBD | TBD |

The optimised blend must beat **both** Step 0 (EW ETFs) and Step 1 (#23 single)
on OOS SP Sharpe to be considered a genuine improvement.

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
  single_alpha_23/       — reference run: single #23 on OOS (comparison)
  equal_weight_blend/    — reference run: equal-weight blend on OOS
```

---

## 7. Results

> Pending — run `backtests/signal_optimization/01 blend/short power/run.py`.

### 7.1 Optimised Weights

| Alpha | Weight |
|-------|:------:|
| #23 | TBD |
| #53 | TBD |
| #31 | TBD |
| #19 | TBD |
| #57 | TBD |

### 7.2 Performance Summary

| Configuration | IS-train Sharpe | IS-val Sharpe | OOS Sharpe | OOS Ann. Return | OOS Vol | OOS Max DD |
|---------------|:---------------:|:-------------:|:----------:|:---------------:|:-------:|:----------:|
| EW ETFs (Step 0) | — | — | −1.537 | — | — | — |
| Single #23 (Step 1) | — | TBD | −0.522 | TBD | TBD | TBD |
| EW blend (all 0.2) | — | TBD | TBD | TBD | TBD | TBD |
| **Optimised blend** | TBD | TBD | TBD | TBD | TBD | TBD |

### 7.3 Key Findings

> To be filled after results are available.

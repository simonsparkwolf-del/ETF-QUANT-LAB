# Signal Optimization — Step 2: LP Signal Blend

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-14  
**Framework**: `architecture.md` §4 Step 2

---

## 1. Motivation

Step 1 OOS LP screening identified five alpha candidates with LP Δ vs EW > 0.29.
Each individually beats the equal-weight baseline, but a **linear blend** may capture
complementary cross-sectional information and produce a more stable composite score.

Step 2 goal: find weights $w_k \geq 0$, $\sum_k w_k = 1$ such that

$$s_i = \sum_k w_k \cdot \alpha^{(k)}_i$$

maximises the LP Sharpe on a held-out validation window, verified on OOS.

---

## 2. Candidate Pool

Five alphas selected from Step 1 OOS LP ranking (see `00_step1_screening.md`).
#24 is included here despite being L-only in the L/S framework — in LP-only
optimisation there is no SP constraint.

| Alpha | OOS LP Sharpe | OOS LP Δ vs EW | L/S status |
|-------|:-------------:|:--------------:|:----------:|
| #57 | 2.174 | +0.637 | ✓ L/S |
| #24 | 2.055 | +0.518 | L only |
| #19 | 2.014 | +0.477 | ✓ L/S |
| #31 | 1.854 | +0.317 | ✓ L/S |
| #23 | 1.829 | +0.292 | ✓ L/S |

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
| Best single alpha — #57 (Step 1) | TBD | 2.174 |
| Equal-weight blend (all $w_k=0.2$) | TBD | TBD |
| **Optimised blend (Step 2)** | TBD | TBD |

The optimised blend must beat **both** Step 0 (EW ETFs) and Step 1 (#57 single)
on OOS LP Sharpe to be considered a genuine improvement.

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
  single_alpha_57/       — reference run: single #57 on OOS (comparison)
  equal_weight_blend/    — reference run: equal-weight blend on OOS
```

---

## 7. Results

> Pending — run `backtests/signal_optimization/step2/long_only/run.py`.

### 7.1 Optimised Weights

| Alpha | Weight |
|-------|:------:|
| #57 | TBD |
| #24 | TBD |
| #19 | TBD |
| #31 | TBD |
| #23 | TBD |

### 7.2 Performance Summary

| Configuration | IS-train Sharpe | IS-val Sharpe | OOS Sharpe | OOS Ann. Return | OOS Max DD |
|---------------|:---------------:|:-------------:|:----------:|:---------------:|:----------:|
| EW ETFs (Step 0) | — | — | 1.537 | — | — |
| Single #57 (Step 1) | TBD | TBD | 2.174 | TBD | TBD |
| EW blend (all 0.2) | TBD | TBD | TBD | TBD | TBD |
| **Optimised blend** | TBD | TBD | TBD | TBD | TBD |

### 7.3 Key Findings

> To be filled after results are available.
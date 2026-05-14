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

### 7.1 Optimised Weights

| Alpha | Weight | Note |
|-------|:------:|------|
| #53 | 38.71% | S-only in Step 1; dominant contributor when freed from LP constraint |
| #57 | 37.53% | Top LP signal; carries meaningful short-side information |
| #19 | 20.53% | Solid all-around contributor |
| #31 | 2.37% | Near-zero — effectively excluded |
| #23 | 0.86% | Near-zero — Step 1 best SP single signal nearly dropped |

The optimiser concentrates weight on #53 and #57, together accounting for ~76% of
the blend. #23 — the dominant single signal in Step 1 — is almost entirely ignored,
mirroring the LP result where #57 collapsed to 0.34%.

### 7.2 Performance Summary

| Configuration | IS-train Sharpe | IS-val Sharpe | OOS Sharpe | OOS Ann. Return | OOS Vol | OOS Max DD |
|---------------|:---------------:|:-------------:|:----------:|:---------------:|:-------:|:----------:|
| EW ETFs (Step 0) | — | — | −1.537 | — | — | — |
| Single #23 (Step 1 screen.) | — | — | −0.522 | — | — | — |
| Single #23 (this backtest) | — | −1.589 | −0.790 | −8.69% | 10.78% | −15.08% |
| EW blend (all 0.2) | — | −1.678 | −0.693 | −8.03% | 11.19% | −16.12% |
| **Optimised blend** | **−1.234** | **−1.523** | **−0.496** | **−6.34%** | **11.81%** | **−15.32%** |

> Note: "Single #23 (this backtest)" uses `SiganlOptimizationStrategy(mode="short")` +
> `BaselineRisk`, producing a slightly different Sharpe than the Step 1 screening value
> (−0.790 vs −0.522). The gap may reflect BaselineRisk drawdown protection triggering
> near the −15% max drawdown level.

### 7.3 Key Findings

1. **Blend beats all baselines on OOS SP Sharpe.** Optimised blend (−0.496) > single #23 screen (−0.522) > EW blend (−0.693) > EW ETFs (−1.537). OOS Δ vs EW = +1.041, comparable to Step 1 best single signal.

2. **#23 weight collapses to near-zero (0.86%).** Mirror of LP blend where #57 fell to 0.34%. The best Step 1 single signal is not the most useful blend component — #53 (S-only, previously constrained) and #57 together dominate at 76%.

3. **IS-train Sharpe (−1.234) is weaker than OOS (−0.496).** The 2021–2023 regime was unfavourable for short signals (persistent bull market). The 2025–2026 OOS window provided better shorting opportunities.

4. **Overfitting diagnostic: borderline pass.** IS-val (−1.523) degrades by 0.289 vs IS-train (−1.234), just below the 0.3 flag threshold. The optimised blend is accepted, but the margin is thin.

5. **#53 (S-only) is the key unlocked contributor.** Excluded from L/S in Step 1 due to weak LP, it becomes the top weight (38.71%) once the LP constraint is lifted in SP-only optimisation — exactly the design intent of separating LP and SP pools.

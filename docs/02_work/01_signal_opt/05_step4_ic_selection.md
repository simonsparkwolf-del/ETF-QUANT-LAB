# Signal Optimization — Step 4: IC-Driven Dynamic Signal Selection

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-15  
**Framework**: `architecture.md` §4 Step 4  
**Strategy**: feeds into `trading_opt/04_dynamic_allocation_test.md`

---

## 1. Motivation

Steps 1–3 all use **static** signal selection: a signal is chosen once based on IS history and deployed unchanged through the OOS period. Design 01 shows the consequence — IS-selected `l24_s66` achieves IS Sharpe 1.236 but collapses to OOS −0.853. The IS 2021–2024 regime does not represent OOS 2025–2026.

Steps 2–3 attempted to improve signal quality via blending (fixed weights). The conclusion: **blending on static weights adds no IS-val benefit and does not resolve IS/OOS divergence.**

Step 4 abandons static selection entirely. Instead of asking "which alpha is best over the IS period?", it asks **"which alpha has been most predictive recently?"** — and re-asks this question every rebalance period.

---

## 2. Candidate Pools

Pools remain fixed at IS-correct Step 1 rankings. Step 4 selects dynamically *within* these pools; it does not change the pool boundaries.

| Side | Pool | Members |
|------|------|---------|
| Long (LP) | IS LP top-5 by Sharpe | #24 (1.122), #66 (0.744), #101 (0.732), #64 (0.726), #136 (0.709) |
| Short (SP) | IS SP top-5 by Sharpe | #24 (−0.420), #57 (−0.559), #19 (−0.593), #51 (−0.621), #66 (−0.630) |

Pool selection uses IS data only. Rolling IC selection within the pool uses only data available up to the current period — no lookahead.

---

## 3. Rolling IC Computation

At each rebalance date `t`, compute rolling Spearman IC for every alpha `a` in the pool over the past `ic_lookback_n` weeks:

$$\text{IC}^a_t = \frac{1}{N} \sum_{k=1}^{N} \text{SpearmanCorr}\!\left(s^a_{t-k},\; r_{t-k+1}\right)$$

| Term | Description |
|------|-------------|
| `s^a_{t-k}` | Cross-sectional alpha scores for alpha `a` at week `t−k` (11 ETFs) |
| `r_{t-k+1}` | Realised weekly returns at week `t−k+1` |
| `N` | Lookback window (`ic_lookback_n`) — hyperparameter |

Spearman (rank) correlation is used throughout — robust to outliers in a small cross-section of 11 ETFs.

---

## 4. Dynamic Alpha Selection

One alpha is selected per side each period based on rolling IC:

**Long side** — select the alpha whose recent scores have been most positively correlated with forward returns:

$$a^*_{\text{long},t} = \arg\max_{a \in \text{LP pool}} \; \text{IC}^a_t$$

**Short side** — select the alpha whose recent scores have been most negatively correlated with forward returns (short the predicted losers):

$$a^*_{\text{short},t} = \arg\min_{a \in \text{SP pool}} \; \text{IC}^a_t$$

Selection is re-evaluated every rebalance. There is no lock-in period — if a better alpha emerges in the pool, it is adopted immediately.

---

## 5. IC as Exposure Signal

The IC of the selected alpha also determines how much capital to deploy on that side. A high IC means the signal is currently strong; near-zero IC means the signal has no predictive power.

$$\text{exposure}^{\text{long}}_t = \text{nav} \times \text{clip}\!\left(\frac{\text{IC}^{a^*_{\text{long}}}_t}{\max_{a \in \text{LP}} \text{IC}^a_t},\; 0,\; 1\right)$$

$$\text{exposure}^{\text{short}}_t = \text{nav} \times \text{clip}\!\left(\frac{|\text{IC}^{a^*_{\text{short}}}_t|}{\max_{a \in \text{SP}} |\text{IC}^a_t|},\; 0,\; 1\right)$$

When the best IC in the pool is ≤ 0, that side automatically goes to zero — no position taken when there is no evidence of predictive power.

---

## 6. Comparison with Prior Steps

| Step | Selection method | Weights | Adapts over time? |
|------|-----------------|---------|:-----------------:|
| Step 1 | IS Sharpe ranking (one-time) | n/a | ✗ |
| Step 2 | Bayesian blend (IS-train weights) | fixed | ✗ |
| Step 3 | Joint optuna (IS-train weights) | fixed | ✗ |
| **Step 4** | **Rolling IC per period** | **IC-proportional** | **✓** |

Step 4 is the only approach that responds to regime change. Steps 1–3 are all static; their weights or selections are frozen at IS time.

---

## 7. Key Properties

**Self-correcting:** if an alpha's IC degrades (as #24 long did in OOS 2025–2026), a better-IC alpha from the pool is automatically promoted.

**No threshold tuning:** exposure scales continuously with IC — no `IC_target` hyperparameter needed. The pool's own IC distribution sets the reference.

**Minimal parameters:** only `ic_lookback_n` controls the signal logic. The two softmax temperatures (`τ_L`, `τ_S`) are strategy-layer parameters, not signal-layer.

**Graceful degradation:** if all pool ICs are ≤ 0, exposure → 0. The strategy goes flat rather than trading a signal with no edge.

---

## 8. Hyperparameter

| Parameter | Description | Search range | Layer |
|-----------|-------------|:------------:|-------|
| `ic_lookback_n` | Rolling IC window (weeks) | 4 – 26 | Signal |
| `tau_long` | Softmax temperature, long positions | 0 – 5 | Strategy |
| `tau_short` | Softmax temperature, short positions | 0 – 5 | Strategy |

Optimisation: optuna TPE on IS-train Sharpe (2021-03-03 → 2023-12-31). Full backtest details in `trading_opt/04_dynamic_allocation_test.md`.

---

## 9. Results

> **TBD** — see `trading_opt/04_dynamic_allocation_test.md` §10.

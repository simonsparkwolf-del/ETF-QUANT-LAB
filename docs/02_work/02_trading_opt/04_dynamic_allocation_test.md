# Design 04 — IC-Driven Dynamic Allocation

**Author**: Simon  
**Version**: v0.2  
**Updated**: 2026-05-15  
**Implementation**: `DynamicAllocStrategy` / `LongShortAlphaSignal` / `BaselineRisk`

---

## Parameter Map

### Optimisable Parameters

| Parameter | Description | Search Range |
|-----------|-------------|:------------:|
| `ic_lookback_n` | Rolling IC lookback window (weeks) | 4 – 26 |
| `tau_long` | Softmax temperature, long-side sizing | 0 – 5 |
| `tau_short` | Softmax temperature, short-side sizing | 0 – 5 |

### Fixed Parameters

| Parameter | Value | Reason |
|-----------|:-----:|--------|
| `long_alpha_pool` | (24, 66, 101, 64, 136) | IS LP top-5 (Step 1) |
| `short_alpha_pool` | (24, 57, 19, 51, 66) | IS SP top-5 (Step 1) |
| `n_long` | 3 | unchanged from Design 01 |
| `n_short` | 3 | unchanged from Design 01 |
| `stickiness_threshold` | **0** | released — IC gate replaces stickiness |
| `dd_light` | 0.10 | Risk module unchanged |
| `dd_heavy` | 0.15 | Risk module unchanged |
| `dd_recovery` | 0.08 | Risk module unchanged |
| `recovery_weeks` | 2 | Risk module unchanged |

> Only 3 parameters to optimise. Pool fixed at IS-correct Step 1 rankings — no new selection step introduced.

---

## 1. Motivation

Design 01 exposes two failures of the fixed-allocation approach:

**Short side destroys OOS value.** Alpha #24 long-only achieves OOS Sharpe 1.935. Adding the short leg (`l24_s24`) collapses OOS to −0.011. A fixed short allocation has no mechanism to respond when the signal loses predictive power.

**Equal weight ignores signal conviction.** All 3 long / 3 short positions receive identical capital regardless of how strong or differentiated the signal scores are.

**Root cause of both failures:** signal selection and position sizing are both static. They are decided at IS time and never updated.

**Design 04 fix:** use rolling IC as the single adaptive mechanism for (1) which alpha to deploy each period and (2) how much capital to risk on each side. Stickiness is released because IC already suppresses unnecessary turnover by scaling down exposure when signal quality degrades.

---

## 2. What Changed vs `DualSignalStrategy`

| Component | `DualSignalStrategy` (Design 01) | `DynamicAllocStrategy` (Design 04) |
|-----------|----------------------------------|-------------------------------------|
| Signal | fixed `long_alpha_id`, `short_alpha_id` | selected each period from pool by rolling IC |
| Long alpha pool | n/a (single alpha) | IS LP top-5: #24, #66, #101, #64, #136 |
| Short alpha pool | n/a (single alpha) | IS SP top-5: #24, #57, #19, #51, #66 |
| Long total exposure | fixed `nav` | `nav × norm(IC_long)` |
| Short total exposure | fixed `nav` | `nav × norm(IC_short)` |
| Within-side sizing | equal weight `exposure / n` | `softmax(τ × scores)` |
| Stickiness | threshold = 2 | **threshold = 0** (released) |
| Risk module | `BaselineRisk` | `BaselineRisk` (identical) |

---

## 3. Signal Pool

Pools are fixed at IS-correct Step 1 rankings. Selection within the pool is dynamic (rolling IC), but the pool boundary itself is determined once from IS data.

| Side | Pool | Selection criterion (Step 1) |
|------|------|------------------------------|
| Long | #24, #66, #101, #64, #136 | IS LP Sharpe descending |
| Short | #24, #57, #19, #51, #66 | IS SP Sharpe ascending (most negative) |

---

## 4. Rolling IC Computation

At each rebalance date `t`, compute rolling Spearman IC for every alpha `a` in the pool over the past `ic_lookback_n` weeks:

$$\text{IC}^a_t = \frac{1}{N} \sum_{k=1}^{N} \text{SpearmanCorr}\!\left(s^a_{t-k},\; r_{t-k+1}\right)$$

Where `s` = alpha scores across the 11 ETFs, `r` = realised weekly returns.

---

## 5. Alpha Selection per Side

Each period, one alpha is selected per side based on rolling IC:

$$a^*_{\text{long}} = \arg\max_{a \in \text{LP pool}} \; \text{IC}^a_t$$

$$a^*_{\text{short}} = \arg\min_{a \in \text{SP pool}} \; \text{IC}^a_t \quad \text{(most negative)}$$

The selected alpha provides the signal scores for that period. Selection updates every rebalance — there is no lock-in period.

---

## 6. Exposure Scaling by IC

Total capital deployed per side scales with the IC of the selected alpha, normalised by the maximum observed IC in the pool:

$$\text{long\_exposure}_t = \text{nav} \times \text{clip}\!\left(\frac{\text{IC}^{a^*_{\text{long}}}_t}{\max_{a} \text{IC}^a_t},\; 0,\; 1\right)$$

$$\text{short\_exposure}_t = \text{nav} \times \text{clip}\!\left(\frac{|\text{IC}^{a^*_{\text{short}}}_t|}{\max_{a} |\text{IC}^a_t|},\; 0,\; 1\right)$$

When the best available IC in the pool is ≤ 0, that side goes to zero exposure automatically.

---

## 7. Softmax Position Sizing

Within each side, capital is distributed across the top-`n` positions via softmax over signal scores:

$$w_i = \frac{e^{\tau \cdot s_i}}{\sum_{j=1}^{n} e^{\tau \cdot s_j}}, \qquad \text{position}_i = \text{exposure} \times w_i$$

`τ = 0` degrades to equal weight. Long and short sides use independent temperatures `τ_L`, `τ_S`.

---

## 8. Baselines

| Reference | IS Sharpe | OOS Sharpe | Note |
|-----------|:---------:|:----------:|------|
| `l24_s66` fixed (Design 01 IS-selected) | 1.236 | −0.853 | static allocation; OOS catastrophic |
| `l24_s24` fixed (Design 01 symmetric) | 0.213 | −0.011 | static allocation; both weak |
| Alpha #24 long-only (SigOpt Step 2) | 2.176 (IS-val) | 1.935 | best IS/OOS consistent reference |

Target: IS-selected Design 04 config must beat `l24_s66` on IS Sharpe; OOS is holdout.

---

## 9. Backtest Parameters

| Parameter | Value |
|-----------|-------|
| IS-train window | 2021-03-03 → 2023-12-31 |
| IS-val window | 2024-01-01 → 2024-12-31 |
| OOS window | 2025-01-01 → 2026-03-01 |
| Initial NAV | 10,000 |
| `n_long` | 3 |
| `n_short` | 3 |
| `long_cost` | 0.0 |
| `short_cost_per_day` | 0.0 |
| `base_slippage` | 0.0 |

Optimisation: optuna TPE, 200 trials, maximise IS-train Sharpe.

Run script: `backtests/dynamic_alloc/no_trans_cost/run.py` *(TBD)*

---

## 10. Results

> **TBD**

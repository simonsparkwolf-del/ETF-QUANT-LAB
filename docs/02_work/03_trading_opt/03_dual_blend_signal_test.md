# Design 02 — Dual-Blend L/S (Step 2 Optimised Blends per Side)

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-14  
**Implementation**: `LongShortBlendSignal` / `DualSignalStrategy` / `BaselineRisk`

---

## 1. Motivation

Step 2 LP/SP blend optimisation produced independent optimised weight vectors for each side:

- **LP blend**: #24 (61%) + #19 (30%) dominates; #57 (best Step 1 single) nearly dropped
- **SP blend**: #53 (39%) + #57 (38%) dominates; #23 (best Step 1 single) nearly dropped

Both blends outperform their respective Step 1 single-signal baselines on OOS SP/LP Sharpe.

Design 02 wires these two optimised blends into a full L/S strategy via `LongShortBlendSignal`,
replacing the fixed single-alpha assignments of Design 01.

**Hypothesis**: LP blend + SP blend should capture more information on both sides
simultaneously, targeting OOS Sharpe > **2.220** (Design 01 best pair `l57_s23`, no-cost).

---

## 2. Signal Layer — `LongShortBlendSignal`

```python
from QuantLab.backtest.signal.dual_blend_signal import LongShortBlendSignal

# Step 2 optimised weights — TBD after re-running Step 2 with IS-correct candidate pools
LP_WEIGHTS = {}  # fill from backtests/signal_optimization/01 blend/long power/run.py output
SP_WEIGHTS = {}  # fill from backtests/signal_optimization/01 blend/short power/run.py output

signal = LongShortBlendSignal(lp_weights=LP_WEIGHTS, sp_weights=SP_WEIGHTS)
# signal.analyze() returns:
# {
#   "long":  OrderedDict[ticker, lp_blend_score],   # higher → better long
#   "short": OrderedDict[ticker, sp_blend_score],   # lower  → better short
# }
```

All alpha IDs from both pools are fetched in a **single** `terminal.alphas()` call.
LP and SP blend scores are computed independently from the same result DataFrame.

---

## 3. What Changed vs Design 01

| Component | Design 01 | Design 02 |
|-----------|-----------|-----------|
| Signal class | `LongShortAlphaSignal(long_id, short_id)` | `LongShortBlendSignal(lp_weights, sp_weights)` |
| Long ranking | Single alpha (e.g. #57) | LP blend: #24 61% + #19 30% + … |
| Short ranking | Single alpha (e.g. #23) | SP blend: #53 39% + #57 38% + … |
| Signal source | Step 1 best single per side | Step 2 Bayesian-optimised blend per side |
| Strategy | `DualSignalStrategy` | `DualSignalStrategy` (unchanged) |
| Risk | `BaselineRisk` | `BaselineRisk` (unchanged) |

---

## 4. Test Design

A **2 × 2 ablation grid** isolating the contribution of each side's blend upgrade:

| Config | Long signal | Short signal | Purpose |
|--------|------------|:------------:|---------|
| `l57_s23` | Single #57 | Single #23 | Design 01 best pair (baseline) |
| `lp_blend_s23` | LP blend | Single #23 | LP-only upgrade |
| `l57_sp_blend` | Single #57 | SP blend | SP-only upgrade |
| `lp_blend_sp_blend` | LP blend | SP blend | **Full Design 02 target** |

Window: **OOS only** (2025-01-01 → 2026-03-01, 61 bars).  
Weights are fixed from Step 2 — no in-sample selection needed here.

---

## 5. Optimised Weights (from Step 2)

> **TBD — fill after re-running Step 2 with IS-correct candidate pools.**
> Run: `backtests/signal_optimization/01 blend/long power/run.py` → LP weights
> Run: `backtests/signal_optimization/01 blend/short power/run.py` → SP weights

### LP Blend Weights (IS candidate pool: #24, #66, #101, #64, #136)

| Alpha | Weight |
|-------|:------:|
| #24 | TBD |
| #66 | TBD |
| #101 | TBD |
| #64 | TBD |
| #136 | TBD |

IS-train Sharpe: TBD · IS-val Sharpe: TBD · **OOS LP Sharpe: TBD**

### SP Blend Weights (IS candidate pool: #24, #57, #19, #51, #66)

| Alpha | Weight |
|-------|:------:|
| #24 | TBD |
| #57 | TBD |
| #19 | TBD |
| #51 | TBD |
| #66 | TBD |

IS-train Sharpe: TBD · IS-val Sharpe: TBD · **OOS SP Sharpe: TBD**

---

## 6. Run Script

```
backtests/dual_signal_blended/out_sample/run.py
```

Outputs:
```
backtests/dual_signal_blended/out_sample/outputs/
  summary.json
  comparison.md
  l57_s23/              Design 01 baseline reference
  lp_blend_s23/         LP-only upgrade
  l57_sp_blend/         SP-only upgrade
  lp_blend_sp_blend/    Design 02 full dual-blend
```

---

## 7. Results

> **TBD — re-run `backtests/dual_signal_blended/out_sample/run.py`**
> after filling LP_WEIGHTS and SP_WEIGHTS from the IS-correct Step 2 re-run.

### 7.1 Performance Summary (OOS 2025-01-01 → 2026-03-01)

| Config | OOS Sharpe | OOS Ann. Return | OOS Vol | OOS Max DD | Turnover Ann. |
|--------|:----------:|:---------------:|:-------:|:----------:|:-------------:|
| `l[IS-best]_s[IS-best]` (Design 01 IS-selected) | TBD | TBD | TBD | TBD | TBD |
| `lp_blend_s[IS-best]` | TBD | TBD | TBD | TBD | TBD |
| `l[IS-best]_sp_blend` | TBD | TBD | TBD | TBD | TBD |
| `lp_blend_sp_blend` | TBD | TBD | TBD | TBD | TBD |

### 7.2 Key Findings

TBD after re-run.

### 7.3 Conclusion

TBD after re-run.

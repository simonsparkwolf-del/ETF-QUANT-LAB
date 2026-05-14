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

# Step 2 optimised weights (normalised)
LP_WEIGHTS = {24: 0.610, 19: 0.304, 23: 0.073, 31: 0.010, 57: 0.003}
SP_WEIGHTS = {53: 0.387, 57: 0.375, 19: 0.205, 31: 0.024, 23: 0.009}

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

### LP Blend Weights

| Alpha | Weight | Step 2 LP OOS Sharpe (LP-only) |
|-------|:------:|:----:|
| #24 | 61.01% | — |
| #19 | 30.38% | — |
| #23 | 7.31% | — |
| #31 | 0.96% | — |
| #57 | 0.34% | — |

IS-train Sharpe: 0.936 · IS-val Sharpe: 2.069 · **OOS LP Sharpe: 2.130**

### SP Blend Weights

| Alpha | Weight | Step 2 SP OOS Sharpe (SP-only) |
|-------|:------:|:----:|
| #53 | 38.71% | — |
| #57 | 37.53% | — |
| #19 | 20.53% | — |
| #31 | 2.37% | — |
| #23 | 0.86% | — |

IS-train Sharpe: −1.234 · IS-val Sharpe: −1.523 · **OOS SP Sharpe: −0.496**

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

### 7.1 Performance Summary (OOS 2025-01-01 → 2026-03-01)

| Config | OOS Sharpe | OOS Ann. Return | OOS Vol | OOS Max DD | Turnover Ann. |
|--------|:----------:|:---------------:|:-------:|:----------:|:-------------:|
| `l57_s23` (Design 01 best) | **2.190** | 28.02% | 11.61% | −4.54% | 5506% |
| `lp_blend_s23` | 0.492 | 4.53% | 9.99% | −7.93% | 3754% |
| `l57_sp_blend` | 1.691 | 19.78% | 11.04% | −6.12% | 5511% |
| `lp_blend_sp_blend` | 0.650 | 5.78% | 9.30% | −9.14% | 3925% |

**Design 02 target missed.** `lp_blend_sp_blend` Sharpe 0.650 << target 2.220.  
`l57_s23` remains the best configuration.

### 7.2 Key Findings

1. **LP blend on the long side catastrophically degrades performance.** Replacing #57 with the LP blend drops Sharpe from 2.190 → 0.492. The blend's dominant component #24 (61% weight) is an L-only signal (OOS SP −2.339) that works in long-only isolation but produces inferior long-side rankings in the full L/S context.

2. **SP blend on the short side also hurts.** `l57_sp_blend` (1.691) < `l57_s23` (2.190), though the degradation is less severe. The SP blend was optimised in short-only mode; the composite ranking it produces is suboptimal when interacting with `DualSignalStrategy`'s conflict-resolution and stickiness logic.

3. **Full dual-blend is the worst config (0.650).** Both side degradations compound — the opposite of what Design 02 hypothesised.

4. **Root cause: context mismatch.** Step 2 LP/SP blends were optimised in side-specific standalone backtests (long-only or short-only) on IS-train 2021–2023. Those weights do not generalise to the full L/S OOS context. The IS-train optimal weights heavily favour #24 (LP blend) and #53/#57 (SP blend), which carry different information than #57/#23 in the 2025–2026 regime.

5. **Single-signal pairing remains more robust than blend aggregation for L/S.** The LP/SP blend approach adds complexity without benefit in the current signal universe. Step 1 single signals remain the strongest direct inputs into the L/S strategy.

### 7.3 Conclusion

Design 02 is a **negative result**: Step 2 Bayesian blend weights do not transfer from side-specific optimisation to the full L/S strategy. Design 01 `l57_s23` (Sharpe 2.190) is retained as the production configuration. Future work should consider optimising blend weights **directly on the full L/S objective** rather than on isolated LP/SP Sharpe.

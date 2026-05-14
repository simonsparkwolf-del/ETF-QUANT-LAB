# Dual-Signal Strategy — Independent L/S Alpha Ranking

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-14  
**Implementation**: `DualSignalStrategy` / `LongShortAlphaSignal` / `BaselineRisk`

---

## 1. Motivation

Step 1 IS screening (`signal_opt/00_step1_screening.md`) shows **#24 dominates both IS LP (1.122) and IS SP (−0.420)**. `BaselineStrategy` forces both sides to share one ranking — a symmetric `l24_s24` pair is the IS-baseline.

This test measures whether giving each side its own independent signal — drawing from the IS LP pool on the long side and the IS SP pool on the short side — produces a higher IS Sharpe than the symmetric baseline. IS Sharpe is the selection criterion; OOS is reported as holdout validation.

**Hypothesis**: asymmetric pairing should improve IS Sharpe over symmetric `l24_s24`, capturing complementary information on each side.

---

## 2. What Changed vs `BaselineStrategy`

| Component | `BaselineStrategy` | `DualSignalStrategy` |
|-----------|-------------------|---------------------|
| Signal class | `AlphaBacktestSignal(id)` | `LongShortAlphaSignal(long_id, short_id)` |
| Long ranking | `scores["long"]` (= only signal) | `scores["long"]` (LP-optimised alpha) |
| Short ranking | same as long | `scores["short"]` (SP-optimised alpha) |
| Conflict resolution | n/a (one ranking, no conflict) | long takes priority; conflicted ticker dropped from short |
| Alpha_110 short filter | unchanged | unchanged |
| Rank stickiness | unified | independent per side (each uses its own ranking) |
| Risk module | `BaselineRisk` | `BaselineRisk` (identical) |
| Position sizing | `nav / n_long` / `nav / n_short` | unchanged |

Symmetric pairs (`long_id == short_id`) reproduce `BaselineStrategy` results exactly and serve as in-grid baselines.

---

## 3. Signal Layer — `LongShortAlphaSignal`

```python
from QuantLab.backtest.signal.dual_head_alpha_signal import LongShortAlphaSignal

signal = LongShortAlphaSignal(long_alpha_id=57, short_alpha_id=23)
# signal.analyze() returns:
# {
#   "long":  OrderedDict[ticker, alpha_57_score],   # higher → better long
#   "short": OrderedDict[ticker, alpha_23_score],   # lower  → better short
# }
```

`DualSignalStrategy` consumes `scores["long"]` for `_target_longs()` and `scores["short"]` for `_target_shorts()`.

---

## 4. Alpha Candidate Pools

Selected from Step 1 **IS LP/SP ranking**. IS Sharpe is the selection criterion.

| Pool | Criterion | Members |
|------|-----------|---------|
| `LONG_ALPHAS` | Top 4 IS LP Sharpe | #24, #66, #101, #64 |
| `SHORT_ALPHAS` | Top 5 IS SP Sharpe | #24, #57, #19, #51, #66 |

**Alpha profiles (IS):**

| Alpha | IS LP Sharpe | IS SP Sharpe | Role |
|-------|:------------:|:------------:|:----:|
| #24 | **1.122** | **−0.420** | IS best on both sides |
| #66 | 0.744 | −0.630 | IS LP #2; IS SP #5 |
| #101 | 0.732 | −0.638 | IS LP #3 |
| #64 | 0.726 | −0.668 | IS LP #4 |
| #57 | 0.691 | −0.559 | IS SP #2 (LP pool boundary) |
| #19 | 0.564 | −0.593 | IS SP #3 |
| #51 | 0.618 | −0.621 | IS SP #4 |

---

## 5. Test Grid

**20 pairs**: `LONG_ALPHAS × SHORT_ALPHAS` (4 × 5).

| Long ↓ \ Short → | #24 | #57 | #19 | #51 | #66 |
|:----------------:|:---:|:---:|:---:|:---:|:---:|
| **#24** | l24_s24 (sym) | l24_s57 | l24_s19 | l24_s51 | l24_s66 |
| **#66** | l66_s24 | l66_s57 | l66_s19 | l66_s51 | l66_s66 (sym) |
| **#101** | l101_s24 | l101_s57 | l101_s19 | l101_s51 | l101_s66 |
| **#64** | l64_s24 | l64_s57 | l64_s19 | l64_s51 | l64_s66 |

Symmetric pairs (marked **sym**) reproduce single-alpha `BaselineStrategy` results.

---

## 6. Baseline Comparison Reference

Results to beat (from `01_warmup_test.md`, `BaselineStrategy` + `BaselineRisk`):

| Split | Best single-alpha (IS) | IS Sharpe | OOS Sharpe |
|-------|------------------------|:---------:|:----------:|
| IS-best | Alpha#66 | 0.967 | — |
| Symmetric baseline in this grid | Alpha#24 `l24_s24` | TBD | TBD |

The primary IS target is: IS-selected pair must beat `l24_s24` (symmetric baseline in the new pool) on IS Sharpe. OOS Sharpe of the IS-selected pair is the holdout result.

---

## 7. Backtest Parameters

All runs: zero fee, zero slippage. Same calendar and initial NAV as Design 00.

| Parameter | Value |
|-----------|-------|
| IS window | 2021-03-03 → 2024-12-31 (200 periods) |
| OOS window | 2025-01-01 → 2026-03-01 (61 periods) |
| Initial NAV | 10,000 |
| `n_long` | 3 |
| `n_short` | 3 |
| `stickiness_threshold` | 2 |
| `long_cost` | 0.0 |
| `short_cost_per_day` | 0.0 |
| `base_slippage` | 0.0 |

Run scripts:
- IS → `backtests/dual_signal/no_trans_cost/in_sample/run.py`
- OOS → `backtests/dual_signal/no_trans_cost/out_sample/run.py`

---

## 8. Results

### 8.1 In-Sample Grid (2021-03-03 → 2024-12-31)

Sorted by Sharpe descending. Symmetric baseline `l24_s24` = 0.213, `l66_s66` = 1.177.

| Long α | Short α | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|:------:|:-------:|:------:|:-----------:|:--------:|:------:|:-------------:|
| **#24** | **#66** ★ | **1.236** | **15.72%** | **12.46%** | **−12.89%** | 3548% |
| #66 | #66 (sym) | 1.177 | 13.60% | 11.39% | −13.02% | 4550% |
| #101 | #66 | 1.177 | 13.27% | 11.12% | −13.47% | 3224% |
| #66 | #19 | 1.163 | 13.36% | 11.34% | −10.43% | 4505% |
| #66 | #51 | 1.124 | 13.08% | 11.54% | −10.19% | 4384% |
| #66 | #24 | 1.117 | 13.38% | 11.88% | −12.59% | 4305% |
| #101 | #19 | 1.092 | 11.44% | 10.43% | −13.78% | 3012% |
| #101 | #24 | 1.088 | 12.17% | 11.14% | −15.04% | 3218% |
| #66 | #57 | 1.049 | 9.83% | 9.36% | −11.13% | 3852% |
| #24 | #51 | 1.004 | 10.59% | 10.60% | −12.76% | 2851% |
| #101 | #57 | 0.980 | 10.05% | 10.32% | −14.07% | 3524% |
| #24 | #19 | 0.906 | 10.62% | 11.93% | −12.73% | 3070% |
| #101 | #51 | 0.882 | 9.58% | 11.07% | −12.78% | 3117% |
| #64 | #66 | 0.456 | 4.08% | 9.85% | −17.96% | 1774% |
| #64 | #19 | 0.450 | 3.97% | 9.72% | −16.97% | 1730% |
| #64 | #51 | 0.403 | 3.56% | 9.94% | −17.10% | 1631% |
| #64 | #57 | 0.378 | 3.25% | 9.75% | −17.27% | 1792% |
| #64 | #24 | 0.324 | 2.73% | 9.81% | −16.78% | 1722% |
| #24 | #24 (sym) | 0.213 | 1.48% | 8.74% | −15.40% | 1635% |
| #24 | #57 | 0.108 | 0.58% | 10.21% | −14.01% | 1916% |

> ★ **IS-selected: `l24_s66`** (Sharpe 1.236). CAPM α 11.83%, β 0.269.
> Artifacts: `backtests/dual_signal/no_trans_cost/in_sample/outputs/best_l24_s66/`

---

### 8.2 Out-of-Sample Validation (2025-01-01 → 2026-03-01)

Sorted by Sharpe descending. OOS baseline `l24_s24` (sym) = −0.011.

| Long α | Short α | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|:------:|:-------:|:------:|:-----------:|:--------:|:------:|:-------------:|
| #66 | #24 | **0.965** | 8.77% | 9.14% | −6.19% | 4853% |
| #66 | #57 | 0.662 | 5.92% | 9.34% | −5.97% | 4883% |
| #66 | #19 | 0.416 | 3.64% | 9.70% | −6.31% | 4800% |
| #101 | #51 | 0.360 | 3.29% | 10.52% | −10.08% | 4360% |
| #66 | #66 (sym) | 0.303 | 2.65% | 10.38% | −7.41% | 4686% |
| #66 | #51 | 0.257 | 2.11% | 10.08% | −7.57% | 4772% |
| #24 | #57 | 0.249 | 2.18% | 11.03% | −8.66% | 3270% |
| #101 | #57 | 0.097 | 0.47% | 10.52% | −10.58% | 4904% |
| #24 | #24 (sym) | −0.011 | −0.68% | 10.80% | −9.92% | 3015% |
| #64 | #24 | −0.028 | −0.45% | 7.16% | −10.38% | 3504% |
| #101 | #66 | −0.057 | −1.14% | 10.51% | −11.96% | 4146% |
| #24 | #51 | −0.138 | −1.93% | 10.35% | −9.02% | 3245% |
| #101 | #19 | −0.273 | −3.05% | 9.66% | −11.08% | 4220% |
| #101 | #24 | −0.279 | −3.16% | 9.79% | −11.82% | 4247% |
| #64 | #57 | −0.312 | −2.96% | 8.48% | −10.35% | 3586% |
| #64 | #51 | −0.585 | −5.24% | 8.57% | −13.42% | 3713% |
| #64 | #19 | −0.760 | −5.85% | 7.56% | −10.80% | 3539% |
| **#24** | **#66 ★IS** | **−0.853** | **−8.02%** | **9.30%** | **−11.18%** | 2454% |
| #24 | #19 | −0.876 | −8.65% | 9.78% | −12.22% | 2515% |
| #64 | #66 | −0.951 | −6.19% | 6.50% | −10.61% | 1766% |

> OOS best: `l66_s24` (0.965) — IS rank #6 (1.117). Reported as divergence finding, not selection.
> **IS-selected `l24_s66` OOS rank: 18/20 (−0.853) — catastrophic IS/OOS divergence.**

---

### 8.3 Best-Pair Summary

> **Methodology:** IS-best pair is the selected configuration. OOS is holdout validation only.

| Split | Best Pair | Sharpe | Ann. Return | Max DD | CAPM α | CAPM β |
|-------|-----------|:------:|:-----------:|:------:|:------:|:------:|
| **IS (selected)** | **`l24_s66` ★** | **1.236** | **15.72%** | **−12.89%** | 11.83% | 0.269 |
| OOS validation of IS winner | `l24_s66` | −0.853 | −8.02% | −11.18% | −11.96% | 0.262 |
| OOS retrospective best | `l66_s24` | 0.965 | 8.77% | −6.19% | 7.01% | 0.118 |

---

### 8.4 Key Findings

**1. IS/OOS divergence is catastrophic for IS-selected pair.**
`l24_s66` (IS Sharpe 1.236) collapses to OOS Sharpe −0.853 — ranking 18th out of 20. #24 long side performs well in IS (2021–2024) but completely fails in OOS (2025–2026).

**2. OOS winner is essentially the IS-selected pair reversed.**
OOS best `l66_s24` (0.965) uses the same two alphas as the IS-best pair (`l24_s66`) but with long/short sides swapped. The relative relationship between #24 and #66 entirely reverses between IS and OOS.

**3. #24 as long signal fails on OOS.**
All 5 pairs with #24 on the long side have OOS Sharpe ≤ 0.249 (`l24_s57`), with most negative. Despite #24 being IS LP best, it provides no long-side edge in 2025–2026.

**4. #66 as long signal is robust on OOS.**
All 5 `l66_*` pairs have positive OOS Sharpe (0.257–0.965). `l66_s24` wins OOS but was IS rank #6. The OOS robustness of #66 long is broad — not one lucky pair.

**5. OOS best (0.965) is far below the original OOS-contaminated run (2.220).**
With IS-correct pools, the best OOS Sharpe is 0.965 vs 2.220 from the previous OOS-selected run. This confirms the previous result was inflated by pool contamination.

**6. Implication.**
IS-based selection fails to predict OOS in this universe. IS/OOS regime shift is severe — the IS winner is the OOS loser. Walk-forward validation would be needed for a methodologically clean selection.

---

## 9. Transaction Cost Sensitivity — OOS Key Pairs

### 9.1 Cost Parameters

SPDR sector ETFs are among the most liquid instruments in the US market. Commission has been $0 at major brokers since 2019; bid-ask spread is typically $0.01/share (0.5–2 bps depending on ETF price); borrow rates for easy-to-borrow (ETB) sector ETFs are ~0.25–0.50% p.a.

| Parameter | Value | Basis |
|-----------|-------|-------|
| `long_cost` | `0.0002` | 2 bps per leg — commission (≈0) + half bid-ask spread |
| `short_cost_per_day` | `0.003 / 365 ≈ 8.22e-6` | 0.30% p.a. borrow rate (ETB tier) |
| `base_slippage` | `0.0` | Already captured in `long_cost`; set to 0 to avoid double-counting |

Run script: `backtests/dual_signal/trans_cost/out_sample/run.py`

---

### 9.2 Key Pairs

> **TBD — select key pairs from IS grid (§8.1) after re-run.**

---

### 9.3 Results (OOS: 2025-01-01 → 2026-03-01)

> **TBD**

---

### 9.4 Key Findings

TBD after re-run.

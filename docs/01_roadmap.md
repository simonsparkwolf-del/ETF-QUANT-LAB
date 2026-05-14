# Roadmap — QuantLab Project

**Last updated:** 2026-05-15

---

## Milestones Completed

| Module | Note |
|--------|------|
| Data pipeline + `datapool.db` | End-to-end: CSV → all DB tables |
| Alpha pool (82 + custom) | IC computed; custom alphas 108–136 incl. `alpha_110` |
| ML signals (signal_id 1–5) | Trained and stored in `weekly_signal` |
| Backtest engine | `QuoteTerminal` / `BacktestEngine` / `BacktestAnalyzer` |
| Signal Opt Step 0 (equal-weight) | Long/short softmax EW baselines (IS/OOS) |
| Signal Opt Step 1 — alpha screening | 40 alphas × long + short × IS/OOS |
| Signal Opt Step 1 — ML screening | 5 ML signals × long + short × IS/OOS |
| Baseline L/S — alpha screening | 40 alphas × IS/OOS |
| Baseline L/S — ML screening | 5 ML signals × IS/OOS |
| Baseline Strategy + Risk framework | 3-state machine, rank stickiness, short momentum filter |
| **Design 01 — Dual-Signal L/S (no-cost)** | IS-selected `l24_s66` (IS 1.236) → OOS −0.853 (rank 18/20). Catastrophic IS/OOS divergence. |
| **Signal Opt Step 2 — LP blend** | IS-correct pool; single #24 IS-selected (IS-val 2.176 > blend 2.006); OOS 1.935 — **NEGATIVE** (blend adds nothing) |
| **Signal Opt Step 2 — SP blend** | IS-correct pool; single #24 IS-selected (IS-val −0.647 >> blend −1.605); OOS −0.704 — **NEGATIVE** (blend adds nothing) |
| **Signal Opt Step 3 — Joint L/S blend** | IS-correct pools; IS-selected `l24_s24` (IS-val 2.602); all OOS near-zero (0.12–0.47) — **NEGATIVE** (severe IS/OOS divergence) |
| **Design 02 — Dual-Blend L/S** | **SUBSUMED.** Step 2 IS-selected = single #24 on both sides → `LP_WEIGHTS={24:1.0}, SP_WEIGHTS={24:1.0}` ≡ `l24_s24`. Result already in Design 01 grid (IS 0.213, OOS −0.011). |

---

## Key Findings So Far

**Signal screening (Step 1) — LP/SP:**

| Best | IS Sharpe | OOS Sharpe |
|------|:---------:|:----------:|
| Alpha LP: #24 (IS) / #57 (OOS) | 1.122 | 2.174 |
| Alpha SP: #24 (IS) / #23 (OOS) | −0.420 | −0.522 |
| ML LP: Signal 5 MLP (IS) / Signal 2 Ensemble (OOS) | 0.705 | 1.730 |
| ML SP: Signal 5 MLP (IS) / Signal 2 Ensemble (OOS) | −0.673 | −1.330 |

**Baseline L/S (warmup test):**

| Best | IS Sharpe | OOS Sharpe | OOS Max DD |
|------|:---------:|:----------:|:----------:|
| Alpha: #66 (IS) / #23 (OOS) | 0.967 | 1.819 | −6.47% |
| ML: Signal 1 LightGBM (IS) / Signal 2 Ensemble (OOS) | 0.601 | 0.862 | −4.59% |

**Design 01 — Dual-Signal L/S (independent alpha per side):**

20-pair grid `LONG_ALPHAS=(24,66,101,64)` × `SHORT_ALPHAS=(24,57,19,51,66)`. IS window 2021-03-03→2024-12-31; OOS 2025-01-01→2026-03-01.

**IS-based selection (correct methodology):**

| Pair | IS Sharpe | IS Ann. Return | Role |
|:----:|:---------:|:--------------:|------|
| **`l24_s66` ★** | **1.236** | **15.72%** | IS-selected |
| Symmetric `l24_s24` | 0.213 | 1.48% | Grid baseline |

**OOS validation (reported after IS selection):**

| Pair | OOS Sharpe (no-cost) | OOS Sharpe (with cost) | OOS Max DD |
|:----:|:--------------------:|:----------------------:|:----------:|
| `l24_s66` (IS winner) | **−0.853** (rank 18/20) | TBD | −11.18% |
| `l24_s24` | −0.011 | — | −9.92% |
| `l66_s24` (OOS best — divergence finding) | 0.965 | — | −6.19% |

**IS/OOS divergence is catastrophic.** IS-selected `l24_s66` (IS 1.236) collapses to OOS −0.853. OOS best `l66_s24` (0.965) is the same two alphas with sides reversed — #24 as long fails entirely in 2025–2026; #66 as long is robustly positive across all 5 OOS pairs.

**Signal Opt Step 2 — LP/SP Bayesian blend (IS-correct pools):**

| Config | IS-train Sharpe | IS-val Sharpe | OOS Sharpe | IS-selected |
|--------|:---------------:|:-------------:|:----------:|:-----------:|
| Single #24 (LP baseline) | — | **2.176** | **1.935** | **★ LP winner** |
| LP blend (#24 55%, #66 30%, #101 8%, #136 7%) | 0.871 | 2.006 | 1.877 | Loses to single #24 |
| Single #24 (SP baseline) | — | **−0.647** | **−0.704** | **★ SP winner** |
| SP blend (#66 51%, #19 24%, #51 15%, #57 11%) | −1.307 | −1.605 | −0.886 | Loses to single #24 |

**Conclusion: single #24 is IS-selected for both LP and SP.** Blending within IS-correct pools adds no IS-val benefit. IS/OOS consistent — no divergence.

**Signal Opt Step 3 — Joint L/S blend (IS-correct pools):**

| Config | IS-train | IS-val | OOS | IS-selected |
|--------|:--------:|:------:|:---:|:-----------:|
| `l24_s24` (IS-best baseline) | — | **2.602** | 0.118 | **★ IS winner** |
| EW blend | — | 1.447 | 0.154 | |
| Jointly optimised blend | 1.851 | 1.206 | 0.474 | |

Severe IS/OOS divergence across all configs. `l24_s24` wins IS-val but collapses on OOS (0.118). Blend improves OOS slightly (0.474) but both near-zero. Signal blending in this universe does not produce viable L/S performance.

**Design 02 — Dual-Blend L/S (subsumed):**

Step 2 IS-selected = single #24 for both LP and SP. `LP_WEIGHTS={24:1.0}`, `SP_WEIGHTS={24:1.0}` makes `LongShortBlendSignal` identical to `LongShortAlphaSignal(24,24)` = `l24_s24`. Already tested in Design 01 grid: **IS Sharpe 0.213, OOS −0.011.** Design 02 adds no new information; not run.

Full results → `signal_opt/` and `trading_opt/`.

---

## Leaderboard

Ranked by OOS Sharpe. IS-selected = chosen by IS criterion only; OOS = holdout never used for selection.

| Rank | Signal | Strategy | IS Sharpe | OOS Sharpe | IS-selected | Consistent |
|:----:|--------|----------|:---------:|:----------:|:-----------:|:----------:|
| 🥇 | Alpha #24 (long-only) | `SigOptStrategy(long)` | 2.176 (IS-val) | **1.935** | ✓ | ✓ |
| 🥈 | `l66_s24` Design 01 | `DualSignalStrategy` | 1.117 | **0.965** | ✗ (IS rank #6) | — |
| 🥉 | Alpha #23 Baseline | `BaselineStrategy` | — | **1.819** | ✗ (OOS best) | — |
| 4 | Alpha #66 Baseline | `BaselineStrategy` | 0.967 | ~0.3* | ✓ (IS-selected) | partial |
| 5 | `l24_s24` Step 3 | `DualSignalStrategy` | 2.602 (IS-val) | 0.118 | ✓ | ✗ |
| 6 | `l24_s66` Design 01 | `DualSignalStrategy` | **1.236** | −0.853 | ✓ (IS-best) | ✗ |

> \* Alpha #66 Baseline OOS estimated from Design 01 `l66_s66` (sym) result.  
> Rank 2–3 are divergence findings, not IS-validated selections.

**Only rank 1 (Alpha #24 long-only) is both IS-selected and OOS-consistent.** All full L/S strategies show IS/OOS divergence.

---

### Charts

| Run | Chart Path |
|-----|-----------|
| Alpha #24 long-only OOS (Tier 1) | `backtests/signal_optimization/01 blend/long power/outputs/single_alpha_24/single_alpha_24_oos_all_in_one_panel.png` |
| `l24_s66` IS-selected IS (Tier 2) | `backtests/dual_signal/no_trans_cost/in_sample/outputs/best_l24_s66/is_dual_l24_s66_all_in_one_panel.png` |
| `l24_s24` Step 3 OOS (Tier 2) | `backtests/signal_optimization/02 ls_blend/outputs/l24_s24/l24_s24_oos_all_in_one_panel.png` |
| `l66_s24` OOS best (Tier 3) | `backtests/dual_signal/no_trans_cost/out_sample/outputs/best_l66_s24/os_dual_l66_s24_all_in_one_panel.png` |
| Alpha #66 Baseline IS (Tier 3) | `backtests/baseline/no_trans_cost/in_sample/alpha/outputs/best_alpha_66/is_baseline_best_alpha_66_all_in_one_panel.png` |

---

## Next Steps

| Priority | Task | Depends On | Status |
|----------|------|-----------|--------|
| ✅ | Re-run Design 01 with IS-correct pools | IS pools fixed | **Done** |
| ✅ | Re-run Step 2 LP/SP blend with IS-correct pools | IS pools fixed | **Done** |
| ✅ | Re-run Step 3 joint L/S blend | IS pools fixed | **Done** |
| ✅ | Design 02 — subsumed by Design 01 result | Step 2 done | **N/A** |
| ⏳ **High** | **Trans cost sensitivity** — run Design 01 key OOS pairs (`l66_s24`, `l66_s57`, `l24_s66`) at 2 bps + 0.3% p.a. borrow | Design 01 done | Pending |
| ⏳ Medium | **Strategy/risk parameter tuning** — `n_long/n_short` (2/4), `stickiness_threshold` (1/3), DD thresholds | Design 01 done | Pending |
| ⏳ Low | Liquidity filter (min avg daily volume) | — | Pending |

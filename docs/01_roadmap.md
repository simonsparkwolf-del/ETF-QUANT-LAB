# Roadmap — QuantLab Project

**Last updated:** 2026-05-14

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
| **Design 01 — Dual-Signal L/S (no-cost)** | `Scores` type + `LongShortAlphaSignal` + `DualSignalStrategy`; 20-pair grid (4 LP × 5 SP) × IS/OOS |
| **Design 01 — Transaction cost sensitivity** | 5 key OOS pairs at realistic SPDR ETF costs (2 bps/leg, 0.30% p.a. borrow) |

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

**Key takeaway:** IS and OOS winners rarely match — IS overfitting is high. Ensemble_RankAvg_frs1 (Signal 2) is the most consistent ML signal across both frameworks OOS. Alpha#23 is the strongest OOS baseline signal.

Full results → `signal_opt/00_screening.md` and `trading_opt/01_warmup_test.md`.

**Design 01 — Dual-Signal L/S (independent alpha per side):**

| Pair | OOS Sharpe (no-cost) | OOS Sharpe (with cost) | OOS Ann. Return | OOS Max DD |
|:----:|:--------------------:|:----------------------:|:---------------:|:----------:|
| l57_s23 ★ | 2.220 | **2.033** | 24.62% | −4.66% |
| l23_s23 (sym) | 2.022 | 1.962 | 21.37% | −5.31% |
| Single-alpha baseline (Alpha#23) | 1.819 | — | 19.34% | −6.47% |

- **LP/SP asymmetry confirmed:** the Step 1 finding that best OOS LP alpha (#57, +0.637 vs EW) ≠ best OOS SP alpha (#23, +1.015 vs EW) translates directly into a 20-pair backtest advantage. `l57_s23` beats the single-signal ceiling by +0.401 Sharpe (no-cost) and +0.214 Sharpe (with realistic costs).
- **Structural robustness:** all five #57-long pairs achieve OOS Sharpe ≥ 1.643 regardless of short-signal choice, confirming #57's long-side edge is genuine.
- **Cost impact is limited:** realistic SPDR ETF transaction costs (~2 bps/leg, 0.30% p.a. borrow) reduce `l57_s23` annual return by ~2.9pp. Strategy remains viable and leads all tested pairs.
- **IS selection is unreliable:** IS best pair (`l23_s31`) ranks last among the 5 key pairs under OOS cost testing. OOS validation is mandatory.
- **CAPM β ≈ 0.024:** `l57_s23` is near-market-neutral; market exposure does not explain the alpha (CAPM α = 22.3% p.a.).

Full results → `trading_opt/02_dual_signal_test.md`.

---

## Next Steps

| Priority | Task | Depends On | Status |
|----------|------|-----------|--------|
| 🔄 High | Signal Opt Step 2 — multi-signal Bayesian blend (LP + SP weight vectors) | Step 1 candidate list ✓ | Pending |
| 🔄 High | Design 02 — strategy/risk parameter tuning (`stickiness`, `n_long/n_short`, DD thresholds) | Design 01 ✓ | Pending |
| ⏳ Medium | Signal Opt Step 3 — neural network (differentiable backtest) | Step 2 baseline | Pending |
| ✅ Done | Design 01 — Dual-Signal L/S grid (no-cost IS + OOS) | Step 1 ✓ | Complete |
| ✅ Done | Transaction cost sensitivity for Design 01 (SPDR ETF realistic costs) | Design 01 ✓ | Complete |
| ⏳ Low | `stickiness_threshold` sweep — high turnover (~5500% p.a.) is a risk | Design 01 ✓ | Pending |
| ⏳ Low | Liquidity filter (min avg daily volume) | — | Pending |

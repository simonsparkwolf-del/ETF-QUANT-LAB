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

---

## Next Steps

| Priority | Task | Depends On |
|----------|------|-----------|
| 🔄 High | Signal Opt Step 2 — multi-signal Bayesian blend | Step 1 candidate list (LP+SP ✓) |
| 🔄 High | trading_opt Design 01 — optimised signal + tuned strategy/risk params | Step 2 results |
| ⏳ Medium | Signal Opt Step 3 — neural network (differentiable backtest) | Step 2 baseline |
| ⏳ Medium | Transaction cost sensitivity sweep (`long_cost` ∈ {0, 5, 10, 20} bps) | Design 01 |
| ⏳ Low | `stickiness_threshold` parameter sweep | Design 01 |
| ⏳ Low | Short borrow cost estimate (`short_cost_per_day`) | — |
| ⏳ Low | Liquidity filter (min avg daily volume) | — |

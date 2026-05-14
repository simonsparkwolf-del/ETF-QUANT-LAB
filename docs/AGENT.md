# AGENT — QuantLab Project Guide

Start here. This file tells you where everything lives and what to look at first.

---

## File Structure

```
docs/
├── AGENT.md                                        ← you are here
├── 00_overview.md                                  ← architecture, layer-by-layer description
├── 01_roadmap.md                                   ← milestones done, key findings, next steps
│
├── 02_work/                                        ← active research & experiments
│   ├── 01_signal_opt/
│   │   └── 00_screening.md                        ← Step 1 signal screening (LP/SP): all alphas + ML signals
│   └── 02_trading_opt/
│       ├── 00_trading_designs.md                  ← registry of active strategy+risk+signal combos
│       └── 01_warmup_test.md                      ← Baseline L/S warmup: design doc + full IS/OOS results
│
├── 03_datapool/                                    ← database schema and metric definitions
│   ├── 00_database.md                             ← DB schema + developer guide for extending metrics
│   ├── 01_signal.md                               ← signal pool (ML + alpha signals)
│   ├── 02_alpha.md                                ← alpha factor pool (WQ101 + custom)
│   └── 03_frs.md                                  ← FRS metric definitions
│
└── 04_infra/                                       ← backtest engine base class interfaces
    ├── 00_engine.md
    ├── 01_risk_module.md
    ├── 02_strategy_module.md
    └── 03_signal_module.md
```

---

## Where to Look First

| Task | File |
|------|------|
| Understand the project | `00_overview.md` |
| Check current progress + next steps | `01_roadmap.md` |
| Find backtest numbers | `02_work/02_trading_opt/01_warmup_test.md` §10, `02_work/01_signal_opt/00_screening.md` §6–8 |
| Check which signals beat EW | `02_work/01_signal_opt/00_screening.md` §7.4 (LP+SP combined table) |
| Understand Baseline strategy design | `02_work/02_trading_opt/01_warmup_test.md` §1–9 |
| See active trading designs | `02_work/02_trading_opt/00_trading_designs.md` |
| Extend DB (add alpha/signal/FRS) | `03_datapool/00_database.md` — Developer Guide section |
| Backtest engine API | `04_infra/00_engine.md` |

---

## Key Conventions

- **Look-ahead prevention:** all data access inside the backtest goes through `QuoteTerminal.at(day)` — never query `datapool.db` directly inside Signal / Strategy / Risk.
- **Signal score convention:** higher = stronger long, lower = stronger short.
- **Backtest calendars:** IS = 2021-03-03 → 2024-12-31 (200 weeks); OOS = 2025-01-01 → 2026-03-01 (61 weeks). Zero fees and slippage unless stated.
- **Sharpe floor (signal optimization only):** in the signal optimization pipeline (Steps 1–3), every signal must beat the equal-weight baseline (Step 0) on Sharpe to be considered valid. This rule does not apply to trading strategy evaluation in `02_trading_opt/`.
- **`alpha_110`** (12-week momentum) is hard-wired as the short-entry filter in `BaselineRisk` — not a ranking signal.
- **Backtest results:** go in `02_work/01_signal_opt/`, `02_work/02_trading_opt/`, or as milestone summaries in `01_roadmap.md`. `03_datapool/` and `04_infra/` are definition-only — no IC tables, no Sharpe numbers.

---

## Files That Need Frequent Updates

| File | When to update |
|------|---------------|
| `01_roadmap.md` | After each major backtest run or milestone |
| `02_work/02_trading_opt/00_trading_designs.md` | When a new design is defined or a result is confirmed |
| `02_work/01_signal_opt/00_screening.md` | After Step 2 / Step 3 results are in |

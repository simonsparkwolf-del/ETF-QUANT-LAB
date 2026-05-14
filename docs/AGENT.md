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
│   │   ├── architecture.md                        ← signal opt pipeline overview (Steps 0–3)
│   │   ├── 00_step1_screening.md                  ← Step 1: single-signal LP/SP sweep (40 alphas + 5 ML)
│   │   ├── 01_step2_lp_blend.md                   ← Step 2: LP Bayesian blend (150 trials); results filled
│   │   ├── 02_step2_sp_blend.md                   ← Step 2: SP Bayesian blend (150 trials); results filled
│   │   └── 03_step3_ls_blend.md                   ← Step 3: joint L/S blend (300 trials); results filled
│   └── 02_trading_opt/
│       ├── 00_trading_designs.md                  ← registry of all designs (00–03) with status + results
│       ├── 01_warmup_test.md                      ← Design 00: Baseline L/S warmup (IS/OOS)
│       ├── 02_dual_signal_test.md                 ← Design 01: Dual-Signal grid + transaction cost test
│       └── 03_dual_blend_signal_test.md           ← Design 02/03: blend experiments (both NEGATIVE)
│
├── 03_datapool/                                    ← database schema and metric definitions
│   ├── 00_database.md
│   ├── 01_signal.md
│   ├── 02_alpha.md
│   └── 03_frs.md
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
| Current best strategy configuration | `02_work/02_trading_opt/00_trading_designs.md` |
| Signal screening numbers | `02_work/01_signal_opt/00_step1_screening.md` |
| Blend experiment results | `02_work/01_signal_opt/01–03_step*.md` |
| Design 01 full backtest results | `02_work/02_trading_opt/02_dual_signal_test.md` §8–9 |
| Blend strategy results (Designs 02–03) | `02_work/02_trading_opt/03_dual_blend_signal_test.md` |
| Extend DB (add alpha/signal/FRS) | `03_datapool/00_database.md` — Developer Guide section |
| Backtest engine API | `04_infra/00_engine.md` |

---

## Key Conventions

### IS/OOS Split — Strict Separation (most important)

Signal selection, strategy parameter decisions, and model choices must be made
using **in-sample (IS) data only**. OOS is a holdout set that is reported once
at the end — it is **never** used to select, tune, or justify a decision.

**Correct reporting structure:**
1. IS analysis — rank/compare all candidates on IS metrics
2. IS-based decision — state the IS winner and why
3. OOS validation — report OOS performance of the IS-selected candidate
4. IS/OOS divergence — if IS winner ≠ OOS winner, report this as a *finding*,
   not as a reason to change the selection

**What NOT to do:**
- Do NOT say "we selected X because it had the best OOS Sharpe" — circular
- Do NOT pick the OOS winner and backfill a justification
- Do NOT present OOS best ≠ IS best as a methodological success

**Current project known issue:**  
Step 1 signal screening and Design 01 pair selection were performed partly by
inspecting OOS results. IS-best pair is `l23_s31`; `l57_s23` is the retrospective
OOS winner (presented as a divergence finding, not the selection). This is
documented honestly in `02_dual_signal_test.md` §8.3–8.4 and `01_roadmap.md`.

### Other Conventions

- **Look-ahead prevention:** all data access inside the backtest goes through `QuoteTerminal.at(day)` — never query `datapool.db` directly inside Signal / Strategy / Risk.
- **Signal score convention:** higher = stronger long, lower = stronger short.
- **Backtest calendars:** IS = 2021-03-03 → 2024-12-31 (200 weeks); OOS = 2025-01-01 → 2026-03-01 (61 weeks). Zero fees and slippage unless stated.
- **Signal optimization windows:** IS-train = 2021-03-03 → 2023-12-31; IS-val = 2024-01-01 → 2024-12-31; OOS = 2025-01-01 → 2026-03-01.
- **Sharpe floor (signal optimization only):** every signal must beat the equal-weight baseline (Step 0) on IS Sharpe to be considered valid for inclusion in the candidate pool.
- **`alpha_110`** (12-week momentum) is hard-wired as the short-entry filter in `BaselineRisk` — not a ranking signal.
- **Result tables:** IS metrics always before OOS metrics. Negative results documented with the same rigour as positive results.
- **Backtest results:** go in `02_work/01_signal_opt/`, `02_work/02_trading_opt/`, or as milestone summaries in `01_roadmap.md`. `03_datapool/` and `04_infra/` are definition-only.

---

## Files That Need Frequent Updates

| File | When to update |
|------|---------------|
| `01_roadmap.md` | After each major backtest run or milestone |
| `02_work/02_trading_opt/00_trading_designs.md` | When a new design is defined or a result is confirmed |
| `02_work/01_signal_opt/` (relevant step doc) | After each Step result is in |
| `AGENT.md` (this file) | When file structure or key conventions change |

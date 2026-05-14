# Trading Designs

Registry of strategy + risk + signal combinations under active development or evaluation.

---

## Baseline Backtest Conventions

### Folder Structure

All baseline backtest outputs live under `backtests/baseline/` with the following layout:

```
backtests/baseline/
├── no_trans_cost/                        # zero fee, zero slippage runs
│   ├── in_sample/                        # IS window: 2021-03-03 → 2024-12-31
│   │   ├── alpha/
│   │   │   └── outputs/
│   │   │       ├── summary.json          # all alpha_id results aggregated
│   │   │       └── best_alpha_<id>/      # full artifacts for best IS alpha
│   │   └── ml_signal/
│   │       └── outputs/
│   │           ├── summary.json
│   │           └── best_signal_<id>/     # full artifacts for best IS ML signal
│   └── out_sample/                       # OOS window: 2025-01-01 → 2026-03-01
│       ├── alpha/
│       │   └── outputs/
│       │       ├── summary.json
│       │       └── best_alpha_<id>/
│       └── ml_signal/
│           └── outputs/
│               ├── summary.json
│               └── best_signal_<id>/
└── trans_cost/                           # friction-cost sensitivity runs (planned)
    └── (same structure as no_trans_cost)
```

### Run Parameters

| Parameter | Value | Note |
|-----------|-------|------|
| IS start | 2021-03-03 | |
| IS end | 2024-12-31 | 200 weekly periods |
| OOS start | 2025-01-01 | |
| OOS end | 2026-03-01 | 61 weekly periods |
| Initial NAV | 10,000 | per run |
| `long_cost` | 0.0 | `no_trans_cost` only |
| `short_cost_per_day` | 0.0 | `no_trans_cost` only |
| `base_slippage` | 0.0 | `no_trans_cost` only |

### Signal-Type → Subfolder Mapping

| Signal type | Subfolder | Class |
|-------------|-----------|-------|
| Alpha factor | `alpha/` | `AlphaBacktestSignal(alpha_id)` |
| ML signal | `ml_signal/` | `MLBacktestSignal(signal_id)` |

### Per-Run Output Artifacts

Each `best_<signal>/` folder (and each individual run directory) contains:

| File | Content |
|------|---------|
| `*_metrics.json` | Sharpe, Ann. Return, Ann. Vol, Max DD, Win Rate, CAPM α/β, Turnover |
| `*_metrics.md` | Human-readable version of the same metrics |
| `*_value_history.csv` | Weekly NAV timeseries |
| `*_holding_history.csv` | Weekly position snapshots |
| `*_all_in_one_panel.png` | Multi-panel dashboard; Panel #1 = NAV vs SPY |

### Naming Rules

- **Friction buckets:** `no_trans_cost/` for frictionless runs; `trans_cost/` for cost-sensitivity sweeps.
- **Split:** always run IS and OOS in separate directories — never mix periods in a single run.
- **Best-pick folders:** after a grid scan, copy or symlink the best artifact folder to `best_alpha_<id>/` or `best_signal_<id>/` so it is easy to locate without reading `summary.json`.
- **summary.json:** aggregated metrics for the full grid (all alpha_ids or all signal_ids) written by the batch runner.

---

## Design 00 — Baseline Long-Short (Warmup)

**Status:** Screening complete (IS + OOS). See `trading_opt/01_warmup_test.md`.

| Component | Class | Key Parameters |
|-----------|-------|----------------|
| Signal | `AlphaBacktestSignal(alpha_id)` / `MLBacktestSignal(signal_id)` | Screened across 40 alphas + 5 ML signals |
| Strategy | `BaselineStrategy` | `n_long=3, n_short=3, stickiness_threshold=2` |
| Risk | `BaselineRisk` | `dd_light=0.10, dd_heavy=0.15, dd_recovery=0.08, recovery_weeks=2` |

**Best signal (IS):** Alpha#66 (Sharpe 0.967) / Signal 1 LightGBM_frs3 (Sharpe 0.601)  
**Best signal (OOS):** Alpha#23 (Sharpe 1.819) / Signal 2 Ensemble_RankAvg_frs1 (Sharpe 0.862)

---

## Design 01 — Dual-Signal L/S (Independent Alpha per Side)

**Status:** Grid defined, backtest pending. See `trading_opt/02_dual_signal_test.md`.

| Component | Class | Key Parameters |
|-----------|-------|----------------|
| Signal | `LongShortAlphaSignal(long_alpha_id, short_alpha_id)` | Grid: `LONG_ALPHAS=(57,19,31,23)` × `SHORT_ALPHAS=(23,53,31,19,57)` |
| Strategy | `DualSignalStrategy` | `n_long=3, n_short=3, stickiness_threshold=2` |
| Risk | `BaselineRisk` | identical to Design 00 |

**Motivation:** Step 1 OOS screening shows best LP alpha (#57, +0.637) ≠ best SP alpha (#23, +1.015). Splitting rankings per side should exceed the OOS Sharpe 1.819 ceiling of Design 00.  
**Target:** OOS Sharpe > **1.819** (Alpha#23 single-signal baseline).  
**Result:** Best pair `l57_s23` OOS Sharpe **2.220** (no-cost), **2.033** (with costs). Ranking preserved under realistic transaction costs.

---

## Design 02 — Dual-Blend L/S (Step 2 Optimised Blends per Side)

**Status:** Signal class implemented; backtest pending. See `trading_opt/03_dual_blend_signal_test.md`.

| Component | Class | Key Parameters |
|-----------|-------|----------------|
| Signal | `LongShortBlendSignal(lp_weights, sp_weights)` | LP: {#24: 61%, #19: 30%, #23: 7%, …}  SP: {#53: 39%, #57: 38%, #19: 21%, …} |
| Strategy | `DualSignalStrategy` | `n_long=3, n_short=3, stickiness_threshold=2` |
| Risk | `BaselineRisk` | identical to Design 00/01 |

**Motivation:** Step 2 LP/SP Bayesian blend optimisation produces side-specific weight vectors that each beat their Step 1 single-signal counterpart (LP OOS 2.130 vs 2.108; SP OOS −0.496 vs −0.790). Wiring both into the L/S strategy should compound both improvements.  
**Target:** OOS Sharpe > **2.220** (Design 01 best pair `l57_s23`, no-cost).  
**Result:** **Negative.** `lp_blend_sp_blend` OOS Sharpe **0.650** — far below baseline. Side-specific blend weights do not generalise to the full L/S context. `l57_s23` (2.190) remains best.

---

## Design 03 — Joint L/S Blend (Step 3 Direct Optimisation)

**Status:** Script and doc ready; backtest pending. See `signal_opt/03_step3_ls_blend.md`.

| Component | Class | Key Parameters |
|-----------|-------|----------------|
| Signal | `LongShortBlendSignal(lp_weights, sp_weights)` | 10 weights jointly optimised on full L/S Sharpe |
| Strategy | `DualSignalStrategy` | `n_long=3, n_short=3, stickiness_threshold=2` |
| Risk | `BaselineRisk` | identical to Design 00/01/02 |

**Motivation:** Design 02 proved that optimising LP/SP weights in isolation (on single-side objectives) does not generalise to the joint L/S strategy. Step 3 optimises all 10 weights simultaneously with the full L/S Sharpe as the objective — no gradient needed, TPE is a black-box sampler.  
**Target:** OOS Sharpe > **2.190** (`l57_s23` from Design 02 ablation).  
**Result:** **Negative.** Jointly optimised blend OOS Sharpe **1.156** vs baseline 2.152. IS-train 1.631 → IS-val 2.248 → OOS 1.156 shows regime overfitting. `l57_s23` is the definitive winner across all blend experiments.

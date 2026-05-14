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

**Status:** Complete. See `trading_opt/02_dual_signal_test.md`.

| Component | Class | Key Parameters |
|-----------|-------|----------------|
| Signal | `LongShortAlphaSignal(long_alpha_id, short_alpha_id)` | Grid: `LONG_ALPHAS=(24,66,101,64)` × `SHORT_ALPHAS=(24,57,19,51,66)` |
| Strategy | `DualSignalStrategy` | `n_long=3, n_short=3, stickiness_threshold=2` |
| Risk | `BaselineRisk` | identical to Design 00 |

**Motivation:** Step 1 IS screening shows #24 dominates both IS LP and IS SP. Full IS LP × IS SP grid tests whether asymmetric pairing outperforms symmetric `l24_s24` on IS Sharpe.  
**IS-selected:** `l24_s66` (IS Sharpe 1.236, Ann Return 15.72%) — beats symmetric baseline `l24_s24` (0.213).  
**OOS validation:** `l24_s66` collapses to −0.853 (rank 18/20). Catastrophic IS/OOS divergence. OOS best `l66_s24` (0.965) = same alphas with sides reversed. #24 as long fails entirely in 2025–2026; #66 long is robustly positive (all 5 `l66_*` pairs OOS > 0).

---

## Design 02 — Dual-Blend L/S (Step 2 Optimised Blends per Side)

**Status:** Signal class implemented; backtest pending. See `trading_opt/03_dual_blend_signal_test.md`.

| Component | Class | Key Parameters |
|-----------|-------|----------------|
| Signal | `LongShortBlendSignal(lp_weights, sp_weights)` | LP: Step 2 IS-correct blend weights (TBD)  SP: Step 2 IS-correct blend weights (TBD) |
| Strategy | `DualSignalStrategy` | `n_long=3, n_short=3, stickiness_threshold=2` |
| Risk | `BaselineRisk` | identical to Design 00/01 |

**Motivation:** Step 2 LP/SP Bayesian blend optimisation produces side-specific weight vectors. Wiring both into the L/S strategy should compound both improvements.  
**Target:** Beat IS-selected Design 01 best pair on IS Sharpe; OOS reported as validation.  
**Result:** TBD — pending Step 2 re-run with IS-correct candidate pools.

---

## Design 03 — Joint L/S Blend (Step 3 Direct Optimisation)

**Status:** Script and doc ready; backtest pending. See `signal_opt/03_step3_ls_blend.md`.

| Component | Class | Key Parameters |
|-----------|-------|----------------|
| Signal | `LongShortBlendSignal(lp_weights, sp_weights)` | 10 weights jointly optimised on full L/S Sharpe |
| Strategy | `DualSignalStrategy` | `n_long=3, n_short=3, stickiness_threshold=2` |
| Risk | `BaselineRisk` | identical to Design 00/01/02 |

**Motivation:** Design 02 proved that optimising LP/SP weights in isolation (on single-side objectives) does not generalise to the joint L/S strategy. Step 3 optimises all 10 weights simultaneously with the full L/S Sharpe as the objective — no gradient needed, TPE is a black-box sampler.  
**Target:** Beat IS-selected Design 01 best pair on IS Sharpe.  
**Result:** TBD — pending Step 2 re-run (Design 03 candidate pools derive from Step 2).

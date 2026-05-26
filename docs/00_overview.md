# QuantLab Project — Architecture & Progress Report

**Date**: 2026-05-26 | **Branch**: `feature-infra`

---

## 1. Project Architecture Overview

**Viewing convention (bottom → top):** read the stack **from the bottom row upward**. **L1** = foundation (raw files → DB); **L5** = consumer (strategies). Layers L2–L4 are the intermediate stack in order.

```
┌─────────────────────────────────────────────────────────────────────┐
│ L5  Strategy Layer                                                  │
│   Signal-Opt  LP/SP softmax  Steps 0→1 ✓  Step 2 blend (pending)  │
│   L/S Design  D00 ✓  D01 ✓  D02 blend (pending)  D03 (planned)    │
├─────────────────────────────────────────────────────────────────────┤
│ L4  Backtest Engine                                                 │
│   BacktestEngine · QuoteTerminal · BacktestAnalyzer                 │
│   Strategy: BaselineStrategy / DualSignalStrategy                   │
│   Risk:     BaselineRisk (3-state DD machine)                       │
├─────────────────────────────────────────────────────────────────────┤
│ L3  Signal Layer — ML (signal_id 1–6)  │  Alpha (82 factors)       │
├─────────────────────────────────────────────────────────────────────┤
│ L2  Data Layer — datapool.db: bars / alpha / frs / signal          │
├─────────────────────────────────────────────────────────────────────┤
│ L1  Raw Data — data/processed/data.csv  +  FRED macro (×5)         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Description

### 2.1 Data Infrastructure

**Docs**: `docs/03_datapool/00_database.md`

**Universe**: 11 SPDR Sector ETFs (XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLRE, XLY) + SPY/SPX/VIX/US10Y benchmark series + 5 FRED Macro series (T10Y2Y, BAMLH0A0HYM2, DTWEXBGS, DCOILWTICO, T10YIE). Data is ingested from Google Drive into `data/processed/data.csv` (FRED columns appended via `scripts/trivial/merge_fred_to_csv.py`), then pushed into `datapool.db` (SQLite) via `scripts/dataset_builder.ipynb`.

**Database schema** (key tables):

| Table | Content | Frequency |
|-------|---------|-----------|
| `daily_bar` | OHLCV + TRI, all 15 assets | Daily |
| `weekly_bar` | Wednesday-close resample, all 15 assets | Weekly |
| `weekly_alpha` | 82 alpha factor values, ETFs only | Weekly |
| `weekly_frs` | FRS1/2/3 forward return scores, ETFs only | Weekly |
| `weekly_signal` | ML / alpha / composite signals, ETFs only | Weekly |

**FRS definitions** (ML model prediction targets / labels):

| Code | Name | Formula |
|------|------|---------|
| FRS1 | 4-week total return | (P₄ − P₀) / P₀ |
| FRS2 | Sharpe proxy | avg(r₁…r₄) / std(r₁…r₄) |
| FRS3 | Vol-penalised return | FRS1 − 2.0 × std(r₁…r₄) |

**Developer workflow** for extending metrics: add a decorated function to `frs_metrics.py` / `alpha_metrics.py` / `signal_metrics.py`, then re-run the corresponding `save_*` function. Registry rows are append-only; fact tables are refreshed per run.

---

### 2.2 Alpha Pool — 101 Formulaic Alphas

**Docs**: `docs/03_datapool/02_alpha.md` | **Code**: `src/QuantLab/alpha/alpha_metrics.py`

Implemented from Kakushadze (2015) *101 Formulaic Alphas*:

| Group | Count | Note |
|-------|-------|------|
| Group A — Fully implementable | 52 | All required fields available |
| Group B — vwap approximated | 30 | vwap ≈ (O+H+L+C)/4 |
| Not implementable | 19 | Requires `IndNeutralize` or market-cap data |

Top alphas by IC (Mean IC > 0.02): Alpha#50 (0.042), #3 (0.034), #41 (0.034), #24 (0.033), #98 (0.031).

The project also defines **custom alphas (alpha_id 108–136)**, including `alpha_110` (12-week cumulative return), which is hard-wired into the risk module as an absolute-momentum filter for short positions.

---

### 2.3 Trading architecture

**Docs**: `docs/03_datapool/01_signal.md` | **Code**: `src/QuantLab/signal/`. The diagram below shows the full execution chain from raw data through to performance output.

```
data.csv + FRED macro (×5)          research/*/walk_forward_predictions.csv
           │                                        │
           ▼  dataset_builder.ipynb                 │ (signal_6.py ffill align)
      datapool.db                                   │
  weekly_bar · weekly_alpha · weekly_frs            │
           │                                        │
           ├──────────────────────────┐             │
           ▼                          ▼             │
  ML signals (signal_id 1–6) ←───────┘   Alpha factors (alpha_id 1–136)
           └──────────────┬────────────────────────┘
                          ▼
                    weekly_signal
                    (SIGNAL pool)
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
   Signal-Opt track              L/S Design track
   LP/SP softmax                 D00  Baseline ✓
   Step 0 EW ✓                   D01  Dual-Signal ✓
   Step 1 grid ✓                 D02  Dual-Blend (pending)
   Step 2 blend (pending)        D03  Joint Blend (planned)
   Step 3 NN (planned)
            └─────────────┬─────────────┘
                          ▼
              Strategy · Risk (BaselineRisk)
              (position intent → DD filter → exposure scale)
                          ▼
          BacktestEngine + QuoteTerminal
          (weekly fills · NAV · anti-look-ahead)
                          ▼
               BacktestAnalyzer
          Sharpe · Ann Return · Max DD · CAPM · NAV panel
```

Six ML signals are currently trained and stored in the **SIGNAL pool** (`weekly_signal`, signal_id 1–6):

| signal_id | Model | Label | OOS IC (weekly) |
|-----------|-------|-------|-----------------|
| 1 | LightGBM | FRS3 | — |
| 2 | Ensemble (Rank Avg) | FRS1 | — |
| 3 | XGBoost | FRS3 | — |
| 4 | PCA + Ridge | FRS3 | — |
| 5 | MLP | FRS2 | — |
| 6 | RF_tuned (daily panel, quarterly refit) | frs_4 proxy | 0.033 (IC-IR 0.077) |

---

### 2.4 Backtest Engine

**Docs**: `docs/04_infra/00_engine.md` | **Code**: `src/QuantLab/backtest/`

Four-module design with strict separation of concerns:

| Module | Role | Key API |
|--------|------|---------|
| `BacktestEngine` | Advances simulation clock, coordinates all modules, applies fills, calls evaluation | `engine.run()`, `engine.evaluate()` |
| `QuoteTerminal` | Single source of truth for time + data (prevents look-ahead bias) | `terminal.at(day)`, `terminal.signals()`, `terminal.etfs()` |
| `Signal / Strategy / Risk` | Signal → ranking → position intent → risk filter | `analyze()`, `on_ranking()`, `on_action()` |
| `BacktestAnalyzer` | Performance metrics + multi-panel dashboard (NAV vs SPY) | outputs: `.json`, `.md`, `.csv`, `.png` |

**Key contract**: all historical queries are cut off at `terminal.day` (inclusive); Signal/Strategy/Risk share the same terminal via `bind(terminal)`.

**Outputs per run**:
- `*_metrics.json` / `*_metrics.md`
- `*_value_history.csv` / `*_holding_history.csv`
- `*_all_in_one_panel.png` (Panel #1: NAV vs SPY)

---

### 2.5 Signal optimization framework

**Docs**: `docs/02_work/01_signal_opt/00_screening.md` | **Code:** `SiganlOptimizationStrategy` and the signal-optimization backtest batch suite

**Purpose:** choose or tune **one signal score per ETF per rebalance**; the strategy maps scores → **softmax weights** → frictionless weekly rebalance. Runs are **zero fee, zero slippage** unless a friction study is specified. Each candidate is compared to the **equal-weight baseline (§0)** on the same calendar via `QuantLab.backtest.benchmark.compare_metrics(baseline, candidate)` when reporting.

**§0 — Equal-weight floor:** identical scores imply $w_i=1/N$; this is the **mandatory Sharpe benchmark** — if Sharpe does not beat §0, the run is unsuccessful (doc §0).

**§1 — Allocator:** $w_i=\exp(s_i)/\sum_j\exp(s_j)$, fully invested on tradable ETFs. **Long-only** (`mode="long"`): weights from raw scores (**Long Power, LP**). **Short-only** (`mode="short"`): softmax on **negated** scores so low scores get short weight (**Short Power, SP**). LP/SP grids are the pre-screen before baseline L/S (doc §1, §7).

**§2 — Soft floor:** $\tilde{V}_t=\max(V_t,\varepsilon)$, $\varepsilon=10^{-6}$, for numerical continuity (doc §2).

**§3 — Objective:** maximize portfolio **Sharpe** only; turnover and drawdown are **informational**, not in the loss (doc §3).

**Steps 0–3** (signal construction and search **outside** the strategy class; doc §4). Objective for scored runs is always **Sharpe** vs the prior steps’ floors:

| Step | What is optimized | Typical method | Must beat |
|------|-------------------|----------------|-----------|
| 0 | — (equal weight) | — | — |
| 1 | Single signal stream (or very few parameters) | IC pre-screen + grid / small search | Step 0 |
| 2 | $\sum_k \alpha_k g^{(k)}$ + low-dimensional hyperparameters | Bayesian optimization + walk-forward CV | Steps 0–1 |
| 3 | Network parameters $\theta$ → per-ETF logits as scores | SGD / Adam + differentiable backtest | Steps 0–2 |

**Backtest tree:** signal optimization runs are grouped by **in-sample vs out-of-sample** and by **long-only vs short-only** (`alphas` vs `step1` grids). Latest numbers: **§2.7**.

---

### 2.6 Baseline Long-Short Strategy

**Docs**: `docs/02_work/02_trading_opt/01_warmup_test.md` | **Code:** `BaselineStrategy` and baseline risk helpers in `QuantLab.backtest`

**Design**: Market-neutral long-short portfolio, weekly rebalancing. Long top-3 / Short bottom-3 ETFs, target weight ±33.3% each, gross exposure 200%, net exposure ~0%.

**Short filter**: a short position is only opened if `alpha_110` (12-week momentum) < 0. This prevents shorting ETFs in upward trends.

**Risk state machine** (`BaselineRisk`):

```
NORMAL (200% gross)  ──[DD ≥ 10%]──►  LIGHT (100% gross)  ──[DD ≥ 15%]──►  HEAVY (0%, cash)
    ▲                                      ▲
    └──[DD < 8%, ≥ 2 weeks]────────────────┘
                                           └──[≥ 2 proposed longs w/ alpha_110 > 0, ≥ 2 weeks]──► LIGHT
```

**Rank stickiness**: existing holdings are retained if their current rank stays within `n_long + 2` (long) or `n_total - n_short + 1 - 2` (short), avoiding whipsaw from minor rank fluctuations.

---

### 2.7 Backtest Results (IS / OOS)

**Calendar:** All **baseline** and **signal-optimization** batch runners share the same two windows — **in-sample 2021-03-03 → 2024-12-31** (200 weekly periods) and **out-of-sample 2025-01-01 → 2026-03-01** (61 weekly periods). Initial NAV: 10,000; zero fees and slippage (per each `run.py`).

**Column tags:** **LP** = long softmax signal-opt grid; **SP** = short softmax on negated scores; **BL** = `BaselineStrategy` + `BaselineRisk` (market-neutral long-3 / short-3); **IS** / **OOS** = in-sample / out-of-sample.

---

#### 2.7.1 Baseline Long-Short — Alpha Signal Screening

40 alpha IDs were run through the full `BaselineStrategy` + `BaselineRisk` pipeline. Tables below are the complete comparison outputs; ★ marks the best Sharpe in each split.

**In-Sample (2021-03-03 → 2024-12-31, 200 periods)**

| alpha_id | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|----------|:------:|:-----------:|:--------:|:------:|:-------------:|
| 6 | −0.068 | −0.74% | 7.18% | −13.15% | 1262% |
| 10 | −0.120 | −1.07% | 6.96% | −15.53% | 1915% |
| 14 | 0.227 | 2.00% | 11.82% | −9.50% | 4518% |
| 16 | 0.298 | 2.17% | 8.37% | −16.37% | 1717% |
| 18 | 0.129 | 0.75% | 8.62% | −15.40% | 1852% |
| 19 | −0.293 | −1.64% | 5.19% | −16.47% | 1362% |
| 20 | 0.102 | 0.49% | 7.87% | −14.45% | 1886% |
| 22 | −0.452 | −2.89% | 6.07% | −16.46% | 2420% |
| 23 | 0.432 | 3.08% | 7.73% | −17.81% | 1834% |
| 24 | 0.119 | 0.64% | 8.27% | −15.39% | 1647% |
| 26 | −0.073 | −0.80% | 7.34% | −15.66% | 2252% |
| 30 | 0.411 | 2.91% | 7.71% | −15.34% | 2057% |
| 31 | 0.254 | 1.82% | 8.57% | −15.59% | 2044% |
| 32 | 0.684 | 7.43% | 11.44% | −13.05% | 2833% |
| 34 | 0.290 | 2.12% | 8.50% | −15.21% | 1969% |
| 37 | 0.088 | 0.37% | 6.75% | −16.14% | 1266% |
| 40 | 0.032 | −0.07% | 8.08% | −15.21% | 1562% |
| 44 | −0.197 | −1.74% | 7.47% | −17.51% | 2143% |
| 51 | 0.111 | 0.53% | 7.01% | −16.80% | 1807% |
| 53 | −0.086 | −0.97% | 7.78% | −16.46% | 1800% |
| 54 | −0.240 | −1.72% | 6.39% | −17.08% | 1374% |
| 57 | 0.352 | 2.44% | 7.67% | −15.68% | 2124% |
| 61 | −0.110 | −1.17% | 7.85% | −17.69% | 1515% |
| 64 | 0.290 | 2.33% | 9.53% | −16.83% | 1753% |
| **66** ★ | **0.967** | **8.90%** | **9.26%** | **−12.83%** | 4535% |
| 72 | 0.237 | 1.24% | 5.95% | −14.69% | 1240% |
| 83 | 0.159 | 0.89% | 7.24% | −17.08% | 1950% |
| 95 | 0.326 | 2.32% | 8.02% | −16.75% | 1509% |
| 101 | 0.923 | 10.37% | 11.39% | −17.27% | 3134% |
| 108 | 0.221 | 1.38% | 7.45% | −17.27% | 1731% |
| 110 | 0.343 | 2.88% | 9.66% | −15.54% | 1434% |
| 116 | 0.302 | 2.24% | 8.57% | −18.24% | 1274% |
| 118 | 0.193 | 1.44% | 10.01% | −16.72% | 938% |
| 123 | 0.026 | −0.20% | 9.42% | −21.03% | 1164% |
| 125 | 0.228 | 1.74% | 9.57% | −13.32% | 1418% |
| 127 | 0.368 | 3.16% | 9.73% | −16.04% | 1320% |
| 128 | 0.609 | 6.60% | 11.60% | −13.89% | 3151% |
| 130 | 0.283 | 2.37% | 10.11% | −17.32% | 1572% |
| 135 | −0.170 | −2.47% | 11.08% | −18.84% | 1466% |
| 136 | 0.244 | 2.54% | 14.75% | −13.29% | 1407% |

**Out-of-Sample (2025-01-01 → 2026-03-01, 61 periods)**

| alpha_id | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|----------|:------:|:-----------:|:--------:|:------:|:-------------:|
| 6 | −0.362 | −4.37% | 10.76% | −12.80% | 3693% |
| 10 | 1.090 | 11.58% | 10.57% | −6.90% | 4976% |
| 14 | −1.681 | −9.97% | 6.13% | −13.90% | 1221% |
| 16 | 1.019 | 9.29% | 9.13% | −6.35% | 4118% |
| 18 | −0.000 | −0.46% | 9.67% | −8.67% | 4777% |
| 19 | −0.618 | −5.66% | 8.80% | −11.16% | 3576% |
| 20 | −0.535 | −4.66% | 8.30% | −11.64% | 4314% |
| 22 | 0.644 | 5.79% | 9.43% | −6.51% | 6414% |
| **23** ★ | **1.819** | **19.34%** | **10.00%** | **−6.47%** | 4787% |
| 24 | −0.375 | −4.18% | 10.06% | −12.46% | 2864% |
| 26 | −0.868 | −7.72% | 8.80% | −11.75% | 3902% |
| 30 | −0.147 | −1.31% | 7.25% | −9.16% | 5092% |
| 31 | 0.514 | 4.46% | 9.33% | −5.14% | 4635% |
| 32 | 0.363 | 3.05% | 9.48% | −7.08% | 2993% |
| 34 | 0.637 | 6.14% | 10.16% | −5.30% | 5551% |
| 37 | 1.463 | 16.38% | 10.77% | −5.78% | 3923% |
| 40 | −0.841 | −9.65% | 11.30% | −13.66% | 3645% |
| 44 | −1.544 | −9.46% | 6.30% | −14.31% | 1508% |
| 51 | 1.478 | 15.09% | 9.84% | −5.84% | 4305% |
| 53 | 0.684 | 6.72% | 10.28% | −6.17% | 5033% |
| 54 | 0.376 | 3.45% | 10.43% | −4.83% | 4970% |
| 57 | 1.315 | 14.40% | 10.67% | −7.40% | 5425% |
| 61 | 0.711 | 7.18% | 10.53% | −7.05% | 3668% |
| 64 | −1.054 | −7.20% | 6.87% | −11.21% | 3100% |
| 66 | −0.483 | −5.25% | 10.11% | −9.27% | 4542% |
| 72 | −1.486 | −9.38% | 6.48% | −11.30% | 1476% |
| 83 | 0.942 | 9.97% | 10.68% | −6.92% | 5407% |
| 95 | 0.659 | 6.46% | 10.30% | −8.20% | 4208% |
| 101 | −0.549 | −6.01% | 10.31% | −12.66% | 3996% |
| 108 | −0.538 | −5.07% | 8.93% | −11.61% | 4123% |
| 110 | −0.444 | −5.16% | 10.65% | −11.66% | 3240% |
| 116 | −1.551 | −9.35% | 6.20% | −12.62% | 1532% |
| 118 | 0.392 | 3.69% | 10.63% | −12.92% | 1707% |
| 123 | −0.302 | −3.33% | 9.68% | −8.37% | 2176% |
| 125 | −1.042 | −9.83% | 9.49% | −14.75% | 3393% |
| 127 | −0.622 | −6.35% | 9.79% | −11.78% | 2477% |
| 128 | −0.679 | −5.09% | 7.29% | −10.36% | 3513% |
| 130 | −0.402 | −5.38% | 11.99% | −11.08% | 2603% |
| 135 | 0.805 | 8.93% | 11.43% | −11.10% | 2696% |
| 136 | 0.595 | 5.89% | 10.54% | −10.99% | 1912% |

> **IS best — Alpha#66**: Sharpe 0.967, Ann. Return 8.90%, Max DD −12.83%, Total Return 38.56% (10,000 → 13,856), Win Rate 57.3%, CAPM α 7.37%, β 0.119. Artifacts: `backtests/baseline/no_trans_cost/in_sample/alpha/outputs/best_alpha_66/`
>
> **OOS best — Alpha#23**: Sharpe 1.819, Ann. Return 19.34%, Max DD −6.47%, Total Return 22.63% (10,000 → 12,263), Win Rate 61.7%, CAPM α 14.71%, β 0.227. Artifacts: `backtests/baseline/no_trans_cost/out_sample/alpha/outputs/best_alpha_23/`
>
> Notable OOS performers: Alpha#37 (Sharpe 1.463, 16.38%), Alpha#51 (1.478, 15.09%), Alpha#57 (1.315, 14.40%). The IS winner Alpha#66 does not generalize OOS (Sharpe −0.483), indicating IS overfitting risk for momentum-style alphas.

---

#### 2.7.2 Baseline Long-Short — ML Signal Screening

All 5 ML signals (signal_id 1–5) were run through the same `BaselineStrategy` + `BaselineRisk` pipeline.

**In-Sample (2021-03-03 → 2024-12-31, 200 periods)**

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| **Signal 1** LightGBM_frs3 ★ | **0.601** | **5.09%** | 8.94% | −13.71% | 1571% |
| Signal 2 Ensemble_RankAvg_frs1 | 0.330 | 2.17% | 7.31% | −16.72% | 1815% |
| Signal 3 XGBoost_frs3 | 0.560 | 4.65% | 8.81% | −16.47% | 1830% |
| Signal 4 PCA_Ridge_frs3 | 0.442 | 3.89% | 9.71% | −18.05% | 1675% |
| Signal 5 MLP_frs2 | 0.247 | 1.61% | 7.66% | −14.06% | 1745% |

**Out-of-Sample (2025-01-01 → 2026-03-01, 61 periods)**

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| Signal 1 LightGBM_frs3 | −1.571 | −8.54% | 5.58% | −11.76% | 2487% |
| **Signal 2** Ensemble_RankAvg_frs1 ★ | **0.862** | **10.24%** | 12.16% | −4.59% | 4633% |
| Signal 3 XGBoost_frs3 | −0.731 | −4.79% | 6.44% | −10.33% | 2644% |
| Signal 4 PCA_Ridge_frs3 | 0.267 | 2.47% | 11.57% | −7.98% | 3951% |
| Signal 5 MLP_frs2 | −0.087 | −1.27% | 9.59% | −10.40% | 4758% |

> **IS best — Signal 1** (LightGBM_frs3): Sharpe 0.601, Ann. Return 5.09%, Max DD −13.71%, CAPM α 6.04%, β −0.051.
>
> **OOS best — Signal 2** (Ensemble_RankAvg_frs1): Sharpe 0.862, Ann. Return 10.24%, Max DD −4.59%, CAPM α 6.76%, β 0.242.
>
> LightGBM_frs3 collapses OOS (Sharpe −1.571), while the rank-average ensemble is the only ML signal to remain consistently positive. FRS3-based single models generalize poorly; ensemble and FRS1 labels are more robust.

---

#### 2.7.3 Signal Optimization — Alpha Factors (LP / SP / BL)

Key alpha IDs evaluated across all three allocator modes. **LP** = long softmax, **SP** = short softmax on negated scores, **BL** = `BaselineStrategy` + `BaselineRisk`.

| Alpha | Sharpe | Ann Ret | Sharpe | Ann Ret | Sharpe | Ann Ret | Sharpe | Ann Ret | Sharpe | Ann Ret | Max DD | Sharpe | Ann Ret | Max DD |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| *Mode→* | LP-IS | LP-IS | LP-OOS | LP-OOS | SP-IS | SP-IS | SP-OOS | SP-OOS | BL-IS | BL-IS | BL-IS | BL-OOS | BL-OOS | BL-OOS |
| **Step 0 EW** | 0.690 | 9.73% | 1.537 | 16.40% | −0.690 | −10.94% | −1.537 | −15.01% | — | — | — | — | — | — |
| **#19** | 0.564 | 8.34% | 2.014 | 23.34% | −0.593 | −10.07% | −1.104 | −12.66% | −0.293 | −1.64% | −16.47% | −0.618 | −5.66% | −11.16% |
| **#23** | 0.666 | 9.47% | 1.829 | 20.42% | −0.787 | −12.37% | −0.522 | −6.76% | 0.432 | 3.08% | −17.81% | **1.819** | **19.34%** | **−6.47%** |
| **#24** | **1.122** | **21.38%** | 2.055 | 29.08% | **−0.420** | −7.35% | −2.339 | −31.19% | 0.119 | 0.64% | −15.39% | −0.375 | −4.18% | −12.46% |
| **#57** | 0.691 | 11.02% | **2.174** | **30.06%** | −0.559 | −10.42% | −1.136 | −12.23% | 0.352 | 2.44% | −15.68% | 1.315 | 14.40% | −7.40% |
| **#66** | 0.744 | 10.84% | 1.532 | 16.91% | −0.630 | −10.13% | −1.475 | −14.52% | **0.967** | **8.90%** | **−12.83%** | −0.483 | −5.25% | −9.27% |

> LP/SP use the same alpha factor scores with different allocator signs; BL runs the full market-neutral book so profiles need not correlate. **#23** = OOS BL best; **#24** = IS LP best and IS SP “least bad”; **#57** = OOS LP best; **#66** = IS BL best.

---

#### 2.7.4 Signal Optimization — ML Step 1

**Long softmax (Step 1, `mode=long`)**

| Split | Layer | Best | Sharpe | Ann. Return |
|-------|-------|------|:------:|:-----------:|
| IS | Step 0 EW | baseline | 0.690 | 9.73% |
| IS | ML Step 1 | **Signal 5** MLP_frs2 | 0.705 | 9.98% |
| OOS | Step 0 EW | baseline | 1.537 | 16.40% |
| OOS | ML Step 1 | **Signal 2** Ensemble_RankAvg_frs1 | 1.730 | 19.12% |

**Short softmax (Step 1, `mode=short`)**

All Sharpe ratios are ≤ 0 — a pure short-only book on US sector ETFs is structurally loss-making in this sample. “Best” = least negative Sharpe.

| Split | Layer | Best | Sharpe | Ann. Return |
|-------|-------|------|:------:|:-----------:|
| IS | Step 0 EW | baseline | −0.690 | −10.94% |
| IS | ML Step 1 | **Signal 5** MLP_frs2 | −0.673 | −10.75% |
| OOS | Step 0 EW | baseline | −1.537 | −15.01% |
| OOS | ML Step 1 | **Signal 2** Ensemble_RankAvg_frs1 | −1.330 | −13.06% |

---

#### 2.7.5 Best-Pick Summary

| Suite | Split | Best Pick | Sharpe | Ann. Return | Max DD |
|-------|-------|-----------|:------:|:-----------:|:------:|
| BL — Alpha (40 ids) | IS | **Alpha#66** | 0.967 | 8.90% | −12.83% |
| BL — Alpha (40 ids) | OOS | **Alpha#23** | 1.819 | 19.34% | −6.47% |
| BL — ML (signals 1–5) | IS | **Signal 1** LightGBM_frs3 | 0.601 | 5.09% | −13.71% |
| BL — ML (signals 1–5) | OOS | **Signal 2** Ensemble_RankAvg_frs1 | 0.862 | 10.24% | −4.59% |
| LP — Alpha (signal-opt) | IS | **Alpha#24** | 1.122 | 21.38% | — |
| LP — Alpha (signal-opt) | OOS | **Alpha#57** | 2.174 | 30.06% | — |
| LP — ML Step 1 | IS | **Signal 5** MLP_frs2 | 0.705 | 9.98% | — |
| LP — ML Step 1 | OOS | **Signal 2** Ensemble_RankAvg_frs1 | 1.730 | 19.12% | — |

> **Key takeaways:** (1) Alpha#23 is the standout OOS baseline L/S signal — high Sharpe with shallow drawdown. (2) Ensemble_RankAvg_frs1 (Signal 2) is the most consistent ML signal across both the baseline L/S and the LP signal-opt framework OOS. (3) IS winners (Alpha#66, LightGBM) do not generalize — IS/OOS signal correlation is low, reinforcing the need for walk-forward validation in Step 2.

## 3. Current Progress Status

### Done

| Module | Status | Note |
|--------|--------|------|
| Data pipeline & `datapool.db` | ✅ Complete | End-to-end pipeline from CSV to all DB tables |
| Alpha pool (82 + custom) | ✅ Complete | IC computed, custom alphas (108–136) including `alpha_110` |
| ML signals (signal_id 1–5) | ✅ Complete | Trained and stored in `weekly_signal` |
| Signal 6 — RF_tuned (signal_id 6) | ✅ Complete | Daily panel RF; walk-forward predictions injected via `signal/ml/signal_6.py`; OOS weekly IC 0.033 |
| FRED Macro data integration | ✅ Complete | 5 FRED series appended to `data.csv`; Macro tickers in `asset` table and `daily_bar`/`weekly_bar` |
| Backtest engine | ✅ Complete | `QuoteTerminal` / `BacktestEngine` / `BacktestAnalyzer` |
| Signal Opt. Step 0 (equal-weight) | ✅ Complete | Long/short softmax EW baselines (IS/OOS) |
| Signal Opt. alpha screening | ✅ Complete | 40 alphas × long-only & short-only × IS/OOS |
| Signal Opt. Step 1 (ML signals) | ✅ Complete | 5 ML signals × long-only & short-only × IS/OOS |
| Baseline L/S — alpha screening | ✅ Complete | 40 alphas × IS/OOS |
| Baseline L/S — ML signal screening | ✅ Complete | 5 signals × IS/OOS |
| Baseline Strategy + Risk framework | ✅ Complete | 3-state risk machine, rank stickiness, short momentum filter |

### In Progress / Pending

| Module | Status | Note |
|--------|--------|------|
| Signal Opt. Step 2 (multi-signal Bayesian) | 🔄 Next | Linear mix $\sum \alpha_k g^{(k)}$ + walk-forward CV |
| Signal Opt. Step 3 (neural network) | ⏳ Planned | Differentiable backtest path |
| Baseline parameter tuning | ⏳ Planned | Optimal `stickiness_threshold`, borrow cost estimate, liquidity filter |
| Transaction cost sensitivity study | ⏳ Planned | Sweep `long_cost` over {0, 5, 10, 20} bps |
| Final performance report | ⏳ Planned | Full comparison table with in-sample / out-of-sample split |

---

## 4. Directory Map

```
LAB/
├── docs/                              # Design documents (AGENT.md + 00–04)
│   ├── 02_work/
│   │   ├── 01_signal_mining/          # Signal research (Signal06_RF.md)
│   │   ├── 02_signal_opt/             # Step 1–4 signal optimisation docs
│   │   └── 03_trading_opt/            # L/S strategy design docs (D00–D03)
│   ├── 03_datapool/                   # DB schema, signal/alpha/frs pool docs
│   └── 04_infra/                      # Engine, risk, strategy, signal module docs
│
├── src/QuantLab/
│   ├── alpha/                         # Alpha registration & compute
│   ├── frs/                           # FRS registration & compute
│   ├── signal/
│   │   ├── signal_metrics.py          # Non-ML signal decorators
│   │   ├── compute_signal.py          # Orchestration — incremental insert
│   │   └── ml/                        # ML signal implementations
│   │       ├── signal_1.py … signal_6.py
│   │       ├── utils/                 # Shared ML utilities
│   │       └── weights/               # Saved model weights / params
│   ├── backtest/
│   │   ├── engine.py                  # Simulation loop
│   │   ├── quote_terminal.py          # Unified data access (anti-look-ahead)
│   │   ├── analyzer.py                # Metrics & visualisation
│   │   ├── exchange.py                # Fill simulation
│   │   ├── trader.py
│   │   ├── signal/                    # Signal adapters
│   │   │   ├── ml_backtest_signal.py  # MLBacktestSignal
│   │   │   ├── dual_head_alpha_signal.py
│   │   │   ├── dual_blend_signal.py
│   │   │   └── signal_blend.py
│   │   ├── strategy/
│   │   │   ├── baseline.py            # BaselineStrategy (D00)
│   │   │   ├── asymmetric_ls.py       # DualSignalStrategy (D01)
│   │   │   └── signal_optimization.py # SignalOptimizationStrategy
│   │   ├── risk/
│   │   │   └── baseline.py            # BaselineRisk — 3-state DD machine
│   │   └── schema/                    # Dataclasses / config schemas
│   └── utils/                         # db / data_loader / load_ml_input / config
│
├── backtests/
│   ├── baseline/                      # Design 00 — Baseline L/S ✓
│   │   ├── no_trans_cost/             # IS: 2021-03-03→2024-12-31  OOS: 2025-01-01→2026-03-01
│   │   │   ├── in_sample/alpha/       # 40-alpha IS grid → summary.json + best_alpha_<id>/
│   │   │   ├── in_sample/ml_signal/   # 5 ML signals IS
│   │   │   ├── out_sample/alpha/
│   │   │   └── out_sample/ml_signal/
│   │   └── trans_cost/                # Friction-cost sensitivity (planned)
│   ├── dual_signal/                   # Design 01 — DualSignalStrategy ✓
│   │   ├── no_trans_cost/
│   │   │   ├── in_sample/run.py + outputs/
│   │   │   └── out_sample/run.py + outputs/
│   │   └── trans_cost/
│   │       ├── in_sample/run.py + outputs/
│   │       └── out_sample/run.py + outputs/
│   ├── dual_signal_blended/           # Design 02 — LongShortBlendSignal (partial)
│   │   └── out_sample/run.py + outputs/ (l57_s23 · lp_blend_s23 · lp_blend_sp_blend)
│   └── signal_optimization/
│       ├── 00 screening/              # Step 0 EW + Step 1 single-signal grid ✓
│       │   ├── in_sample/long_only | short_only
│       │   └── out_sample/long_only | short_only
│       ├── 01 blend/                  # Step 2 LP/SP per-side Bayesian blend ✓
│       │   ├── long power/run.py + outputs/
│       │   └── short power/run.py + outputs/
│       └── 02 ls_blend/              # Step 3 joint L/S 10-weight optimisation ✓
│           └── run.py + outputs/ (best_ls_blend · best_weights.json · study.pkl)
│
├── data/
│   ├── datapool.db                    # SQLite datapool (sole DB file)
│   ├── processed/                     # data.csv (124 cols after FRED append)
│   └── raw/
│
├── debrief/
│   └── 20260513/report.md + report.html + report.pdf
│
├── research/
│   ├── 20260426_Team_Early-Baseline/  # ARCHIVED: original prototype
│   ├── 20260426 _Simon_ML Infra/
│   ├── 20260426_David_Alpha-signals/  # WQ101 alpha library & IC output
│   ├── 20260509_Simon_Signal_Infra/
│   ├── 20260513_Simon_Strategy/
│   └── 20260526_David_RF model/       # RF daily panel (David) ← signal_6 source
│       ├── config.py · daily_features.py · daily_model.py · run_daily.py
│       ├── data/fred/                 # Raw FRED CSVs (T10Y2Y · HY OAS · WTI · USD · BE10Y)
│       └── outputs/daily/rf_tuned/    # walk_forward_predictions.csv · metrics_summary.json
│
├── scripts/
│   ├── dataset_builder.ipynb          # DB build orchestration (sole DB write entry point)
│   ├── data_download_template.ipynb
│   ├── tasks/ML001_TASK.ipynb
│   └── trivial/
│       └── merge_fred_to_csv.py       # Append 5 FRED macro columns to data/processed/data.csv
│
└── simon_test/                        # Personal scratch space (archived prototypes)
```

---

## 5. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Wed-close signal / Thu-close execution** | Eliminates look-ahead bias; compresses weekend gap to a single overnight |
| **`QuoteTerminal` as the single time truth** | All modules share the same data cut-off via `bind(terminal)`, preventing date drift |
| **`alpha_110` hard-wired short filter** | Prevents shorting ETFs in upward 12-week trends; non-negotiable risk rule |
| **Softmax allocation (no hard top-k)** | Preserves gradient flow for Step 3 neural network training |
| **Soft floor ε = 1e-6** | Numerical continuity for differentiable backtest paths |
| **Equal-weight as mandatory Sharpe floor** | Forces signals to prove cross-sectional information content, not just market beta |

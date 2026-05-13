# QuantLab Project — Architecture & Progress Report

**Date**: 2026-05-13 | **Branch**: `feature-infra`

---

## 1. Project Architecture Overview

**Viewing convention (bottom → top):** read the stack **from the bottom row upward**. **L1** = foundation (raw files → DB); **L5** = consumer (strategies). Layers L2–L4 are the intermediate stack in order.

```
┌──────────────────────────────────────────────────────────────────┐
│ L5  Strategy Layer                                               │
│     Baseline L/S  │  Signal optimization (long / short)          │
├──────────────────────────────────────────────────────────────────┤
│ L4  Backtest Engine — BacktestEngine / QuoteTerminal / Analyzer  │
├──────────────────────────────────────────────────────────────────┤
│ L3  Signal Layer — ML (signal_id 1–5) │ Alpha (82 factors)       │
├──────────────────────────────────────────────────────────────────┤
│ L2  Data Layer — datapool.db: bars / alpha / frs / signal        │
├──────────────────────────────────────────────────────────────────┤
│ L1  Raw Data Layer — Google Drive → data/processed/data.csv      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer-by-Layer Description

### 2.1 Data Infrastructure

**Docs**: `docs/01 Data Infra.md`, `docs/02 Data Instruction.md`

**Universe**: 11 SPDR Sector ETFs (XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLRE, XLY) + SPY/SPX/VIX/US10Y benchmark series. Data is ingested from Google Drive into `data/processed/data.csv`, then pushed into `datapool.db` (SQLite) via `scripts/dataset_builder.ipynb`.

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

**Docs**: `docs/05 Alpha.md` | **Code**: `src/QuantLab/alpha/alpha_metrics.py`

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

**Docs**: `docs/03 Architecture.md` — **§B. Architecture** (illustration and coworking). The figure below extends that sketch with a **SIGNAL pool** layer before **ranking score** (weekly per-ETF score used for ranking).

Pipeline: **Data Pool** feeds **ML model module** and **Traditional quant signals**; their outputs (and other registered channels) live in the **SIGNAL pool** (e.g. `weekly_signal` in `datapool.db`). Each week those inputs are turned into a **ranking score** (cross-sectional score per ETF); the **Trading module** consumes the ranking, applies risk/strategy rules, and the **Backtest Engine** simulates fills.

```
Data Pool: bars + alpha pool + additional data
        │
        ├─────────────────────────────┐
        ▼                             ▼
   ML model module           Traditional quant signals
        │                             │
        └─────────────┬───────────────┘
                      ▼
                   SIGNAL pool
                      ▼
                Ranking score
                      ▼
             Trading module
                      ▼
           Backtest Engine
```

Five ML signals are currently trained and stored in the **SIGNAL pool** (`weekly_signal`, signal_id 1–5):

| signal_id | Model | Label |
|-----------|-------|-------|
| 1 | LightGBM | FRS3 |
| 2 | Ensemble (Rank Avg) | FRS1 |
| 3 | XGBoost | FRS3 |
| 4 | PCA + Ridge | FRS3 |
| 5 | MLP | FRS2 |

---

### 2.4 Backtest Engine

**Docs**: `docs/06 Backtest Engine.md` | **Code**: `src/QuantLab/backtest/`

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

**Docs**: `docs/07 Signal Optimization.md` | **Code:** `SiganlOptimizationStrategy` and the signal-optimization backtest batch suite

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

**Docs**: `docs/08 baseline strategy.md` | **Code:** `BaselineStrategy` and baseline risk helpers in `QuantLab.backtest`

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

### 2.7 Backtest results (IS / OOS)

**Calendar:** all **baseline** and **signal-optimization** batch runners use **in-sample 2021-03-03 → 2024-12-31** (200 weekly periods) and **out-of-sample 2025-01-01 → 2026-03-01** (61 weekly periods); initial NAV 10,000; zero fees and slippage (per each `run.py`).

**Metrics:** **LP** / **SP** (signal optimization) report **Sharpe** and **annualized return** only — not max drawdown. **BL** (Baseline L/S) adds **max drawdown**. **LP** = long softmax alpha grid; **SP** = short softmax on negated scores; **BL** = `BaselineStrategy` + `BaselineRisk` on the same alpha id per cell.

**Wide-table header:** first row = column labels (**Sharpe**, **ANN return**, **Max DD**). The first body row lists **backtest tags** per column (**LP** / **SP** = signal-opt softmax grids; **BL** = baseline L/S; **IS** / **OOS** = in-sample / out-of-sample, same calendars as §2.7).

#### 1) Signal optimization — key alphas (LP / SP + same alpha under baseline L/S)

| **Alpha** (WQ # or Step 0 EW) | **Sharpe** | **ANN return** | **Sharpe** | **ANN return** | **Sharpe** | **ANN return** | **Sharpe** | **ANN return** | **Sharpe** | **ANN return** | **Max DD** | **Sharpe** | **ANN return** | **Max DD** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| *backtest* | LP-IS | LP-IS | LP-OOS | LP-OOS | SP-IS | SP-IS | SP-OOS | SP-OOS | BL-IS | BL-IS | BL-IS | BL-OOS | BL-OOS | BL-OOS |
| **Step 0 EW** | 0.690 | 9.73% | 1.537 | 16.40% | −0.690 | −10.94% | −1.537 | −15.01% | — | — | — | — | — | — |
| **#19** | 0.564 | 8.34% | 2.014 | 23.34% | −0.593 | −10.07% | −1.104 | −12.66% | −0.293 | −1.64% | −16.47% | −0.618 | −5.66% | −11.16% |
| **#23** | 0.666 | 9.47% | 1.829 | 20.42% | −0.787 | −12.37% | −0.522 | −6.76% | 0.432 | 3.08% | −17.81% | **1.819** | **19.34%** | **−6.47%** |
| **#24** | **1.122** | **21.38%** | 2.055 | 29.08% | **−0.420** | −7.35% | −2.339 | −31.19% | 0.119 | 0.64% | −15.39% | −0.375 | −4.18% | −12.46% |
| **#57** | 0.691 | 11.02% | **2.174** | **30.06%** | −0.559 | −10.42% | −1.136 | −12.23% | 0.352 | 2.44% | −15.68% | 1.315 | 14.40% | −7.40% |
| **#66** | 0.744 | 10.84% | 1.532 | 16.91% | −0.630 | −10.13% | −1.475 | −14.52% | **0.967** | **8.90%** | **−12.83%** | −0.483 | −5.25% | −9.27% |

> **Read across:** LP/SP come from the same weekly alpha factor columns, different allocator sign; BL is the market-neutral long-3 / short-3 book, so Sharpe profiles need not match LP. **#23** is OOS BL best; **#24** is IS LP best and IS SP “least bad”; **#57** is OOS LP best; **#66** is IS BL best.

#### 2) Signal optimization — ML Step 1 — **long** softmax (long-only Step 1 grid)

| Split | Layer | Best | Sharpe | Ann. return |
|-------|-------|------|:------:|:-----------:|
| IS | Step 0 EW | baseline | 0.690 | 9.73% |
| IS | ML Step 1 | **Signal 5** MLP_frs2 | 0.705 | 9.98% |
| OOS | Step 0 EW | baseline | 1.537 | 16.40% |
| OOS | ML Step 1 | **Signal 2** Ensemble_RankAvg_frs1 | 1.730 | 19.12% |

#### 3) Signal optimization — ML Step 1 — **short** softmax (short-only Step 1 grid, `mode=short`)

All Sharpe ratios are **≤ 0** (short-only book on sector ETFs is structurally loss-making here); “best” = least negative Sharpe vs the same-split EW baseline.

| Split | Layer | Best | Sharpe | Ann. return |
|-------|-------|------|:------:|:-----------:|
| IS | Step 0 EW | baseline | −0.690 | −10.94% |
| IS | ML Step 1 | **Signal 5** MLP_frs2 | −0.673 | −10.75% |
| OOS | Step 0 EW | baseline | −1.537 | −15.01% |
| OOS | ML Step 1 | **Signal 2** Ensemble_RankAvg_frs1 | −1.330 | −13.06% |

#### 4) Baseline long–short — alpha & ML (aggregate best picks)

| Suite | Split | Best pick | Sharpe | Ann. return | Max DD |
|-------|-------|-----------|:------:|:-----------:|:------:|
| Alpha (40 ids) | IS | **Alpha#66** | 0.967 | 8.90% | −12.83% |
| Alpha (40 ids) | OOS | **Alpha#23** | 1.819 | 19.34% | −6.47% |
| ML (signals 1–5) | IS | **Signal 1** LightGBM_frs3 | 0.601 | 5.09% | −13.71% |
| ML (signals 1–5) | OOS | **Signal 2** Ensemble_RankAvg_frs1 | 0.862 | 10.24% | −4.59% |

Per-alpha baseline L/S metrics are already in the **BL·** columns of the wide panel above.

## 3. Current Progress Status

### Done

| Module | Status | Note |
|--------|--------|------|
| Data pipeline & `datapool.db` | ✅ Complete | End-to-end pipeline from CSV to all DB tables |
| Alpha pool (82 + custom) | ✅ Complete | IC computed, custom alphas (108–136) including `alpha_110` |
| ML signals (signal_id 1–5) | ✅ Complete | Trained and stored in `weekly_signal` |
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
├── docs/                              # Design documents (01–08)
├── src/QuantLab/
│   ├── alpha/                         # Alpha registration & compute
│   ├── frs/                           # FRS registration & compute
│   ├── signal/                        # Signal registration (incl. ML sub-module)
│   ├── backtest/
│   │   ├── engine.py                  # Main simulation loop
│   │   ├── quote_terminal.py          # Unified data access (anti-look-ahead)
│   │   ├── analyzer.py                # Metrics & visualization
│   │   ├── signal/                    # AlphaBacktestSignal, MLBacktestSignal, etc.
│   │   ├── strategy/                  # SiganlOptimizationStrategy, BaselineStrategy
│   │   └── risk/                      # BaselineRisk, DebugRisk
│   └── utils/                         # db / data_loader / load_ml_input / config
├── backtests/
│   ├── baseline/
│   │   ├── in_sample/alpha/           # L/S alpha grid → summary.json
│   │   ├── out_sample/alpha/
│   │   ├── in_sample/ml_signal/
│   │   └── out_sample/ml_signal/
│   └── signal_optimization/
│       ├── in_sample/
│       │   ├── long_only/alphas/ | long_only/step1/
│       │   └── short_only/alphas/ | short_only/step1/
│       └── out_sample/
│           ├── long_only/alphas/ | long_only/step1/
│           └── short_only/alphas/ | short_only/step1/
└── scripts/
    └── dataset_builder.ipynb          # DB build orchestration
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

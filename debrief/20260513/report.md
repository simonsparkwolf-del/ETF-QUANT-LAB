# QuantLab Research Report — 2026-05-13

**Branch:** `feature-infra`  
**In-Sample (IS):** 2021-03-03 → 2024-12-31 · 200 weekly periods  
**Out-of-Sample (OOS):** 2025-01-01 → 2026-03-01 · 61 weekly periods  
**Universe:** 11 SPDR Sector ETFs · Zero fees, zero slippage unless stated

---

## 1. System Architecture

QuantLab is a five-layer quantitative research stack for weekly sector ETF rotation. Each layer has a single well-defined responsibility; data flows strictly upward from raw files to strategy execution.

```
┌──────────────────────────────────────────────────────────────────┐
│ L5  Strategy Layer                                               │
│     Baseline L/S  │  Signal Optimization (long / short)         │
├──────────────────────────────────────────────────────────────────┤
│ L4  Backtest Engine — BacktestEngine / QuoteTerminal / Analyzer  │
├──────────────────────────────────────────────────────────────────┤
│ L3  Signal Layer — ML (signal_id 1–5) │ Alpha (82 + 30 custom)  │
├──────────────────────────────────────────────────────────────────┤
│ L2  Data Layer — datapool.db: bar / alpha / frs / signal         │
├──────────────────────────────────────────────────────────────────┤
│ L1  Raw Data Layer — Google Drive → data/processed/data.csv      │
└──────────────────────────────────────────────────────────────────┘
```

### Module Responsibilities

| Module | Answers | Key Output | Constraint |
|--------|---------|-----------|-----------|
| **Signal** | *What* to trade | `OrderedDict[ticker → score]` | Read-only; no account access |
| **Strategy** | *How* to trade | List of `Action` objects | Proposes only; no risk enforcement |
| **Risk** | *Whether* to trade | Filtered / clamped action list | Final gatekeeper; all constraints here |

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Wednesday-close signal / Thursday-close execution | Eliminates look-ahead bias; compresses weekend gap to a single overnight hold |
| `QuoteTerminal` as the single time truth | All modules share the same data cut-off via `bind(terminal)`, preventing date drift |
| `alpha_110` hard-wired short filter | Prevents shorting ETFs in upward 12-week momentum trends; non-negotiable risk rule |
| Softmax allocation (no hard top-k) | Preserves gradient flow for Step 3 neural-network differentiable backtest training |
| Soft NAV floor ε = 1e-6 | Numerical continuity for differentiable backtest paths; prevents log(0) |
| Equal-weight as mandatory Sharpe floor | Forces signals to prove cross-sectional information content, not just market beta |

### Project Directory

```
LAB/
├── src/QuantLab/
│   ├── alpha/                         # Alpha registration & compute
│   ├── frs/                           # FRS registration & compute
│   ├── signal/                        # Signal registration
│   │   └── ml/                        # ML signal implementations (signal_1–5)
│   ├── backtest/
│   │   ├── engine.py                  # Main simulation loop
│   │   ├── quote_terminal.py          # Unified data access (anti-look-ahead)
│   │   ├── analyzer.py                # Metrics & visualization
│   │   ├── signal/                    # AlphaBacktestSignal, MLBacktestSignal
│   │   ├── strategy/                  # SiganlOptimizationStrategy, BaselineStrategy
│   │   └── risk/                      # BaselineRisk, DebugRisk
│   └── utils/                         # db / data_loader / load_ml_input / config
├── backtests/
│   ├── baseline/
│   │   ├── no_trans_cost/             # zero-fee / zero-slippage runs
│   │   │   ├── in_sample/alpha/
│   │   │   ├── out_sample/alpha/
│   │   │   ├── in_sample/ml_signal/
│   │   │   └── out_sample/ml_signal/
│   │   └── trans_cost/                # friction-cost runs (planned)
│   └── signal_optimization/
│       ├── in_sample/long_only/ | in_sample/short_only/
│       └── out_sample/long_only/ | out_sample/short_only/
├── data/processed/                    # data.csv (main input)
├── debrief/                           # Periodic team reports
├── docs/                              # Design documents (AGENT.md + 00–04)
├── research/                          # Per-contributor notes & archives
│   ├── 20260426_Team_Early-Baseline/  # ARCHIVED: original prototype
│   ├── 20260426_David_Alpha-signals/
│   ├── 20260426 _Simon_ML Infra/
│   ├── 20260509_Simon_Signal_Infra/
│   └── 20260513_Simon_Strategy/
└── scripts/                           # dataset_builder.ipynb
```

---

## 2. Data Layer

### Universe

**11 SPDR Sector ETFs:** XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLRE, XLY  
**Benchmark series (read-only):** SPY, SPX, VIX, US10Y

### Database Schema — datapool.db

| Table | Content | Frequency | Key Columns |
|-------|---------|-----------|-------------|
| `daily_bar` | OHLCV + TRI, all 15 assets | Daily | ticker, date, open, high, low, close, volume, tri |
| `weekly_bar` | Wednesday-close resampled, all 15 assets | Weekly | ticker, date, open, high, low, close, volume, tri |
| `weekly_alpha` | Alpha factor values, ETFs only | Weekly | ticker, date, alpha_id, value, group (wq101 / andy) |
| `weekly_frs` | FRS1/2/3 forward return scores, ETFs only | Weekly | ticker, date, frs_id, value |
| `weekly_signal` | ML / alpha / composite signals, ETFs only | Weekly | ticker, date, signal_id, value |

### FRS Label Definitions

| Code | Name | Formula | Use |
|------|------|---------|-----|
| FRS1 | 4-week total return | `(P₄ − P₀) / P₀` | Signal 2 label; used in rank-average ensemble |
| FRS2 | Sharpe proxy | `avg(r₁…r₄) / std(r₁…r₄)` | Signal 5 label (MLP) |
| FRS3 | Vol-penalized return | `FRS1 − 2.0 × std(r₁…r₄)` | Signals 1, 3, 4 label (LightGBM / XGBoost / PCA-Ridge) |

### Data Pipeline

```
Google Drive → data/processed/data.csv
        ↓
dataset_builder.ipynb → datapool.db (daily_bar, weekly_bar)
        ↓  alpha_metrics.py
weekly_alpha (WQ101 + Andy factors, IDs 1–101 and 108–137)
        ↓  frs_metrics.py
weekly_frs (FRS1, FRS2, FRS3)
        ↓  signal_metrics.py + ML training
weekly_signal (ML signal_id 1–5)
        ↓
QuoteTerminal → BacktestEngine → Strategy / Risk
```

> **Developer extension rule:** add a decorated function to `*_metrics.py` and re-run the `save_*` function. Registry rows are append-only; fact tables are refreshed per run.

---

## 3. Signal Pool

### 3.1 WQ101 Alpha Factors

Implemented from Kakushadze (2015) *101 Formulaic Alphas*. All factors stored in `weekly_alpha` with `group='wq101'`.

| Group | Count | Note |
|-------|------:|------|
| Group A — Fully implementable | 52 | All required fields (OHLCV + volume) available |
| Group B — vwap approximated | 30 | vwap ≈ (O + H + L + C) / 4 |
| Not implementable | 19 | Requires `IndNeutralize` or market-cap data — unavailable for ETFs |

Top alphas by mean IC: Alpha#50 (0.042), #3 (0.034), #41 (0.034), #24 (0.033), #98 (0.031).

### 3.2 Andy Alpha Factors (Custom Group)

30 custom alpha factors (IDs 108–137), stored with `group='andy'`. Designed to capture trend, risk-adjusted momentum, liquidity, and relative-strength effects specific to the sector ETF universe.

| Family | IDs | Description |
|--------|-----|-------------|
| Price Momentum | 108–112 | Cumulative returns over 1w, 4w, 8w, 12w, 26w windows |
| Risk-Adjusted Momentum | 113–117 | Return / rolling σ over matched windows |
| Realized Volatility | 118–122 | Rolling σ of weekly returns (4w–52w) |
| Log Dollar Volume | 123–124 | log(price × volume) rolling 4w / 12w |
| Amihud Illiquidity | 125–126 | \|return\| / dollar_volume rolling 4w / 12w |
| Drawdown from Peak | 127–128 | Current price / rolling max over 12w / 52w |
| Distance from Moving Average | 129–131 | (Price − SMA) / SMA over 4w, 12w, 26w |
| SPY Relative Strength | 132–134 | ETF return − SPY return over 4w, 12w, 26w |
| Negated SPY Correlation | 135–137 | −corr(ETF, SPY) over 12w, 26w, 52w |

> **Note:** `alpha_110` (12-week cumulative return) is hard-wired as the short-entry filter in BaselineRisk and is not used as a ranking signal.

### 3.3 ML Signals

Five ML signals trained on the ETF universe and stored in `weekly_signal` (signal_id 1–5). All models use walk-forward cross-validation on the IS period.

| signal_id | Model | Label | OOS Baseline Sharpe |
|-----------|-------|-------|:-------------------:|
| 1 | LightGBM | FRS3 | −1.571 |
| **2 ★** | **Ensemble (Rank Average)** | **FRS1** | **0.862** |
| 3 | XGBoost | FRS3 | −0.731 |
| 4 | PCA + Ridge | FRS3 | 0.267 |
| 5 | MLP | FRS2 | −0.087 |

---

## 4. Backtest Engine

### 4.1 Four-Module Design

| Module | Role | Key API |
|--------|------|---------|
| `BacktestEngine` | Simulation loop — advances clock, coordinates modules, applies fills | `engine.run()`, `engine.evaluate()` |
| `QuoteTerminal` | Single source of truth for time + data (anti-look-ahead) | `terminal.at(day)`, `terminal.signals()` |
| `Signal / Strategy / Risk` | Signal → ranking → position intent → risk filter | `analyze()`, `on_ranking()`, `on_action()` |
| `BacktestAnalyzer` | Performance metrics + multi-panel dashboard (NAV vs SPY) | `.json`, `.md`, `.csv`, `.png` artifacts |

### 4.2 Simulation Flow (per weekly period)

| Step | Who | What happens |
|------|-----|-------------|
| 1 | BacktestEngine | `terminal.at(today)` — advances data cut-off to current Wednesday close |
| 2 | Signal | `analyze()` — reads history via QuoteTerminal, returns `OrderedDict[ticker → score]` |
| 3 | Strategy | `on_ranking(ranking)` — converts scores to a list of proposed Actions with sizes |
| 4 | Risk | `on_action(actions)` — filters, clamps, or blocks actions; updates internal risk state |
| 5 | Trader | `on_action(filtered)` — converts Actions to Trades at Thursday-close prices |
| 6 | Account | `on_trades(trades)` — updates cash, positions, NAV; records snapshot |
| 7 | BacktestAnalyzer | `evaluate()` — writes `*_metrics.json`, `*_metrics.md`, `*_value_history.csv`, `*_all_in_one_panel.png` |

### 4.3 Anti-Look-Ahead Architecture

**Core contract:** inside `Signal.analyze()`, `Strategy.on_ranking()`, and `Risk.on_action()`, all data access goes through `self.terminal.*()` queries. Every method on `QuoteTerminal` applies a hard filter `date ≤ terminal.day` before returning any row. There is no path for future data to leak in.

### 4.4 QuoteTerminal API

| Method | Returns | Data cut-off |
|--------|---------|-------------|
| `terminal.at(day)` | Sets simulation date | N/A (setter) |
| `terminal.day` | Current simulation date | N/A (getter) |
| `terminal.quote(ticker)` | Single `weekly_bar` row for today | Exactly `terminal.day` |
| `terminal.today_etfs()` | ETF cross-section for today | Exactly `terminal.day` |
| `terminal.etfs()` | ETF `weekly_bar` history (wide) | ≤ `terminal.day` inclusive |
| `terminal.signals()` | `weekly_signal` wide history | ≤ `terminal.day` inclusive |
| `terminal.benchmarks()` | SPY / SPX / VIX / US10Y history | ≤ `terminal.day` inclusive |

---

## 5. Signal Optimization Framework

The signal optimization pipeline evaluates individual signals by mapping cross-sectional scores to portfolio weights via a softmax allocator, then backtesting frictionlessly.

### 5.1 Softmax Allocator

```
Long (LP):   w_i = exp(s_i) / Σ_j exp(s_j)

Short (SP):  w_i = exp(−s_i) / Σ_j exp(−s_j)   [negated scores → low-score ETFs get short weight]
```

- **Long Power (LP):** softmax on raw scores — higher score → more weight → bets on outperformers
- **Short Power (SP):** softmax on negated scores — lower score → more short weight → bets against underperformers

### 5.2 Equal-Weight Baseline (Step 0)

Identical scores imply w_i = 1/N. This is the mandatory Sharpe floor in the signal optimization pipeline.

| Period | LP Sharpe | LP Ann. Return | SP Sharpe | SP Ann. Return |
|--------|:---------:|:--------------:|:---------:|:--------------:|
| IS | 0.690 | 9.73% | −0.690 | −10.94% |
| OOS | 1.537 | 16.40% | −1.537 | −15.01% |

> **Short-only structural loss:** all SP Sharpes are ≤ 0. A pure short-only book on US sector ETFs is structurally loss-making in a secular bull market.

### 5.3 Optimization Steps

| Step | What is optimized | Method | Must beat | Status |
|------|-------------------|--------|-----------|--------|
| Step 0 | Equal-weight baseline | — | — | ✅ Complete |
| Step 1 | Single signal / alpha score stream | IC pre-screen + grid search | Step 0 Sharpe | ✅ Complete |
| Step 2 | Linear multi-signal mix Σ α_k g^(k) | Bayesian opt + walk-forward CV | Steps 0–1 | 🔄 Next |
| Step 3 | Neural network parameters θ → per-ETF logits | SGD / Adam + differentiable backtest | Steps 0–2 | ⏳ Planned |

---

## 6. Baseline Long-Short Strategy

### 6.1 Position Structure

| Parameter | Value | Note |
|-----------|-------|------|
| Long positions | Top 3 by signal rank | +33.3% weight each |
| Short positions | Bottom 3 by signal rank | −33.3% weight each |
| Target gross exposure | 200% | NORMAL state |
| Target net exposure | ~0% | Market-neutral |
| Rebalance frequency | Weekly | Wednesday signal / Thursday execute |

### 6.2 Short-Entry Filter

A short position is only opened if `alpha_110 < 0` (12-week cumulative return is negative). This prevents shorting ETFs with positive intermediate-term momentum. If fewer than 3 ETFs satisfy the filter, the short book shrinks proportionally.

### 6.3 Rank Stickiness

Existing holdings are retained without rebalancing if the ETF's current rank stays within a tolerance band of the cutoff, avoiding whipsaw from minor rank fluctuations.

| Side | Retained if |
|------|-------------|
| Long | Rank ≤ n_long + 2 (i.e., ≤ 5 out of 11) |
| Short | Rank ≥ n_total − n_short + 1 − 2 (i.e., ≥ 7 out of 11) |

### 6.4 3-Tier Risk State Machine (BaselineRisk)

```
          DD ≥ 10%                  DD ≥ 15%
NORMAL ─────────────► LIGHT ─────────────────► HEAVY
(200% gross)         (100% gross)               (0%, cash)
   ▲                      ▲
   │  DD < 8% for ≥2w     │  ≥2 longs w/ alpha_110 > 0, for ≥2w
   └──────────────────────┘
```

| Transition | Trigger | Recovery condition |
|-----------|---------|-------------------|
| NORMAL → LIGHT | Portfolio drawdown ≥ 10% | DD < 8% for ≥ 2 consecutive weeks |
| LIGHT → HEAVY | Portfolio drawdown ≥ 15% | — |
| LIGHT → NORMAL | — | DD < 8% for ≥ 2 consecutive weeks |
| HEAVY → LIGHT | — | ≥ 2 proposed longs with alpha_110 > 0, for ≥ 2 consecutive weeks |

---

## 7. Backtest Results

> **Parameters:** IS = 2021-03-03 → 2024-12-31 (200 weekly periods) | OOS = 2025-01-01 → 2026-03-01 (61 weekly periods) | Initial NAV = 10,000 | Zero fees and slippage

### 7.1 Best-Pick Summary

| Suite | Split | Best Pick | Sharpe | Ann. Return | Max DD |
|-------|-------|-----------|:------:|:-----------:|:------:|
| BL — Alpha (40 IDs) | IS | Alpha#66 | 0.967 | 8.90% | −12.83% |
| BL — Alpha (40 IDs) | **OOS** | **Alpha#23 ★** | **1.819** | **19.34%** | **−6.47%** |
| BL — ML (signals 1–5) | IS | Signal 1 LightGBM_frs3 | 0.601 | 5.09% | −13.71% |
| BL — ML (signals 1–5) | **OOS** | **Signal 2 Ensemble_RankAvg ★** | **0.862** | **10.24%** | **−4.59%** |
| LP — Alpha (signal-opt) | IS | Alpha#24 | 1.122 | 21.38% | — |
| LP — Alpha (signal-opt) | **OOS** | **Alpha#57 ★** | **2.174** | **30.06%** | — |
| LP — ML Step 1 | IS | Signal 5 MLP_frs2 | 0.705 | 9.98% | — |
| LP — ML Step 1 | **OOS** | **Signal 2 Ensemble_RankAvg ★** | **1.730** | **19.12%** | — |

### 7.2 Signal Optimization — Alpha Grid (LP / SP / BL)

| Alpha | LP-IS Sharpe | LP-OOS Sharpe | SP-IS Sharpe | SP-OOS Sharpe | BL-IS Sharpe | BL-OOS Sharpe |
|-------|:------------:|:-------------:|:------------:|:-------------:|:------------:|:-------------:|
| EW Step 0 | 0.690 | 1.537 | −0.690 | −1.537 | — | — |
| #19 | 0.564 | 2.014 | −0.593 | −1.104 | −0.293 | −0.618 |
| #23 | 0.666 | 1.829 | −0.787 | −0.522 | 0.432 | **1.819** |
| #24 | **1.122** | 2.055 | −0.420 | −2.339 | 0.119 | −0.375 |
| **#57** | 0.691 | **2.174** | −0.559 | −1.136 | 0.352 | 1.315 |
| #66 | 0.744 | 1.532 | −0.630 | −1.475 | 0.967 | −0.483 |

### 7.3 Baseline L/S — Alpha Screening (selected)

**In-Sample (2021-03-03 → 2024-12-31):**

| alpha_id | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|----------|:------:|:-----------:|:--------:|:------:|:-------------:|
| **66 ★** | **0.967** | **8.90%** | 9.26% | −12.83% | 4535% |
| 101 | 0.923 | 10.37% | 11.39% | −17.27% | 3134% |
| 32 | 0.684 | 7.43% | 11.44% | −13.05% | 2833% |
| 128 (Andy) | 0.609 | 6.60% | 11.60% | −13.89% | 3151% |
| 57 | 0.352 | 2.44% | 7.67% | −15.68% | 2124% |
| 23 | 0.432 | 3.08% | 7.73% | −17.81% | 1834% |

**Out-of-Sample (2025-01-01 → 2026-03-01):**

| alpha_id | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|----------|:------:|:-----------:|:--------:|:------:|:-------------:|
| **23 ★** | **1.819** | **19.34%** | 10.00% | −6.47% | 4787% |
| 51 | 1.478 | 15.09% | 9.84% | −5.84% | 4305% |
| 37 | 1.463 | 16.38% | 10.77% | −5.78% | 3923% |
| 57 | 1.315 | 14.40% | 10.67% | −7.40% | 5425% |
| 10 | 1.090 | 11.58% | 10.57% | −6.90% | 4976% |
| 66 | −0.483 | −5.25% | 10.11% | −9.27% | 4542% |

> IS best (Alpha#66) collapses OOS (Sharpe −0.483). Weak IS/OOS rank correlation across all 40 alphas confirms high overfitting risk in IS-only selection.

### 7.4 Baseline L/S — ML Signal Screening

**In-Sample:**

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| **1 LightGBM_frs3 ★** | **0.601** | **5.09%** | 8.94% | −13.71% | 1571% |
| 3 XGBoost_frs3 | 0.560 | 4.65% | 8.81% | −16.47% | 1830% |
| 4 PCA_Ridge_frs3 | 0.442 | 3.89% | 9.71% | −18.05% | 1675% |
| 2 Ensemble_RankAvg_frs1 | 0.330 | 2.17% | 7.31% | −16.72% | 1815% |
| 5 MLP_frs2 | 0.247 | 1.61% | 7.66% | −14.06% | 1745% |

**Out-of-Sample:**

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| **2 Ensemble_RankAvg_frs1 ★** | **0.862** | **10.24%** | 12.16% | −4.59% | 4633% |
| 4 PCA_Ridge_frs3 | 0.267 | 2.47% | 11.57% | −7.98% | 3951% |
| 5 MLP_frs2 | −0.087 | −1.27% | 9.59% | −10.40% | 4758% |
| 3 XGBoost_frs3 | −0.731 | −4.79% | 6.44% | −10.33% | 2644% |
| 1 LightGBM_frs3 | −1.571 | −8.54% | 5.58% | −11.76% | 2487% |

> LightGBM_frs3 (IS winner) collapses OOS (Sharpe −1.571). Ensemble (Signal 2) is the only ML signal clearly positive OOS. Single-model FRS3-label approaches overfit; blending and FRS1 labels generalise better.

---

## 8. Key Findings

**Finding 01 — IS Winners Do Not Generalize OOS**  
Alpha#66 (IS BL Sharpe 0.967) collapses to Sharpe −0.483 OOS. Signal 1 / LightGBM_frs3 (IS BL Sharpe 0.601) collapses to −1.571 OOS. IS rank-order correlation with OOS is near zero, making IS-only selection unreliable for this universe.

**Finding 02 — Alpha#23 is the Standout OOS Baseline Signal**  
Alpha#23 achieves OOS Baseline Sharpe 1.819, Ann. Return 19.34%, and a shallow Max DD of only −6.47%. Consistent across the LP signal-opt framework (OOS Sharpe 1.829). Its low IS Sharpe (0.432) means it would be rejected by IS-only selection — reinforcing the need for proper OOS evaluation.

**Finding 03 — Signal 2 (Ensemble Rank Average) is the Most Robust ML Signal**  
The rank-average ensemble (FRS1 label) is the only ML signal with positive OOS Sharpe in both the Baseline L/S (0.862) and LP signal-opt (1.730) frameworks. FRS3-labeled single models generalize poorly OOS. Ensemble averaging and simpler return labels are more robust than complex single-model FRS3 forecasts.

**Finding 04 — Alpha#57 Achieves the Highest OOS Sharpe in LP Mode**  
Alpha#57 reaches OOS LP Sharpe 2.174, Ann. Return 30.06% — the best single-signal result in the entire LP grid. It also performs well in BL mode (OOS Sharpe 1.315), suggesting consistent information content across both long-only and market-neutral contexts.

**Finding 05 — Short-Only (SP) is Structurally Loss-Making**  
All SP Sharpes are ≤ 0, reflecting the secular bull trend in US sector ETFs during the sample period. SP tracking remains useful for identifying short candidates for the Baseline L/S strategy, but standalone short-only portfolios are not viable here.

**Finding 06 — Signal Quality is Framework-Specific**  
IS-strong signals in LP mode (Alpha#24, IS Sharpe 1.122) perform poorly in BL mode (IS Sharpe 0.119) and collapse OOS in BL (−0.375). A good long-only softmax signal is not automatically a good market-neutral signal. Both frameworks must be evaluated independently.

---

## 9. Next Steps

| Priority | Task | Detail |
|----------|------|--------|
| 🔴 High | Signal Opt. Step 2 — Multi-Signal Bayesian Optimization | Linear mix Σ α_k g^(k) over Step 1 candidates; Bayesian opt + walk-forward CV; must beat Steps 0–1 |
| 🔴 High | Baseline Parameter Tuning | Optimize stickiness threshold; add liquidity filter; evaluate borrow cost estimates |
| 🟡 Medium | Transaction Cost Sensitivity | Sweep `long_cost` over {0, 5, 10, 20} bps on Alpha#23, Alpha#57, Signal 2 |
| 🟡 Medium | Walk-Forward OOS Validation | Rolling 12-month windows on best picks to confirm results are not period-specific |
| 🔵 Low | Signal Opt. Step 3 — Differentiable Neural Backtest | Neural network θ → per-ETF logits → softmax → NAV; gradient through soft floor ε = 1e-6 |

---

> **Limitation:** All results are frictionless (zero fees, zero slippage). This is intentional — the goal is to evaluate signal predictive power in isolation. Transaction costs, particularly for high-turnover strategies, will materially reduce realised Sharpe. Cost sensitivity analysis is a planned next step.

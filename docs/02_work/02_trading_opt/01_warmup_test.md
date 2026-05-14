# Baseline Strategy — Sector ETF Long-Short Rotation

**Author**: Simon  
**Version**: v0.3  
**Updated**: 2026-05-13  
**Implementation**: `BaselineStrategy` / `BaselineRisk`

---

## 1. Strategy Overview

Each week, one signal from the signal pool is used to rank all 11 sector ETFs by score. The strategy goes long the top 3 and short the bottom 3, constructing a market-neutral (net ~0%) long-short portfolio that rebalances weekly.

---

## 2. Signal Layer

### 2.1 Signal Pool (Current)

The signal pool contains two types of signals. Both implement `Signal.analyze()` and output `OrderedDict[ticker, score]`:

| Type | Implementation | Currently Available |
|------|---------------|---------------------|
| ML model output | `MLBacktestSignal(signal_id)` | signal 1–5 |
| Single alpha factor | `AlphaBacktestSignal(alpha_id)` | all IDs in the alpha pool |

> ML signals and alpha signals are screened independently via batch backtests; the optimal signal is then wired into the § 8 parameter table.

### 2.2 Risk-Control Alpha

The following alpha is used **exclusively within the risk module** for internal decisions and does not participate in the ranking signal.

**Interface constraint**: all alpha data must be retrieved only through `QuoteTerminal` — direct database queries are not permitted. The risk module calls `terminal.alphas(alpha_ids=(110,))` within `on_action()`. Results are cached per `terminal.day`, so multiple calls within the same week hit the DB only once.

| Alpha | Interface | Purpose |
|-------|-----------|---------|
| `alpha_110` (12-week cumulative return) | `terminal.alphas(alpha_ids=(110,))` | Short-entry filter + HEAVY→LIGHT recovery gate |

---

## 3. Position Structure

### 3.1 Normal State (Full Position)

| Direction | # Holdings | Weight per ETF | Total NAV% |
|-----------|-----------|---------------|-----------|
| Long | 3 | +33.3% | +100% |
| Short | 3 | −33.3% | −100% |
| **Gross exposure** | | | **200%** |
| **Net exposure** | | | **~0%** |

### 3.2 Position by Risk State

| State | Long | Short | Gross Exposure |
|-------|------|-------|---------------|
| NORMAL | +100% | −100% | 200% |
| LIGHT | +50% | −50% | 100% |
| HEAVY | 0% | 0% | 0% (full cash) |

The LIGHT state is implemented by `BaselineRisk` issuing `PositionChange(ratio=0.5)`. The HEAVY state issues `EndTrade + NoTrade` to fully liquidate all positions and block new entries.

---

## 4. Selection Rules (`BaselineStrategy`)

### 4.1 Long Side

- Top `n_long` ranked ETFs by signal score — no additional filter.

### 4.2 Short Side

- Bottom `n_short` ranked ETFs by signal score
- **AND** `alpha_110` **< 0** (12-week cumulative return is negative, i.e. absolute momentum is negative)
- If a bottom-`n_short` ETF has `alpha_110 ≥ 0`, that short slot is **left vacant**; the remaining qualifying shorts are equal-weighted.

> The momentum filter prevents initiating short positions against ETFs in an upward trend.

### 4.3 Position Sizing

New positions are sized at `nav / n_long` (long) or `nav / n_short` (short), converted to share counts using the current closing price. **Existing positions are not rebalanced** — they drift at market value and are fully closed then rebuilt only when a turnover is triggered.

---

## 5. Rebalancing Rules (`BaselineStrategy`)

### 5.1 Frequency

Executed once per week, aligned with the `weekly_bar` period, handled entirely in `on_ranking()`. `on_holding()` returns an empty list — all position management is consolidated in `on_ranking()`.

### 5.2 Rank Stickiness

Avoids excessive turnover from minor rank fluctuations. Long and short sides are evaluated independently.

**Stickiness boundaries (absolute rank):**

| Direction | Retain if |
|-----------|----------|
| Long | Current rank ≤ `n_long + stickiness_threshold` (default ≤ 5) |
| Short | Current rank ≥ `n_total − n_short + 1 − stickiness_threshold` (default ≥ 7 for universe of 11 ETFs) |

Example (`n_long=3, stickiness_threshold=2, n_total=11`):

| Holding | Current Rank | Condition | Decision |
|---------|-------------|-----------|----------|
| Long | #5 | 5 ≤ 5 | **Retain** |
| Long | #6 | 6 > 5 | **Replace** |
| Short | #7 | 7 ≥ 7 | **Retain** |
| Short | #6 | 6 < 7 | **Replace** |

**Forced close (not protected by stickiness):**

- An existing short holding whose `alpha_110` turns from negative to positive is closed immediately.

**New entry logic:**

After retaining existing holdings, vacant slots are filled from the current top ranks (long) or bottom ranks (short, subject to the momentum filter).

---

## 6. Risk Control (`BaselineRisk`)

### 6.1 Drawdown Calculation

```
drawdown = max(0, (peak_nav − current_nav) / peak_nav)

peak_nav = max(
    highest total_value in value_history snapshots,
    current total_value   # today's MTM, pre-snapshot
)
Initial state (no history): peak_nav defaults to account.initial_cash
```

### 6.2 State Transitions

```
             DD ≥ dd_light              DD ≥ dd_heavy
  NORMAL ──────────────────► LIGHT ──────────────────► HEAVY
     ▲                          ▲
     │  DD < dd_recovery         │  ≥ heavy_recovery_min_pos proposed longs
     │  for recovery_weeks       │  with alpha_110 > 0, for recovery_weeks
     └──────────────────────────┘
```

> If drawdown crosses `dd_heavy` without first passing through `dd_light`, the state jumps directly to HEAVY.

### 6.3 Recovery Conditions

| Recovery Path | Condition | Consecutive Weeks Required |
|---------------|-----------|--------------------------|
| LIGHT → NORMAL | `drawdown < dd_recovery` | ≥ `recovery_weeks` |
| HEAVY → LIGHT | ≥ `heavy_recovery_min_pos` proposed long buys have `alpha_110 > 0` | ≥ `recovery_weeks` |

- If any week's condition is not met, the counter **resets to 0**.
- After HEAVY → LIGHT, the LIGHT → NORMAL condition must be satisfied independently to fully restore normal exposure.

**Proposed longs during HEAVY recovery**: `BaselineStrategy` always generates a complete long-side proposal based on signal rankings, regardless of the current risk state. `BaselineRisk.on_action()` reads the `direction="long", side="buy"` tickers from this proposal as a proxy for the current Top-N candidate set.

---

## 7. Edge Cases

| Scenario | Handling |
|----------|---------|
| ETF with no `terminal.quote()` this week | Skip that ticker; existing position carries last week's closing price |
| Fewer than `n_short` ETFs pass the momentum filter | Short as many as qualify; each sized at `nav / n_short`, total short < 100% |
| Initial startup (no value history) | `peak_nav` defaults to `account.initial_cash`; state initializes to NORMAL |
| New signal arrives during HEAVY | Strategy generates proposals, but `NoTrade` blocks execution; `EndTrade` ensures all existing positions are liquidated |

---

## 8. Parameter Reference

### `BaselineStrategy`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `n_long` | 3 | Number of long holdings |
| `n_short` | 3 | Number of short holdings |
| `stickiness_threshold` | 2 | Rank buffer beyond the long/short boundary before a holding is replaced |
| `long_cost` | 0.0 | Long-side transaction cost rate |
| `base_slippage` | 0.0 | Base slippage rate |

### `BaselineRisk`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dd_light` | 0.10 | NORMAL→LIGHT drawdown trigger |
| `dd_heavy` | 0.15 | LIGHT→HEAVY drawdown trigger (also triggers direct HEAVY skip from NORMAL) |
| `dd_recovery` | 0.08 | Drawdown level required to begin LIGHT→NORMAL recovery |
| `recovery_weeks` | 2 | Consecutive weeks the recovery condition must hold |
| `heavy_recovery_min_pos` | 2 | Min proposed longs with positive `alpha_110` momentum for HEAVY→LIGHT recovery |
| ~~`short_momentum_alpha`~~ | fixed `alpha_110` | Hard-coded; not configurable via constructor |

---

## 9. Open Items

- [ ] Estimate `short_cost_per_day` (ETF borrow cost)
- [ ] Liquidity filter (minimum average daily volume threshold)
- [ ] Optimal `stickiness_threshold` via parameter sweep

---

## 10. Backtest Results

**Calendar:** In-sample (IS) 2021-03-03 → 2024-12-31 (200 weekly periods); out-of-sample (OOS) 2025-01-01 → 2026-03-01 (61 weekly periods). Initial NAV: 10,000; zero fees and slippage.

---

### 10.1 Alpha Signal Screening (40 alpha IDs)

**In-Sample (2021-03-03 → 2024-12-31)**

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

**Out-of-Sample (2025-01-01 → 2026-03-01)**

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

**Alpha screening highlights:**

| Split | Best | Sharpe | Ann. Return | Ann. Vol | Max DD | Total Return | Win Rate | CAPM α | CAPM β |
|-------|------|:------:|:-----------:|:--------:|:------:|:------------:|:--------:|:------:|:------:|
| IS | Alpha#66 | 0.967 | 8.90% | 9.26% | −12.83% | 38.56% | 57.3% | 7.37% | 0.119 |
| OOS | Alpha#23 | 1.819 | 19.34% | 10.00% | −6.47% | 22.63% | 61.7% | 14.71% | 0.227 |

> Alpha#66 is the IS winner but fails OOS (Sharpe −0.483). Alpha#23 is the OOS standout with a shallow drawdown and strong CAPM alpha. Other strong OOS performers: #37 (1.463), #51 (1.478), #57 (1.315), #10 (1.090). Low IS/OOS rank correlation signals overfitting risk in IS selection.

---

### 10.2 ML Signal Screening (Signals 1–5)

**In-Sample (2021-03-03 → 2024-12-31)**

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| **Signal 1** LightGBM_frs3 ★ | **0.601** | **5.09%** | 8.94% | −13.71% | 1571% |
| Signal 2 Ensemble_RankAvg_frs1 | 0.330 | 2.17% | 7.31% | −16.72% | 1815% |
| Signal 3 XGBoost_frs3 | 0.560 | 4.65% | 8.81% | −16.47% | 1830% |
| Signal 4 PCA_Ridge_frs3 | 0.442 | 3.89% | 9.71% | −18.05% | 1675% |
| Signal 5 MLP_frs2 | 0.247 | 1.61% | 7.66% | −14.06% | 1745% |

**Out-of-Sample (2025-01-01 → 2026-03-01)**

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| Signal 1 LightGBM_frs3 | −1.571 | −8.54% | 5.58% | −11.76% | 2487% |
| **Signal 2** Ensemble_RankAvg_frs1 ★ | **0.862** | **10.24%** | 12.16% | −4.59% | 4633% |
| Signal 3 XGBoost_frs3 | −0.731 | −4.79% | 6.44% | −10.33% | 2644% |
| Signal 4 PCA_Ridge_frs3 | 0.267 | 2.47% | 11.57% | −7.98% | 3951% |
| Signal 5 MLP_frs2 | −0.087 | −1.27% | 9.59% | −10.40% | 4758% |

**ML screening highlights:**

| Split | Best | Sharpe | Ann. Return | Ann. Vol | Max DD | Total Return | Win Rate | CAPM α | CAPM β |
|-------|------|:------:|:-----------:|:--------:|:------:|:------------:|:--------:|:------:|:------:|
| IS | Signal 1 (LightGBM_frs3) | 0.601 | 5.09% | 8.94% | −13.71% | 20.93% | 53.3% | 6.04% | −0.051 |
| OOS | Signal 2 (Ensemble_RankAvg_frs1) | 0.862 | 10.24% | 12.16% | −4.59% | 11.91% | 46.7% | 6.76% | 0.242 |

> LightGBM_frs3 (Signal 1) collapses OOS (Sharpe −1.571). The rank-average ensemble (Signal 2) is the only ML signal to remain clearly positive in both splits. Single FRS3-label tree models overfit; blending or FRS1 labels generalize better.

---

### 10.3 Best-Pick Summary

| Suite | Split | Best Pick | Sharpe | Ann. Return | Max DD |
|-------|-------|-----------|:------:|:-----------:|:------:|
| Alpha (40 ids) | IS | **Alpha#66** | 0.967 | 8.90% | −12.83% |
| Alpha (40 ids) | OOS | **Alpha#23** | 1.819 | 19.34% | −6.47% |
| ML (signals 1–5) | IS | **Signal 1** LightGBM_frs3 | 0.601 | 5.09% | −13.71% |
| ML (signals 1–5) | OOS | **Signal 2** Ensemble_RankAvg_frs1 | 0.862 | 10.24% | −4.59% |

> Artifacts: `backtests/baseline/no_trans_cost/in_sample/` and `backtests/baseline/no_trans_cost/out_sample/`

# RF Daily Sector-ETF Strategy - Backtest Summary

Window: **2023-07-03 -> 2026-03-12** | Initial NAV: **10,000** | Universe: 11 SPDR sectors

Signal: `RFDailySignal` (signal_id=6 in `daily_signal`), Wed-anchored weekly rebalance with NYSE holiday fallback.

## Top-level configs

| Config | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|--------|:------:|:-----------:|:--------:|:------:|:-------------:|
| baseline_no_trans_cost | 1.259 | 16.30% | 12.63% | -10.80% | 1342.31% |
| baseline_trans_cost | 1.232 | 15.93% | 12.65% | -10.97% | 1342.83% |
| dual_signal | 1.217 | 16.57% | 13.33% | -11.60% | 1318.75% |
| dual_signal_blended | 0.429 | 4.18% | 10.96% | -15.85% | 1168.75% |

## Signal optimization grid

| (n_long, n_short) | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |
|-------------------|:------:|:-----------:|:--------:|:------:|:-------------:|
| nl2_ns2 | 0.235 | 2.20% | 12.70% | -14.85% | 1287.78% |
| nl3_ns3 | 1.259 | 16.30% | 12.63% | -10.80% | 1342.31% |
| nl5_ns5 | 0.388 | 3.82% | 11.34% | -14.23% | 1019.97% |
| nl3_ns2 | 1.083 | 14.10% | 12.97% | -14.22% | 1488.77% |
| nl2_ns3 | 0.210 | 1.69% | 10.74% | -13.83% | 781.58% |

## Notes
- `dual_signal` uses the RF score as BOTH long and short head (symmetric).
  Pair-with-another-signal variants need a second comparable signal; can be added later.
- `dual_signal_blended` is a 50/50 z-scored blend of RF + alpha_24 (best IS LP per the
  repo's reference `dual_signal/no_trans_cost/out_sample/run.py`).
- Short book is filtered by alpha_110 (12-week return < 0), computed during setup_db.
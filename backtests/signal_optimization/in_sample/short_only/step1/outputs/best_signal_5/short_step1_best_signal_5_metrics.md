# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `6,471.81`
- Total Return: `-35.28%`
- Annual Return: `-10.75%`
- Annual Volatility: `15.18%`
- Sharpe Ratio: `-0.673`
- Max Drawdown: `-37.98%`
- Turnover (avg per period): `11.49%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `597.25%` — avg per period × periods_per_year
- Win Rate: `40.20%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-23.49%`
- CAPM Alpha (annualized) vs SPY: `1.44%`
- CAPM Beta vs SPY: `-0.879`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `short_step1_best_signal_5_metrics.json`: machine-readable metrics
- `short_step1_best_signal_5_metrics.md`: human-readable metrics summary
- `short_step1_best_signal_5_value_history.csv`: portfolio value time series
- `short_step1_best_signal_5_holding_history.csv`: position snapshots
- `short_step1_best_signal_5_all_in_one_panel.png`: high-resolution all-in-one dashboard

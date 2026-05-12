# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `11,815.97`
- Total Return: `18.16%`
- Annual Return: `16.76%`
- Annual Volatility: `10.68%`
- Sharpe Ratio: `1.506`
- Max Drawdown: `-10.27%`
- Turnover (avg per period): `12.55%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `652.67%` — avg per period × periods_per_year
- Win Rate: `60.71%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `57`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-0.65%`
- CAPM Alpha (annualized) vs SPY: `4.52%`
- CAPM Beta vs SPY: `0.691`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `step1_best_signal_2_metrics.json`: machine-readable metrics
- `step1_best_signal_2_metrics.md`: human-readable metrics summary
- `step1_best_signal_2_value_history.csv`: portfolio value time series
- `step1_best_signal_2_holding_history.csv`: position snapshots
- `step1_best_signal_2_all_in_one_panel.png`: high-resolution all-in-one dashboard

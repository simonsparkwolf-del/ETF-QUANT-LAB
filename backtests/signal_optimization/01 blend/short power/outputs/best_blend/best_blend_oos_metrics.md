# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `9,272.14`
- Total Return: `-7.28%`
- Annual Return: `-6.34%`
- Annual Volatility: `11.81%`
- Sharpe Ratio: `-0.496`
- Max Drawdown: `-15.32%`
- Turnover (avg per period): `32.21%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1674.76%` — avg per period × periods_per_year
- Win Rate: `37.93%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-21.21%`
- CAPM Alpha (annualized) vs SPY: `3.50%`
- CAPM Beta vs SPY: `-0.610`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `best_blend_oos_metrics.json`: machine-readable metrics
- `best_blend_oos_metrics.md`: human-readable metrics summary
- `best_blend_oos_value_history.csv`: portfolio value time series
- `best_blend_oos_holding_history.csv`: position snapshots
- `best_blend_oos_all_in_one_panel.png`: high-resolution all-in-one dashboard

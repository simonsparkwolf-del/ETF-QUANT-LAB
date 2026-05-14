# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `10,125.93`
- Total Return: `1.26%`
- Annual Return: `1.09%`
- Annual Volatility: `10.72%`
- Sharpe Ratio: `0.154`
- Max Drawdown: `-8.59%`
- Turnover (avg per period): `70.12%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `3646.20%` — avg per period × periods_per_year
- Win Rate: `55.00%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-13.70%`
- CAPM Alpha (annualized) vs SPY: `-1.68%`
- CAPM Beta vs SPY: `0.217`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `equal_weight_blend_oos_metrics.json`: machine-readable metrics
- `equal_weight_blend_oos_metrics.md`: human-readable metrics summary
- `equal_weight_blend_oos_value_history.csv`: portfolio value time series
- `equal_weight_blend_oos_holding_history.csv`: position snapshots
- `equal_weight_blend_oos_all_in_one_panel.png`: high-resolution all-in-one dashboard

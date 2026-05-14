# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `9,005.63`
- Total Return: `-9.94%`
- Annual Return: `-8.68%`
- Annual Volatility: `11.13%`
- Sharpe Ratio: `-0.760`
- Max Drawdown: `-15.83%`
- Turnover (avg per period): `12.07%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `627.53%` — avg per period × periods_per_year
- Win Rate: `32.00%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-23.81%`
- CAPM Alpha (annualized) vs SPY: `1.17%`
- CAPM Beta vs SPY: `-0.628`

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

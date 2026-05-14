# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `13,380.47`
- Total Return: `33.80%`
- Annual Return: `28.71%`
- Annual Volatility: `12.36%`
- Sharpe Ratio: `2.108`
- Max Drawdown: `-10.24%`
- Turnover (avg per period): `51.26%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `2665.31%` — avg per period × periods_per_year
- Win Rate: `63.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `10.71%`
- CAPM Alpha (annualized) vs SPY: `15.05%`
- CAPM Beta vs SPY: `0.717`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `single_alpha_57_oos_metrics.json`: machine-readable metrics
- `single_alpha_57_oos_metrics.md`: human-readable metrics summary
- `single_alpha_57_oos_value_history.csv`: portfolio value time series
- `single_alpha_57_oos_holding_history.csv`: position snapshots
- `single_alpha_57_oos_all_in_one_panel.png`: high-resolution all-in-one dashboard

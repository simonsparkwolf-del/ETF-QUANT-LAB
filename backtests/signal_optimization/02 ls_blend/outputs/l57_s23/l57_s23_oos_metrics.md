# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `13,144.43`
- Total Return: `31.44%`
- Annual Return: `26.74%`
- Annual Volatility: `11.33%`
- Sharpe Ratio: `2.152`
- Max Drawdown: `-4.54%`
- Turnover (avg per period): `105.33%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `5476.95%` — avg per period × periods_per_year
- Win Rate: `58.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `9.02%`
- CAPM Alpha (annualized) vs SPY: `23.54%`
- CAPM Beta vs SPY: `0.054`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `l57_s23_oos_metrics.json`: machine-readable metrics
- `l57_s23_oos_metrics.md`: human-readable metrics summary
- `l57_s23_oos_value_history.csv`: portfolio value time series
- `l57_s23_oos_holding_history.csv`: position snapshots
- `l57_s23_oos_all_in_one_panel.png`: high-resolution all-in-one dashboard

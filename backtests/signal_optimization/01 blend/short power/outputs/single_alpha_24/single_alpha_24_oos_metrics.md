# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `9,046.19`
- Total Return: `-9.54%`
- Annual Return: `-8.32%`
- Annual Volatility: `11.41%`
- Sharpe Ratio: `-0.704`
- Max Drawdown: `-15.81%`
- Turnover (avg per period): `8.78%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `456.43%` — avg per period × periods_per_year
- Win Rate: `36.36%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-23.38%`
- CAPM Alpha (annualized) vs SPY: `0.68%`
- CAPM Beta vs SPY: `-0.568`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `single_alpha_24_oos_metrics.json`: machine-readable metrics
- `single_alpha_24_oos_metrics.md`: human-readable metrics summary
- `single_alpha_24_oos_value_history.csv`: portfolio value time series
- `single_alpha_24_oos_holding_history.csv`: position snapshots
- `single_alpha_24_oos_all_in_one_panel.png`: high-resolution all-in-one dashboard

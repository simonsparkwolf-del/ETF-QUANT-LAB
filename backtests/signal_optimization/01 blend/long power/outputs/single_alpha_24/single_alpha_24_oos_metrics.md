# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `13,198.83`
- Total Return: `31.99%`
- Annual Return: `27.19%`
- Annual Volatility: `12.88%`
- Sharpe Ratio: `1.935`
- Max Drawdown: `-12.21%`
- Turnover (avg per period): `49.08%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `2552.27%` — avg per period × periods_per_year
- Win Rate: `65.00%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `9.58%`
- CAPM Alpha (annualized) vs SPY: `12.48%`
- CAPM Beta vs SPY: `0.811`

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

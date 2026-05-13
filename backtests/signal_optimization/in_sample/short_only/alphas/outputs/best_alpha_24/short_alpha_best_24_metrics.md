# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `7,465.09`
- Total Return: `-25.35%`
- Annual Return: `-7.35%`
- Annual Volatility: `15.40%`
- Sharpe Ratio: `-0.420`
- Max Drawdown: `-36.63%`
- Turnover (avg per period): `31.70%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1648.31%` — avg per period × periods_per_year
- Win Rate: `40.20%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-19.73%`
- CAPM Alpha (annualized) vs SPY: `3.30%`
- CAPM Beta vs SPY: `-0.736`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `short_alpha_best_24_metrics.json`: machine-readable metrics
- `short_alpha_best_24_metrics.md`: human-readable metrics summary
- `short_alpha_best_24_value_history.csv`: portfolio value time series
- `short_alpha_best_24_holding_history.csv`: position snapshots
- `short_alpha_best_24_all_in_one_panel.png`: high-resolution all-in-one dashboard

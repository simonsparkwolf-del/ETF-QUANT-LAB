# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,533.18`
- Total Return: `25.33%`
- Annual Return: `23.33%`
- Annual Volatility: `10.97%`
- Sharpe Ratio: `1.968`
- Max Drawdown: `-7.26%`
- Turnover (avg per period): `52.93%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `2752.24%` — avg per period × periods_per_year
- Win Rate: `66.07%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `57`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `4.87%`
- CAPM Alpha (annualized) vs SPY: `11.35%`
- CAPM Beta vs SPY: `0.613`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `alpha_best_19_metrics.json`: machine-readable metrics
- `alpha_best_19_metrics.md`: human-readable metrics summary
- `alpha_best_19_value_history.csv`: portfolio value time series
- `alpha_best_19_holding_history.csv`: position snapshots
- `alpha_best_19_all_in_one_panel.png`: high-resolution all-in-one dashboard

# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `13,424.80`
- Total Return: `34.25%`
- Annual Return: `29.08%`
- Annual Volatility: `12.85%`
- Sharpe Ratio: `2.055`
- Max Drawdown: `-11.32%`
- Turnover (avg per period): `51.53%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `2679.34%` — avg per period × periods_per_year
- Win Rate: `66.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `11.05%`
- CAPM Alpha (annualized) vs SPY: `14.53%`
- CAPM Beta vs SPY: `0.773`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `alpha_best_24_metrics.json`: machine-readable metrics
- `alpha_best_24_metrics.md`: human-readable metrics summary
- `alpha_best_24_value_history.csv`: portfolio value time series
- `alpha_best_24_holding_history.csv`: position snapshots
- `alpha_best_24_all_in_one_panel.png`: high-resolution all-in-one dashboard

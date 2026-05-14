# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `9,012.90`
- Total Return: `-9.87%`
- Annual Return: `-8.61%`
- Annual Volatility: `9.64%`
- Sharpe Ratio: `-0.886`
- Max Drawdown: `-15.12%`
- Turnover (avg per period): `12.70%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `660.20%` — avg per period × periods_per_year
- Win Rate: `38.46%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-23.89%`
- CAPM Alpha (annualized) vs SPY: `0.43%`
- CAPM Beta vs SPY: `-0.585`

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

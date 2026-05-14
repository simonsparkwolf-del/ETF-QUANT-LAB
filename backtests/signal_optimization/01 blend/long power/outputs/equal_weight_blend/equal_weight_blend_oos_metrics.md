# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,718.40`
- Total Return: `27.18%`
- Annual Return: `23.17%`
- Annual Volatility: `10.38%`
- Sharpe Ratio: `2.062`
- Max Drawdown: `-9.46%`
- Turnover (avg per period): `34.82%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1810.85%` — avg per period × periods_per_year
- Win Rate: `66.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `6.07%`
- CAPM Alpha (annualized) vs SPY: `12.07%`
- CAPM Beta vs SPY: `0.609`

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

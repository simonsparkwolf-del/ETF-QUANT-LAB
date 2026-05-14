# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `11,534.35`
- Total Return: `15.34%`
- Annual Return: `13.17%`
- Annual Volatility: `11.24%`
- Sharpe Ratio: `1.156`
- Max Drawdown: `-5.35%`
- Turnover (avg per period): `77.63%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4036.88%` — avg per period × periods_per_year
- Win Rate: `53.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-2.35%`
- CAPM Alpha (annualized) vs SPY: `11.09%`
- CAPM Beta vs SPY: `0.124`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `best_ls_blend_oos_metrics.json`: machine-readable metrics
- `best_ls_blend_oos_metrics.md`: human-readable metrics summary
- `best_ls_blend_oos_value_history.csv`: portfolio value time series
- `best_ls_blend_oos_holding_history.csv`: position snapshots
- `best_ls_blend_oos_all_in_one_panel.png`: high-resolution all-in-one dashboard

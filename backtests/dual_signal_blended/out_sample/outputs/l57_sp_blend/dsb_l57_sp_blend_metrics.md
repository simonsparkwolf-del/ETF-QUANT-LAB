# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,314.79`
- Total Return: `23.15%`
- Annual Return: `19.78%`
- Annual Volatility: `11.04%`
- Sharpe Ratio: `1.691`
- Max Drawdown: `-6.12%`
- Turnover (avg per period): `105.99%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `5511.28%` — avg per period × periods_per_year
- Win Rate: `58.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `3.32%`
- CAPM Alpha (annualized) vs SPY: `17.49%`
- CAPM Beta vs SPY: `0.077`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `dsb_l57_sp_blend_metrics.json`: machine-readable metrics
- `dsb_l57_sp_blend_metrics.md`: human-readable metrics summary
- `dsb_l57_sp_blend_value_history.csv`: portfolio value time series
- `dsb_l57_sp_blend_holding_history.csv`: position snapshots
- `dsb_l57_sp_blend_all_in_one_panel.png`: high-resolution all-in-one dashboard

# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `10,670.17`
- Total Return: `6.70%`
- Annual Return: `5.78%`
- Annual Volatility: `9.30%`
- Sharpe Ratio: `0.650`
- Max Drawdown: `-9.14%`
- Turnover (avg per period): `75.49%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `3925.34%` — avg per period × periods_per_year
- Win Rate: `43.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-9.30%`
- CAPM Alpha (annualized) vs SPY: `3.31%`
- CAPM Beta vs SPY: `0.178`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `dsb_lp_blend_sp_blend_metrics.json`: machine-readable metrics
- `dsb_lp_blend_sp_blend_metrics.md`: human-readable metrics summary
- `dsb_lp_blend_sp_blend_value_history.csv`: portfolio value time series
- `dsb_lp_blend_sp_blend_holding_history.csv`: position snapshots
- `dsb_lp_blend_sp_blend_all_in_one_panel.png`: high-resolution all-in-one dashboard

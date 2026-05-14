# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `10,523.92`
- Total Return: `5.24%`
- Annual Return: `4.53%`
- Annual Volatility: `9.99%`
- Sharpe Ratio: `0.492`
- Max Drawdown: `-7.93%`
- Turnover (avg per period): `72.19%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `3753.77%` — avg per period × periods_per_year
- Win Rate: `43.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-10.43%`
- CAPM Alpha (annualized) vs SPY: `0.39%`
- CAPM Beta vs SPY: `0.295`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `dsb_lp_blend_s23_metrics.json`: machine-readable metrics
- `dsb_lp_blend_s23_metrics.md`: human-readable metrics summary
- `dsb_lp_blend_s23_value_history.csv`: portfolio value time series
- `dsb_lp_blend_s23_holding_history.csv`: position snapshots
- `dsb_lp_blend_s23_all_in_one_panel.png`: high-resolution all-in-one dashboard

# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `11,018.60`
- Total Return: `10.19%`
- Annual Return: `8.77%`
- Annual Volatility: `9.14%`
- Sharpe Ratio: `0.965`
- Max Drawdown: `-6.19%`
- Turnover (avg per period): `93.33%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4852.91%` — avg per period × periods_per_year
- Win Rate: `55.00%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-6.53%`
- CAPM Alpha (annualized) vs SPY: `7.01%`
- CAPM Beta vs SPY: `0.118`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `os_dual_l66_s24_metrics.json`: machine-readable metrics
- `os_dual_l66_s24_metrics.md`: human-readable metrics summary
- `os_dual_l66_s24_value_history.csv`: portfolio value time series
- `os_dual_l66_s24_holding_history.csv`: position snapshots
- `os_dual_l66_s24_all_in_one_panel.png`: high-resolution all-in-one dashboard

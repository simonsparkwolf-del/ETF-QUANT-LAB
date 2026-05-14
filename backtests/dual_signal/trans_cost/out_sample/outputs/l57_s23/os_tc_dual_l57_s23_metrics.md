# Backtest Metrics Report

## Core Metrics
- Start Value: `9,998.67`
- End Value: `12,889.75`
- Total Return: `28.91%`
- Annual Return: `24.62%`
- Annual Volatility: `11.15%`
- Sharpe Ratio: `2.033`
- Max Drawdown: `-4.66%`
- Turnover (avg per period): `105.40%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `5480.71%` — avg per period × periods_per_year
- Win Rate: `56.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `7.31%`
- CAPM Alpha (annualized) vs SPY: `22.29%`
- CAPM Beta vs SPY: `0.024`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `os_tc_dual_l57_s23_metrics.json`: machine-readable metrics
- `os_tc_dual_l57_s23_metrics.md`: human-readable metrics summary
- `os_tc_dual_l57_s23_value_history.csv`: portfolio value time series
- `os_tc_dual_l57_s23_holding_history.csv`: position snapshots
- `os_tc_dual_l57_s23_all_in_one_panel.png`: high-resolution all-in-one dashboard

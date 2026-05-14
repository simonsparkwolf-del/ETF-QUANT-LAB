# Backtest Metrics Report

## Core Metrics
- Start Value: `9,998.67`
- End Value: `11,911.29`
- Total Return: `19.13%`
- Annual Return: `16.38%`
- Annual Volatility: `10.09%`
- Sharpe Ratio: `1.556`
- Max Drawdown: `-5.32%`
- Turnover (avg per period): `93.54%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4864.32%` — avg per period × periods_per_year
- Win Rate: `56.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `0.34%`
- CAPM Alpha (annualized) vs SPY: `11.86%`
- CAPM Beta vs SPY: `0.249`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `os_tc_dual_l23_s31_metrics.json`: machine-readable metrics
- `os_tc_dual_l23_s31_metrics.md`: human-readable metrics summary
- `os_tc_dual_l23_s31_value_history.csv`: portfolio value time series
- `os_tc_dual_l23_s31_holding_history.csv`: position snapshots
- `os_tc_dual_l23_s31_all_in_one_panel.png`: high-resolution all-in-one dashboard

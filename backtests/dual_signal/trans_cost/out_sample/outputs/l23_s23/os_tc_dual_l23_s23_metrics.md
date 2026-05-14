# Backtest Metrics Report

## Core Metrics
- Start Value: `9,998.67`
- End Value: `12,502.21`
- Total Return: `25.04%`
- Annual Return: `21.37%`
- Annual Volatility: `10.15%`
- Sharpe Ratio: `1.962`
- Max Drawdown: `-5.31%`
- Turnover (avg per period): `90.14%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4687.33%` — avg per period × periods_per_year
- Win Rate: `63.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `4.56%`
- CAPM Alpha (annualized) vs SPY: `16.16%`
- CAPM Beta vs SPY: `0.244`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `os_tc_dual_l23_s23_metrics.json`: machine-readable metrics
- `os_tc_dual_l23_s23_metrics.md`: human-readable metrics summary
- `os_tc_dual_l23_s23_value_history.csv`: portfolio value time series
- `os_tc_dual_l23_s23_holding_history.csv`: position snapshots
- `os_tc_dual_l23_s23_all_in_one_panel.png`: high-resolution all-in-one dashboard

# Backtest Metrics Report

## Core Metrics
- Start Value: `9,998.67`
- End Value: `19,225.47`
- Total Return: `92.28%`
- Annual Return: `18.63%`
- Annual Volatility: `12.30%`
- Sharpe Ratio: `1.452`
- Max Drawdown: `-9.22%`
- Turnover (avg per period): `87.99%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4575.41%` — avg per period × periods_per_year
- Win Rate: `60.80%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `4.60%`
- CAPM Alpha (annualized) vs SPY: `14.92%`
- CAPM Beta vs SPY: `0.222`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `is_tc_dual_l23_s31_metrics.json`: machine-readable metrics
- `is_tc_dual_l23_s31_metrics.md`: human-readable metrics summary
- `is_tc_dual_l23_s31_value_history.csv`: portfolio value time series
- `is_tc_dual_l23_s31_holding_history.csv`: position snapshots
- `is_tc_dual_l23_s31_all_in_one_panel.png`: high-resolution all-in-one dashboard

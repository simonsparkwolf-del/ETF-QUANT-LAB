# Backtest Metrics Report

## Core Metrics
- Start Value: `9,998.67`
- End Value: `12,154.09`
- Total Return: `21.56%`
- Annual Return: `18.43%`
- Annual Volatility: `9.72%`
- Sharpe Ratio: `1.790`
- Max Drawdown: `-4.63%`
- Turnover (avg per period): `106.59%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `5542.85%` — avg per period × periods_per_year
- Win Rate: `56.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `2.06%`
- CAPM Alpha (annualized) vs SPY: `16.24%`
- CAPM Beta vs SPY: `0.076`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `os_tc_dual_l57_s19_metrics.json`: machine-readable metrics
- `os_tc_dual_l57_s19_metrics.md`: human-readable metrics summary
- `os_tc_dual_l57_s19_value_history.csv`: portfolio value time series
- `os_tc_dual_l57_s19_holding_history.csv`: position snapshots
- `os_tc_dual_l57_s19_all_in_one_panel.png`: high-resolution all-in-one dashboard

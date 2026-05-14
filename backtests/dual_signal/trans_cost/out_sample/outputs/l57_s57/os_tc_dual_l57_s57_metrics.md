# Backtest Metrics Report

## Core Metrics
- Start Value: `9,998.67`
- End Value: `12,042.31`
- Total Return: `20.44%`
- Annual Return: `17.49%`
- Annual Volatility: `11.04%`
- Sharpe Ratio: `1.516`
- Max Drawdown: `-7.53%`
- Turnover (avg per period): `108.28%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `5630.64%` — avg per period × periods_per_year
- Win Rate: `56.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `1.39%`
- CAPM Alpha (annualized) vs SPY: `15.67%`
- CAPM Beta vs SPY: `0.070`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `os_tc_dual_l57_s57_metrics.json`: machine-readable metrics
- `os_tc_dual_l57_s57_metrics.md`: human-readable metrics summary
- `os_tc_dual_l57_s57_value_history.csv`: portfolio value time series
- `os_tc_dual_l57_s57_holding_history.csv`: position snapshots
- `os_tc_dual_l57_s57_all_in_one_panel.png`: high-resolution all-in-one dashboard

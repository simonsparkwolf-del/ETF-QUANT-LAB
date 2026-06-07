# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `14,822.56`
- Total Return: `48.23%`
- Annual Return: `15.93%`
- Annual Volatility: `12.65%`
- Sharpe Ratio: `1.232`
- Max Drawdown: `-10.97%`
- Turnover (avg per period): `5.33%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1342.83%` — avg per period × periods_per_year
- Win Rate: `56.57%` — profitable weeks / total trade weeks
- Periods Per Year: `252`
- Number of Periods: `672`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-0.84%`
- CAPM Alpha (annualized) vs SPY: `7.96%`
- CAPM Beta vs SPY: `0.465`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `rf_baseline_tc_metrics.json`: machine-readable metrics
- `rf_baseline_tc_metrics.md`: human-readable metrics summary
- `rf_baseline_tc_value_history.csv`: portfolio value time series
- `rf_baseline_tc_holding_history.csv`: position snapshots
- `rf_baseline_tc_all_in_one_panel.png`: high-resolution all-in-one dashboard

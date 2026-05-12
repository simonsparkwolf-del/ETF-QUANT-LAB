# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `11,513.64`
- Total Return: `15.14%`
- Annual Return: `13.98%`
- Annual Volatility: `10.46%`
- Sharpe Ratio: `1.305`
- Max Drawdown: `-10.64%`
- Turnover (avg per period): `0.54%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `28.24%` — avg per period × periods_per_year
- Win Rate: `58.93%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `57`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-3.08%`
- CAPM Alpha (annualized) vs SPY: `2.37%`
- CAPM Beta vs SPY: `0.674`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `signal_optimization_smoketest_metrics.json`: machine-readable metrics
- `signal_optimization_smoketest_metrics.md`: human-readable metrics summary
- `signal_optimization_smoketest_value_history.csv`: portfolio value time series
- `signal_optimization_smoketest_holding_history.csv`: position snapshots
- `signal_optimization_smoketest_all_in_one_panel.png`: high-resolution all-in-one dashboard

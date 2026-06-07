# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `11,050.69`
- Total Return: `10.51%`
- Annual Return: `3.82%`
- Annual Volatility: `11.34%`
- Sharpe Ratio: `0.388`
- Max Drawdown: `-14.23%`
- Turnover (avg per period): `4.05%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1019.97%` — avg per period × periods_per_year
- Win Rate: `53.28%` — profitable weeks / total trade weeks
- Periods Per Year: `252`
- Number of Periods: `672`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-12.03%`
- CAPM Alpha (annualized) vs SPY: `-4.52%`
- CAPM Beta vs SPY: `0.543`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `rf_so_nl5_ns5_metrics.json`: machine-readable metrics
- `rf_so_nl5_ns5_metrics.md`: human-readable metrics summary
- `rf_so_nl5_ns5_value_history.csv`: portfolio value time series
- `rf_so_nl5_ns5_holding_history.csv`: position snapshots
- `rf_so_nl5_ns5_all_in_one_panel.png`: high-resolution all-in-one dashboard

# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `10,455.81`
- Total Return: `4.56%`
- Annual Return: `1.69%`
- Annual Volatility: `10.74%`
- Sharpe Ratio: `0.210`
- Max Drawdown: `-13.83%`
- Turnover (avg per period): `3.10%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `781.58%` — avg per period × periods_per_year
- Win Rate: `53.28%` — profitable weeks / total trade weeks
- Periods Per Year: `252`
- Number of Periods: `672`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-14.17%`
- CAPM Alpha (annualized) vs SPY: `0.76%`
- CAPM Beta vs SPY: `0.091`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `rf_so_nl2_ns3_metrics.json`: machine-readable metrics
- `rf_so_nl2_ns3_metrics.md`: human-readable metrics summary
- `rf_so_nl2_ns3_value_history.csv`: portfolio value time series
- `rf_so_nl2_ns3_holding_history.csv`: position snapshots
- `rf_so_nl2_ns3_all_in_one_panel.png`: high-resolution all-in-one dashboard

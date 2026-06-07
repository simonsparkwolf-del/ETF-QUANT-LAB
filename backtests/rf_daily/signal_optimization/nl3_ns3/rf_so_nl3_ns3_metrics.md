# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `14,950.45`
- Total Return: `49.50%`
- Annual Return: `16.30%`
- Annual Volatility: `12.63%`
- Sharpe Ratio: `1.259`
- Max Drawdown: `-10.80%`
- Turnover (avg per period): `5.33%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1342.31%` — avg per period × periods_per_year
- Win Rate: `56.57%` — profitable weeks / total trade weeks
- Periods Per Year: `252`
- Number of Periods: `672`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-0.52%`
- CAPM Alpha (annualized) vs SPY: `8.28%`
- CAPM Beta vs SPY: `0.464`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `rf_so_nl3_ns3_metrics.json`: machine-readable metrics
- `rf_so_nl3_ns3_metrics.md`: human-readable metrics summary
- `rf_so_nl3_ns3_value_history.csv`: portfolio value time series
- `rf_so_nl3_ns3_holding_history.csv`: position snapshots
- `rf_so_nl3_ns3_all_in_one_panel.png`: high-resolution all-in-one dashboard

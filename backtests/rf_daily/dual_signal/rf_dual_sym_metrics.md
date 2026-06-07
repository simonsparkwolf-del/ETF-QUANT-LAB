# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `15,041.16`
- Total Return: `50.41%`
- Annual Return: `16.57%`
- Annual Volatility: `13.33%`
- Sharpe Ratio: `1.217`
- Max Drawdown: `-11.60%`
- Turnover (avg per period): `5.23%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1318.75%` — avg per period × periods_per_year
- Win Rate: `55.07%` — profitable weeks / total trade weeks
- Periods Per Year: `252`
- Number of Periods: `672`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-0.20%`
- CAPM Alpha (annualized) vs SPY: `8.52%`
- CAPM Beta vs SPY: `0.469`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `rf_dual_sym_metrics.json`: machine-readable metrics
- `rf_dual_sym_metrics.md`: human-readable metrics summary
- `rf_dual_sym_value_history.csv`: portfolio value time series
- `rf_dual_sym_holding_history.csv`: position snapshots
- `rf_dual_sym_all_in_one_panel.png`: high-resolution all-in-one dashboard

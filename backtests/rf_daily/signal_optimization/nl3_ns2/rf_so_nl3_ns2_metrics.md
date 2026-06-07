# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `14,208.86`
- Total Return: `42.09%`
- Annual Return: `14.10%`
- Annual Volatility: `12.97%`
- Sharpe Ratio: `1.083`
- Max Drawdown: `-14.22%`
- Turnover (avg per period): `5.91%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1488.77%` — avg per period × periods_per_year
- Win Rate: `55.97%` — profitable weeks / total trade weeks
- Periods Per Year: `252`
- Number of Periods: `672`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-2.39%`
- CAPM Alpha (annualized) vs SPY: `6.85%`
- CAPM Beta vs SPY: `0.438`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `rf_so_nl3_ns2_metrics.json`: machine-readable metrics
- `rf_so_nl3_ns2_metrics.md`: human-readable metrics summary
- `rf_so_nl3_ns2_value_history.csv`: portfolio value time series
- `rf_so_nl3_ns2_holding_history.csv`: position snapshots
- `rf_so_nl3_ns2_all_in_one_panel.png`: high-resolution all-in-one dashboard

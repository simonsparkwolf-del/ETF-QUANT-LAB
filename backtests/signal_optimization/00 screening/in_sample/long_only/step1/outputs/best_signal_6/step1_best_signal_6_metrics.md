# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,203.69`
- Total Return: `22.04%`
- Annual Return: `5.34%`
- Annual Volatility: `7.30%`
- Sharpe Ratio: `0.750`
- Max Drawdown: `-9.33%`
- Turnover (avg per period): `0.51%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `26.36%` — avg per period × periods_per_year
- Win Rate: `58.97%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-7.79%`
- CAPM Alpha (annualized) vs SPY: `2.81%`
- CAPM Beta vs SPY: `0.201`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `step1_best_signal_6_metrics.json`: machine-readable metrics
- `step1_best_signal_6_metrics.md`: human-readable metrics summary
- `step1_best_signal_6_value_history.csv`: portfolio value time series
- `step1_best_signal_6_holding_history.csv`: position snapshots
- `step1_best_signal_6_all_in_one_panel.png`: high-resolution all-in-one dashboard

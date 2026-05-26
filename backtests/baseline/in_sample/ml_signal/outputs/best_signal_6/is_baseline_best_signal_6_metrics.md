# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,436.35`
- Total Return: `24.36%`
- Annual Return: `5.86%`
- Annual Volatility: `8.74%`
- Sharpe Ratio: `0.696`
- Max Drawdown: `-9.21%`
- Turnover (avg per period): `8.91%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `463.12%` — avg per period × periods_per_year
- Win Rate: `56.41%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-7.18%`
- CAPM Alpha (annualized) vs SPY: `3.70%`
- CAPM Beta vs SPY: `0.180`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `is_baseline_best_signal_6_metrics.json`: machine-readable metrics
- `is_baseline_best_signal_6_metrics.md`: human-readable metrics summary
- `is_baseline_best_signal_6_value_history.csv`: portfolio value time series
- `is_baseline_best_signal_6_holding_history.csv`: position snapshots
- `is_baseline_best_signal_6_all_in_one_panel.png`: high-resolution all-in-one dashboard

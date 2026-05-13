# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `11,190.74`
- Total Return: `11.91%`
- Annual Return: `10.24%`
- Annual Volatility: `12.16%`
- Sharpe Ratio: `0.862`
- Max Drawdown: `-4.59%`
- Turnover (avg per period): `89.10%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4633.34%` — avg per period × periods_per_year
- Win Rate: `46.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-4.87%`
- CAPM Alpha (annualized) vs SPY: `6.76%`
- CAPM Beta vs SPY: `0.242`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `os_baseline_best_signal_2_metrics.json`: machine-readable metrics
- `os_baseline_best_signal_2_metrics.md`: human-readable metrics summary
- `os_baseline_best_signal_2_value_history.csv`: portfolio value time series
- `os_baseline_best_signal_2_holding_history.csv`: position snapshots
- `os_baseline_best_signal_2_all_in_one_panel.png`: high-resolution all-in-one dashboard

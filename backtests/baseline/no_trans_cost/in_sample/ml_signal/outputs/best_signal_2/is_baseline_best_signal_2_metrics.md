# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,755.01`
- Total Return: `27.55%`
- Annual Return: `6.57%`
- Annual Volatility: `9.30%`
- Sharpe Ratio: `0.730`
- Max Drawdown: `-10.74%`
- Turnover (avg per period): `49.22%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `2559.53%` — avg per period × periods_per_year
- Win Rate: `53.27%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-6.47%`
- CAPM Alpha (annualized) vs SPY: `5.09%`
- CAPM Beta vs SPY: `0.129`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `is_baseline_best_signal_2_metrics.json`: machine-readable metrics
- `is_baseline_best_signal_2_metrics.md`: human-readable metrics summary
- `is_baseline_best_signal_2_value_history.csv`: portfolio value time series
- `is_baseline_best_signal_2_holding_history.csv`: position snapshots
- `is_baseline_best_signal_2_all_in_one_panel.png`: high-resolution all-in-one dashboard

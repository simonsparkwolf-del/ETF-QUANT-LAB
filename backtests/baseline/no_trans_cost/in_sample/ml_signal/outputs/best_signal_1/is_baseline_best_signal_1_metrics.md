# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,093.28`
- Total Return: `20.93%`
- Annual Return: `5.09%`
- Annual Volatility: `8.94%`
- Sharpe Ratio: `0.601`
- Max Drawdown: `-13.71%`
- Turnover (avg per period): `30.21%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1570.79%` — avg per period × periods_per_year
- Win Rate: `53.27%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-7.89%`
- CAPM Alpha (annualized) vs SPY: `6.04%`
- CAPM Beta vs SPY: `-0.051`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `is_baseline_best_signal_1_metrics.json`: machine-readable metrics
- `is_baseline_best_signal_1_metrics.md`: human-readable metrics summary
- `is_baseline_best_signal_1_value_history.csv`: portfolio value time series
- `is_baseline_best_signal_1_holding_history.csv`: position snapshots
- `is_baseline_best_signal_1_all_in_one_panel.png`: high-resolution all-in-one dashboard

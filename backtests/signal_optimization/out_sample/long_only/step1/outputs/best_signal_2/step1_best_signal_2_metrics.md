# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,236.40`
- Total Return: `22.36%`
- Annual Return: `19.12%`
- Annual Volatility: `10.44%`
- Sharpe Ratio: `1.730`
- Max Drawdown: `-10.27%`
- Turnover (avg per period): `12.47%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `648.57%` — avg per period × periods_per_year
- Win Rate: `61.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `2.71%`
- CAPM Alpha (annualized) vs SPY: `7.74%`
- CAPM Beta vs SPY: `0.673`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `step1_best_signal_2_metrics.json`: machine-readable metrics
- `step1_best_signal_2_metrics.md`: human-readable metrics summary
- `step1_best_signal_2_value_history.csv`: portfolio value time series
- `step1_best_signal_2_holding_history.csv`: position snapshots
- `step1_best_signal_2_all_in_one_panel.png`: high-resolution all-in-one dashboard

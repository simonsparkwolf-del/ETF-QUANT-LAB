# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `8,509.32`
- Total Return: `-14.91%`
- Annual Return: `-13.06%`
- Annual Volatility: `10.13%`
- Sharpe Ratio: `-1.330`
- Max Drawdown: `-19.26%`
- Turnover (avg per period): `12.65%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `657.61%` — avg per period × periods_per_year
- Win Rate: `38.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-28.82%`
- CAPM Alpha (annualized) vs SPY: `-3.65%`
- CAPM Beta vs SPY: `-0.640`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `short_step1_best_signal_2_metrics.json`: machine-readable metrics
- `short_step1_best_signal_2_metrics.md`: human-readable metrics summary
- `short_step1_best_signal_2_value_history.csv`: portfolio value time series
- `short_step1_best_signal_2_holding_history.csv`: position snapshots
- `short_step1_best_signal_2_all_in_one_panel.png`: high-resolution all-in-one dashboard

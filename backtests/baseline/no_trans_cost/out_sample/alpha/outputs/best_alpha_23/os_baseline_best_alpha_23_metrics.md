# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,262.71`
- Total Return: `22.63%`
- Annual Return: `19.34%`
- Annual Volatility: `10.00%`
- Sharpe Ratio: `1.819`
- Max Drawdown: `-6.47%`
- Turnover (avg per period): `92.06%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4787.33%` — avg per period × periods_per_year
- Win Rate: `61.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `2.85%`
- CAPM Alpha (annualized) vs SPY: `14.71%`
- CAPM Beta vs SPY: `0.227`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `os_baseline_best_alpha_23_metrics.json`: machine-readable metrics
- `os_baseline_best_alpha_23_metrics.md`: human-readable metrics summary
- `os_baseline_best_alpha_23_value_history.csv`: portfolio value time series
- `os_baseline_best_alpha_23_holding_history.csv`: position snapshots
- `os_baseline_best_alpha_23_all_in_one_panel.png`: high-resolution all-in-one dashboard

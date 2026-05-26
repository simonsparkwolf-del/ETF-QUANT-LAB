# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `12,289.26`
- Total Return: `22.89%`
- Annual Return: `19.56%`
- Annual Volatility: `11.37%`
- Sharpe Ratio: `1.629`
- Max Drawdown: `-2.97%`
- Turnover (avg per period): `96.64%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `5025.20%` — avg per period × periods_per_year
- Win Rate: `58.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `3.18%`
- CAPM Alpha (annualized) vs SPY: `16.59%`
- CAPM Beta vs SPY: `0.126`

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

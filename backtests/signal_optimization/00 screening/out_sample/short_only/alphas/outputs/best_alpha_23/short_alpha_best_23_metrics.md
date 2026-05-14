# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `9,223.94`
- Total Return: `-7.76%`
- Annual Return: `-6.76%`
- Annual Volatility: `12.05%`
- Sharpe Ratio: `-0.522`
- Max Drawdown: `-13.84%`
- Turnover (avg per period): `47.24%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `2456.54%` — avg per period × periods_per_year
- Win Rate: `40.00%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-21.63%`
- CAPM Alpha (annualized) vs SPY: `5.07%`
- CAPM Beta vs SPY: `-0.740`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `short_alpha_best_23_metrics.json`: machine-readable metrics
- `short_alpha_best_23_metrics.md`: human-readable metrics summary
- `short_alpha_best_23_value_history.csv`: portfolio value time series
- `short_alpha_best_23_holding_history.csv`: position snapshots
- `short_alpha_best_23_all_in_one_panel.png`: high-resolution all-in-one dashboard

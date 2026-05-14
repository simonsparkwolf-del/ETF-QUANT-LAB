# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `13,542.21`
- Total Return: `35.42%`
- Annual Return: `30.06%`
- Annual Volatility: `12.47%`
- Sharpe Ratio: `2.174`
- Max Drawdown: `-10.17%`
- Turnover (avg per period): `53.55%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `2784.36%` — avg per period × periods_per_year
- Win Rate: `65.00%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `11.77%`
- CAPM Alpha (annualized) vs SPY: `15.99%`
- CAPM Beta vs SPY: `0.725`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `alpha_best_57_metrics.json`: machine-readable metrics
- `alpha_best_57_metrics.md`: human-readable metrics summary
- `alpha_best_57_value_history.csv`: portfolio value time series
- `alpha_best_57_holding_history.csv`: position snapshots
- `alpha_best_57_all_in_one_panel.png`: high-resolution all-in-one dashboard

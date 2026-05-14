# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `20,989.09`
- Total Return: `109.89%`
- Annual Return: `21.38%`
- Annual Volatility: `18.89%`
- Sharpe Ratio: `1.122`
- Max Drawdown: `-16.24%`
- Turnover (avg per period): `46.33%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `2409.16%` — avg per period × periods_per_year
- Win Rate: `60.80%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `7.93%`
- CAPM Alpha (annualized) vs SPY: `8.52%`
- CAPM Beta vs SPY: `0.956`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `alpha_best_24_metrics.json`: machine-readable metrics
- `alpha_best_24_metrics.md`: human-readable metrics summary
- `alpha_best_24_value_history.csv`: portfolio value time series
- `alpha_best_24_holding_history.csv`: position snapshots
- `alpha_best_24_all_in_one_panel.png`: high-resolution all-in-one dashboard

# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `10,081.77`
- Total Return: `0.82%`
- Annual Return: `0.71%`
- Annual Volatility: `10.82%`
- Sharpe Ratio: `0.118`
- Max Drawdown: `-9.92%`
- Turnover (avg per period): `58.51%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `3042.38%` — avg per period × periods_per_year
- Win Rate: `51.67%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-14.07%`
- CAPM Alpha (annualized) vs SPY: `-2.25%`
- CAPM Beta vs SPY: `0.230`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `l24_s24_oos_metrics.json`: machine-readable metrics
- `l24_s24_oos_metrics.md`: human-readable metrics summary
- `l24_s24_oos_value_history.csv`: portfolio value time series
- `l24_s24_oos_holding_history.csv`: position snapshots
- `l24_s24_oos_all_in_one_panel.png`: high-resolution all-in-one dashboard

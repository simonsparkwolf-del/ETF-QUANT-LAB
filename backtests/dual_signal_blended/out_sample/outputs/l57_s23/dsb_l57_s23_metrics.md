# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `13,297.88`
- Total Return: `32.98%`
- Annual Return: `28.02%`
- Annual Volatility: `11.61%`
- Sharpe Ratio: `2.190`
- Max Drawdown: `-4.54%`
- Turnover (avg per period): `105.89%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `5506.47%` — avg per period × periods_per_year
- Win Rate: `58.33%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `10.07%`
- CAPM Alpha (annualized) vs SPY: `23.80%`
- CAPM Beta vs SPY: `0.105`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `dsb_l57_s23_metrics.json`: machine-readable metrics
- `dsb_l57_s23_metrics.md`: human-readable metrics summary
- `dsb_l57_s23_value_history.csv`: portfolio value time series
- `dsb_l57_s23_holding_history.csv`: position snapshots
- `dsb_l57_s23_all_in_one_panel.png`: high-resolution all-in-one dashboard

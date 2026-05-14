# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `9,003.63`
- Total Return: `-9.96%`
- Annual Return: `-8.69%`
- Annual Volatility: `10.78%`
- Sharpe Ratio: `-0.790`
- Max Drawdown: `-15.08%`
- Turnover (avg per period): `29.23%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1519.78%` — avg per period × periods_per_year
- Win Rate: `38.18%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `61`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-23.86%`
- CAPM Alpha (annualized) vs SPY: `2.25%`
- CAPM Beta vs SPY: `-0.701`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `single_alpha_23_oos_metrics.json`: machine-readable metrics
- `single_alpha_23_oos_metrics.md`: human-readable metrics summary
- `single_alpha_23_oos_value_history.csv`: portfolio value time series
- `single_alpha_23_oos_holding_history.csv`: position snapshots
- `single_alpha_23_oos_all_in_one_panel.png`: high-resolution all-in-one dashboard

# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `19,272.26`
- Total Return: `92.72%`
- Annual Return: `18.70%`
- Annual Volatility: `12.46%`
- Sharpe Ratio: `1.440`
- Max Drawdown: `-9.14%`
- Turnover (avg per period): `87.80%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4565.56%` — avg per period × periods_per_year
- Win Rate: `61.31%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `4.68%`
- CAPM Alpha (annualized) vs SPY: `14.92%`
- CAPM Beta vs SPY: `0.228`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `is_dual_l23_s31_metrics.json`: machine-readable metrics
- `is_dual_l23_s31_metrics.md`: human-readable metrics summary
- `is_dual_l23_s31_value_history.csv`: portfolio value time series
- `is_dual_l23_s31_holding_history.csv`: position snapshots
- `is_dual_l23_s31_all_in_one_panel.png`: high-resolution all-in-one dashboard

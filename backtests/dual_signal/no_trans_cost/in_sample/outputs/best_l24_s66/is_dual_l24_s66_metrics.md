# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `17,483.20`
- Total Return: `74.83%`
- Annual Return: `15.72%`
- Annual Volatility: `12.46%`
- Sharpe Ratio: `1.236`
- Max Drawdown: `-12.89%`
- Turnover (avg per period): `68.23%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `3547.90%` — avg per period × periods_per_year
- Win Rate: `60.80%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `2.13%`
- CAPM Alpha (annualized) vs SPY: `11.83%`
- CAPM Beta vs SPY: `0.269`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `is_dual_l24_s66_metrics.json`: machine-readable metrics
- `is_dual_l24_s66_metrics.md`: human-readable metrics summary
- `is_dual_l24_s66_value_history.csv`: portfolio value time series
- `is_dual_l24_s66_holding_history.csv`: position snapshots
- `is_dual_l24_s66_all_in_one_panel.png`: high-resolution all-in-one dashboard

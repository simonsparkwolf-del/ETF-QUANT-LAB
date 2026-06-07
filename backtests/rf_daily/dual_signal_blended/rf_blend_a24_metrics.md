# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `11,152.49`
- Total Return: `11.52%`
- Annual Return: `4.18%`
- Annual Volatility: `10.96%`
- Sharpe Ratio: `0.429`
- Max Drawdown: `-15.85%`
- Turnover (avg per period): `4.64%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `1168.75%` — avg per period × periods_per_year
- Win Rate: `52.97%` — profitable weeks / total trade weeks
- Periods Per Year: `252`
- Number of Periods: `672`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-11.72%`
- CAPM Alpha (annualized) vs SPY: `-1.10%`
- CAPM Beta vs SPY: `0.353`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `rf_blend_a24_metrics.json`: machine-readable metrics
- `rf_blend_a24_metrics.md`: human-readable metrics summary
- `rf_blend_a24_value_history.csv`: portfolio value time series
- `rf_blend_a24_holding_history.csv`: position snapshots
- `rf_blend_a24_all_in_one_panel.png`: high-resolution all-in-one dashboard

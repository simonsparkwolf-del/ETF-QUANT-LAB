# Backtest Metrics Report

## Core Metrics
- Start Value: `10,000.00`
- End Value: `13,856.34`
- Total Return: `38.56%`
- Annual Return: `8.90%`
- Annual Volatility: `9.26%`
- Sharpe Ratio: `0.967`
- Max Drawdown: `-12.83%`
- Turnover (avg per period): `87.21%` — sum(|Δ signed MV|) / (2 × total_value), by date
- Turnover (annualized): `4534.90%` — avg per period × periods_per_year
- Win Rate: `57.29%` — profitable weeks / total trade weeks
- Periods Per Year: `52`
- Number of Periods: `200`

## Benchmark / Alpha
- Annual Excess Return vs SPY: `-4.31%`
- CAPM Alpha (annualized) vs SPY: `7.37%`
- CAPM Beta vs SPY: `0.119`

## Exposure Notes
- `Exposure` means the portfolio's market value exposure to risk.
- In this implementation, `long` exposure is positive and `short` exposure is negative.
- `Net Holding Exposure` = algebraic sum of all long and short exposures for each date.
- Net exposure > 0 means net-long, < 0 means net-short, and near 0 means directionally neutral.

## Output Files
- `is_baseline_best_alpha_66_metrics.json`: machine-readable metrics
- `is_baseline_best_alpha_66_metrics.md`: human-readable metrics summary
- `is_baseline_best_alpha_66_value_history.csv`: portfolio value time series
- `is_baseline_best_alpha_66_holding_history.csv`: position snapshots
- `is_baseline_best_alpha_66_all_in_one_panel.png`: high-resolution all-in-one dashboard

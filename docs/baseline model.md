# Baseline Model
## 1. Data Preprocessing & Feature Engineering
### 1.1 Data Cleaning & Alignment
* Universe: 11 Level-1 Sector SPDR ETFs (XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLRE, XLY).
* Benchmark: SPY Index (S&P 500).
* Data Frequency: Daily data, resampled to weekly frequency (Wednesday close) for signal calculation.
* Fields Used:
* TOT_RETURN_INDEX_GROSS_DVDS (Total Return Index, TRI): The only data field used throughout the entire process. It is used to calculate all momentum signals and holding period returns, ensuring dividend reinvestment is correctly accounted for and that the signal and return evaluation methodologies are perfectly aligned.
### 1.2 Return Calculation Methodology (Wed Decision, Thu Execution)
To eliminate look-ahead bias while reducing the uncertainty of a two-day weekend gap to a single overnight gap, this model adopts the following architecture:
* Signal Calculation Point: After Wednesday's close, using the daily TRI up to Wednesday.
* Trade Execution Point: Thursday's close (the trading day immediately following the signal calculation), when the position officially takes effect.
* Single-Period Return Evaluation: From this Thursday's close TRI to next Thursday's close TRI.
## 2. Core Signal Construction (Three-Factor System)
The model constructs three orthogonalized price momentum signals, which are then standardized using cross-sectional Z-Scores and equally weighted.
### 2.1 Signal 1: Multi-Window Time-Series Momentum (MOM)
Calculates the cumulative return for each ETF over 20-day, 40-day, and 60-day windows, and synthesizes them with specific weights to reduce short-term noise interference.

```Formula
MOM(i,t) = 0.5 × R(i,t)^(60) + 0.3 × R(i,t)^(40) + 0.2 × R(i,t)^(20)
Where:
R(i,t)^(w) is the w-day cumulative return calculated based on the TRI
```

### 2.2 Signal 2: Relative Strength vs Benchmark (RS)
Measures the excess momentum of the sector ETF relative to the S&P 500 Index, followed by long-term standardization.

Step 1 - Relative Return Ratio:
```Formula
RS(i,t) = [1 + MOM(i,t)] / [1 + MOM(SPY,t)] - 1
```
Step 2 - Standardization (Z-Score):

Calculate the mean and standard deviation of RS over the past 252 trading days (approx. 52 weeks):
```Formula
RS_Score(i,t) = [RS(i,t) - μ(RS_i)] / σ(RS_i)
Where:
•	μ(RS_i) is the mean of RS over 252 days
•	σ(RS_i) is the standard deviation of RS over 252 days
```

### 2.3 Signal 3: Volatility-Adjusted Momentum (VA_MOM)
A Sharpe-ratio-like momentum indicator that penalizes high-volatility sectors.

Step 1 - Composite Realized Volatility:

Calculate the annualized standard deviation of returns over the past 60, 40, and 20 days, weighted using the same proportions as momentum (0.5, 0.3, 0.2):
```Formula
σ(composite) = 0.5 × σ(60) + 0.3 × σ(40) + 0.2 × σ(20)
```
Step 2 - Adjusted Momentum:
```Formula
VA_MOM(i,t) = MOM(i,t) / σ(i,t)^(composite)
```
Step 3 - Directional Constraint:

If the raw momentum MOM(i,t) < 0, then VA_MOM(i,t) is forced to be negative to ensure the signal direction is correct.

### 2.4 Composite Signal Synthesis
After Wednesday's close, the three signals above are standardized across the 11 sectors using cross-sectional Z-Scores, and then equally weighted to derive the final composite score:
```Formula
Composite_Score(i,t) = [Z_MOM + Z_RS + Z_VA_MOM] / 3
Where:
•	Z_MOM, Z_RS, Z_VA_MOM are the Z-scored values of each signal
```

## 3. Portfolio Construction & Position Management
### 3.1 Absolute Momentum Filter & Portfolio Construction Logic
The 11 sectors are ranked in descending order based on their composite scores, and an absolute momentum filter is introduced on the long side:
* Long-Only Strategy: Go long only the top 3 ranked sectors provided their raw momentum MOM > 0. If fewer than 3 sectors meet this condition, the unfilled positions are held in cash (assumed to earn 0% interest in the backtest).
* Long-Only Strategy & Cash Allocation: Go long only the top 3 ranked sectors, provided their raw momentum MOM > 0. Each selected ETF targets a base allocation of 33.3% (1/3 of the portfolio). If fewer than 3 sectors meet the positive momentum condition, the unfilled allocations (33.3% per unfilled slot) are held in cash, which is assumed to earn a 0% return in the backtest.

### 3.2 Rank Stickiness Mechanism (Hold Threshold)
To avoid excessive trading (whipsaw) caused by minor rank changes, a hold threshold is introduced:
* A rebalance is triggered only if an ETF's rank changes by more than 2 positions (e.g., dropping from 1st to 4th place).
* If the rank fluctuates slightly within the target range (e.g., 1→2→1), the original position is maintained.
* Rank Stickiness & Momentum Override: To avoid excessive trading (whipsaw) caused by minor rank changes, a hold threshold is introduced: a rebalance is triggered if an existing holding's rank changes by more than 2 positions. 
* Crucially, the absolute momentum filter (MOM > 0) has the highest priority. Even if an ETF's rank fluctuation remains within the allowable threshold, it will be immediately liquidated and replaced if its raw momentum turns negative.
### 3.3 Inverse Volatility Weighting
Within the selected Top-3 portfolio, positions are inversely weighted based on their realized volatility over the past 20 days:
```Formula
w(i) = [1/σ(i,t)] / Σ[1/σ(j,t)]  for j in Top-3
```
This allows low-volatility sectors to receive higher weights. Additionally, a single-sector weight cap of 25% is enforced, with any excess weight proportionally redistributed to the other selected sectors.

Inverse Volatility Weighting: Within the selected portfolio (maximum of 3 sectors), positions are inversely weighted based on their realized volatility over the past 20 days. The weight formula is adjusted to account for potential cash positions:
```Formula
w(i) = [1/σ(i,t)] / Σ[1/σ(j,t)] × (N / 3)
Where N is the number of valid ETFs selected (N ≤ 3).
```
This ensures that low-volatility sectors receive higher relative weights within the invested portion of the portfolio, while strictly maintaining the required cash buffer if N < 3. (Note: The 25% single-sector weight cap has been removed for the Top-3 strategy, as it mathematically conflicts with achieving a fully invested 100% portfolio when exactly 3 sectors are selected).

## 4. Rebalancing Mechanism & Trade Execution
### 4.1 Trading Frequency & Cost Assumptions
* Rebalancing Frequency: Weekly rebalancing (target weights calculated after Wednesday's close, executed at Thursday's close).
* Transaction Costs & Slippage: This baseline model assumes zero transaction costs and zero slippage (0 bps) to purely evaluate the effectiveness of the strategy signals.

### 4.2 Backtest Engine Data Flow
1. Daily: Receive daily TRI data.
2. Wednesday Close: Snapshot the TRI data up to that day, calculate the three-factor signals, and generate the target weight matrix.
3. Thursday Close: Positions officially take effect. Calculate the single-period return from this Thursday's close TRI to next Thursday's close TRI.
4. NAV Update: Multiply the target weights by the single-period return to update the cumulative Net Asset Value (NAV) of the portfolio.

## 5. Performance Evaluation Metrics & Visualizations
### 5.1 Core Performance Metrics
The model outputs the following core performance metrics:
* Return Metrics: Total Return, Compound Annual Growth Rate (CAGR), Annualized Excess Return (Ann. Alpha vs SPY).
* Risk Metrics: Annualized Volatility, Maximum Drawdown.
* Risk-Adjusted Returns: Sharpe Ratio, Sortino Ratio, Calmar Ratio, Information Ratio.
* Trading & Exposure Metrics:
* Win Rate: Percentage of profitable weeks.
* Annualized Turnover: Annualized one-way turnover. Due to the inverse volatility weighting mechanism slightly adjusting weights every week based on the latest volatility, a high baseline turnover (approx. 800%) is expected.
* Average Exposure: Average percentage of the portfolio allocated to long positions (100% means fully invested).

### 5.2 Visualizations
The backtest engine automatically generates the following visualizations to aid analysis:

5. Cumulative Returns & Drawdown: Displays the equity curves of the strategy, SPX benchmark, and equal-weight benchmark, along with the strategy's dynamic drawdown and rolling 26-week Sharpe ratio.
6. Monthly Returns Heatmap: Intuitively displays the strategy's absolute return performance across different months.
7. Weekly Sector Weights: Shows the historical weight changes of each sector ETF in the portfolio.
8. ETF Selection Frequency: A bar chart showing the total number of weeks each ETF was selected into the long portfolio, used to analyze the strategy's sector preferences.



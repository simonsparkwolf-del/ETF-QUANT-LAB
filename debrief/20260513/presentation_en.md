# Data-Driven Sector ETF Rotation Strategy
## — A Quantitative Research Framework Based on Large-Scale Signal Mining and Machine Learning

> **Core Positioning**: This project replaces subjective judgment and single hand-picked indicators with a systematic, data-driven pipeline. We screen 80+ price-volume factors and multiple ML models under a unified quantitative standard, automatically identifying effective signals, then deploy them through a trading execution framework to capture Alpha. The entire research process is data-driven, reusable, iterable, and extensible.

---

**Audience**: Finance Industry Professionals  
**Date**: 2026-05-13  
**Backtest Period**: 2025-01-01 to 2026-01-31 (57 weekly periods, zero fees, zero slippage)

---

## I. Research Motivation

### 1.1 Market Background

Sector rotation in US equities is well-established. Different phases of the economic cycle correspond to different sector leadership — defensive sectors lead in recessions, cyclical sectors surge in recoveries. **SPDR Sector ETFs** are the most direct instrument for capturing this pattern: 11 ETFs cover all GICS Level-1 sectors (Technology, Financials, Energy, Healthcare, Consumer, etc.), with strong liquidity and low trading costs — naturally suited for rotation strategies.

### 1.2 Limitations of Traditional Approaches

Most sector rotation strategies rely on **a handful of manually constructed momentum indicators**, such as 3-month or 6-month price momentum. These approaches have two fundamental flaws:

- **Subjective factor selection**: researchers pick indicators based on intuition, with no systematic way to assess which factors genuinely have predictive power
- **No framework for parameter tuning**: the combination space of lookback windows, position counts, and other parameters is enormous — manual search is both inefficient and prone to overfitting

### 1.3 Our Starting Point

Our goal is to build a **systematic, iterable quantitative research framework**:

> Use a unified evaluation standard to objectively test a large number of signals, and let the data tell us which signals are effective — rather than guessing.

This framework not only answers "which factor is best," but also lays the foundation for continuous iteration (adding new factors, optimising combination weights, incorporating machine learning).

---

## II. Research Framework Overview

**Core Question**: What kind of signal can accurately predict the relative strength of sector ETFs over the next 4 weeks, after each Wednesday close?

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Raw Data (Weekly Update)                          │
│          11 Sector ETFs  ×  OHLCV + Total Return Index (TRI)            │
└───────────────────────┬─────────────────────────┬───────────────────────┘
                        │                         │
           ┌────────────▼────────────┐   ┌────────▼────────────────────────┐
           │     Alpha Factor Factory │   │        ML Prediction Pipeline   │
           │                         │   │                                  │
           │  101 Formulaic Alphas    │   │  Labels: FRS (4-week returns)   │
           │  + 29 Andy Factors       │   │  ┌──────────────────────────┐   │
           │         ↓               │   │  │ FRS1  Total Return        │   │
           │  IC Pre-Screen           │   │  │ FRS2  Sharpe Proxy        │   │
           │  (Mean IC > 0.02)        │   │  │ FRS3  Vol-Penalised Ret.  │   │
           │         ↓               │   │  └──────────────────────────┘   │
           │  82 Viable Alpha Factors │   │         ↓ Train on FRS labels   │
           └────────────┬────────────┘   │  LightGBM / XGBoost / MLP /     │
                        │               │  PCA+Ridge / Ensemble             │
                        │               │         ↓                         │
                        │               │  5 ML Signals (weekly ETF scores) │
                        │               └────────────────┬──────────────────┘
                        │                                │
                        └──────────────┬─────────────────┘
                                       │
                              ┌────────▼────────┐
                              │  Signal Pool     │
                              │ 82 Alpha + 5 ML  │
                              └────────┬─────────┘
                                       │
          ┌────────────────────────────▼──────────────────────────────────┐
          │                  Layer 1: Signal Evaluation Framework          │
          │                                                               │
          │  Baseline: Equal-Weight (Sharpe 1.305) — mandatory floor      │
          │                                                               │
          │  Each signal → Softmax weights → Long-only backtest → Sharpe  │
          │                                                               │
          │  Screening Results:                                           │
          │    Best Alpha:  Alpha#19  (Sharpe 1.968)                      │
          │    Best ML:     Signal 2 Ensemble  (Sharpe 1.506)             │
          └────────────────────────────┬──────────────────────────────────┘
                                       │ Top signals passed down
          ┌────────────────────────────▼──────────────────────────────────┐
          │                  Layer 2: Signal Deployment                    │
          │                                                               │
          │  Market-Neutral Long-Short Strategy                           │
          │  Long Top-3  ←── Signal Ranking ──►  Short Bottom-3           │
          │                                        (momentum filter)      │
          │  Risk Control: 3-Tier State Machine (NORMAL/LIGHT/HEAVY)      │
          │                                                               │
          │  Deployment Results:                                          │
          │    Best Alpha:  Alpha#23  (Sharpe 2.081, Beta 0.234)          │
          │    Best ML:     Signal 2  (Sharpe 0.806)                      │
          └───────────────────────────────────────────────────────────────┘
```

**Research Logic**: Layer 1 standardises the comparison environment to screen signals at scale (signal predictive power in isolation). Layer 2 validates how signals perform inside a real trading framework. The two layers are decoupled — a signal must prove itself in both dimensions to be considered production-ready.

---

## III. Signal Pool

Before explaining how we evaluate signals, here is what we are testing.

### 3.1 Price-Volume Alpha Factors

#### Source: 101 Formulaic Alphas

The core of the factor library comes from the academic paper *101 Formulaic Alphas* (Kakushadze, 2015), a widely cited factor set in Wall Street quant practice. Of the original 101 factors, **82 implementable factors** are retained — the remaining 19 require market-cap data or industry neutralisation (meaningless in an 11-ETF universe).

#### Economic Classification

| Category | Representative Factors | Core Logic |
|----------|----------------------|------------|
| Momentum / Trend | Alpha#19, #24, #37 | Trend continuation — strong sectors stay strong |
| Mean Reversion | Alpha#23, #9, #49 | Price recovery after short-term over-extension |
| Volume-Price | Alpha#3, #12, #13 | Volume-price divergence or co-movement signals |
| Vol-Adjusted | Alpha#34, #35, #55 | Strip out high-volatility noise, isolate trend |

#### Andy Factors

Beyond the 101 formulaic factors, we developed **29 custom factors (Andy Factors)** designed specifically for sector ETF rotation. The most critical:

- **12-Week Cumulative Return Factor**: measures absolute momentum direction. Used in the baseline strategy as the **short-side filter** — only ETFs with negative absolute momentum (downward trend) are eligible for shorting, preventing short positions against rising sectors.

#### IC Pre-Screening

All factors pass through an **Information Coefficient (IC)** filter before entering the full backtest. IC measures rank correlation between predicted and realised returns: higher mean IC means more accurate directional predictions. Only factors with Mean IC > 0.02 and IC-IR > 0.3 enter the full backtest.

Top factors after pre-screening:

| Factor | Mean IC | Economic Intuition |
|--------|---------|-------------------|
| Alpha#50 | 0.042 | Volume-VWAP correlation structure |
| Alpha#3  | 0.034 | Open-volume negative correlation |
| Alpha#41 | 0.034 | Geometric mid-price vs VWAP spread |
| Alpha#24 | 0.033 | 100-day moving average momentum |
| Alpha#98 | 0.031 | VWAP × short-term turnover interaction |

---

### 3.2 Machine Learning Signals

#### Why Machine Learning

Traditional factor combinations depend on researcher judgement, and parameter search requires extensive manual trial-and-error. The core value of ML is:

> **Let the model automatically learn effective combination weights across all 82 factors, using forward returns as supervision labels — discovering non-linear relationships that humans cannot easily detect.**

#### Prediction Target Design (FRS)

ML models predict a **Future Return Score (FRS)** — each ETF's performance over the next 4 weeks. Three label variants target different investment preferences:

| Label | Definition | Use Case |
|-------|-----------|----------|
| FRS1 | 4-week total return | Directional return prediction |
| FRS2 | 4-week Sharpe proxy | Risk-adjusted performance |
| FRS3 | FRS1 − 2 × volatility | Penalises high-vol outperformance |

Each model scores all 11 ETFs weekly — higher score means "more worth buying."

#### Five ML Signals

| Signal | Model | Target | Approach |
|--------|-------|--------|----------|
| Signal 1 | LightGBM | FRS3 | Industry-standard gradient boosting for tabular data |
| Signal 2 | Ensemble (rank-avg) | FRS1 | Combines multiple models — reduces single-model bias |
| Signal 3 | XGBoost | FRS3 | Paired with LightGBM to validate model robustness |
| Signal 4 | PCA + Ridge | FRS3 | Linear baseline after dimensionality reduction |
| Signal 5 | MLP | FRS2 | Captures non-linear factor interactions |

---

## IV. Signal Evaluation Methodology

### 4.1 Why a Unified Evaluation Framework

The most direct way to evaluate a signal is to plug it into a real strategy and observe the resulting Sharpe. But this creates a problem: **if different signals use different execution logic, we cannot attribute performance differences to the signal itself vs. the strategy design.**

Our solution: design a **standardised evaluation strategy**, where all signals compete under identical execution logic — isolating each signal's pure information content.

### 4.2 Evaluation Strategy: Softmax Weight Allocation

**Core Mechanism**:

1. Signal scores all 11 ETFs (higher score = stronger expected performance)
2. Softmax converts scores to weights — higher-scoring ETFs get larger positions; all ETFs always held (fully invested long)
3. Weights rebalanced each week based on new signal

$$w_{\text{ETF}_i} = \frac{e^{s_i}}{\sum_{j=1}^{11} e^{s_j}}$$

**Advantages**:
- Weights change continuously — no hard "buy top N" cutoff that triggers excessive rebalancing at rank boundaries
- Signal strength maps directly to weight — comparison between signals is completely fair
- Naturally extensible to multi-signal weighted combinations

#### Weekly Allocation Flow

```
Every Wednesday after close
      │
      ▼
┌─────────────────────────────────────────────────────┐
│             Signal Scoring (11 ETFs)                 │
│                                                     │
│   XLK  ████████████████  +2.1  (Tech, Strong)       │
│   XLV  ████████████      +1.4  (Healthcare)         │
│   XLF  ████████          +0.9  (Financials)         │
│   XLI  ██████            +0.5  (Industrials)        │
│   XLB  ████              +0.2  (Materials)          │
│   XLP  ███               +0.0  (Staples)            │
│   XLY  ██                −0.3  (Discretionary)      │
│   XLC  ██                −0.5  (Communication)      │
│   XLRE █                 −0.8  (Real Estate)        │
│   XLU  █                 −1.1  (Utilities)          │
│   XLE                    −1.6  (Energy, Weak)       │
└─────────────────────────────────────────────────────┘
      │
      │  Softmax: high score → large weight, low score → small weight
      │  All weights sum to 100%, no market timing needed
      ▼
┌─────────────────────────────────────────────────────┐
│                 Portfolio Weights                    │
│                                                     │
│   XLK  ████████████████  18.2%                      │
│   XLV  █████████████     14.5%                      │
│   XLF  ██████████        11.0%                      │
│   XLI  ████████           8.6%                      │
│   XLB  ███████            7.4%                      │
│   XLP  ██████             6.8%  ← lower score =     │
│   XLY  ██████             6.4%    smaller weight,   │
│   XLC  █████              6.0%    but still held    │
│   XLRE █████              5.5%                      │
│   XLU  ████               4.8%                      │
│   XLE  ████               4.4%                      │
│        ─────────────────────────                    │
│        Total              100% (fully invested)     │
└─────────────────────────────────────────────────────┘
      │
      │  Execute rebalancing on Thursday close
      ▼
   Hold until next Wednesday close, repeat
```

> **vs. traditional top-N strategies**: A hard cutoff treats rank 3 and rank 4 identically and forces a full rebalance whenever they swap. In the Softmax strategy, a small rank movement causes only a small weight shift — naturally reducing turnover at rank boundaries.

### 4.3 Equal-Weight Baseline: The Mandatory Floor

Before evaluating any signal, we establish the **equal-weight portfolio** as the benchmark floor: hold all 11 ETFs at 1/11 each, every week, with no signal. This represents market average performance under zero information.

**Any signal that cannot beat the equal-weight baseline is considered statistically uninformative.**

| Metric | Equal-Weight Baseline |
|--------|:--------------------:|
| Sharpe | **1.305** |
| Annual Return | 13.98% |
| Annual Volatility | 10.46% |
| Max Drawdown | −10.64% |
| Excess Return vs SPY | −3.08% |


### 4.4 Three-Step Optimisation Roadmap

The sole evaluation metric is **Sharpe Ratio**.

| Step | Content | Method | Status |
|------|---------|--------|--------|
| **Step 0** | Equal-weight baseline (mandatory floor) | — | ✅ Complete |
| **Step 1** | Single-signal screening: test each factor or ML signal individually | IC pre-screen + Sharpe ranking | ✅ Complete |
| **Step 2** | Multi-signal linear blend: find optimal weighting | Bayesian optimisation + walk-forward CV | 🔄 In Progress |
| **Step 3** | Neural network end-to-end learning | Gradient descent, Sharpe as training loss | ⏳ Planned |

### 4.5 Alpha Factor Screening Results (Step 1)

40 factors backtested under the unified evaluation framework:

| Factor | Sharpe | Ann. Return | Ann. Vol | Max DD | vs Equal-Wt |
|--------|:------:|:-----------:|:--------:|:------:|:-----------:|
| **Alpha#19 ★** | **1.968** | **23.33%** | 10.97% | **−7.26%** | **+0.663** |
| Alpha#24 | 1.758 | 24.60% | 13.01% | −11.32% | +0.453 |
| Alpha#23 | 1.665 | 18.78% | 10.69% | −10.66% | +0.360 |
| Alpha#31 | 1.561 | 16.57% | 10.16% | −9.30% | +0.256 |
| Equal-Weight (floor) | 1.305 | 13.98% | 10.46% | −10.64% | — |
| Alpha#101 | 1.108 | 11.73% | 10.51% | −10.18% | −0.197 |

**Best single factor: Alpha#19** (Sharpe 1.968, CAPM Alpha 11.35% vs SPY, Beta 0.613)

Alpha#19 is a **long-horizon momentum reversal signal** (250-day cumulative return direction + cross-sectional ranking) — takes contrarian positions when a sector shows extended outperformance.

> **Screening conclusion**: Of 40 factors tested, only a handful meaningfully beat the equal-weight floor. The majority are statistically indistinguishable from holding all 11 ETFs equally — confirming the necessity of systematic screening. Manual factor selection would almost certainly misjudge these results.


### 4.6 ML Signal Screening Results (Step 1)

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | vs Equal-Wt |
|--------|:------:|:-----------:|:--------:|:------:|:-----------:|
| **Signal 2 (Ensemble) ★** | **1.506** | **16.76%** | 10.68% | −10.27% | **+0.201** |
| Signal 5 (MLP) | 1.329 | 14.06% | 10.31% | −10.26% | +0.024 |
| Equal-Weight (floor) | 1.305 | 13.98% | 10.46% | −10.64% | — |
| Signal 3 (XGBoost) | 1.304 | 13.97% | 10.46% | −10.62% | −0.001 |
| Signal 4 (PCA+Ridge) | 1.304 | 13.96% | 10.44% | −10.61% | −0.001 |
| Signal 1 (LightGBM) | 1.300 | 13.92% | 10.46% | −10.64% | −0.005 |

**Best ML signal: Signal 2 (Ensemble / FRS1)**, Sharpe 1.506, CAPM Alpha 4.52% vs SPY.

**Key finding**: The three FRS3-targeting models are statistically indistinguishable from equal-weight. Predicting vol-penalised returns is far harder than directional returns (FRS1). The ensemble's rank-averaging across models suppresses single-model noise — this is the path forward for ML signals.

> **Going forward**: Ensemble approach + directional label (FRS1) should be the primary ML signal direction.


---

## V. Signal Deployment: Market-Neutral Long-Short Baseline Strategy

### 5.1 Strategy Positioning

The baseline strategy is our **actual trading execution layer**, designed as a **market-neutral long-short hedge**:

- Long the top-ranked (strongest) sector ETFs by signal
- Short the bottom-ranked (weakest) sector ETFs by signal
- Long and short positions are equal and offsetting — near-zero net exposure

This design strips out the effect of overall market direction (Beta) — P&L comes entirely from cross-sectional sector calls (Alpha).

### 5.2 Position Structure

| Direction | Count | Weight per Position | Total |
|-----------|-------|-------------------|-------|
| Long | 3 | +33.3% | +100% |
| Short | 3 | −33.3% | −100% |
| Gross Exposure | | | **200%** |
| **Net Exposure** | | | **~0%** |

### 5.3 Short Filter Mechanism

Shorting is not unconditional. For bottom-ranked ETFs, one additional condition must be met:

> **12-week cumulative return must be negative** (absolute momentum pointing down)

If a bottom-ranked ETF is still up over the past 12 weeks, the short slot is left in cash. This prevents **shorting rising sectors** — even if a sector is relatively weak versus peers, forcibly shorting an absolute uptrend carries extreme risk.

### 5.4 Rank Stickiness

To avoid excessive rebalancing from minor rank fluctuations (e.g., rank 3 vs. rank 4 swapping):

- Long holdings: retained unless rank falls outside top **5** (±2 tolerance zone)
- Short holdings: closed only if rank rises above bottom **5**
- Exception: short positions with **absolute momentum turning positive are closed immediately**, regardless of stickiness

### 5.5 3-Tier Drawdown Risk Machine

The strategy has a built-in dynamic risk control mechanism that automatically adjusts gross exposure based on portfolio drawdown:

```
           DD ≥ 10%                  DD ≥ 15%
NORMAL ─────────────► LIGHT ────────────────► HEAVY
(200% gross)         (100% gross)             (0%, full cash)
    ▲                    ▲
    │  DD < 8%            │  ≥ 2 proposed longs w/ positive
    │  for ≥ 2 weeks      │  absolute momentum, for ≥ 2 weeks
    └────────────────────┘
```

Recovery conditions are deliberately strict, requiring **consecutive weeks** of meeting the threshold — preventing premature re-entry after a brief bounce that leads to a second drawdown.

### 5.6 Baseline Strategy Backtest Results

#### Alpha Signals (40 factors fully tested)

| Factor | Sharpe | Ann. Return | Ann. Vol | Max DD | Beta vs SPY | CAPM Alpha |
|--------|:------:|:-----------:|:--------:|:------:|:-----------:|:----------:|
| **Alpha#23 ★** | **2.081** | **23.00%** | 10.21% | **−5.85%** | **0.234** | **17.33%** |
| Alpha#57 | 1.528 | 17.72% | 11.08% | −7.40% | — | — |
| Alpha#37 | 1.478 | 16.98% | 11.03% | −5.78% | — | — |
| Alpha#10 | 1.230 | 13.37% | 10.67% | −6.90% | — | — |
| Alpha#19 *(best in Softmax)* | −0.591 | −5.66% | 9.15% | −11.16% | — | — |

**Best result: L/S + Alpha#23** (Sharpe 2.081, CAPM Alpha **17.33%** vs SPY, Beta **0.234**)

Alpha#23 is a **near-peak breakout reversal signal**: when a sector's price breaks above recent highs, it anticipates short-term mean reversion and positions contrarily. Market Beta is only 0.234 — strategy returns are highly independent of overall market direction.

Note: **Alpha#19 (best in Softmax) produces negative Sharpe in the L/S framework**. This demonstrates that different signals have clear framework compatibility — the Softmax long-only framework tests absolute ranking ability, while the L/S framework demands two-way predictive accuracy (both strong and weak side).


#### ML Signals (5 models fully tested)

| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Beta vs SPY |
|--------|:------:|:-----------:|:--------:|:------:|:-----------:|
| **Signal 2 (Ensemble) ★** | **0.806** | **9.62%** | 12.32% | **−4.59%** | 0.275 |
| Signal 4 (PCA+Ridge) | −0.083 | −1.53% | 11.20% | −7.98% | — |
| Signal 5 (MLP) | −0.388 | −4.12% | 9.67% | −10.40% | — |
| Signal 3 (XGBoost) | −0.468 | −3.38% | 6.85% | −10.76% | — |
| Signal 1 (LightGBM) | −1.681 | −9.85% | 6.05% | −13.37% | — |

ML signals perform significantly worse in the L/S framework. Signal 2 is the only model with positive Sharpe (0.806); the remaining four all lose money. This indicates that current ML signals lack sufficient **short-side predictive accuracy** — identifying which sectors will underperform is harder than identifying outperformers.


---

## VI. Overall Comparison & Key Conclusions

### 6.1 Full Strategy Comparison

| Framework | Signal | Sharpe | Ann. Return | Max DD | Beta vs SPY | CAPM Alpha |
|-----------|--------|:------:|:-----------:|:------:|:-----------:|:----------:|
| **L/S Baseline** | **Alpha#23** | **2.081** | **23.00%** | **−5.85%** | **0.234** | **17.33%** |
| Softmax Long-Only | Alpha#19 | 1.968 | 23.33% | −7.26% | 0.613 | 11.35% |
| Softmax Long-Only | Signal 2 (ML) | 1.506 | 16.76% | −10.27% | 0.691 | 4.52% |
| **Equal-Weight** | **—** | **1.305** | **13.98%** | **−10.64%** | **0.674** | **2.37%** |
| L/S Baseline | Signal 2 (ML) | 0.806 | 9.62% | −4.59% | 0.275 | 5.33% |

### 6.2 Three Core Conclusions

**① L/S + Alpha#23 is the best current configuration**

Sharpe 2.08, max drawdown only −5.85%, market Beta 0.23. Returns come almost entirely from cross-sectional sector calls, not from passive market exposure. This is a textbook **pure-Alpha strategy** profile. CAPM Alpha of 17.33% vs SPY.

**② Formulaic alphas significantly outperform ML signals in the L/S framework**

Price-structure alphas capture structural price patterns and have stable discriminatory power on both long and short sides. Current ML signals lack adequate two-way predictive accuracy — further improvement is needed in Steps 2 and 3.

**③ Signal quality is framework-specific — results cannot be cross-applied**

The best Softmax signal (Alpha#19, Sharpe 1.968) flips to Sharpe −0.59 in the L/S framework. The best L/S signal (Alpha#23, Sharpe 2.08) scores only 1.665 in Softmax. **Signal screening must be conducted within the target execution framework** — cross-framework conclusions are not transferable.

---

## VII. Next Research Directions

### 7.1 Multi-Signal Combination Optimisation (Step 2)

Step 1 has demonstrated that Alpha#23 (L/S framework) and Signal 2 (long-only framework) are each effective individually. The next step is to **linearly blend multiple signals**:

$$s_{\text{combined}} = \alpha_1 \cdot g_{\text{Alpha\#23}} + \alpha_2 \cdot g_{\text{Signal 2}} + \cdots$$

Bayesian optimisation searches for optimal weight combinations, paired with **walk-forward out-of-sample validation** to prevent overfitting.

### 7.2 Neural Network End-to-End Learning (Step 3)

Feed all 82 factors as input directly into a neural network to learn optimal output weights, with the entire backtest Sharpe as the training objective. This is the highest form of signal optimisation, but requires more rigorous overfitting controls.

---

> **Research Limitation**
>
> All backtest results in this report are produced under **zero transaction fees and zero slippage** assumptions. This is intentional: to purely evaluate signal predictive power, removing transaction cost interference. In live trading, costs (especially for high-turnover strategies) will materially reduce Sharpe. Current results do not represent achievable live returns. Live feasibility requires a dedicated cost-sensitivity study.

*This report is based on backtest data from 2025-01-01 to 2026-01-31. Results are for research purposes only and do not constitute investment advice.*

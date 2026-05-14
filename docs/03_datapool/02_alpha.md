# Alpha Factor Pool

Two groups of alpha factors are available in `weekly_alpha`: **WQ101** (formulaic alphas, IDs 1–101) and **Andy** (custom derived factors, IDs 108–137). All factors output a cross-sectional score per ETF per week via `AlphaBacktestSignal(alpha_id)`.

Screening results (IC, LP/SP Sharpe) → `02_work/01_signal_opt/00_step1_screening.md`

---

# WQ101 Alphas

**Source:** Kakushadze, Z. (2015). "101 Formulaic Alphas." arXiv:1601.00991  
**Universe:** 11 SPDR Sector ETFs (XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLRE, XLY)

---

## Available Data Fields

| Field | Source column | Notes |
|:------|:-------------|:------|
| `close` | `{T} US Equity PX_LAST` | Direct |
| `open` | `{T} US Equity PX_OPEN` | Direct |
| `high` | `{T} US Equity PX_HIGH` | Direct |
| `low` | `{T} US Equity PX_LOW` | Direct |
| `volume` | `{T} US Equity PX_VOLUME` | Direct |
| `returns` | derived | `close.pct_change()` |
| `adv{d}` | derived | rolling mean of `close * volume` |
| `vwap` | **approximated** | `(open+high+low+close)/4` — intraday tick data not available |
| `cap` | **missing** | Market capitalisation not in dataset |
| `IndClass` | **not applicable** | Each ETF *is* a sector; sub-industry neutralisation is meaningless |

---

## Summary

| Category | Count | Alpha IDs |
|:---------|------:|:---------|
| **Group A — Fully implementable** | 52 | 1,2,3,4,6,7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23,24,26,28,29,30,31,33,34,35,37,38,39,40,43,44,45,46,49,51,52,53,54,55,60,68,85,88,92,95,99,101 |
| **Group B — Implementable (vwap approximated)** | 30 | 5,11,25,27,32,36,41,42,47,50,57,61,62,64,65,66,71,72,73,74,75,77,78,81,83,84,86,94,96,98 |
| **Not implementable** | 19 | 48,56,58,59,63,67,69,70,76,79,80,82,87,89,90,91,93,97,100 |
| **Total** | **101** | |

---

## Per-Alpha Assessments

### Alpha#1 ✅ Group A
**Formula:** `rank(Ts_ArgMax(SignedPower(((returns<0)?stddev(returns,20):close),2.),5)) - 0.5`  
**Required inputs:** returns, close, stddev — all available.  
**Assessment:** Fully implementable. Uses a conditional on negative returns to switch between volatility and price, then applies a signed power and finds the arg-max over 5 days. Cross-sectional rank across the 11 ETFs is well-defined.

### Alpha#2 ✅ Group A
**Formula:** `-1 * correlation(rank(delta(log(volume),2)), rank((close-open)/open), 6)`  
**Required inputs:** volume, close, open — all available.  
**Assessment:** Fully implementable. Time-series correlation (6-day window) between volume change and intraday return, both cross-sectionally ranked.

### Alpha#3 ✅ Group A
**Formula:** `-1 * correlation(rank(open), rank(volume), 10)`  
**Required inputs:** open, volume — all available.  
**Assessment:** Fully implementable. Simple negative correlation between ranked open and ranked volume over 10-day window.

### Alpha#4 ✅ Group A
**Formula:** `-1 * Ts_Rank(rank(low), 9)`  
**Required inputs:** low — available.  
**Assessment:** Fully implementable. 9-day time-series rank of the cross-sectional rank of low prices.

### Alpha#5 ✅ Group B
**Formula:** `rank(open - sum(vwap,10)/10) * (-abs(rank(close-vwap)))`  
**Required inputs:** open, close, vwap (approximated).  
**Assessment:** Implementable with vwap approximation. Measures open relative to rolling vwap average, penalised by close-vwap spread.

### Alpha#6 ✅ Group A
**Formula:** `-1 * correlation(open, volume, 10)`  
**Required inputs:** open, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#7 ✅ Group A
**Formula:** `(adv20<volume)?(-ts_rank(|delta(close,7)|,60)*sign(delta(close,7))):(-1)`  
**Required inputs:** close, volume, adv20 — all available.  
**Assessment:** Fully implementable. Volume surge detector with momentum direction filter.

### Alpha#8 ✅ Group A
**Formula:** `-1 * rank(sum(open,5)*sum(returns,5) - delay(sum(open,5)*sum(returns,5),10))`  
**Required inputs:** open, returns — all available.  
**Assessment:** Fully implementable.

### Alpha#9 ✅ Group A
**Formula:** Ternary on ts_min/ts_max of delta(close,1) over 5 days.  
**Required inputs:** close — available.  
**Assessment:** Fully implementable. Mean-reversion vs momentum switch based on 5-day price-change extremes.

### Alpha#10 ✅ Group A
**Formula:** `rank(alpha_9_logic with window=4)`  
**Required inputs:** close — available.  
**Assessment:** Fully implementable. Cross-sectional ranking of Alpha#9-style signal with 4-day window.

### Alpha#11 ✅ Group B
**Formula:** `(rank(ts_max(vwap-close,3))+rank(ts_min(vwap-close,3)))*rank(delta(volume,3))`  
**Required inputs:** close, volume, vwap (approximated).  
**Assessment:** Implementable with vwap approximation.

### Alpha#12 ✅ Group A
**Formula:** `sign(delta(volume,1)) * (-delta(close,1))`  
**Required inputs:** volume, close — all available.  
**Assessment:** Fully implementable. Classic mean-reversion sign: if volume went up and price went up, bet on reversal.

### Alpha#13 ✅ Group A
**Formula:** `-1 * rank(covariance(rank(close), rank(volume), 5))`  
**Required inputs:** close, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#14 ✅ Group A
**Formula:** `(-rank(delta(returns,3))) * correlation(open, volume, 10)`  
**Required inputs:** returns, open, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#15 ✅ Group A
**Formula:** `-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3)`  
**Required inputs:** high, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#16 ✅ Group A
**Formula:** `-1 * rank(covariance(rank(high), rank(volume), 5))`  
**Required inputs:** high, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#17 ✅ Group A
**Formula:** `(-rank(ts_rank(close,10))) * rank(delta(delta(close,1),1)) * rank(ts_rank(volume/adv20,5))`  
**Required inputs:** close, volume, adv20 — all available.  
**Assessment:** Fully implementable.

### Alpha#18 ✅ Group A
**Formula:** `-1 * rank(stddev(|close-open|,5) + (close-open) + correlation(close,open,10))`  
**Required inputs:** close, open — all available.  
**Assessment:** Fully implementable.

### Alpha#19 ✅ Group A
**Formula:** `(-sign((close-delay(close,7))+delta(close,7))) * (1+rank(1+sum(returns,250)))`  
**Required inputs:** close, returns — all available. Requires 250-day warmup.  
**Assessment:** Fully implementable. Note: 250-day window means ~250 trading days needed before signal is valid.

### Alpha#20 ✅ Group A
**Formula:** `(-rank(open-delay(high,1))) * rank(open-delay(close,1)) * rank(open-delay(low,1))`  
**Required inputs:** open, high, close, low — all available.  
**Assessment:** Fully implementable. Overnight gap signal vs prior day OHLC.

### Alpha#21 ✅ Group A
**Formula:** Conditional on 8-day vs 2-day close mean and stddev vs volume/adv20 ratio.  
**Required inputs:** close, volume, adv20 — all available.  
**Assessment:** Fully implementable.

### Alpha#22 ✅ Group A
**Formula:** `-1 * (delta(correlation(high,volume,5),5) * rank(stddev(close,20)))`  
**Required inputs:** high, volume, close — all available.  
**Assessment:** Fully implementable.

### Alpha#23 ✅ Group A
**Formula:** `(sum(high,20)/20 < high) ? (-delta(high,2)) : 0`  
**Required inputs:** high — available.  
**Assessment:** Fully implementable. High-breakout momentum reversal signal.

### Alpha#24 ✅ Group A
**Formula:** Conditional on 100-day SMA trend vs 5% threshold.  
**Required inputs:** close — available. Requires 100+ day warmup.  
**Assessment:** Fully implementable.

### Alpha#25 ✅ Group B
**Formula:** `rank((-returns * adv20 * vwap * (high-close)))`  
**Required inputs:** returns, adv20, vwap (approx), high, close.  
**Assessment:** Implementable with vwap approximation.

### Alpha#26 ✅ Group A
**Formula:** `-1 * ts_max(correlation(ts_rank(volume,5), ts_rank(high,5), 5), 3)`  
**Required inputs:** volume, high — all available.  
**Assessment:** Fully implementable.

### Alpha#27 ✅ Group B
**Formula:** `(rank(sum(corr(rank(vol),rank(vwap),6),2)/2) > 0.5) ? -1 : 1`  
**Required inputs:** volume, vwap (approx).  
**Assessment:** Implementable with vwap approximation.

### Alpha#28 ✅ Group A
**Formula:** `scale(correlation(adv20,low,5) + (high+low)/2 - close)`  
**Required inputs:** adv20, low, high, close — all available.  
**Assessment:** Fully implementable.

### Alpha#29 ✅ Group A
**Formula:** Complex nested rank/scale/log/product + ts_rank(delay(-returns,6),5).  
**Required inputs:** close, returns — all available. Requires warmup.  
**Assessment:** Fully implementable.

### Alpha#30 ✅ Group A
**Formula:** `(1-rank(sign(dc)+sign(dc1)+sign(dc2))) * sum(vol,5) / sum(vol,20)`  
**Required inputs:** close, volume — all available.  
**Assessment:** Fully implementable. Consecutive-days sign pattern, volume-adjusted.

### Alpha#31 ✅ Group A
**Formula:** `rank(rank(rank(decay_linear(-rank(rank(delta(close,10))),10)))) + rank(-delta(close,3)) + sign(scale(corr(adv20,low,12)))`  
**Required inputs:** close, adv20, low — all available.  
**Assessment:** Fully implementable.

### Alpha#32 ✅ Group B
**Formula:** `scale((sum(close,7)/7-close)) + 20*scale(corr(vwap,delay(close,5),230))`  
**Required inputs:** close, vwap (approx). 230-day correlation window.  
**Assessment:** Implementable with vwap approximation. Long warmup (230 days) required.

### Alpha#33 ✅ Group A
**Formula:** `rank(-(1 - open/close))` = `rank(open/close - 1)`  
**Required inputs:** open, close — all available.  
**Assessment:** Fully implementable.

### Alpha#34 ✅ Group A
**Formula:** `rank((1-rank(std(ret,2)/std(ret,5))) + (1-rank(delta(close,1))))`  
**Required inputs:** returns, close — all available.  
**Assessment:** Fully implementable.

### Alpha#35 ✅ Group A
**Formula:** `Ts_Rank(vol,32) * (1-Ts_Rank(close+high-low,16)) * (1-Ts_Rank(ret,32))`  
**Required inputs:** volume, close, high, low, returns — all available.  
**Assessment:** Fully implementable.

### Alpha#36 ✅ Group B
**Formula:** Linear combination of 5 terms including `rank(|corr(vwap,adv20,6)|)` and 200-day SMA.  
**Required inputs:** open, close, volume, vwap (approx), adv20, returns.  
**Assessment:** Implementable with vwap approximation.

### Alpha#37 ✅ Group A
**Formula:** `rank(corr(delay(open-close,1),close,200)) + rank(open-close)`  
**Required inputs:** open, close — all available. 200-day window.  
**Assessment:** Fully implementable. Long warmup required.

### Alpha#38 ✅ Group A
**Formula:** `(-rank(Ts_Rank(close,10))) * rank(close/open)`  
**Required inputs:** close, open — all available.  
**Assessment:** Fully implementable.

### Alpha#39 ✅ Group A
**Formula:** `(-rank(delta(close,7)*(1-rank(decay_linear(vol/adv20,9))))) * (1+rank(sum(ret,250)))`  
**Required inputs:** close, volume, adv20, returns — all available.  
**Assessment:** Fully implementable. 250-day sum requires warmup.

### Alpha#40 ✅ Group A
**Formula:** `(-rank(stddev(high,10))) * correlation(high, volume, 10)`  
**Required inputs:** high, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#41 ✅ Group B
**Formula:** `sqrt(high*low) - vwap`  
**Required inputs:** high, low, vwap (approx).  
**Assessment:** Implementable with vwap approximation. Geometric mean of high-low vs vwap spread.

### Alpha#42 ✅ Group B
**Formula:** `rank(vwap-close) / rank(vwap+close)`  
**Required inputs:** close, vwap (approx).  
**Assessment:** Implementable with vwap approximation.

### Alpha#43 ✅ Group A
**Formula:** `ts_rank(volume/adv20, 20) * ts_rank(-delta(close,7), 8)`  
**Required inputs:** volume, adv20, close — all available.  
**Assessment:** Fully implementable.

### Alpha#44 ✅ Group A
**Formula:** `-1 * correlation(high, rank(volume), 5)`  
**Required inputs:** high, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#45 ✅ Group A
**Formula:** `-1 * (rank(sum(delay(close,5),20)/20) * corr(close,vol,2) * rank(corr(sum(c,5),sum(c,20),2)))`  
**Required inputs:** close, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#46 ✅ Group A
**Formula:** Conditional on 20/10-day momentum acceleration vs thresholds 0.25 and 0.  
**Required inputs:** close — available.  
**Assessment:** Fully implementable.

### Alpha#47 ✅ Group B
**Formula:** `(rank(1/close)*vol/adv20) * (high*rank(high-close)/(sum(high,5)/5)) - rank(vwap-delay(vwap,5))`  
**Required inputs:** close, high, volume, adv20, vwap (approx).  
**Assessment:** Implementable with vwap approximation.

### Alpha#48 ❌ Not implementable
**Formula:** `indneutralize((corr(delta(close,1), delta(delay(close,1),1), 250)*delta(close,1))/close, IndClass.subindustry) / sum(...)` 
**Missing:** `IndNeutralize(subindustry)` — each ETF is itself a sector; sub-industry demeaning across this 11-instrument universe is undefined.

### Alpha#49 ✅ Group A
**Formula:** `(accel < -0.1) ? 1 : (-1*(close-delay(close,1)))`  
**Required inputs:** close — available.  
**Assessment:** Fully implementable.

### Alpha#50 ✅ Group B
**Formula:** `-1 * ts_max(rank(corr(rank(vol), rank(vwap), 5)), 5)`  
**Required inputs:** volume, vwap (approx).  
**Assessment:** Implementable with vwap approximation.

### Alpha#51 ✅ Group A
**Formula:** Same as Alpha#49 with threshold -0.05.  
**Required inputs:** close — available.  
**Assessment:** Fully implementable.

### Alpha#52 ✅ Group A
**Formula:** `(-ts_min(low,5)+delay(ts_min(low,5),5)) * rank((sum(ret,240)-sum(ret,20))/220) * ts_rank(vol,5)`  
**Required inputs:** low, returns, volume — all available.  
**Assessment:** Fully implementable.

### Alpha#53 ✅ Group A
**Formula:** `-1 * delta(((close-low)-(high-close))/(close-low), 9)`  
**Required inputs:** close, high, low — all available.  
**Assessment:** Fully implementable. Note: division guarded when close == low.

### Alpha#54 ✅ Group A
**Formula:** `(-1*(low-close)*(open^5)) / ((low-high)*(close^5))`  
**Required inputs:** open, high, low, close — all available.  
**Assessment:** Fully implementable. Division guarded when low == high.

### Alpha#55 ✅ Group A
**Formula:** `-1 * corr(rank((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12))), rank(vol), 6)`  
**Required inputs:** close, high, low, volume — all available.  
**Assessment:** Fully implementable. Stochastic oscillator normalisation, guarded for zero range.

### Alpha#56 ❌ Not implementable
**Formula:** `0-(1*(rank(sum(ret,10)/sum(sum(ret,2),3)) * rank(ret*cap)))`  
**Missing:** `cap` (market capitalisation) — not present in the dataset.

### Alpha#57 ✅ Group B
**Formula:** `0 - ((close-vwap) / decay_linear(rank(ts_argmax(close,30)), 2))`  
**Required inputs:** close, vwap (approx).  
**Assessment:** Implementable with vwap approximation.

### Alpha#58 ❌ Not implementable
**Formula:** `-1 * Ts_Rank(decay_linear(corr(IndNeutralize(vwap,sector), vol, 3.9), 7.9), 5.5)`  
**Missing:** `IndNeutralize(sector)` — not applicable to a sector-ETF universe.

### Alpha#59 ❌ Not implementable
**Formula:** `-1 * Ts_Rank(decay_linear(corr(IndNeutralize(vwap*0.728+vwap*0.272, industry), vol, 4.25), 16.2), 8.2)`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#60 ✅ Group A
**Formula:** `0 - (2*scale(rank(CLV*volume)) - scale(rank(ts_argmax(close,10))))`  
**Required inputs:** close, high, low, volume — all available.  
**Assessment:** Fully implementable. CLV = ((close-low)-(high-close))/(high-low).

### Alpha#61 ✅ Group B
**Formula:** `rank(vwap-ts_min(vwap,16)) < rank(corr(vwap,adv180,18))`  
**Required inputs:** vwap (approx), adv180.  
**Assessment:** Implementable with vwap approximation.

### Alpha#62 ✅ Group B
**Formula:** `(rank(corr(vwap,sum(adv20,22),10)) < rank(...)) * -1`  
**Required inputs:** open, high, low, vwap (approx), adv20.  
**Assessment:** Implementable with vwap approximation.

### Alpha#63 ❌ Not implementable
**Formula:** `(rank(decay_linear(delta(IndNeutralize(close,industry),2.25),8.2)) - ...) * -1`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#64 ✅ Group B
**Formula:** Correlation-based comparison using weighted open/low/vwap vs adv120.  
**Required inputs:** open, high, low, vwap (approx), adv120.  
**Assessment:** Implementable with vwap approximation.

### Alpha#65 ✅ Group B
**Formula:** `(rank(corr(o*0.008+vwap*0.992, sum(adv60,9), 6)) < rank(o-ts_min(o,14))) * -1`  
**Required inputs:** open, vwap (approx), adv60.  
**Assessment:** Implementable with vwap approximation.

### Alpha#66 ✅ Group B
**Formula:** Decay-linear delta vwap plus ts_rank of a low/vwap/open expression.  
**Required inputs:** open, high, low, vwap (approx).  
**Assessment:** Implementable with vwap approximation.

### Alpha#67 ❌ Not implementable
**Formula:** `(rank(high-ts_min(high,2))^rank(corr(IndNeutralize(vwap,sector), IndNeutralize(adv20,subindustry), 6))) * -1`  
**Missing:** `IndNeutralize(sector, subindustry)`.

### Alpha#68 ✅ Group A
**Formula:** `(Ts_Rank(corr(rank(high),rank(adv15),9),14) < rank(delta(close*0.518+low*0.482,1))) * -1`  
**Required inputs:** high, adv15, close, low — all available.  
**Assessment:** Fully implementable.

### Alpha#69 ❌ Not implementable
**Formula:** `(rank(ts_max(delta(IndNeutralize(vwap,industry),2.7),4.8))^...) * -1`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#70 ❌ Not implementable
**Formula:** `(rank(delta(vwap,1.3))^Ts_Rank(corr(IndNeutralize(close,industry),adv50,17.8),17.9)) * -1`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#71 ✅ Group B
**Formula:** `max(Ts_Rank(decay_linear(corr(Ts_Rank(c,3),Ts_Rank(adv180,12),18),4),16), Ts_Rank(decay_linear(rank((l+o-2*vwap))^2,16),4))`  
**Required inputs:** close, low, open, vwap (approx), adv180.  
**Assessment:** Implementable with vwap approximation.

### Alpha#72 ✅ Group B
**Formula:** `rank(decay_linear(corr((h+l)/2,adv40,9),10)) / rank(decay_linear(corr(Ts_Rank(vwap,4),Ts_Rank(vol,19),7),3))`  
**Required inputs:** high, low, vwap (approx), volume, adv40.  
**Assessment:** Implementable with vwap approximation.

### Alpha#73 ✅ Group B
**Formula:** `max(rank(decay_linear(delta(vwap,5),3)), Ts_Rank(decay_linear((-delta(combo,2)/combo),3),17)) * -1`  
**Required inputs:** open, low, vwap (approx).  
**Assessment:** Implementable with vwap approximation.

### Alpha#74 ✅ Group B
**Formula:** `(rank(corr(c,sum(adv30,37),15)) < rank(corr(rank(h*0.026+vwap*0.974),rank(vol),11))) * -1`  
**Required inputs:** high, close, vwap (approx), volume, adv30.  
**Assessment:** Implementable with vwap approximation.

### Alpha#75 ✅ Group B
**Formula:** `rank(corr(vwap,vol,4)) < rank(corr(rank(low),rank(adv50),12))`  
**Required inputs:** low, vwap (approx), volume, adv50.  
**Assessment:** Implementable with vwap approximation.

### Alpha#76 ❌ Not implementable
**Formula:** `max(rank(decay_linear(delta(vwap,1.2),11.8)), Ts_Rank(decay_linear(Ts_Rank(corr(IndNeutralize(low,sector),adv81,8),19),17),19)) * -1`  
**Missing:** `IndNeutralize(sector)`.

### Alpha#77 ✅ Group B
**Formula:** `min(rank(decay_linear((h+l)/2+h-(vwap+h),20)), rank(decay_linear(corr((h+l)/2,adv40,3),6)))`  
**Required inputs:** high, low, vwap (approx), adv40.  
**Assessment:** Implementable with vwap approximation.

### Alpha#78 ✅ Group B
**Formula:** `rank(corr(sum(l*0.352+vwap*0.648,20),sum(adv40,20),7))^rank(corr(rank(vwap),rank(vol),6))`  
**Required inputs:** low, vwap (approx), volume, adv40.  
**Assessment:** Implementable with vwap approximation.

### Alpha#79 ❌ Not implementable
**Formula:** `rank(delta(IndNeutralize(close*0.607+open*0.393,sector),1)) < rank(corr(Ts_Rank(vwap,4),Ts_Rank(adv150,9),15))`  
**Missing:** `IndNeutralize(sector)`.

### Alpha#80 ❌ Not implementable
**Formula:** `(rank(Sign(delta(IndNeutralize(open*0.868+high*0.132,industry),4)))^...) * -1`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#81 ✅ Group B
**Formula:** `(rank(log(product(rank(rank(corr(vwap,sum(adv10,50),8))^4),15))) < rank(corr(rank(vwap),rank(vol),5))) * -1`  
**Required inputs:** vwap (approx), volume, adv10.  
**Assessment:** Implementable with vwap approximation.

### Alpha#82 ❌ Not implementable
**Formula:** `min(rank(decay_linear(delta(open,1.5),14.9)), Ts_Rank(decay_linear(corr(IndNeutralize(vol,sector),(open*0.634+open*0.366),17.5),6.9),13.4)) * -1`  
**Missing:** `IndNeutralize(sector)`.

### Alpha#83 ✅ Group B
**Formula:** `(rank(delay((h-l)/(sum(c,5)/5),2))*rank(rank(vol))) / ((h-l)/(sum(c,5)/5)/(vwap-c))`  
**Required inputs:** high, low, close, volume, vwap (approx).  
**Assessment:** Implementable with vwap approximation.

### Alpha#84 ✅ Group B
**Formula:** `SignedPower(Ts_Rank(vwap-ts_max(vwap,15),21), delta(close,5))`  
**Required inputs:** vwap (approx), close.  
**Assessment:** Implementable with vwap approximation.

### Alpha#85 ✅ Group A
**Formula:** `rank(corr(h*0.877+c*0.123,adv30,10))^rank(corr(Ts_Rank((h+l)/2,4),Ts_Rank(vol,10),7))`  
**Required inputs:** high, close, low, volume, adv30 — all available.  
**Assessment:** Fully implementable.

### Alpha#86 ✅ Group B
**Formula:** `(Ts_Rank(corr(c,sum(adv20,15),6),20) < rank((o+c)-(vwap+o))) * -1`  
**Required inputs:** open, close, vwap (approx), adv20.  
**Assessment:** Implementable with vwap approximation.

### Alpha#87 ❌ Not implementable
**Formula:** `max(rank(decay_linear(delta(c*0.37+vwap*0.63,1.9),2.7)), Ts_Rank(decay_linear(|corr(IndNeutralize(adv81,industry),c,13.4)|,4.9),14.5)) * -1`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#88 ✅ Group A
**Formula:** `min(rank(decay_linear((rank(o)+rank(l))-(rank(h)+rank(c)),8)), Ts_Rank(decay_linear(corr(Ts_Rank(c,8),Ts_Rank(adv60,21),8),7),3))`  
**Required inputs:** open, high, low, close, adv60 — all available.  
**Assessment:** Fully implementable.

### Alpha#89 ❌ Not implementable
**Formula:** `Ts_Rank(decay_linear(corr(l*0.967+l*0.033,adv10,7),5.5),3.8) - Ts_Rank(decay_linear(delta(IndNeutralize(vwap,industry),3.5),10.1),15.3)`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#90 ❌ Not implementable
**Formula:** `(rank(close-ts_max(close,4.7))^Ts_Rank(corr(IndNeutralize(adv40,subindustry),low,5.4),3.2)) * -1`  
**Missing:** `IndNeutralize(subindustry)`.

### Alpha#91 ❌ Not implementable
**Formula:** `(Ts_Rank(decay_linear(decay_linear(corr(IndNeutralize(close,industry),vol,9.7),16.4),3.8),4.9) - rank(decay_linear(corr(vwap,adv30,4.0),2.7))) * -1`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#92 ✅ Group A
**Formula:** `min(Ts_Rank(decay_linear(((h+l)/2+c)<(l+o),15),19), Ts_Rank(decay_linear(corr(rank(l),rank(adv30),8),7),7))`  
**Required inputs:** high, low, close, open, adv30 — all available.  
**Assessment:** Fully implementable.

### Alpha#93 ❌ Not implementable
**Formula:** `Ts_Rank(decay_linear(corr(IndNeutralize(vwap,industry),adv81,17.4),19.8),7.5) / rank(decay_linear(delta(c*0.524+vwap*0.476,2.8),16.3))`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#94 ✅ Group B
**Formula:** `(rank(vwap-ts_min(vwap,12))^Ts_Rank(corr(Ts_Rank(vwap,20),Ts_Rank(adv60,4),18),3)) * -1`  
**Required inputs:** vwap (approx), adv60.  
**Assessment:** Implementable with vwap approximation.

### Alpha#95 ✅ Group A
**Formula:** `rank(open-ts_min(open,12)) < Ts_Rank((rank(corr(sum((h+l)/2,19),sum(adv40,19),13))^5),12)`  
**Required inputs:** open, high, low, adv40 — all available.  
**Assessment:** Fully implementable.

### Alpha#96 ✅ Group B
**Formula:** `max(Ts_Rank(decay_linear(corr(rank(vwap),rank(vol),4),4),8), Ts_Rank(decay_linear(Ts_ArgMax(corr(Ts_Rank(c,7),Ts_Rank(adv60,4),4),13),14),13)) * -1`  
**Required inputs:** close, vwap (approx), volume, adv60.  
**Assessment:** Implementable with vwap approximation.

### Alpha#97 ❌ Not implementable
**Formula:** `(rank(decay_linear(delta(IndNeutralize(l*0.721+vwap*0.279,industry),3.4),20.5)) - Ts_Rank(decay_linear(Ts_Rank(corr(Ts_Rank(low,7.9),Ts_Rank(adv60,17.3),5.0),18.6),15.7),6.7)) * -1`  
**Missing:** `IndNeutralize(industry)`.

### Alpha#98 ✅ Group B
**Formula:** `rank(decay_linear(corr(vwap,sum(adv5,26),5),7)) - rank(decay_linear(Ts_Rank(Ts_ArgMin(corr(rank(o),rank(adv15),21),9),7),8))`  
**Required inputs:** vwap (approx), open, adv5, adv15.  
**Assessment:** Implementable with vwap approximation.

### Alpha#99 ✅ Group A
**Formula:** `(rank(corr(sum((h+l)/2,20),sum(adv60,20),9)) < rank(corr(low,vol,6))) * -1`  
**Required inputs:** high, low, volume, adv60 — all available.  
**Assessment:** Fully implementable.

### Alpha#100 ❌ Not implementable
**Formula:** `0-(1*(1.5*scale(indneutralize(indneutralize(rank(CLV*vol),subindustry),subindustry)) - scale(indneutralize(corr(c,rank(adv20),5)-rank(ts_argmin(c,30)),subindustry))) * vol/adv20)`  
**Missing:** `IndNeutralize(subindustry)` applied twice.

### Alpha#101 ✅ Group A
**Formula:** `(close - open) / ((high - low) + 0.001)`  
**Required inputs:** open, high, low, close — all available.  
**Assessment:** Fully implementable. Simple intraday return normalised by daily range. The `+0.001` guard prevents division by zero on doji days.

## Not-Implemented Alphas (19)

| Alpha | Reason |
|------:|:-------|
| 48 | Requires `IndNeutralize(subindustry)` — not meaningful for sector-ETF universe |
| 56 | Requires market cap (`cap`) — not available in dataset |
| 58 | Requires `IndNeutralize(sector)` + exact vwap |
| 59 | Requires `IndNeutralize(industry)` + exact vwap |
| 63 | Requires `IndNeutralize(industry)` + exact vwap |
| 67 | Requires `IndNeutralize(sector, subindustry)` + exact vwap |
| 69 | Requires `IndNeutralize(industry)` + exact vwap |
| 70 | Requires `IndNeutralize(industry)` + exact vwap |
| 76 | Requires `IndNeutralize(sector)` + exact vwap |
| 79 | Requires `IndNeutralize(sector)` + exact vwap |
| 80 | Requires `IndNeutralize(industry)` |
| 82 | Requires `IndNeutralize(sector)` |
| 87 | Requires `IndNeutralize(industry)` + exact adv81/vwap |
| 89 | Requires `IndNeutralize(industry)` + exact vwap |
| 90 | Requires `IndNeutralize(subindustry)` |
| 91 | Requires `IndNeutralize(industry)` + exact vwap |
| 93 | Requires `IndNeutralize(industry)` + exact vwap |
| 97 | Requires `IndNeutralize(industry)` + exact vwap |
| 100 | Requires `IndNeutralize(subindustry)` twice |

---

# Andy Alpha Factors (Group `andy`)

**IDs:** 108–137 (30 factors)  
**Source:** `src/QuantLab/alpha/alpha_metrics.py` · `group="andy"`  
**Data:** Weekly bars. Close required for all families; volume required for liquidity families (119–124); SPY index (`p["index"]`) required for relative-strength and correlation families (131–137).

---

## Factor Families

| Family | IDs | Formula sketch | Inputs |
|--------|-----|----------------|--------|
| Momentum | 108–112 | `close.pct_change(n)` for n = 1, 4, 12, 26, 52 weeks | close |
| Risk-adj. momentum | 113–115 | `close.pct_change(n) / rolling_std(ret, n)` for n = 4, 12, 26 w | close |
| Realised volatility (negated) | 116–118 | `−rolling_std(ret, n)` for n = 12, 26, 52 w | close |
| Log dollar volume | 119–121 | `rolling_mean(log1p(close × volume), n)` for n = 4, 12, 26 w | close, volume |
| Amihud illiquidity (negated) | 122–124 | `−rolling_mean(|ret| / dollar_vol, n)` for n = 4, 12, 26 w | close, volume |
| Distance from rolling high | 125–127 | `close / rolling_max(close, n) − 1` for n = 12, 26, 52 w | close |
| Distance from moving average | 128–130 | `close / rolling_mean(close, n) − 1` for n = 4, 12, 52 w | close |
| Relative strength vs SPY | 131–134 | `ETF_ret(n) − SPY_ret(n)` for n = 1, 4, 12, 26 w | close, index |
| Negated corr with SPY | 135–137 | `−|rolling_corr(ETF_ret, SPY_ret, n)|` for n = 12, 26, 52 w | close, index |

**SPY fallback:** factors 131–134 fall back to raw ETF return if SPY is absent; factors 135–137 return NaN.

**`alpha_110` special role:** 12-week momentum (ID 110) is hard-wired as the short-entry filter inside `BaselineRisk`. It does **not** participate in ranking signals — access only via `terminal.alphas(alpha_ids=(110,))`.

---

## Per-Factor Reference

| ID | Name (desc) | Family | Window |
|----|-------------|--------|--------|
| 108 | ext_mom_r1w | Momentum | 1 w |
| 109 | ext_mom_r4w | Momentum | 4 w |
| 110 | ext_mom_r12w | Momentum | 12 w |
| 111 | ext_mom_r26w | Momentum | 26 w |
| 112 | ext_mom_r52w | Momentum | 52 w |
| 113 | ext_rmom_r4w | Risk-adj. momentum | 4 w |
| 114 | ext_rmom_r12w | Risk-adj. momentum | 12 w |
| 115 | ext_rmom_r26w | Risk-adj. momentum | 26 w |
| 116 | ext_vol_neg_12w | Realised vol (neg) | 12 w |
| 117 | ext_vol_neg_26w | Realised vol (neg) | 26 w |
| 118 | ext_vol_neg_52w | Realised vol (neg) | 52 w |
| 119 | ext_dvol_log4w | Log dollar volume | 4 w |
| 120 | ext_dvol_log12w | Log dollar volume | 12 w |
| 121 | ext_dvol_log26w | Log dollar volume | 26 w |
| 122 | ext_amh_neg_4w | Amihud illiquidity (neg) | 4 w |
| 123 | ext_amh_neg_12w | Amihud illiquidity (neg) | 12 w |
| 124 | ext_amh_neg_26w | Amihud illiquidity (neg) | 26 w |
| 125 | ext_dd_12w | Distance from rolling high | 12 w |
| 126 | ext_dd_26w | Distance from rolling high | 26 w |
| 127 | ext_dd_52w | Distance from rolling high | 52 w |
| 128 | ext_ma_4w | Distance from MA | 4 w |
| 129 | ext_ma_12w | Distance from MA | 12 w |
| 130 | ext_ma_52w | Distance from MA | 52 w |
| 131 | ext_rs_spy_r1w | Relative strength vs SPY | 1 w |
| 132 | ext_rs_spy_r4w | Relative strength vs SPY | 4 w |
| 133 | ext_rs_spy_r12w | Relative strength vs SPY | 12 w |
| 134 | ext_rs_spy_r26w | Relative strength vs SPY | 26 w |
| 135 | ext_corrspy_neg_12w | Negated corr with SPY | 12 w |
| 136 | ext_corrspy_neg_26w | Negated corr with SPY | 26 w |
| 137 | ext_corrspy_neg_52w | Negated corr with SPY | 52 w |

**LP/SP screening results** → `02_work/01_signal_opt/00_step1_screening.md`
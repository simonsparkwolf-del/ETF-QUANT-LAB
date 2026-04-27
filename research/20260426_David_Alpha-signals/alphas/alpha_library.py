"""
alpha_library.py — implementations of all implementable alphas from
Kakushadze (2015) "101 Formulaic Alphas".

Implementability categories
----------------------------
GROUP_A (52 alphas): fully implementable — uses only {open, high, low, close,
    volume, returns, adv{d}}.  All data are directly available in the repo.

GROUP_B (30 alphas): implementable with vwap approximation.  True intraday
    VWAP is not available; we substitute:
        vwap ≈ (open + high + low + close) / 4
    Results are directionally valid but may differ in magnitude.

NOT_IMPLEMENTED (19 alphas): require either industry-neutralisation
    (IndNeutralize) — meaningless for a single-instrument-per-sector universe —
    or market cap, neither of which is available.
    Alphas: 48, 56, 58, 59, 63, 67, 69, 70, 76, 79, 80, 82, 87, 89, 90,
            91, 93, 97, 100.

Universe note
-------------
Cross-sectional operations (rank, scale) act across the 11 SPDR sector ETFs
on each date.  With only 11 instruments the rank granularity is coarse;
results are meaningful for relative-value signals within this small universe.

Each alpha function
-------------------
    alpha_N(panel: dict) -> pd.DataFrame  shape (dates, 11 tickers)

The `panel` dict is produced by data_loader.load_panel().
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from alphas.operators import (
    abs_val, adv, correlation, covariance, decay_linear,
    delay, delta, df_max, df_min, log, product,
    rank, rolling_sum, scale, sign, signedpower,
    stddev, ts_argmax, ts_argmin, ts_max, ts_min, ts_rank,
)


# ── shorthand to make formulas readable ──────────────────────────────────────

def _tern(cond: pd.DataFrame, true_val, false_val) -> pd.DataFrame:
    """Vectorised ternary: cond ? true_val : false_val."""
    c = cond.astype(float)
    return c * true_val + (1 - c) * false_val


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP A — fully implementable (no vwap, no cap, no IndNeutralize)
# ═════════════════════════════════════════════════════════════════════════════

def alpha_1(p: dict) -> pd.DataFrame:
    """rank(Ts_ArgMax(SignedPower(((returns<0)?stddev(returns,20):close),2.),5))-0.5"""
    c, r = p["close"], p["returns"]
    inner = _tern(r < 0, stddev(r, 20), c)
    return rank(ts_argmax(signedpower(inner, 2.0), 5)) - 0.5


def alpha_2(p: dict) -> pd.DataFrame:
    """-1 * correlation(rank(delta(log(volume),2)), rank((close-open)/open), 6)"""
    v, c, o = p["volume"], p["close"], p["open"]
    return -1 * correlation(rank(delta(log(v), 2)), rank((c - o) / o), 6)


def alpha_3(p: dict) -> pd.DataFrame:
    """-1 * correlation(rank(open), rank(volume), 10)"""
    return -1 * correlation(rank(p["open"]), rank(p["volume"]), 10)


def alpha_4(p: dict) -> pd.DataFrame:
    """-1 * Ts_Rank(rank(low), 9)"""
    return -1 * ts_rank(rank(p["low"]), 9)


def alpha_6(p: dict) -> pd.DataFrame:
    """-1 * correlation(open, volume, 10)"""
    return -1 * correlation(p["open"], p["volume"], 10)


def alpha_7(p: dict) -> pd.DataFrame:
    """(adv20<volume)?(-ts_rank(abs(delta(close,7)),60)*sign(delta(close,7))):(-1)"""
    c, v = p["close"], p["volume"]
    dv = p["dv"]
    adv20 = adv(dv, 20)
    dc7 = delta(c, 7)
    true_val = -1 * ts_rank(abs_val(dc7), 60) * sign(dc7)
    return _tern(adv20 < v, true_val, pd.DataFrame(-1.0, index=c.index, columns=c.columns))


def alpha_8(p: dict) -> pd.DataFrame:
    """-1 * rank((sum(open,5)*sum(returns,5)) - delay((sum(open,5)*sum(returns,5)),10))"""
    o, r = p["open"], p["returns"]
    s = rolling_sum(o, 5) * rolling_sum(r, 5)
    return -1 * rank(s - delay(s, 10))


def alpha_9(p: dict) -> pd.DataFrame:
    """(0<ts_min(delta(close,1),5))?delta(close,1):((ts_max(delta(close,1),5)<0)?delta(close,1):(-delta(close,1)))"""
    dc = delta(p["close"], 1)
    cond1 = pd.DataFrame(0.0, index=dc.index, columns=dc.columns) < ts_min(dc, 5)
    cond2 = ts_max(dc, 5) < pd.DataFrame(0.0, index=dc.index, columns=dc.columns)
    inner = _tern(cond2, dc, -dc)
    return _tern(cond1, dc, inner)


def alpha_10(p: dict) -> pd.DataFrame:
    """rank(alpha_9 logic with window 4)"""
    dc = delta(p["close"], 1)
    z = pd.DataFrame(0.0, index=dc.index, columns=dc.columns)
    cond1 = z < ts_min(dc, 4)
    cond2 = ts_max(dc, 4) < z
    inner = _tern(cond2, dc, -dc)
    return rank(_tern(cond1, dc, inner))


def alpha_12(p: dict) -> pd.DataFrame:
    """sign(delta(volume,1)) * (-1 * delta(close,1))"""
    return sign(delta(p["volume"], 1)) * (-1 * delta(p["close"], 1))


def alpha_13(p: dict) -> pd.DataFrame:
    """-1 * rank(covariance(rank(close), rank(volume), 5))"""
    return -1 * rank(covariance(rank(p["close"]), rank(p["volume"]), 5))


def alpha_14(p: dict) -> pd.DataFrame:
    """(-1 * rank(delta(returns,3))) * correlation(open, volume, 10)"""
    return (-1 * rank(delta(p["returns"], 3))) * correlation(p["open"], p["volume"], 10)


def alpha_15(p: dict) -> pd.DataFrame:
    """-1 * sum(rank(correlation(rank(high), rank(volume), 3)), 3)"""
    return -1 * rolling_sum(rank(correlation(rank(p["high"]), rank(p["volume"]), 3)), 3)


def alpha_16(p: dict) -> pd.DataFrame:
    """-1 * rank(covariance(rank(high), rank(volume), 5))"""
    return -1 * rank(covariance(rank(p["high"]), rank(p["volume"]), 5))


def alpha_17(p: dict) -> pd.DataFrame:
    """((-rank(ts_rank(close,10))) * rank(delta(delta(close,1),1))) * rank(ts_rank(volume/adv20,5))"""
    c, v, dv = p["close"], p["volume"], p["dv"]
    adv20 = adv(dv, 20)
    return (
        (-1 * rank(ts_rank(c, 10)))
        * rank(delta(delta(c, 1), 1))
        * rank(ts_rank(v / adv20, 5))
    )


def alpha_18(p: dict) -> pd.DataFrame:
    """-1*rank(stddev(|close-open|,5)+(close-open)+correlation(close,open,10))"""
    c, o = p["close"], p["open"]
    return -1 * rank(stddev(abs_val(c - o), 5) + (c - o) + correlation(c, o, 10))


def alpha_19(p: dict) -> pd.DataFrame:
    """(-sign((close-delay(close,7))+delta(close,7))) * (1+rank(1+sum(returns,250)))"""
    c, r = p["close"], p["returns"]
    return (-1 * sign((c - delay(c, 7)) + delta(c, 7))) * (1 + rank(1 + rolling_sum(r, 250)))


def alpha_20(p: dict) -> pd.DataFrame:
    """((-rank(open-delay(high,1)))*rank(open-delay(close,1)))*rank(open-delay(low,1))"""
    o, h, c, l = p["open"], p["high"], p["close"], p["low"]
    return (
        (-1 * rank(o - delay(h, 1)))
        * rank(o - delay(c, 1))
        * rank(o - delay(l, 1))
    )


def alpha_21(p: dict) -> pd.DataFrame:
    """Complex conditional on 8-day vs 2-day close mean, then volume/adv20 check."""
    c, v, dv = p["close"], p["volume"], p["dv"]
    adv20 = adv(dv, 20)
    ma8 = rolling_sum(c, 8) / 8
    ma2 = rolling_sum(c, 2) / 2
    std8 = stddev(c, 8)
    vol_ratio = v / adv20
    ones = pd.DataFrame(1.0, index=c.index, columns=c.columns)
    cond1 = (ma8 + std8) < ma2
    cond2 = ma2 < (ma8 - std8)
    cond3 = (ones <= vol_ratio)
    inner2 = _tern(cond3, ones, -ones)
    inner1 = _tern(cond2, ones, inner2)
    return _tern(cond1, -ones, inner1)


def alpha_22(p: dict) -> pd.DataFrame:
    """-1 * (delta(correlation(high,volume,5),5) * rank(stddev(close,20)))"""
    return -1 * (delta(correlation(p["high"], p["volume"], 5), 5) * rank(stddev(p["close"], 20)))


def alpha_23(p: dict) -> pd.DataFrame:
    """((sum(high,20)/20)<high) ? (-delta(high,2)) : 0"""
    h = p["high"]
    cond = (rolling_sum(h, 20) / 20) < h
    return _tern(cond, -delta(h, 2), pd.DataFrame(0.0, index=h.index, columns=h.columns))


def alpha_24(p: dict) -> pd.DataFrame:
    """Conditional on 100-day trend vs 5% threshold."""
    c = p["close"]
    ma100 = rolling_sum(c, 100) / 100
    trend = delta(ma100, 100) / delay(c, 100)
    threshold = pd.DataFrame(0.05, index=c.index, columns=c.columns)
    cond = trend <= threshold
    return _tern(cond, -1 * (c - ts_min(c, 100)), -delta(c, 3))


def alpha_26(p: dict) -> pd.DataFrame:
    """-1 * ts_max(correlation(ts_rank(volume,5), ts_rank(high,5), 5), 3)"""
    return -1 * ts_max(
        correlation(ts_rank(p["volume"], 5), ts_rank(p["high"], 5), 5), 3
    )


def alpha_28(p: dict) -> pd.DataFrame:
    """scale(correlation(adv20,low,5) + (high+low)/2 - close)"""
    c, h, l, dv = p["close"], p["high"], p["low"], p["dv"]
    adv20 = adv(dv, 20)
    return scale(correlation(adv20, l, 5) + (h + l) / 2 - c)


def alpha_29(p: dict) -> pd.DataFrame:
    """min(product(rank(rank(scale(log(sum(ts_min(rank(rank(-rank(delta(close-1,5)))),2),1))))),1),5)
       + ts_rank(delay(-returns,6),5)"""
    c, r = p["close"], p["returns"]
    inner = -1 * rank(delta(c - 1, 5))
    layer = rank(rank(inner))
    rolled = rolling_sum(ts_min(layer, 2), 1)
    part1 = df_min(
        product(rank(rank(scale(log(rolled)))), 1),
        pd.DataFrame(5.0, index=c.index, columns=c.columns),
    )
    part2 = ts_rank(delay(-r, 6), 5)
    return part1 + part2


def alpha_30(p: dict) -> pd.DataFrame:
    """(1-rank(sign(dc)+sign(dc1)+sign(dc2))) * sum(vol,5) / sum(vol,20)"""
    c, v = p["close"], p["volume"]
    dc  = sign(c - delay(c, 1))
    dc1 = sign(delay(c, 1) - delay(c, 2))
    dc2 = sign(delay(c, 2) - delay(c, 3))
    return (1.0 - rank(dc + dc1 + dc2)) * rolling_sum(v, 5) / rolling_sum(v, 20)


def alpha_31(p: dict) -> pd.DataFrame:
    """rank(rank(rank(decay_linear(-rank(rank(delta(close,10))),10))))
       + rank(-delta(close,3)) + sign(scale(correlation(adv20,low,12)))"""
    c, l, dv = p["close"], p["low"], p["dv"]
    adv20 = adv(dv, 20)
    part1 = rank(rank(rank(decay_linear(-1 * rank(rank(delta(c, 10))), 10))))
    part2 = rank(-delta(c, 3))
    part3 = sign(scale(correlation(adv20, l, 12)))
    return part1 + part2 + part3


def alpha_33(p: dict) -> pd.DataFrame:
    """rank(-(1 - open/close))  i.e. rank(open/close - 1)"""
    return rank(-1 * (1 - p["open"] / p["close"]))


def alpha_34(p: dict) -> pd.DataFrame:
    """rank((1-rank(std(returns,2)/std(returns,5))) + (1-rank(delta(close,1))))"""
    r, c = p["returns"], p["close"]
    return rank(
        (1 - rank(stddev(r, 2) / stddev(r, 5)))
        + (1 - rank(delta(c, 1)))
    )


def alpha_35(p: dict) -> pd.DataFrame:
    """Ts_Rank(volume,32)*(1-Ts_Rank((close+high-low),16))*(1-Ts_Rank(returns,32))"""
    c, h, l, v, r = p["close"], p["high"], p["low"], p["volume"], p["returns"]
    return (
        ts_rank(v, 32)
        * (1 - ts_rank(c + h - l, 16))
        * (1 - ts_rank(r, 32))
    )


def alpha_37(p: dict) -> pd.DataFrame:
    """rank(correlation(delay(open-close,1), close, 200)) + rank(open-close)"""
    o, c = p["open"], p["close"]
    return rank(correlation(delay(o - c, 1), c, 200)) + rank(o - c)


def alpha_38(p: dict) -> pd.DataFrame:
    """(-rank(Ts_Rank(close,10))) * rank(close/open)"""
    c, o = p["close"], p["open"]
    return (-1 * rank(ts_rank(c, 10))) * rank(c / o)


def alpha_39(p: dict) -> pd.DataFrame:
    """(-rank(delta(close,7)*(1-rank(decay_linear(volume/adv20,9))))) * (1+rank(sum(returns,250)))"""
    c, v, r, dv = p["close"], p["volume"], p["returns"], p["dv"]
    adv20 = adv(dv, 20)
    return (
        (-1 * rank(delta(c, 7) * (1 - rank(decay_linear(v / adv20, 9)))))
        * (1 + rank(rolling_sum(r, 250)))
    )


def alpha_40(p: dict) -> pd.DataFrame:
    """(-rank(stddev(high,10))) * correlation(high, volume, 10)"""
    h, v = p["high"], p["volume"]
    return (-1 * rank(stddev(h, 10))) * correlation(h, v, 10)


def alpha_43(p: dict) -> pd.DataFrame:
    """ts_rank(volume/adv20, 20) * ts_rank(-delta(close,7), 8)"""
    c, v, dv = p["close"], p["volume"], p["dv"]
    adv20 = adv(dv, 20)
    return ts_rank(v / adv20, 20) * ts_rank(-delta(c, 7), 8)


def alpha_44(p: dict) -> pd.DataFrame:
    """-1 * correlation(high, rank(volume), 5)"""
    return -1 * correlation(p["high"], rank(p["volume"]), 5)


def alpha_45(p: dict) -> pd.DataFrame:
    """-1 * (rank(sum(delay(close,5),20)/20) * corr(close,vol,2) * rank(corr(sum(c,5),sum(c,20),2)))"""
    c, v = p["close"], p["volume"]
    return -1 * (
        rank(rolling_sum(delay(c, 5), 20) / 20)
        * correlation(c, v, 2)
        * rank(correlation(rolling_sum(c, 5), rolling_sum(c, 20), 2))
    )


def alpha_46(p: dict) -> pd.DataFrame:
    """Conditional on momentum acceleration vs 0.25 and 0 thresholds."""
    c = p["close"]
    accel = ((delay(c, 20) - delay(c, 10)) / 10) - ((delay(c, 10) - c) / 10)
    z = pd.DataFrame(0.0, index=c.index, columns=c.columns)
    cond1 = accel > 0.25
    cond2 = accel < z
    inner = _tern(cond2, pd.DataFrame(1.0, index=c.index, columns=c.columns),
                  -1 * (c - delay(c, 1)))
    return _tern(cond1, pd.DataFrame(-1.0, index=c.index, columns=c.columns), inner)


def alpha_49(p: dict) -> pd.DataFrame:
    """((accel < -0.1) ? 1 : (-1*(close-delay(close,1))))"""
    c = p["close"]
    accel = ((delay(c, 20) - delay(c, 10)) / 10) - ((delay(c, 10) - c) / 10)
    cond = accel < -0.1
    return _tern(cond,
                 pd.DataFrame(1.0, index=c.index, columns=c.columns),
                 -1 * (c - delay(c, 1)))


def alpha_51(p: dict) -> pd.DataFrame:
    """Same as 49 but threshold -0.05."""
    c = p["close"]
    accel = ((delay(c, 20) - delay(c, 10)) / 10) - ((delay(c, 10) - c) / 10)
    cond = accel < -0.05
    return _tern(cond,
                 pd.DataFrame(1.0, index=c.index, columns=c.columns),
                 -1 * (c - delay(c, 1)))


def alpha_52(p: dict) -> pd.DataFrame:
    """((-ts_min(low,5)+delay(ts_min(low,5),5)) * rank((sum(ret,240)-sum(ret,20))/220)) * ts_rank(vol,5)"""
    l, r, v = p["low"], p["returns"], p["volume"]
    tmin5 = ts_min(l, 5)
    return (
        (-tmin5 + delay(tmin5, 5))
        * rank((rolling_sum(r, 240) - rolling_sum(r, 20)) / 220)
        * ts_rank(v, 5)
    )


def alpha_53(p: dict) -> pd.DataFrame:
    """-1 * delta(((close-low)-(high-close))/(close-low), 9)"""
    c, h, l = p["close"], p["high"], p["low"]
    denom = (c - l).replace(0, np.nan)
    inner = ((c - l) - (h - c)) / denom
    return -1 * delta(inner, 9)


def alpha_54(p: dict) -> pd.DataFrame:
    """(-1*(low-close)*(open^5)) / ((low-high)*(close^5))"""
    o, h, l, c = p["open"], p["high"], p["low"], p["close"]
    denom = ((l - h) * (c ** 5)).replace(0, np.nan)
    return (-1 * (l - c) * (o ** 5)) / denom


def alpha_55(p: dict) -> pd.DataFrame:
    """-1*correlation(rank((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12))), rank(volume), 6)"""
    c, h, l, v = p["close"], p["high"], p["low"], p["volume"]
    rng = (ts_max(h, 12) - ts_min(l, 12)).replace(0, np.nan)
    x = rank((c - ts_min(l, 12)) / rng)
    return -1 * correlation(x, rank(v), 6)


def alpha_60(p: dict) -> pd.DataFrame:
    """0-(2*scale(rank(((close-low-high+close)/(high-low))*volume))-scale(rank(ts_argmax(close,10))))"""
    c, h, l, v = p["close"], p["high"], p["low"], p["volume"]
    rng = (h - l).replace(0, np.nan)
    clv = ((c - l) - (h - c)) / rng * v
    return 0 - (2 * scale(rank(clv)) - scale(rank(ts_argmax(c, 10))))


def alpha_68(p: dict) -> pd.DataFrame:
    """(Ts_Rank(corr(rank(high),rank(adv15),8.91),13.93) < rank(delta(close*0.518+low*0.482,1.06))) * -1"""
    h, c, l, dv = p["high"], p["close"], p["low"], p["dv"]
    adv15 = adv(dv, 15)
    lhs = ts_rank(correlation(rank(h), rank(adv15), 9), 14)
    rhs = rank(delta(c * 0.518371 + l * (1 - 0.518371), 1))
    return (lhs < rhs).astype(float) * -1


def alpha_85(p: dict) -> pd.DataFrame:
    """rank(corr(high*0.877+close*0.123,adv30,9.6))^rank(corr(Ts_Rank((h+l)/2,3.7),Ts_Rank(vol,10.2),7.1))"""
    h, c, l, v, dv = p["high"], p["close"], p["low"], p["volume"], p["dv"]
    adv30 = adv(dv, 30)
    base = rank(correlation(h * 0.876703 + c * (1 - 0.876703), adv30, 10))
    exp_ = rank(correlation(ts_rank((h + l) / 2, 4), ts_rank(v, 10), 7))
    return base ** exp_


def alpha_88(p: dict) -> pd.DataFrame:
    """min(rank(decay_linear((rank(o)+rank(l))-(rank(h)+rank(c)),8)),Ts_Rank(decay_linear(corr(Ts_Rank(c,8),Ts_Rank(adv60,21),8),6.65),2.62))"""
    o, h, l, c, dv = p["open"], p["high"], p["low"], p["close"], p["dv"]
    adv60 = adv(dv, 60)
    part1 = rank(decay_linear((rank(o) + rank(l)) - (rank(h) + rank(c)), 8))
    part2 = ts_rank(decay_linear(correlation(ts_rank(c, 8), ts_rank(adv60, 21), 8), 7), 3)
    return df_min(part1, part2)


def alpha_92(p: dict) -> pd.DataFrame:
    """min(Ts_Rank(decay_linear(((h+l)/2+c)<(l+o),14.7),18.9), Ts_Rank(decay_linear(corr(rank(l),rank(adv30),7.6),6.9),6.8))"""
    o, h, l, c, dv = p["open"], p["high"], p["low"], p["close"], p["dv"]
    adv30 = adv(dv, 30)
    cond = (((h + l) / 2 + c) < (l + o)).astype(float)
    part1 = ts_rank(decay_linear(cond, 15), 19)
    part2 = ts_rank(decay_linear(correlation(rank(l), rank(adv30), 8), 7), 7)
    return df_min(part1, part2)


def alpha_95(p: dict) -> pd.DataFrame:
    """rank(open-ts_min(open,12.4)) < Ts_Rank((rank(corr(sum((h+l)/2,19),sum(adv40,19),12.9))^5),11.8)"""
    o, h, l, dv = p["open"], p["high"], p["low"], p["dv"]
    adv40 = adv(dv, 40)
    lhs = rank(o - ts_min(o, 12))
    rhs = ts_rank(rank(correlation(rolling_sum((h + l) / 2, 19), rolling_sum(adv40, 19), 13)) ** 5, 12)
    return (lhs < rhs).astype(float)


def alpha_99(p: dict) -> pd.DataFrame:
    """(rank(corr(sum((h+l)/2,19.9),sum(adv60,19.9),8.8)) < rank(corr(low,vol,6.3))) * -1"""
    h, l, v, dv = p["high"], p["low"], p["volume"], p["dv"]
    adv60 = adv(dv, 60)
    lhs = rank(correlation(rolling_sum((h + l) / 2, 20), rolling_sum(adv60, 20), 9))
    rhs = rank(correlation(l, v, 6))
    return (lhs < rhs).astype(float) * -1


def alpha_101(p: dict) -> pd.DataFrame:
    """(close - open) / ((high - low) + 0.001)"""
    o, h, l, c = p["open"], p["high"], p["low"], p["close"]
    return (c - o) / ((h - l) + 0.001)


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP B — implementable with vwap approximation
# ═════════════════════════════════════════════════════════════════════════════

def alpha_5(p: dict) -> pd.DataFrame:
    """rank(open-sum(vwap,10)/10) * (-abs(rank(close-vwap)))"""
    o, c, vwap = p["open"], p["close"], p["vwap"]
    return rank(o - rolling_sum(vwap, 10) / 10) * (-1 * abs_val(rank(c - vwap)))


def alpha_11(p: dict) -> pd.DataFrame:
    """(rank(ts_max(vwap-close,3))+rank(ts_min(vwap-close,3))) * rank(delta(volume,3))"""
    c, vwap, v = p["close"], p["vwap"], p["volume"]
    diff = vwap - c
    return (rank(ts_max(diff, 3)) + rank(ts_min(diff, 3))) * rank(delta(v, 3))


def alpha_25(p: dict) -> pd.DataFrame:
    """rank((-returns*adv20*vwap*(high-close)))"""
    r, h, c, vwap, dv = p["returns"], p["high"], p["close"], p["vwap"], p["dv"]
    adv20 = adv(dv, 20)
    return rank((-r) * adv20 * vwap * (h - c))


def alpha_27(p: dict) -> pd.DataFrame:
    """(0.5 < rank(sum(corr(rank(vol),rank(vwap),6),2)/2)) ? -1 : 1"""
    vwap, v = p["vwap"], p["volume"]
    x = rank(rolling_sum(correlation(rank(v), rank(vwap), 6), 2) / 2.0)
    ones = pd.DataFrame(1.0, index=x.index, columns=x.columns)
    return _tern(x > 0.5, -ones, ones)


def alpha_32(p: dict) -> pd.DataFrame:
    """scale((sum(close,7)/7-close)) + 20*scale(corr(vwap,delay(close,5),230))"""
    c, vwap = p["close"], p["vwap"]
    return (
        scale(rolling_sum(c, 7) / 7 - c)
        + 20 * scale(correlation(vwap, delay(c, 5), 230))
    )


def alpha_36(p: dict) -> pd.DataFrame:
    """2.21*rank(corr(close-open,delay(vol,1),15))+0.7*rank(open-close)
       +0.73*rank(Ts_Rank(delay(-returns,6),5))+rank(|corr(vwap,adv20,6)|)
       +0.6*rank((sum(close,200)/200-open)*(close-open))"""
    o, c, vwap, r = p["open"], p["close"], p["vwap"], p["returns"]
    dv = p["dv"]
    adv20 = adv(dv, 20)
    return (
        2.21 * rank(correlation(c - o, delay(p["volume"], 1), 15))
        + 0.70 * rank(o - c)
        + 0.73 * rank(ts_rank(delay(-r, 6), 5))
        + rank(abs_val(correlation(vwap, adv20, 6)))
        + 0.60 * rank((rolling_sum(c, 200) / 200 - o) * (c - o))
    )


def alpha_41(p: dict) -> pd.DataFrame:
    """((high*low)^0.5) - vwap"""
    return (p["high"] * p["low"]) ** 0.5 - p["vwap"]


def alpha_42(p: dict) -> pd.DataFrame:
    """rank(vwap-close) / rank(vwap+close)"""
    c, vwap = p["close"], p["vwap"]
    denom = rank(vwap + c).replace(0, np.nan)
    return rank(vwap - c) / denom


def alpha_47(p: dict) -> pd.DataFrame:
    """((rank(1/close)*vol/adv20) * (high*rank(high-close)/(sum(high,5)/5))) - rank(vwap-delay(vwap,5))"""
    o, h, c, v, vwap, dv = p["open"], p["high"], p["close"], p["volume"], p["vwap"], p["dv"]
    adv20 = adv(dv, 20)
    return (
        (rank(1 / c) * v / adv20)
        * (h * rank(h - c) / (rolling_sum(h, 5) / 5))
        - rank(vwap - delay(vwap, 5))
    )


def alpha_50(p: dict) -> pd.DataFrame:
    """-1 * ts_max(rank(corr(rank(vol), rank(vwap), 5)), 5)"""
    return -1 * ts_max(correlation(rank(p["volume"]), rank(p["vwap"]), 5), 5)


def alpha_57(p: dict) -> pd.DataFrame:
    """0 - ((close - vwap) / decay_linear(rank(ts_argmax(close, 30)), 2))"""
    c, vwap = p["close"], p["vwap"]
    denom = decay_linear(rank(ts_argmax(c, 30)), 2).replace(0, np.nan)
    return 0 - (c - vwap) / denom


def alpha_61(p: dict) -> pd.DataFrame:
    """rank(vwap-ts_min(vwap,16.1)) < rank(corr(vwap,adv180,17.9))"""
    vwap, dv = p["vwap"], p["dv"]
    adv180 = adv(dv, 180)
    return (rank(vwap - ts_min(vwap, 16)) < rank(correlation(vwap, adv180, 18))).astype(float)


def alpha_62(p: dict) -> pd.DataFrame:
    """(rank(corr(vwap,sum(adv20,22.4),9.9)) < rank((rank(o)+rank(o)) < (rank((h+l)/2)+rank(h)))) * -1"""
    o, h, l, vwap, dv = p["open"], p["high"], p["low"], p["vwap"], p["dv"]
    adv20 = adv(dv, 20)
    lhs = rank(correlation(vwap, rolling_sum(adv20, 22), 10))
    rhs = rank((rank(o) + rank(o)) < (rank((h + l) / 2) + rank(h)))
    return (lhs < rhs).astype(float) * -1


def alpha_64(p: dict) -> pd.DataFrame:
    """(rank(corr(sum(o*0.178+l*0.822,12.7),sum(adv120,12.7),16.6)) < rank(delta((h+l)/2*0.178+vwap*0.822,3.7))) * -1"""
    o, h, l, vwap, dv = p["open"], p["high"], p["low"], p["vwap"], p["dv"]
    adv120 = adv(dv, 120)
    x = rolling_sum(o * 0.178404 + l * (1 - 0.178404), 13)
    lhs = rank(correlation(x, rolling_sum(adv120, 13), 17))
    rhs = rank(delta((h + l) / 2 * 0.178404 + vwap * (1 - 0.178404), 4))
    return (lhs < rhs).astype(float) * -1


def alpha_65(p: dict) -> pd.DataFrame:
    """(rank(corr(o*0.008+vwap*0.992, sum(adv60,8.7), 6.4)) < rank(o-ts_min(o,13.6))) * -1"""
    o, vwap, dv = p["open"], p["vwap"], p["dv"]
    adv60 = adv(dv, 60)
    lhs = rank(correlation(o * 0.00817205 + vwap * (1 - 0.00817205), rolling_sum(adv60, 9), 6))
    rhs = rank(o - ts_min(o, 14))
    return (lhs < rhs).astype(float) * -1


def alpha_66(p: dict) -> pd.DataFrame:
    """(rank(decay_linear(delta(vwap,3.5),7.2)) + Ts_Rank(decay_linear(((l*0.966+l*0.034)-vwap)/(o-(h+l)/2),11.4),6.7)) * -1"""
    o, h, l, vwap = p["open"], p["high"], p["low"], p["vwap"]
    inner = (l * 0.96633 + l * (1 - 0.96633) - vwap) / (o - (h + l) / 2).replace(0, np.nan)
    return (
        rank(decay_linear(delta(vwap, 4), 7))
        + ts_rank(decay_linear(inner, 11), 7)
    ) * -1


def alpha_71(p: dict) -> pd.DataFrame:
    """max(Ts_Rank(decay_linear(corr(Ts_Rank(c,3.4),Ts_Rank(adv180,12.1),18.0),4.2),15.7),
           Ts_Rank(decay_linear((rank((l+o)-(vwap+vwap)))^2,16.5),4.4))"""
    o, l, c, vwap, dv = p["open"], p["low"], p["close"], p["vwap"], p["dv"]
    adv180 = adv(dv, 180)
    part1 = ts_rank(decay_linear(correlation(ts_rank(c, 3), ts_rank(adv180, 12), 18), 4), 16)
    part2 = ts_rank(decay_linear(rank(l + o - 2 * vwap) ** 2, 16), 4)
    return df_max(part1, part2)


def alpha_72(p: dict) -> pd.DataFrame:
    """rank(decay_linear(corr((h+l)/2,adv40,8.9),10.2)) / rank(decay_linear(corr(Ts_Rank(vwap,3.7),Ts_Rank(vol,18.5),6.9),3.0))"""
    h, l, vwap, v, dv = p["high"], p["low"], p["vwap"], p["volume"], p["dv"]
    adv40 = adv(dv, 40)
    numer = rank(decay_linear(correlation((h + l) / 2, adv40, 9), 10))
    denom = rank(decay_linear(correlation(ts_rank(vwap, 4), ts_rank(v, 19), 7), 3)).replace(0, np.nan)
    return numer / denom


def alpha_73(p: dict) -> pd.DataFrame:
    """max(rank(decay_linear(delta(vwap,4.7),2.9)),
          Ts_Rank(decay_linear((delta(o*0.147+l*0.853,2.0)/(o*0.147+l*0.853))*-1,3.3),16.7)) * -1"""
    o, l, vwap = p["open"], p["low"], p["vwap"]
    combo = o * 0.147155 + l * (1 - 0.147155)
    part1 = rank(decay_linear(delta(vwap, 5), 3))
    part2 = ts_rank(decay_linear(-delta(combo, 2) / combo.replace(0, np.nan), 3), 17)
    return df_max(part1, part2) * -1


def alpha_74(p: dict) -> pd.DataFrame:
    """(rank(corr(c,sum(adv30,37.5),15.1)) < rank(corr(rank(h*0.026+vwap*0.974),rank(vol),11.5))) * -1"""
    h, c, vwap, v, dv = p["high"], p["close"], p["vwap"], p["volume"], p["dv"]
    adv30 = adv(dv, 30)
    lhs = rank(correlation(c, rolling_sum(adv30, 37), 15))
    rhs = rank(correlation(rank(h * 0.0261661 + vwap * (1 - 0.0261661)), rank(v), 11))
    return (lhs < rhs).astype(float) * -1


def alpha_75(p: dict) -> pd.DataFrame:
    """rank(corr(vwap,vol,4.2)) < rank(corr(rank(low),rank(adv50),12.4))"""
    l, vwap, v, dv = p["low"], p["vwap"], p["volume"], p["dv"]
    adv50 = adv(dv, 50)
    return (rank(correlation(vwap, v, 4)) < rank(correlation(rank(l), rank(adv50), 12))).astype(float)


def alpha_77(p: dict) -> pd.DataFrame:
    """min(rank(decay_linear((h+l)/2+h-(vwap+h),20.0)), rank(decay_linear(corr((h+l)/2,adv40,3.2),5.6)))"""
    h, l, vwap, dv = p["high"], p["low"], p["vwap"], p["dv"]
    adv40 = adv(dv, 40)
    part1 = rank(decay_linear((h + l) / 2 + h - (vwap + h), 20))
    part2 = rank(decay_linear(correlation((h + l) / 2, adv40, 3), 6))
    return df_min(part1, part2)


def alpha_78(p: dict) -> pd.DataFrame:
    """rank(corr(sum(l*0.352+vwap*0.648,19.7),sum(adv40,19.7),6.8))^rank(corr(rank(vwap),rank(vol),5.8))"""
    l, vwap, v, dv = p["low"], p["vwap"], p["volume"], p["dv"]
    adv40 = adv(dv, 40)
    base = rank(correlation(rolling_sum(l * 0.352233 + vwap * (1 - 0.352233), 20),
                            rolling_sum(adv40, 20), 7))
    exp_ = rank(correlation(rank(vwap), rank(v), 6))
    return base ** exp_


def alpha_81(p: dict) -> pd.DataFrame:
    """(rank(log(product(rank(rank(corr(vwap,sum(adv10,49.6),8.5))^4),14.97))) < rank(corr(rank(vwap),rank(vol),5.1))) * -1"""
    vwap, v, dv = p["vwap"], p["volume"], p["dv"]
    adv10 = adv(dv, 10)
    inner = rank(rank(correlation(vwap, rolling_sum(adv10, 50), 8))) ** 4
    lhs = rank(log(product(inner, 15)))
    rhs = rank(correlation(rank(vwap), rank(v), 5))
    return (lhs < rhs).astype(float) * -1


def alpha_83(p: dict) -> pd.DataFrame:
    """(rank(delay((h-l)/(sum(c,5)/5),2))*rank(rank(vol))) / ((h-l)/(sum(c,5)/5)/(vwap-c))"""
    h, l, c, vwap, v = p["high"], p["low"], p["close"], p["vwap"], p["volume"]
    ratio = (h - l) / (rolling_sum(c, 5) / 5).replace(0, np.nan)
    numer = rank(delay(ratio, 2)) * rank(rank(v))
    denom = (ratio / (vwap - c).replace(0, np.nan)).replace(0, np.nan)
    return numer / denom


def alpha_84(p: dict) -> pd.DataFrame:
    """SignedPower(Ts_Rank(vwap-ts_max(vwap,15.3),20.7), delta(close,4.97))"""
    c, vwap = p["close"], p["vwap"]
    return signedpower(ts_rank(vwap - ts_max(vwap, 15), 21), delta(c, 5))


def alpha_86(p: dict) -> pd.DataFrame:
    """(Ts_Rank(corr(c,sum(adv20,14.7),6.0),20.4) < rank((o+c)-(vwap+o))) * -1"""
    o, c, vwap, dv = p["open"], p["close"], p["vwap"], p["dv"]
    adv20 = adv(dv, 20)
    lhs = ts_rank(correlation(c, rolling_sum(adv20, 15), 6), 20)
    rhs = rank((o + c) - (vwap + o))
    return (lhs < rhs).astype(float) * -1


def alpha_94(p: dict) -> pd.DataFrame:
    """(rank(vwap-ts_min(vwap,11.6))^Ts_Rank(corr(Ts_Rank(vwap,19.6),Ts_Rank(adv60,4.0),18.1),2.7)) * -1"""
    vwap, dv = p["vwap"], p["dv"]
    adv60 = adv(dv, 60)
    base = rank(vwap - ts_min(vwap, 12))
    exp_ = ts_rank(correlation(ts_rank(vwap, 20), ts_rank(adv60, 4), 18), 3)
    return (base ** exp_) * -1


def alpha_96(p: dict) -> pd.DataFrame:
    """max(Ts_Rank(decay_linear(corr(rank(vwap),rank(vol),3.8),4.2),8.4),
          Ts_Rank(decay_linear(Ts_ArgMax(corr(Ts_Rank(c,7.5),Ts_Rank(adv60,4.1),3.7),12.7),14.0),13.4)) * -1"""
    c, vwap, v, dv = p["close"], p["vwap"], p["volume"], p["dv"]
    adv60 = adv(dv, 60)
    part1 = ts_rank(decay_linear(correlation(rank(vwap), rank(v), 4), 4), 8)
    part2 = ts_rank(decay_linear(ts_argmax(correlation(ts_rank(c, 7), ts_rank(adv60, 4), 4), 13), 14), 13)
    return df_max(part1, part2) * -1


def alpha_98(p: dict) -> pd.DataFrame:
    """rank(decay_linear(corr(vwap,sum(adv5,26.5),4.6),7.2))
       - rank(decay_linear(Ts_Rank(Ts_ArgMin(corr(rank(o),rank(adv15),20.8),8.6),7.0),8.1))"""
    o, vwap, dv = p["open"], p["vwap"], p["dv"]
    adv5  = adv(dv, 5)
    adv15 = adv(dv, 15)
    part1 = rank(decay_linear(correlation(vwap, rolling_sum(adv5, 26), 5), 7))
    part2 = rank(decay_linear(ts_rank(ts_argmin(correlation(rank(o), rank(adv15), 21), 9), 7), 8))
    return part1 - part2


# ═════════════════════════════════════════════════════════════════════════════
#  Registry
# ═════════════════════════════════════════════════════════════════════════════

GROUP_A: dict[int, Callable] = {
    1: alpha_1,   2: alpha_2,   3: alpha_3,   4: alpha_4,
    6: alpha_6,   7: alpha_7,   8: alpha_8,   9: alpha_9,
    10: alpha_10, 12: alpha_12, 13: alpha_13, 14: alpha_14,
    15: alpha_15, 16: alpha_16, 17: alpha_17, 18: alpha_18,
    19: alpha_19, 20: alpha_20, 21: alpha_21, 22: alpha_22,
    23: alpha_23, 24: alpha_24, 26: alpha_26, 28: alpha_28,
    29: alpha_29, 30: alpha_30, 31: alpha_31, 33: alpha_33,
    34: alpha_34, 35: alpha_35, 37: alpha_37, 38: alpha_38,
    39: alpha_39, 40: alpha_40, 43: alpha_43, 44: alpha_44,
    45: alpha_45, 46: alpha_46, 49: alpha_49, 51: alpha_51,
    52: alpha_52, 53: alpha_53, 54: alpha_54, 55: alpha_55,
    60: alpha_60, 68: alpha_68, 85: alpha_85, 88: alpha_88,
    92: alpha_92, 95: alpha_95, 99: alpha_99, 101: alpha_101,
}

GROUP_B: dict[int, Callable] = {
    5: alpha_5,   11: alpha_11, 25: alpha_25, 27: alpha_27,
    32: alpha_32, 36: alpha_36, 41: alpha_41, 42: alpha_42,
    47: alpha_47, 50: alpha_50, 57: alpha_57, 61: alpha_61,
    62: alpha_62, 64: alpha_64, 65: alpha_65, 66: alpha_66,
    71: alpha_71, 72: alpha_72, 73: alpha_73, 74: alpha_74,
    75: alpha_75, 77: alpha_77, 78: alpha_78, 81: alpha_81,
    83: alpha_83, 84: alpha_84, 86: alpha_86, 94: alpha_94,
    96: alpha_96, 98: alpha_98,
}

NOT_IMPLEMENTED: list[int] = [48, 56, 58, 59, 63, 67, 69, 70, 76, 79, 80, 82, 87, 89, 90, 91, 93, 97, 100]

ALL_ALPHA_FNS: dict[int, Callable] = {**GROUP_A, **GROUP_B}


def compute_all_alphas(panel: dict) -> dict[int, pd.DataFrame]:
    """
    Compute all implementable alphas and return a dict {alpha_id: DataFrame}.
    """
    results: dict[int, pd.DataFrame] = {}
    for aid, fn in ALL_ALPHA_FNS.items():
        try:
            results[aid] = fn(panel)
        except Exception as exc:
            import warnings
            warnings.warn(f"Alpha#{aid} failed: {exc}")
    return results

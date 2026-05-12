"""
alpha_metrics.py — 101 Formulaic Alphas (Kakushadze 2015) adapted for the
11-ETF sector universe.

Each function is registered via @register_alpha and will be picked up
automatically by compute_alpha.py.

Groups
------
A  (52 alphas): fully implementable — open, high, low, close, volume, returns, adv{d}
B  (30 alphas): implementable with vwap approximation  vwap ≈ (O+H+L+C)/4
NOT_IMPLEMENTED (19): require IndNeutralize or market cap — not available.
    IDs: 48,56,58,59,63,67,69,70,76,79,80,82,87,89,90,91,93,97,100

Add new alphas at the bottom of this file.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from QuantLab.utils.operators import (
    abs_val, adv, correlation, covariance, decay_linear,
    delay, delta, df_max, df_min, log, product,
    rank, rolling_sum, scale, sign, signedpower,
    stddev, ts_argmax, ts_argmin, ts_max, ts_min, ts_rank,
)
from .alpha_registry import register_alpha


def _tern(cond: pd.DataFrame, true_val, false_val) -> pd.DataFrame:
    """Vectorised ternary: cond ? true_val : false_val."""
    c = cond.astype(float)
    return c * true_val + (1 - c) * false_val


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP A — fully implementable
# ═════════════════════════════════════════════════════════════════════════════

@register_alpha(id=1, group="A", required=["close", "returns"],
                desc="rank(Ts_ArgMax(SignedPower((ret<0?std:close),2),5))-0.5")
def alpha_1(p: dict) -> pd.DataFrame:
    c, r = p["close"], p["returns"]
    inner = _tern(r < 0, stddev(r, 20), c)
    return rank(ts_argmax(signedpower(inner, 2.0), 5)) - 0.5


@register_alpha(id=2, group="A", required=["volume", "close", "open"],
                desc="-corr(rank(delta(log(vol),2)), rank((close-open)/open), 6)")
def alpha_2(p: dict) -> pd.DataFrame:
    v, c, o = p["volume"], p["close"], p["open"]
    return -1 * correlation(rank(delta(log(v), 2)), rank((c - o) / o), 6)


@register_alpha(id=3, group="A", required=["open", "volume"],
                desc="-corr(rank(open), rank(volume), 10)")
def alpha_3(p: dict) -> pd.DataFrame:
    return -1 * correlation(rank(p["open"]), rank(p["volume"]), 10)


@register_alpha(id=4, group="A", required=["low"],
                desc="-Ts_Rank(rank(low), 9)")
def alpha_4(p: dict) -> pd.DataFrame:
    return -1 * ts_rank(rank(p["low"]), 9)


@register_alpha(id=6, group="A", required=["open", "volume"],
                desc="-corr(open, volume, 10)")
def alpha_6(p: dict) -> pd.DataFrame:
    return -1 * correlation(p["open"], p["volume"], 10)


@register_alpha(id=7, group="A", required=["close", "volume", "dv"],
                desc="(adv20<vol)?(-ts_rank(|delta(c,7)|,60)*sign(delta(c,7))):(-1)")
def alpha_7(p: dict) -> pd.DataFrame:
    c, v, dv = p["close"], p["volume"], p["dv"]
    adv20 = adv(dv, 20)
    dc7 = delta(c, 7)
    true_val = -1 * ts_rank(abs_val(dc7), 60) * sign(dc7)
    return _tern(adv20 < v, true_val, pd.DataFrame(-1.0, index=c.index, columns=c.columns))


@register_alpha(id=8, group="A", required=["open", "returns"],
                desc="-rank(sum(open,5)*sum(ret,5) - delay(same,10))")
def alpha_8(p: dict) -> pd.DataFrame:
    o, r = p["open"], p["returns"]
    s = rolling_sum(o, 5) * rolling_sum(r, 5)
    return -1 * rank(s - delay(s, 10))


@register_alpha(id=9, group="A", required=["close"],
                desc="conditional on ts_min/ts_max of delta(close,1) over 5 days")
def alpha_9(p: dict) -> pd.DataFrame:
    dc = delta(p["close"], 1)
    cond1 = pd.DataFrame(0.0, index=dc.index, columns=dc.columns) < ts_min(dc, 5)
    cond2 = ts_max(dc, 5) < pd.DataFrame(0.0, index=dc.index, columns=dc.columns)
    inner = _tern(cond2, dc, -dc)
    return _tern(cond1, dc, inner)

@register_alpha(id=10, group="A", required=["close"],
                desc="rank(alpha_9 logic with window 4)")
def alpha_10(p: dict) -> pd.DataFrame:
    dc = delta(p["close"], 1)
    z = pd.DataFrame(0.0, index=dc.index, columns=dc.columns)
    cond1 = z < ts_min(dc, 4)
    cond2 = ts_max(dc, 4) < z
    inner = _tern(cond2, dc, -dc)
    return rank(_tern(cond1, dc, inner))


@register_alpha(id=12, group="A", required=["volume", "close"],
                desc="sign(delta(vol,1)) * (-delta(close,1))")
def alpha_12(p: dict) -> pd.DataFrame:
    return sign(delta(p["volume"], 1)) * (-1 * delta(p["close"], 1))


@register_alpha(id=13, group="A", required=["close", "volume"],
                desc="-rank(cov(rank(close), rank(volume), 5))")
def alpha_13(p: dict) -> pd.DataFrame:
    return -1 * rank(covariance(rank(p["close"]), rank(p["volume"]), 5))


@register_alpha(id=14, group="A", required=["returns", "open", "volume"],
                desc="-rank(delta(ret,3)) * corr(open, vol, 10)")
def alpha_14(p: dict) -> pd.DataFrame:
    return (-1 * rank(delta(p["returns"], 3))) * correlation(p["open"], p["volume"], 10)


@register_alpha(id=15, group="A", required=["high", "volume"],
                desc="-sum(rank(corr(rank(high), rank(vol), 3)), 3)")
def alpha_15(p: dict) -> pd.DataFrame:
    return -1 * rolling_sum(rank(correlation(rank(p["high"]), rank(p["volume"]), 3)), 3)


@register_alpha(id=16, group="A", required=["high", "volume"],
                desc="-rank(cov(rank(high), rank(vol), 5))")
def alpha_16(p: dict) -> pd.DataFrame:
    return -1 * rank(covariance(rank(p["high"]), rank(p["volume"]), 5))


@register_alpha(id=17, group="A", required=["close", "volume", "dv"],
                desc="-rank(ts_rank(c,10))*rank(delta(delta(c,1),1))*rank(ts_rank(vol/adv20,5))")
def alpha_17(p: dict) -> pd.DataFrame:
    c, v, dv = p["close"], p["volume"], p["dv"]
    adv20 = adv(dv, 20)
    return (
        (-1 * rank(ts_rank(c, 10)))
        * rank(delta(delta(c, 1), 1))
        * rank(ts_rank(v / adv20, 5))
    )


@register_alpha(id=18, group="A", required=["close", "open"],
                desc="-rank(std(|c-o|,5)+(c-o)+corr(c,o,10))")
def alpha_18(p: dict) -> pd.DataFrame:
    c, o = p["close"], p["open"]
    return -1 * rank(stddev(abs_val(c - o), 5) + (c - o) + correlation(c, o, 10))


@register_alpha(id=19, group="A", required=["close", "returns"],
                desc="-sign(c-delay(c,7)+delta(c,7)) * (1+rank(1+sum(ret,250)))")
def alpha_19(p: dict) -> pd.DataFrame:
    c, r = p["close"], p["returns"]
    return (-1 * sign((c - delay(c, 7)) + delta(c, 7))) * (1 + rank(1 + rolling_sum(r, 250)))


@register_alpha(id=20, group="A", required=["open", "high", "close", "low"],
                desc="-rank(o-delay(h,1))*rank(o-delay(c,1))*rank(o-delay(l,1))")
def alpha_20(p: dict) -> pd.DataFrame:
    o, h, c, l = p["open"], p["high"], p["close"], p["low"]
    return (
        (-1 * rank(o - delay(h, 1)))
        * rank(o - delay(c, 1))
        * rank(o - delay(l, 1))
    )


@register_alpha(id=21, group="A", required=["close", "volume", "dv"],
                desc="conditional on 8-day vs 2-day close mean and vol/adv20")
def alpha_21(p: dict) -> pd.DataFrame:
    c, v, dv = p["close"], p["volume"], p["dv"]
    adv20 = adv(dv, 20)
    ma8 = rolling_sum(c, 8) / 8
    ma2 = rolling_sum(c, 2) / 2
    std8 = stddev(c, 8)
    vol_ratio = v / adv20
    ones = pd.DataFrame(1.0, index=c.index, columns=c.columns)
    cond1 = (ma8 + std8) < ma2
    cond2 = ma2 < (ma8 - std8)
    cond3 = ones <= vol_ratio
    inner2 = _tern(cond3, ones, -ones)
    inner1 = _tern(cond2, ones, inner2)
    return _tern(cond1, -ones, inner1)


@register_alpha(id=22, group="A", required=["high", "volume", "close"],
                desc="-delta(corr(high,vol,5),5) * rank(std(close,20))")
def alpha_22(p: dict) -> pd.DataFrame:
    return -1 * (delta(correlation(p["high"], p["volume"], 5), 5) * rank(stddev(p["close"], 20)))


@register_alpha(id=23, group="A", required=["high"],
                desc="(sum(high,20)/20 < high) ? -delta(high,2) : 0")
def alpha_23(p: dict) -> pd.DataFrame:
    h = p["high"]
    cond = (rolling_sum(h, 20) / 20) < h
    return _tern(cond, -delta(h, 2), pd.DataFrame(0.0, index=h.index, columns=h.columns))


@register_alpha(id=24, group="A", required=["close"],
                desc="conditional on 100-day trend vs 5% threshold")
def alpha_24(p: dict) -> pd.DataFrame:
    c = p["close"]
    ma100 = rolling_sum(c, 100) / 100
    trend = delta(ma100, 100) / delay(c, 100)
    threshold = pd.DataFrame(0.05, index=c.index, columns=c.columns)
    cond = trend <= threshold
    return _tern(cond, -1 * (c - ts_min(c, 100)), -delta(c, 3))


@register_alpha(id=26, group="A", required=["volume", "high"],
                desc="-ts_max(corr(ts_rank(vol,5), ts_rank(high,5), 5), 3)")
def alpha_26(p: dict) -> pd.DataFrame:
    return -1 * ts_max(
        correlation(ts_rank(p["volume"], 5), ts_rank(p["high"], 5), 5), 3
    )


@register_alpha(id=28, group="A", required=["close", "high", "low", "dv"],
                desc="scale(corr(adv20,low,5) + (high+low)/2 - close)")
def alpha_28(p: dict) -> pd.DataFrame:
    c, h, l, dv = p["close"], p["high"], p["low"], p["dv"]
    adv20 = adv(dv, 20)
    return scale(correlation(adv20, l, 5) + (h + l) / 2 - c)


@register_alpha(id=29, group="A", required=["close", "returns"],
                desc="min(product(rank(rank(scale(log(sum(ts_min(...),2),1))))),5)+ts_rank(delay(-ret,6),5)")
def alpha_29(p: dict) -> pd.DataFrame:
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


@register_alpha(id=30, group="A", required=["close", "volume"],
                desc="(1-rank(sign(dc)+sign(dc1)+sign(dc2))) * sum(vol,5)/sum(vol,20)")
def alpha_30(p: dict) -> pd.DataFrame:
    c, v = p["close"], p["volume"]
    dc  = sign(c - delay(c, 1))
    dc1 = sign(delay(c, 1) - delay(c, 2))
    dc2 = sign(delay(c, 2) - delay(c, 3))
    return (1.0 - rank(dc + dc1 + dc2)) * rolling_sum(v, 5) / rolling_sum(v, 20)


@register_alpha(id=31, group="A", required=["close", "low", "dv"],
                desc="rank(rank(rank(decay(-rank(rank(delta(c,10))),10))))+rank(-delta(c,3))+sign(scale(corr(adv20,l,12)))")
def alpha_31(p: dict) -> pd.DataFrame:
    c, l, dv = p["close"], p["low"], p["dv"]
    adv20 = adv(dv, 20)
    part1 = rank(rank(rank(decay_linear(-1 * rank(rank(delta(c, 10))), 10))))
    part2 = rank(-delta(c, 3))
    part3 = sign(scale(correlation(adv20, l, 12)))
    return part1 + part2 + part3


@register_alpha(id=33, group="A", required=["open", "close"],
                desc="rank(-(1 - open/close))")
def alpha_33(p: dict) -> pd.DataFrame:
    return rank(-1 * (1 - p["open"] / p["close"]))


@register_alpha(id=34, group="A", required=["returns", "close"],
                desc="rank((1-rank(std(ret,2)/std(ret,5)))+(1-rank(delta(c,1))))")
def alpha_34(p: dict) -> pd.DataFrame:
    r, c = p["returns"], p["close"]
    return rank(
        (1 - rank(stddev(r, 2) / stddev(r, 5)))
        + (1 - rank(delta(c, 1)))
    )


@register_alpha(id=35, group="A", required=["close", "high", "low", "volume", "returns"],
                desc="ts_rank(vol,32)*(1-ts_rank(c+h-l,16))*(1-ts_rank(ret,32))")
def alpha_35(p: dict) -> pd.DataFrame:
    c, h, l, v, r = p["close"], p["high"], p["low"], p["volume"], p["returns"]
    return (
        ts_rank(v, 32)
        * (1 - ts_rank(c + h - l, 16))
        * (1 - ts_rank(r, 32))
    )


@register_alpha(id=37, group="A", required=["open", "close"],
                desc="rank(corr(delay(o-c,1),c,200)) + rank(o-c)")
def alpha_37(p: dict) -> pd.DataFrame:
    o, c = p["open"], p["close"]
    return rank(correlation(delay(o - c, 1), c, 200)) + rank(o - c)


@register_alpha(id=38, group="A", required=["close", "open"],
                desc="-rank(ts_rank(c,10)) * rank(c/o)")
def alpha_38(p: dict) -> pd.DataFrame:
    c, o = p["close"], p["open"]
    return (-1 * rank(ts_rank(c, 10))) * rank(c / o)


@register_alpha(id=39, group="A", required=["close", "volume", "returns", "dv"],
                desc="-rank(delta(c,7)*(1-rank(decay(vol/adv20,9)))) * (1+rank(sum(ret,250)))")
def alpha_39(p: dict) -> pd.DataFrame:
    c, v, r, dv = p["close"], p["volume"], p["returns"], p["dv"]
    adv20 = adv(dv, 20)
    return (
        (-1 * rank(delta(c, 7) * (1 - rank(decay_linear(v / adv20, 9)))))
        * (1 + rank(rolling_sum(r, 250)))
    )


@register_alpha(id=40, group="A", required=["high", "volume"],
                desc="-rank(std(high,10)) * corr(high, vol, 10)")
def alpha_40(p: dict) -> pd.DataFrame:
    h, v = p["high"], p["volume"]
    return (-1 * rank(stddev(h, 10))) * correlation(h, v, 10)


@register_alpha(id=43, group="A", required=["close", "volume", "dv"],
                desc="ts_rank(vol/adv20,20) * ts_rank(-delta(c,7),8)")
def alpha_43(p: dict) -> pd.DataFrame:
    c, v, dv = p["close"], p["volume"], p["dv"]
    adv20 = adv(dv, 20)
    return ts_rank(v / adv20, 20) * ts_rank(-delta(c, 7), 8)


@register_alpha(id=44, group="A", required=["high", "volume"],
                desc="-corr(high, rank(vol), 5)")
def alpha_44(p: dict) -> pd.DataFrame:
    return -1 * correlation(p["high"], rank(p["volume"]), 5)


@register_alpha(id=45, group="A", required=["close", "volume"],
                desc="-rank(sum(delay(c,5),20)/20) * corr(c,vol,2) * rank(corr(sum(c,5),sum(c,20),2))")
def alpha_45(p: dict) -> pd.DataFrame:
    c, v = p["close"], p["volume"]
    return -1 * (
        rank(rolling_sum(delay(c, 5), 20) / 20)
        * correlation(c, v, 2)
        * rank(correlation(rolling_sum(c, 5), rolling_sum(c, 20), 2))
    )


@register_alpha(id=46, group="A", required=["close"],
                desc="conditional on momentum acceleration vs 0.25 and 0 thresholds")
def alpha_46(p: dict) -> pd.DataFrame:
    c = p["close"]
    accel = ((delay(c, 20) - delay(c, 10)) / 10) - ((delay(c, 10) - c) / 10)
    z = pd.DataFrame(0.0, index=c.index, columns=c.columns)
    cond1 = accel > 0.25
    cond2 = accel < z
    inner = _tern(cond2, pd.DataFrame(1.0, index=c.index, columns=c.columns),
                  -1 * (c - delay(c, 1)))
    return _tern(cond1, pd.DataFrame(-1.0, index=c.index, columns=c.columns), inner)


@register_alpha(id=49, group="A", required=["close"],
                desc="(accel < -0.1) ? 1 : (-1*(c-delay(c,1)))")
def alpha_49(p: dict) -> pd.DataFrame:
    c = p["close"]
    accel = ((delay(c, 20) - delay(c, 10)) / 10) - ((delay(c, 10) - c) / 10)
    cond = accel < -0.1
    return _tern(cond,
                 pd.DataFrame(1.0, index=c.index, columns=c.columns),
                 -1 * (c - delay(c, 1)))


@register_alpha(id=51, group="A", required=["close"],
                desc="same as alpha_49 but threshold -0.05")
def alpha_51(p: dict) -> pd.DataFrame:
    c = p["close"]
    accel = ((delay(c, 20) - delay(c, 10)) / 10) - ((delay(c, 10) - c) / 10)
    cond = accel < -0.05
    return _tern(cond,
                 pd.DataFrame(1.0, index=c.index, columns=c.columns),
                 -1 * (c - delay(c, 1)))


@register_alpha(id=52, group="A", required=["low", "returns", "volume"],
                desc="(-ts_min(l,5)+delay(ts_min(l,5),5))*rank((sum(ret,240)-sum(ret,20))/220)*ts_rank(vol,5)")
def alpha_52(p: dict) -> pd.DataFrame:
    l, r, v = p["low"], p["returns"], p["volume"]
    tmin5 = ts_min(l, 5)
    return (
        (-tmin5 + delay(tmin5, 5))
        * rank((rolling_sum(r, 240) - rolling_sum(r, 20)) / 220)
        * ts_rank(v, 5)
    )


@register_alpha(id=53, group="A", required=["close", "high", "low"],
                desc="-delta(((c-l)-(h-c))/(c-l), 9)")
def alpha_53(p: dict) -> pd.DataFrame:
    c, h, l = p["close"], p["high"], p["low"]
    denom = (c - l).replace(0, np.nan)
    inner = ((c - l) - (h - c)) / denom
    return -1 * delta(inner, 9)


@register_alpha(id=54, group="A", required=["open", "high", "low", "close"],
                desc="(-1*(l-c)*(o^5)) / ((l-h)*(c^5))")
def alpha_54(p: dict) -> pd.DataFrame:
    o, h, l, c = p["open"], p["high"], p["low"], p["close"]
    denom = ((l - h) * (c ** 5)).replace(0, np.nan)
    return (-1 * (l - c) * (o ** 5)) / denom


@register_alpha(id=55, group="A", required=["close", "high", "low", "volume"],
                desc="-corr(rank((c-ts_min(l,12))/(ts_max(h,12)-ts_min(l,12))), rank(vol), 6)")
def alpha_55(p: dict) -> pd.DataFrame:
    c, h, l, v = p["close"], p["high"], p["low"], p["volume"]
    rng = (ts_max(h, 12) - ts_min(l, 12)).replace(0, np.nan)
    x = rank((c - ts_min(l, 12)) / rng)
    return -1 * correlation(x, rank(v), 6)


@register_alpha(id=60, group="A", required=["close", "high", "low", "volume"],
                desc="0-(2*scale(rank(clv*vol))-scale(rank(ts_argmax(c,10))))")
def alpha_60(p: dict) -> pd.DataFrame:
    c, h, l, v = p["close"], p["high"], p["low"], p["volume"]
    rng = (h - l).replace(0, np.nan)
    clv = ((c - l) - (h - c)) / rng * v
    return 0 - (2 * scale(rank(clv)) - scale(rank(ts_argmax(c, 10))))


@register_alpha(id=68, group="A", required=["high", "close", "low", "dv"],
                desc="(ts_rank(corr(rank(h),rank(adv15),8),13) < rank(delta(c*0.518+l*0.482,1)))*-1")
def alpha_68(p: dict) -> pd.DataFrame:
    h, c, l, dv = p["high"], p["close"], p["low"], p["dv"]
    adv15 = adv(dv, 15)
    lhs = ts_rank(correlation(rank(h), rank(adv15), 9), 14)
    rhs = rank(delta(c * 0.518371 + l * (1 - 0.518371), 1))
    return (lhs < rhs).astype(float) * -1


@register_alpha(id=85, group="A", required=["high", "close", "low", "volume", "dv"],
                desc="rank(corr(h*0.877+c*0.123,adv30,9))^rank(corr(ts_rank((h+l)/2,3),ts_rank(vol,10),7))")
def alpha_85(p: dict) -> pd.DataFrame:
    h, c, l, v, dv = p["high"], p["close"], p["low"], p["volume"], p["dv"]
    adv30 = adv(dv, 30)
    base = rank(correlation(h * 0.876703 + c * (1 - 0.876703), adv30, 10))
    exp_ = rank(correlation(ts_rank((h + l) / 2, 4), ts_rank(v, 10), 7))
    return base ** exp_


@register_alpha(id=88, group="A", required=["open", "high", "low", "close", "dv"],
                desc="min(rank(decay((rank(o)+rank(l))-(rank(h)+rank(c)),8)),ts_rank(decay(corr(ts_rank(c,8),ts_rank(adv60,21),8),6),2))")
def alpha_88(p: dict) -> pd.DataFrame:
    o, h, l, c, dv = p["open"], p["high"], p["low"], p["close"], p["dv"]
    adv60 = adv(dv, 60)
    part1 = rank(decay_linear((rank(o) + rank(l)) - (rank(h) + rank(c)), 8))
    part2 = ts_rank(decay_linear(correlation(ts_rank(c, 8), ts_rank(adv60, 21), 8), 7), 3)
    return df_min(part1, part2)


@register_alpha(id=92, group="A", required=["open", "high", "low", "close", "dv"],
                desc="min(ts_rank(decay(((h+l)/2+c)<(l+o),14),18),ts_rank(decay(corr(rank(l),rank(adv30),7),6),6))")
def alpha_92(p: dict) -> pd.DataFrame:
    o, h, l, c, dv = p["open"], p["high"], p["low"], p["close"], p["dv"]
    adv30 = adv(dv, 30)
    cond = (((h + l) / 2 + c) < (l + o)).astype(float)
    part1 = ts_rank(decay_linear(cond, 15), 19)
    part2 = ts_rank(decay_linear(correlation(rank(l), rank(adv30), 8), 7), 7)
    return df_min(part1, part2)


@register_alpha(id=95, group="A", required=["open", "high", "low", "dv"],
                desc="rank(o-ts_min(o,12)) < ts_rank((rank(corr(sum((h+l)/2,19),sum(adv40,19),12))^5),11)")
def alpha_95(p: dict) -> pd.DataFrame:
    o, h, l, dv = p["open"], p["high"], p["low"], p["dv"]
    adv40 = adv(dv, 40)
    lhs = rank(o - ts_min(o, 12))
    rhs = ts_rank(rank(correlation(rolling_sum((h + l) / 2, 19), rolling_sum(adv40, 19), 13)) ** 5, 12)
    return (lhs < rhs).astype(float)


@register_alpha(id=99, group="A", required=["high", "low", "volume", "dv"],
                desc="(rank(corr(sum((h+l)/2,20),sum(adv60,20),9)) < rank(corr(low,vol,6)))*-1")
def alpha_99(p: dict) -> pd.DataFrame:
    h, l, v, dv = p["high"], p["low"], p["volume"], p["dv"]
    adv60 = adv(dv, 60)
    lhs = rank(correlation(rolling_sum((h + l) / 2, 20), rolling_sum(adv60, 20), 9))
    rhs = rank(correlation(l, v, 6))
    return (lhs < rhs).astype(float) * -1


@register_alpha(id=101, group="A", required=["open", "high", "low", "close"],
                desc="(close - open) / ((high - low) + 0.001)")
def alpha_101(p: dict) -> pd.DataFrame:
    o, h, l, c = p["open"], p["high"], p["low"], p["close"]
    return (c - o) / ((h - l) + 0.001)


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP B — implementable with vwap approximation  vwap ≈ (O+H+L+C)/4
# ═════════════════════════════════════════════════════════════════════════════

@register_alpha(id=5, group="B", required=["open", "close", "vwap"],
                desc="rank(o-sum(vwap,10)/10) * (-|rank(c-vwap)|)")
def alpha_5(p: dict) -> pd.DataFrame:
    o, c, vwap = p["open"], p["close"], p["vwap"]
    return rank(o - rolling_sum(vwap, 10) / 10) * (-1 * abs_val(rank(c - vwap)))


@register_alpha(id=11, group="B", required=["close", "vwap", "volume"],
                desc="(rank(ts_max(vwap-c,3))+rank(ts_min(vwap-c,3)))*rank(delta(vol,3))")
def alpha_11(p: dict) -> pd.DataFrame:
    c, vwap, v = p["close"], p["vwap"], p["volume"]
    diff = vwap - c
    return (rank(ts_max(diff, 3)) + rank(ts_min(diff, 3))) * rank(delta(v, 3))


@register_alpha(id=25, group="B", required=["returns", "high", "close", "vwap", "dv"],
                desc="rank(-ret*adv20*vwap*(h-c))")
def alpha_25(p: dict) -> pd.DataFrame:
    r, h, c, vwap, dv = p["returns"], p["high"], p["close"], p["vwap"], p["dv"]
    adv20 = adv(dv, 20)
    return rank((-r) * adv20 * vwap * (h - c))


@register_alpha(id=27, group="B", required=["vwap", "volume"],
                desc="(0.5 < rank(sum(corr(rank(vol),rank(vwap),6),2)/2)) ? -1 : 1")
def alpha_27(p: dict) -> pd.DataFrame:
    vwap, v = p["vwap"], p["volume"]
    x = rank(rolling_sum(correlation(rank(v), rank(vwap), 6), 2) / 2.0)
    ones = pd.DataFrame(1.0, index=x.index, columns=x.columns)
    return _tern(x > 0.5, -ones, ones)


@register_alpha(id=32, group="B", required=["close", "vwap"],
                desc="scale((sum(c,7)/7-c)) + 20*scale(corr(vwap,delay(c,5),230))")
def alpha_32(p: dict) -> pd.DataFrame:
    c, vwap = p["close"], p["vwap"]
    return (
        scale(rolling_sum(c, 7) / 7 - c)
        + 20 * scale(correlation(vwap, delay(c, 5), 230))
    )


@register_alpha(id=36, group="B", required=["open", "close", "vwap", "returns", "volume", "dv"],
                desc="2.21*rank(corr(c-o,delay(vol,1),15))+0.7*rank(o-c)+0.73*rank(ts_rank(delay(-ret,6),5))+rank(|corr(vwap,adv20,6)|)+0.6*rank((sum(c,200)/200-o)*(c-o))")
def alpha_36(p: dict) -> pd.DataFrame:
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


@register_alpha(id=41, group="B", required=["high", "low", "vwap"],
                desc="(high*low)^0.5 - vwap")
def alpha_41(p: dict) -> pd.DataFrame:
    return (p["high"] * p["low"]) ** 0.5 - p["vwap"]


@register_alpha(id=42, group="B", required=["close", "vwap"],
                desc="rank(vwap-c) / rank(vwap+c)")
def alpha_42(p: dict) -> pd.DataFrame:
    c, vwap = p["close"], p["vwap"]
    denom = rank(vwap + c).replace(0, np.nan)
    return rank(vwap - c) / denom


@register_alpha(id=47, group="B", required=["open", "high", "close", "volume", "vwap", "dv"],
                desc="(rank(1/c)*vol/adv20)*(h*rank(h-c)/(sum(h,5)/5)) - rank(vwap-delay(vwap,5))")
def alpha_47(p: dict) -> pd.DataFrame:
    o, h, c, v, vwap, dv = p["open"], p["high"], p["close"], p["volume"], p["vwap"], p["dv"]
    adv20 = adv(dv, 20)
    return (
        (rank(1 / c) * v / adv20)
        * (h * rank(h - c) / (rolling_sum(h, 5) / 5))
        - rank(vwap - delay(vwap, 5))
    )


@register_alpha(id=50, group="B", required=["volume", "vwap"],
                desc="-ts_max(rank(corr(rank(vol), rank(vwap), 5)), 5)")
def alpha_50(p: dict) -> pd.DataFrame:
    return -1 * ts_max(correlation(rank(p["volume"]), rank(p["vwap"]), 5), 5)


@register_alpha(id=57, group="B", required=["close", "vwap"],
                desc="0-(c-vwap)/decay_linear(rank(ts_argmax(c,30)),2)")
def alpha_57(p: dict) -> pd.DataFrame:
    c, vwap = p["close"], p["vwap"]
    denom = decay_linear(rank(ts_argmax(c, 30)), 2).replace(0, np.nan)
    return 0 - (c - vwap) / denom


@register_alpha(id=61, group="B", required=["vwap", "dv"],
                desc="rank(vwap-ts_min(vwap,16)) < rank(corr(vwap,adv180,18))")
def alpha_61(p: dict) -> pd.DataFrame:
    vwap, dv = p["vwap"], p["dv"]
    adv180 = adv(dv, 180)
    return (rank(vwap - ts_min(vwap, 16)) < rank(correlation(vwap, adv180, 18))).astype(float)


@register_alpha(id=62, group="B", required=["open", "high", "low", "vwap", "dv"],
                desc="(rank(corr(vwap,sum(adv20,22),10)) < rank((rank(o)+rank(o))<(rank((h+l)/2)+rank(h))))*-1")
def alpha_62(p: dict) -> pd.DataFrame:
    o, h, l, vwap, dv = p["open"], p["high"], p["low"], p["vwap"], p["dv"]
    adv20 = adv(dv, 20)
    lhs = rank(correlation(vwap, rolling_sum(adv20, 22), 10))
    rhs = rank((rank(o) + rank(o)) < (rank((h + l) / 2) + rank(h)))
    return (lhs < rhs).astype(float) * -1


@register_alpha(id=64, group="B", required=["open", "high", "low", "vwap", "dv"],
                desc="(rank(corr(sum(o*0.178+l*0.822,13),sum(adv120,13),17)) < rank(delta((h+l)/2*0.178+vwap*0.822,4)))*-1")
def alpha_64(p: dict) -> pd.DataFrame:
    o, h, l, vwap, dv = p["open"], p["high"], p["low"], p["vwap"], p["dv"]
    adv120 = adv(dv, 120)
    x = rolling_sum(o * 0.178404 + l * (1 - 0.178404), 13)
    lhs = rank(correlation(x, rolling_sum(adv120, 13), 17))
    rhs = rank(delta((h + l) / 2 * 0.178404 + vwap * (1 - 0.178404), 4))
    return (lhs < rhs).astype(float) * -1


@register_alpha(id=65, group="B", required=["open", "vwap", "dv"],
                desc="(rank(corr(o*0.008+vwap*0.992,sum(adv60,9),6)) < rank(o-ts_min(o,14)))*-1")
def alpha_65(p: dict) -> pd.DataFrame:
    o, vwap, dv = p["open"], p["vwap"], p["dv"]
    adv60 = adv(dv, 60)
    lhs = rank(correlation(o * 0.00817205 + vwap * (1 - 0.00817205), rolling_sum(adv60, 9), 6))
    rhs = rank(o - ts_min(o, 14))
    return (lhs < rhs).astype(float) * -1


@register_alpha(id=66, group="B", required=["open", "high", "low", "vwap"],
                desc="(rank(decay(delta(vwap,4),7))+ts_rank(decay((l-vwap)/(o-(h+l)/2),11),7))*-1")
def alpha_66(p: dict) -> pd.DataFrame:
    o, h, l, vwap = p["open"], p["high"], p["low"], p["vwap"]
    inner = (l * 0.96633 + l * (1 - 0.96633) - vwap) / (o - (h + l) / 2).replace(0, np.nan)
    return (
        rank(decay_linear(delta(vwap, 4), 7))
        + ts_rank(decay_linear(inner, 11), 7)
    ) * -1


@register_alpha(id=71, group="B", required=["open", "low", "close", "vwap", "dv"],
                desc="max(ts_rank(decay(corr(ts_rank(c,3),ts_rank(adv180,12),18),4),16), ts_rank(decay(rank(l+o-2*vwap)^2,16),4))")
def alpha_71(p: dict) -> pd.DataFrame:
    o, l, c, vwap, dv = p["open"], p["low"], p["close"], p["vwap"], p["dv"]
    adv180 = adv(dv, 180)
    part1 = ts_rank(decay_linear(correlation(ts_rank(c, 3), ts_rank(adv180, 12), 18), 4), 16)
    part2 = ts_rank(decay_linear(rank(l + o - 2 * vwap) ** 2, 16), 4)
    return df_max(part1, part2)


@register_alpha(id=72, group="B", required=["high", "low", "vwap", "volume", "dv"],
                desc="rank(decay(corr((h+l)/2,adv40,9),10)) / rank(decay(corr(ts_rank(vwap,4),ts_rank(vol,19),7),3))")
def alpha_72(p: dict) -> pd.DataFrame:
    h, l, vwap, v, dv = p["high"], p["low"], p["vwap"], p["volume"], p["dv"]
    adv40 = adv(dv, 40)
    numer = rank(decay_linear(correlation((h + l) / 2, adv40, 9), 10))
    denom = rank(decay_linear(correlation(ts_rank(vwap, 4), ts_rank(v, 19), 7), 3)).replace(0, np.nan)
    return numer / denom


@register_alpha(id=73, group="B", required=["open", "low", "vwap"],
                desc="max(rank(decay(delta(vwap,5),3)), ts_rank(decay(-delta(combo,2)/combo,3),17))*-1")
def alpha_73(p: dict) -> pd.DataFrame:
    o, l, vwap = p["open"], p["low"], p["vwap"]
    combo = o * 0.147155 + l * (1 - 0.147155)
    part1 = rank(decay_linear(delta(vwap, 5), 3))
    part2 = ts_rank(decay_linear(-delta(combo, 2) / combo.replace(0, np.nan), 3), 17)
    return df_max(part1, part2) * -1


@register_alpha(id=74, group="B", required=["high", "close", "vwap", "volume", "dv"],
                desc="(rank(corr(c,sum(adv30,37),15)) < rank(corr(rank(h*0.026+vwap*0.974),rank(vol),11)))*-1")
def alpha_74(p: dict) -> pd.DataFrame:
    h, c, vwap, v, dv = p["high"], p["close"], p["vwap"], p["volume"], p["dv"]
    adv30 = adv(dv, 30)
    lhs = rank(correlation(c, rolling_sum(adv30, 37), 15))
    rhs = rank(correlation(rank(h * 0.0261661 + vwap * (1 - 0.0261661)), rank(v), 11))
    return (lhs < rhs).astype(float) * -1


@register_alpha(id=75, group="B", required=["low", "vwap", "volume", "dv"],
                desc="rank(corr(vwap,vol,4)) < rank(corr(rank(low),rank(adv50),12))")
def alpha_75(p: dict) -> pd.DataFrame:
    l, vwap, v, dv = p["low"], p["vwap"], p["volume"], p["dv"]
    adv50 = adv(dv, 50)
    return (rank(correlation(vwap, v, 4)) < rank(correlation(rank(l), rank(adv50), 12))).astype(float)


@register_alpha(id=77, group="B", required=["high", "low", "vwap", "dv"],
                desc="min(rank(decay((h+l)/2+h-(vwap+h),20)), rank(decay(corr((h+l)/2,adv40,3),6)))")
def alpha_77(p: dict) -> pd.DataFrame:
    h, l, vwap, dv = p["high"], p["low"], p["vwap"], p["dv"]
    adv40 = adv(dv, 40)
    part1 = rank(decay_linear((h + l) / 2 + h - (vwap + h), 20))
    part2 = rank(decay_linear(correlation((h + l) / 2, adv40, 3), 6))
    return df_min(part1, part2)


@register_alpha(id=78, group="B", required=["low", "vwap", "volume", "dv"],
                desc="rank(corr(sum(l*0.352+vwap*0.648,20),sum(adv40,20),7))^rank(corr(rank(vwap),rank(vol),6))")
def alpha_78(p: dict) -> pd.DataFrame:
    l, vwap, v, dv = p["low"], p["vwap"], p["volume"], p["dv"]
    adv40 = adv(dv, 40)
    base = rank(correlation(rolling_sum(l * 0.352233 + vwap * (1 - 0.352233), 20),
                            rolling_sum(adv40, 20), 7))
    exp_ = rank(correlation(rank(vwap), rank(v), 6))
    return base ** exp_


@register_alpha(id=81, group="B", required=["vwap", "volume", "dv"],
                desc="(rank(log(product(rank(rank(corr(vwap,sum(adv10,50),8)))^4),15))) < rank(corr(rank(vwap),rank(vol),5)))*-1")
def alpha_81(p: dict) -> pd.DataFrame:
    vwap, v, dv = p["vwap"], p["volume"], p["dv"]
    adv10 = adv(dv, 10)
    inner = rank(rank(correlation(vwap, rolling_sum(adv10, 50), 8))) ** 4
    lhs = rank(log(product(inner, 15)))
    rhs = rank(correlation(rank(vwap), rank(v), 5))
    return (lhs < rhs).astype(float) * -1


@register_alpha(id=83, group="B", required=["high", "low", "close", "vwap", "volume"],
                desc="(rank(delay((h-l)/(sum(c,5)/5),2))*rank(rank(vol))) / ((h-l)/(sum(c,5)/5)/(vwap-c))")
def alpha_83(p: dict) -> pd.DataFrame:
    h, l, c, vwap, v = p["high"], p["low"], p["close"], p["vwap"], p["volume"]
    ratio = (h - l) / (rolling_sum(c, 5) / 5).replace(0, np.nan)
    numer = rank(delay(ratio, 2)) * rank(rank(v))
    denom = (ratio / (vwap - c).replace(0, np.nan)).replace(0, np.nan)
    return numer / denom


@register_alpha(id=84, group="B", required=["close", "vwap"],
                desc="SignedPower(ts_rank(vwap-ts_max(vwap,15),21), delta(c,5))")
def alpha_84(p: dict) -> pd.DataFrame:
    c, vwap = p["close"], p["vwap"]
    return signedpower(ts_rank(vwap - ts_max(vwap, 15), 21), delta(c, 5))


@register_alpha(id=86, group="B", required=["open", "close", "vwap", "dv"],
                desc="(ts_rank(corr(c,sum(adv20,15),6),20) < rank((o+c)-(vwap+o)))*-1")
def alpha_86(p: dict) -> pd.DataFrame:
    o, c, vwap, dv = p["open"], p["close"], p["vwap"], p["dv"]
    adv20 = adv(dv, 20)
    lhs = ts_rank(correlation(c, rolling_sum(adv20, 15), 6), 20)
    rhs = rank((o + c) - (vwap + o))
    return (lhs < rhs).astype(float) * -1


@register_alpha(id=94, group="B", required=["vwap", "dv"],
                desc="(rank(vwap-ts_min(vwap,12))^ts_rank(corr(ts_rank(vwap,20),ts_rank(adv60,4),18),3))*-1")
def alpha_94(p: dict) -> pd.DataFrame:
    vwap, dv = p["vwap"], p["dv"]
    adv60 = adv(dv, 60)
    base = rank(vwap - ts_min(vwap, 12))
    exp_ = ts_rank(correlation(ts_rank(vwap, 20), ts_rank(adv60, 4), 18), 3)
    return (base ** exp_) * -1


@register_alpha(id=96, group="B", required=["close", "vwap", "volume", "dv"],
                desc="max(ts_rank(decay(corr(rank(vwap),rank(vol),4),4),8), ts_rank(decay(ts_argmax(corr(ts_rank(c,7),ts_rank(adv60,4),4),13),14),13))*-1")
def alpha_96(p: dict) -> pd.DataFrame:
    c, vwap, v, dv = p["close"], p["vwap"], p["volume"], p["dv"]
    adv60 = adv(dv, 60)
    part1 = ts_rank(decay_linear(correlation(rank(vwap), rank(v), 4), 4), 8)
    part2 = ts_rank(decay_linear(ts_argmax(correlation(ts_rank(c, 7), ts_rank(adv60, 4), 4), 13), 14), 13)
    return df_max(part1, part2) * -1


@register_alpha(id=98, group="B", required=["open", "vwap", "dv"],
                desc="rank(decay(corr(vwap,sum(adv5,26),5),7)) - rank(decay(ts_rank(ts_argmin(corr(rank(o),rank(adv15),21),9),7),8))")
def alpha_98(p: dict) -> pd.DataFrame:
    o, vwap, dv = p["open"], p["vwap"], p["dv"]
    adv5  = adv(dv, 5)
    adv15 = adv(dv, 15)
    part1 = rank(decay_linear(correlation(vwap, rolling_sum(adv5, 26), 5), 7))
    part2 = rank(decay_linear(ts_rank(ts_argmin(correlation(rank(o), rank(adv15), 21), 9), 7), 8))
    return part1 - part2


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP mac — Macro features (SPY / VIX / USGG10YR)
#  IDs 102–107  |  applicable = 'mac'  in DB
#  Broadcast one date-level value to all tickers (cross-section constant).
#  Requires SPY / VIX / USGG10YR rows present in panel["close"] columns.
# ═════════════════════════════════════════════════════════════════════════════

def _broadcast(series: pd.Series, ref: pd.DataFrame) -> pd.DataFrame:
    """Broadcast a date-indexed Series to the full panel shape (same index/columns as ref)."""
    aligned = series.reindex(ref.index)
    return pd.DataFrame(
        np.tile(aligned.values[:, None], (1, len(ref.columns))),
        index=ref.index,
        columns=ref.columns,
    )


def _rolling_z(s: pd.Series, w: int, min_periods: int = 4) -> pd.Series:
    mu = s.rolling(w, min_periods=min_periods).mean()
    sd = s.rolling(w, min_periods=min_periods).std().replace(0.0, np.nan)
    return (s - mu) / sd


@register_alpha(id=102, group="mac", required=["index"],
                desc="mac_SPY_ret: SPY 1-week return, broadcast to all tickers")
def alpha_102(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    spy = ix["SPY"].pct_change() if (ix is not None and "SPY" in ix.columns) else pd.Series(np.nan, index=c.index)
    return _broadcast(spy, c)


@register_alpha(id=103, group="mac", required=["index"],
                desc="mac_VIX: VIX close level, broadcast to all tickers")
def alpha_103(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    vix = ix["VIX"] if (ix is not None and "VIX" in ix.columns) else pd.Series(np.nan, index=c.index)
    return _broadcast(vix, c)


@register_alpha(id=104, group="mac", required=["index"],
                desc="mac_dUS10Y: 1-period diff of USGG10YR, broadcast to all tickers")
def alpha_104(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    us10y = ix["USGG10YR"] if (ix is not None and "USGG10YR" in ix.columns) else pd.Series(np.nan, index=c.index)
    return _broadcast(us10y.diff(), c)


@register_alpha(id=105, group="mac", required=["index"],
                desc="mac_SPY_ret_z: 12-week rolling z-score of SPY weekly return")
def alpha_105(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    spy = ix["SPY"].pct_change() if (ix is not None and "SPY" in ix.columns) else pd.Series(np.nan, index=c.index)
    return _broadcast(_rolling_z(spy, 12), c)


@register_alpha(id=106, group="mac", required=["index"],
                desc="mac_VIX_z: 12-week rolling z-score of VIX level")
def alpha_106(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    vix = ix["VIX"] if (ix is not None and "VIX" in ix.columns) else pd.Series(np.nan, index=c.index)
    return _broadcast(_rolling_z(vix, 12), c)


@register_alpha(id=107, group="mac", required=["index"],
                desc="mac_dUS10Y_z: 12-week rolling z-score of USGG10YR 1-period diff")
def alpha_107(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    us10y = ix["USGG10YR"] if (ix is not None and "USGG10YR" in ix.columns) else pd.Series(np.nan, index=c.index)
    return _broadcast(_rolling_z(us10y.diff(), 12), c)


# ═════════════════════════════════════════════════════════════════════════════
#  GROUP andy — Per-ticker derived factors
#  IDs 108–137  |  applicable = 'andy'  in DB
#  All rolling windows are right-aligned (no look-ahead).
#  Requires SPY rows in panel["close"] for rs_spy and corrspy families.
# ═════════════════════════════════════════════════════════════════════════════

def _corr_with_spy(
    close: pd.DataFrame,
    w: int,
    min_p: int,
    spy_ret: pd.Series | None = None,
) -> pd.DataFrame:
    ret1 = close.pct_change()
    if spy_ret is None:
        return pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    return -(ret1.rolling(w, min_periods=min_p).corr(spy_ret).abs())


# --- Momentum (raw pct return) ---

@register_alpha(id=108, group="andy", required=["close"],
                desc="ext_mom_r1w: 1-week price return")
def alpha_108(p: dict) -> pd.DataFrame:
    return p["close"].pct_change(1)


@register_alpha(id=109, group="andy", required=["close"],
                desc="ext_mom_r4w: 4-week price return")
def alpha_109(p: dict) -> pd.DataFrame:
    return p["close"].pct_change(4)


@register_alpha(id=110, group="andy", required=["close"],
                desc="ext_mom_r12w: 12-week price return")
def alpha_110(p: dict) -> pd.DataFrame:
    return p["close"].pct_change(12)


@register_alpha(id=111, group="andy", required=["close"],
                desc="ext_mom_r26w: 26-week price return")
def alpha_111(p: dict) -> pd.DataFrame:
    return p["close"].pct_change(26)


@register_alpha(id=112, group="andy", required=["close"],
                desc="ext_mom_r52w: 52-week price return")
def alpha_112(p: dict) -> pd.DataFrame:
    return p["close"].pct_change(52)


# --- Risk-adjusted momentum (return / rolling std) ---

@register_alpha(id=113, group="andy", required=["close"],
                desc="ext_rmom_r4w: 4-week return / rolling 4w weekly-return std")
def alpha_113(p: dict) -> pd.DataFrame:
    c = p["close"]
    sd = c.pct_change().rolling(4, min_periods=2).std().replace(0.0, np.nan)
    return c.pct_change(4) / sd


@register_alpha(id=114, group="andy", required=["close"],
                desc="ext_rmom_r12w: 12-week return / rolling 12w weekly-return std")
def alpha_114(p: dict) -> pd.DataFrame:
    c = p["close"]
    sd = c.pct_change().rolling(12, min_periods=4).std().replace(0.0, np.nan)
    return c.pct_change(12) / sd


@register_alpha(id=115, group="andy", required=["close"],
                desc="ext_rmom_r26w: 26-week return / rolling 26w weekly-return std")
def alpha_115(p: dict) -> pd.DataFrame:
    c = p["close"]
    sd = c.pct_change().rolling(26, min_periods=9).std().replace(0.0, np.nan)
    return c.pct_change(26) / sd


# --- Realised volatility (negated: low-vol premium) ---

@register_alpha(id=116, group="andy", required=["close"],
                desc="ext_vol_neg_12w: negative 12-week rolling std of weekly returns")
def alpha_116(p: dict) -> pd.DataFrame:
    return -p["close"].pct_change().rolling(12, min_periods=4).std()


@register_alpha(id=117, group="andy", required=["close"],
                desc="ext_vol_neg_26w: negative 26-week rolling std of weekly returns")
def alpha_117(p: dict) -> pd.DataFrame:
    return -p["close"].pct_change().rolling(26, min_periods=9).std()


@register_alpha(id=118, group="andy", required=["close"],
                desc="ext_vol_neg_52w: negative 52-week rolling std of weekly returns")
def alpha_118(p: dict) -> pd.DataFrame:
    return -p["close"].pct_change().rolling(52, min_periods=17).std()


# --- Log dollar volume (rolling mean) ---

@register_alpha(id=119, group="andy", required=["close", "volume"],
                desc="ext_dvol_log4w: 4-week rolling mean of log1p(close * volume)")
def alpha_119(p: dict) -> pd.DataFrame:
    ldv = np.log1p((p["close"] * p["volume"]).clip(lower=0))
    return ldv.rolling(4, min_periods=2).mean()


@register_alpha(id=120, group="andy", required=["close", "volume"],
                desc="ext_dvol_log12w: 12-week rolling mean of log1p(close * volume)")
def alpha_120(p: dict) -> pd.DataFrame:
    ldv = np.log1p((p["close"] * p["volume"]).clip(lower=0))
    return ldv.rolling(12, min_periods=4).mean()


@register_alpha(id=121, group="andy", required=["close", "volume"],
                desc="ext_dvol_log26w: 26-week rolling mean of log1p(close * volume)")
def alpha_121(p: dict) -> pd.DataFrame:
    ldv = np.log1p((p["close"] * p["volume"]).clip(lower=0))
    return ldv.rolling(26, min_periods=9).mean()


# --- Amihud illiquidity (negated) ---

@register_alpha(id=122, group="andy", required=["close", "volume"],
                desc="ext_amh_neg_4w: negative 4-week rolling mean Amihud ratio")
def alpha_122(p: dict) -> pd.DataFrame:
    dvol = (p["close"] * p["volume"]).replace(0.0, np.nan)
    amihud = p["close"].pct_change().abs() / dvol
    return -amihud.rolling(4, min_periods=2).mean()


@register_alpha(id=123, group="andy", required=["close", "volume"],
                desc="ext_amh_neg_12w: negative 12-week rolling mean Amihud ratio")
def alpha_123(p: dict) -> pd.DataFrame:
    dvol = (p["close"] * p["volume"]).replace(0.0, np.nan)
    amihud = p["close"].pct_change().abs() / dvol
    return -amihud.rolling(12, min_periods=4).mean()


@register_alpha(id=124, group="andy", required=["close", "volume"],
                desc="ext_amh_neg_26w: negative 26-week rolling mean Amihud ratio")
def alpha_124(p: dict) -> pd.DataFrame:
    dvol = (p["close"] * p["volume"]).replace(0.0, np.nan)
    amihud = p["close"].pct_change().abs() / dvol
    return -amihud.rolling(26, min_periods=9).mean()


# --- Distance from rolling high (drawdown-from-peak) ---

@register_alpha(id=125, group="andy", required=["close"],
                desc="ext_dd_12w: close / rolling_max(close, 12w) - 1")
def alpha_125(p: dict) -> pd.DataFrame:
    c = p["close"]
    return c / c.rolling(12, min_periods=4).max() - 1


@register_alpha(id=126, group="andy", required=["close"],
                desc="ext_dd_26w: close / rolling_max(close, 26w) - 1")
def alpha_126(p: dict) -> pd.DataFrame:
    c = p["close"]
    return c / c.rolling(26, min_periods=9).max() - 1


@register_alpha(id=127, group="andy", required=["close"],
                desc="ext_dd_52w: close / rolling_max(close, 52w) - 1")
def alpha_127(p: dict) -> pd.DataFrame:
    c = p["close"]
    return c / c.rolling(52, min_periods=17).max() - 1


# --- Distance from moving average ---

@register_alpha(id=128, group="andy", required=["close"],
                desc="ext_ma_4w: close / MA(4w) - 1")
def alpha_128(p: dict) -> pd.DataFrame:
    c = p["close"]
    return c / c.rolling(4, min_periods=2).mean() - 1


@register_alpha(id=129, group="andy", required=["close"],
                desc="ext_ma_12w: close / MA(12w) - 1")
def alpha_129(p: dict) -> pd.DataFrame:
    c = p["close"]
    return c / c.rolling(12, min_periods=4).mean() - 1


@register_alpha(id=130, group="andy", required=["close"],
                desc="ext_ma_52w: close / MA(52w) - 1")
def alpha_130(p: dict) -> pd.DataFrame:
    c = p["close"]
    return c / c.rolling(52, min_periods=17).mean() - 1


# --- Relative strength vs SPY ---

@register_alpha(id=131, group="andy", required=["close", "index"],
                desc="ext_rs_spy_r1w: ETF 1w return minus SPY 1w return")
def alpha_131(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    etf_ret = c.pct_change(1)
    if ix is None or "SPY" not in ix.columns:
        return etf_ret
    return etf_ret.sub(ix["SPY"].pct_change(1), axis=0)


@register_alpha(id=132, group="andy", required=["close", "index"],
                desc="ext_rs_spy_r4w: ETF 4w return minus SPY 4w return")
def alpha_132(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    etf_ret = c.pct_change(4)
    if ix is None or "SPY" not in ix.columns:
        return etf_ret
    return etf_ret.sub(ix["SPY"].pct_change(4), axis=0)


@register_alpha(id=133, group="andy", required=["close", "index"],
                desc="ext_rs_spy_r12w: ETF 12w return minus SPY 12w return")
def alpha_133(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    etf_ret = c.pct_change(12)
    if ix is None or "SPY" not in ix.columns:
        return etf_ret
    return etf_ret.sub(ix["SPY"].pct_change(12), axis=0)


@register_alpha(id=134, group="andy", required=["close", "index"],
                desc="ext_rs_spy_r26w: ETF 26w return minus SPY 26w return")
def alpha_134(p: dict) -> pd.DataFrame:
    c = p["close"]
    ix = p.get("index")
    etf_ret = c.pct_change(26)
    if ix is None or "SPY" not in ix.columns:
        return etf_ret
    return etf_ret.sub(ix["SPY"].pct_change(26), axis=0)


# --- Negated rolling |corr| with SPY (diversification factor) ---

@register_alpha(id=135, group="andy", required=["close", "index"],
                desc="ext_corrspy_neg_12w: negative |12w rolling corr of weekly returns with SPY|")
def alpha_135(p: dict) -> pd.DataFrame:
    ix = p.get("index")
    spy_ret = ix["SPY"].pct_change() if (ix is not None and "SPY" in ix.columns) else None
    return _corr_with_spy(p["close"], 12, 4, spy_ret)


@register_alpha(id=136, group="andy", required=["close", "index"],
                desc="ext_corrspy_neg_26w: negative |26w rolling corr of weekly returns with SPY|")
def alpha_136(p: dict) -> pd.DataFrame:
    ix = p.get("index")
    spy_ret = ix["SPY"].pct_change() if (ix is not None and "SPY" in ix.columns) else None
    return _corr_with_spy(p["close"], 26, 9, spy_ret)


@register_alpha(id=137, group="andy", required=["close", "index"],
                desc="ext_corrspy_neg_52w: negative |52w rolling corr of weekly returns with SPY|")
def alpha_137(p: dict) -> pd.DataFrame:
    ix = p.get("index")
    spy_ret = ix["SPY"].pct_change() if (ix is not None and "SPY" in ix.columns) else None
    return _corr_with_spy(p["close"], 52, 17, spy_ret)

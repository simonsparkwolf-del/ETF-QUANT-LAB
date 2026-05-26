from __future__ import annotations

import numpy as np
import pandas as pd

from config import (
    SECTOR_ETFS, SPY_TICKER, MACRO_ROLL_WEEKS,
    DEFENSIVES_BUCKET, CYCLICALS_BUCKET,
    RATE_SENSITIVES_BUCKET, TECH_GROWTH_BUCKET,
)

BASE_FEATURES = [
    'f_ret_4w', 'f_ret_12w', 'f_mom_12_1', 'f_ret_1w',
    'f_vol_12w', 'f_dd_52w', 'f_rs_spy_12w',
    'f_beta_spy_26w', 'f_dvol_log_z12w', 'f_ma_dist_12w',
]
DAILY_FEATURES = [
    'd_rv_60d', 'd_skew_60d', 'd_up_ratio_60d', 'd_idio_vol_60d',
]
DISPERSION_FEATURES = [
    'x_disp4w_mom12w',
]
MACRO_FEATURES = [
    'm_defensive_x_VIXz', 'm_cyclical_x_VIXz',
    'm_ratesens_x_dUS10Yz', 'm_techgrowth_x_dUS10Yz',
]
ALL_FEATURES = BASE_FEATURES + DAILY_FEATURES + DISPERSION_FEATURES + MACRO_FEATURES

SIGN_FLIPS = {
    'f_ret_1w':                  -1.0,
    'f_vol_12w':                 -1.0,
    'd_rv_60d':                  -1.0,
    'd_idio_vol_60d':            -1.0,
    'm_cyclical_x_VIXz':         -1.0,
    'm_ratesens_x_dUS10Yz':      -1.0,
    'm_techgrowth_x_dUS10Yz':    -1.0,
}
SIGN_CONSTRAINED_FEATURES = [
    'f_ret_4w', 'f_ret_12w', 'f_mom_12_1', 'f_ret_1w',
    'f_vol_12w', 'f_dd_52w', 'f_rs_spy_12w', 'f_ma_dist_12w',
    'd_rv_60d', 'd_skew_60d', 'd_up_ratio_60d', 'd_idio_vol_60d',
    'x_disp4w_mom12w',
    'm_defensive_x_VIXz', 'm_cyclical_x_VIXz',
    'm_ratesens_x_dUS10Yz', 'm_techgrowth_x_dUS10Yz',
]


def _wide_to_long(wide: pd.DataFrame, name: str) -> pd.DataFrame:
    out = wide[SECTOR_ETFS].stack().rename(name).reset_index()
    out.columns = ['date', 'ticker', name]
    return out


def build_base_features(close: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    sec_close = close[SECTOR_ETFS]
    spy_close = close[SPY_TICKER]

    ret_1w  = sec_close.pct_change(1)
    ret_4w  = sec_close.pct_change(4)
    ret_12w = sec_close.pct_change(12)
    spy_ret_12w = spy_close.pct_change(12)

    mom_12_1 = sec_close.shift(1) / sec_close.shift(12) - 1.0

    vol_12w = ret_1w.rolling(12).std()

    dd_52w = sec_close / sec_close.rolling(52, min_periods=20).max() - 1.0

    rs_spy_12w = ret_12w.sub(spy_ret_12w, axis=0)

    spy_ret_1w = spy_close.pct_change(1)
    spy_var_26w = spy_ret_1w.rolling(26).var()
    beta = {}
    for t in SECTOR_ETFS:
        cov = ret_1w[t].rolling(26).cov(spy_ret_1w)
        beta[t] = cov / spy_var_26w
    beta = pd.DataFrame(beta)

    dvol = (sec_close * volume[SECTOR_ETFS]).replace(0, np.nan)
    log_dvol_12w = np.log(dvol).rolling(12).mean()
    mu = log_dvol_12w.mean(axis=1)
    sd = log_dvol_12w.std(axis=1).replace(0, np.nan)
    dvol_z = log_dvol_12w.sub(mu, axis=0).div(sd, axis=0)

    ma_dist_12w = sec_close / sec_close.rolling(12).mean() - 1.0

    parts = {
        'f_ret_4w'      : ret_4w,
        'f_ret_12w'     : ret_12w,
        'f_mom_12_1'    : mom_12_1,
        'f_ret_1w'      : ret_1w,
        'f_vol_12w'     : vol_12w,
        'f_dd_52w'      : dd_52w,
        'f_rs_spy_12w'  : rs_spy_12w,
        'f_beta_spy_26w': beta,
        'f_dvol_log_z12w': dvol_z,
        'f_ma_dist_12w' : ma_dist_12w,
    }
    long = None
    for name, wide in parts.items():
        ll = _wide_to_long(wide, name)
        long = ll if long is None else long.merge(ll, on=['date','ticker'], how='outer')
    return long


def build_daily_features(daily_close: pd.DataFrame,
                         weekly_dates: pd.DatetimeIndex,
                         window: int = 60) -> pd.DataFrame:
    """Compute daily-frequency features then sample at Wednesday cadence.
    Holiday-Wednesdays use the previous trading day's value (ffill).

    Features:
      d_rv_60d        : 60-day realized vol of daily close-to-close returns
      d_skew_60d      : 60-day skew of daily returns
      d_up_ratio_60d  : fraction of up days in last 60 trading days
      d_idio_vol_60d  : 60-day std of residual from r_i = beta * r_SPY
    """
    sec_d = daily_close[SECTOR_ETFS]
    spy_d = daily_close[SPY_TICKER]
    ret_d = sec_d.pct_change()
    spy_ret_d = spy_d.pct_change()

    rv = ret_d.rolling(window).std()
    sk = ret_d.rolling(window).skew()
    up = (ret_d > 0).astype(float).rolling(window).mean()

    spy_var = spy_ret_d.rolling(window).var()
    idio = {}
    for t in SECTOR_ETFS:
        cov = ret_d[t].rolling(window).cov(spy_ret_d)
        beta = cov / spy_var
        resid = ret_d[t] - beta * spy_ret_d
        idio[t] = resid.rolling(window).std()
    idio = pd.DataFrame(idio)

    parts = {
        'd_rv_60d':       rv,
        'd_skew_60d':     sk,
        'd_up_ratio_60d': up,
        'd_idio_vol_60d': idio,
    }
    sampled = {name: wide.reindex(weekly_dates, method='ffill')
               for name, wide in parts.items()}

    long = None
    for name, wide in sampled.items():
        ll = _wide_to_long(wide, name)
        long = ll if long is None else long.merge(ll, on=['date','ticker'], how='outer')
    return long


def build_dispersion_features(close: pd.DataFrame,
                              ret_12w_long: pd.DataFrame | None = None) -> pd.DataFrame:
    """Cross-sectional dispersion of past 4-week returns across the 11 sectors.
    Returned long with one row per (date, ticker); dispersion is constant
    across tickers within a date. Also returns the interaction
    `x_disp4w_mom12w = dispersion_4w * f_ret_12w` for use as a feature.
    """
    sec_close = close[SECTOR_ETFS]
    ret_4w = sec_close.pct_change(4)
    disp_4w = ret_4w.std(axis=1)
    ret_12w = sec_close.pct_change(12)

    rows = []
    for d in sec_close.index:
        for t in SECTOR_ETFS:
            r12 = ret_12w.at[d, t] if d in ret_12w.index else float('nan')
            rows.append((d, t, disp_4w.get(d, float('nan')), r12))
    df = pd.DataFrame(rows, columns=['date','ticker','disp_4w','_ret_12w_tmp'])
    df['x_disp4w_mom12w'] = df['disp_4w'] * df['_ret_12w_tmp']
    return df[['date','ticker','x_disp4w_mom12w']]


def build_macro_features(macro_weekly: pd.DataFrame) -> pd.DataFrame:
    """Return per-date macro z-scores (12-week rolling)."""
    w = MACRO_ROLL_WEEKS
    df = macro_weekly.copy()
    out = pd.DataFrame(index=df.index)
    for col in ['SPY_ret', 'VIX', 'dUS10Y']:
        if col not in df.columns:
            continue
        s = df[col]
        mu = s.rolling(w, min_periods=4).mean()
        sd = s.rolling(w, min_periods=4).std().replace(0, np.nan)
        out[col + '_z'] = (s - mu) / sd
    out = out.reset_index().rename(columns={'index': 'date', out.index.name or 'date': 'date'})
    return out


def attach_macro_interactions(features_long: pd.DataFrame,
                              macro_z: pd.DataFrame) -> pd.DataFrame:
    """Add 4 macro-bucket interaction columns to the long feature panel."""
    df = features_long.merge(macro_z, on='date', how='left')

    def in_set(s):
        return df['ticker'].isin(s).astype(float)

    vix_z = df.get('VIX_z', pd.Series(0.0, index=df.index)).fillna(0.0)
    d10_z = df.get('dUS10Y_z', pd.Series(0.0, index=df.index)).fillna(0.0)

    df['m_defensive_x_VIXz']     = in_set(DEFENSIVES_BUCKET)      * vix_z
    df['m_cyclical_x_VIXz']      = in_set(CYCLICALS_BUCKET)       * vix_z
    df['m_ratesens_x_dUS10Yz']   = in_set(RATE_SENSITIVES_BUCKET) * d10_z
    df['m_techgrowth_x_dUS10Yz'] = in_set(TECH_GROWTH_BUCKET)     * d10_z

    drop_cols = [c for c in ['SPY_ret_z', 'VIX_z', 'dUS10Y_z'] if c in df.columns]
    return df.drop(columns=drop_cols)


def apply_sign_flips(df: pd.DataFrame, flips: dict[str, float] = SIGN_FLIPS) -> pd.DataFrame:
    """Multiply listed columns by -1 so their economic sign aligns with the
    expected positive coefficient under a sign-constrained model."""
    out = df.copy()
    for col, mult in flips.items():
        if col in out.columns:
            out[col] = out[col] * mult
    return out


def per_date_zscore(df: pd.DataFrame, cols: list[str],
                    winsor: tuple[float, float] = (0.05, 0.95)) -> pd.DataFrame:
    out = df.copy()
    for d, idx in out.groupby('date').groups.items():
        b = out.loc[idx, cols].copy()
        b = b.apply(lambda c: c.fillna(c.median()), axis=0)
        lo = b.quantile(winsor[0])
        hi = b.quantile(winsor[1])
        b = b.clip(lower=lo, upper=hi, axis=1)
        mu = b.mean()
        sd = b.std().replace(0, 1.0)
        b = (b - mu) / sd
        out.loc[idx, cols] = b.values
    out[cols] = out[cols].fillna(0.0)
    return out

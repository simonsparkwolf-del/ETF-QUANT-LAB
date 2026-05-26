"""
daily_features.py — daily-cadence panel for the new ML pipeline.

Each row = (trading_day, ticker). Target = 5-trading-day forward excess return
over SPY (i.e., the daily-frequency analog of `frs_4`; same 1-week horizon,
just measurable on any trading day).

Features (45 columns total) are documented inline. All are economically
motivated. No statistical pre-selection — penalised / regularised models
handle correlation among them.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import SECTOR_ETFS, SPY_TICKER


# ----------------------------------------------------------------------------
# Feature group manifest (for reporting and downstream selection).
# ----------------------------------------------------------------------------
MOMENTUM_FEATURES = ['ret_5d', 'ret_20d', 'ret_60d', 'ret_120d', 'mom_240_20']
REVERSAL_FEATURES = ['ret_1d']
VOL_FEATURES      = ['vol_20d', 'vol_60d', 'vol_ratio_20_60', 'skew_60d']
TREND_FEATURES    = ['ma_dist_20d', 'ma_dist_60d', 'dd_252d']
LIQUIDITY_FEATURES = ['log_dvol_60d', 'dvol_z_60d']
SPY_REL_FEATURES  = ['rs_spy_20d', 'rs_spy_60d', 'beta_60d', 'idio_vol_60d']
DISPERSION_FEATURES = ['disp_5d', 'disp_20d', 'disp_60d']
MACRO_FEATURES    = ['spy_ret_20d', 'spy_vol_60d', 'spy_dd_252d',
                     'vix_level', 'vix_z_60d', 'd_vix_20d',
                     'ust10y_level', 'd_ust10y_20d', 'ust10y_z_60d']

FRED_FEATURES = [
    # Yield curve slope (10Y - 2Y)
    't10y2y_level', 't10y2y_z_60d', 't10y2y_d_20d',
    # HY credit spread (starts 2023-05-22 -> NaN before that filled with 0)
    'hyoas_level', 'hyoas_z_60d', 'hyoas_d_20d',
    # USD broad index
    'usd_ret_20d', 'usd_vol_60d',
    # WTI crude
    'crude_ret_20d', 'crude_ret_60d',
    # 10Y breakeven inflation (z_60d added for parity with T10Y2Y / HY OAS)
    'be10y_level', 'be10y_z_60d', 'be10y_d_20d',
]
SECTOR_DUMMY_FEATURES = [f'is_{t}' for t in SECTOR_ETFS]
INTERACTION_FEATURES = [
    # Original it1 interactions
    'inter_vixz_x_mom60d',
    'inter_dust10y_x_beta60d',
    'inter_disp20_x_mom60d',
    # FRED x feature-type interactions (it2 parity with it1 style)
    'inter_t10y2yz_x_beta60d',
    'inter_hyoasz_x_mom60d',
    'inter_crude60_x_disp20',
    'inter_be10yz_x_beta60d',
    'inter_usd20_x_mom60d',
]

ALL_FEATURES = (
    MOMENTUM_FEATURES + REVERSAL_FEATURES + VOL_FEATURES + TREND_FEATURES
    + LIQUIDITY_FEATURES + SPY_REL_FEATURES + DISPERSION_FEATURES
    + MACRO_FEATURES + FRED_FEATURES
    + SECTOR_DUMMY_FEATURES + INTERACTION_FEATURES
)


def _wide_to_long(wide: pd.DataFrame, name: str) -> pd.DataFrame:
    out = wide[SECTOR_ETFS].stack(dropna=False).rename(name).reset_index()
    out.columns = ['date', 'ticker', name]
    return out


def _date_series_to_long(series: pd.Series, name: str) -> pd.DataFrame:
    """Broadcast a date-indexed Series to all 11 tickers."""
    rows = []
    for d, v in series.items():
        for t in SECTOR_ETFS:
            rows.append((d, t, v))
    return pd.DataFrame(rows, columns=['date', 'ticker', name])


def build_fred_features(fred_wide: pd.DataFrame,
                        target_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Compute 12 FRED-derived macro features at daily cadence, aligned to
    `target_index` (the trading-day calendar of our sector panel).

    Forward-fills the FRED series onto trading days before computing
    rolling stats. BAMLH0A0HYM2 NaNs before 2023-05-22 are left as NaN
    here; the build_daily_panel step fills them with 0 along with other
    leading-edge NaNs.

    Returns a date-indexed DataFrame with 12 columns.
    """
    aligned = fred_wide.reindex(target_index, method='ffill')

    out = pd.DataFrame(index=target_index)

    if 'T10Y2Y' in aligned.columns:
        s = aligned['T10Y2Y']
        mu = s.rolling(60, min_periods=20).mean()
        sd = s.rolling(60, min_periods=20).std().replace(0, np.nan)
        out['t10y2y_level'] = s
        out['t10y2y_z_60d'] = (s - mu) / sd
        out['t10y2y_d_20d'] = s.diff(20)

    if 'BAMLH0A0HYM2' in aligned.columns:
        s = aligned['BAMLH0A0HYM2']
        mu = s.rolling(60, min_periods=20).mean()
        sd = s.rolling(60, min_periods=20).std().replace(0, np.nan)
        out['hyoas_level'] = s
        out['hyoas_z_60d'] = (s - mu) / sd
        out['hyoas_d_20d'] = s.diff(20)

    if 'DTWEXBGS' in aligned.columns:
        s = aligned['DTWEXBGS']
        out['usd_ret_20d'] = s.pct_change(20)
        out['usd_vol_60d'] = s.pct_change().rolling(60).std()

    if 'DCOILWTICO' in aligned.columns:
        s = aligned['DCOILWTICO']
        out['crude_ret_20d'] = s.pct_change(20)
        out['crude_ret_60d'] = s.pct_change(60)

    if 'T10YIE' in aligned.columns:
        s = aligned['T10YIE']
        mu = s.rolling(60, min_periods=20).mean()
        sd = s.rolling(60, min_periods=20).std().replace(0, np.nan)
        out['be10y_level'] = s
        out['be10y_z_60d'] = (s - mu) / sd
        out['be10y_d_20d'] = s.diff(20)

    return out


def build_daily_panel(daily_close: pd.DataFrame,
                      daily_volume: pd.DataFrame,
                      daily_macro: pd.DataFrame,
                      fred_wide: pd.DataFrame | None = None,
                      target_fwd_days: int = 5) -> pd.DataFrame:
    """Construct the full daily long panel: (date, ticker) x features + target.

    Returns a long DataFrame with columns:
      date, ticker, y_5d_excess (target), <ALL_FEATURES>
    """
    sec_close = daily_close[SECTOR_ETFS]
    spy_close = daily_close[SPY_TICKER]

    ret_1d   = sec_close.pct_change()
    ret_5d   = sec_close.pct_change(5)
    ret_20d  = sec_close.pct_change(20)
    ret_60d  = sec_close.pct_change(60)
    ret_120d = sec_close.pct_change(120)
    mom_240_20 = sec_close.shift(20) / sec_close.shift(240) - 1.0

    vol_20d = ret_1d.rolling(20).std()
    vol_60d = ret_1d.rolling(60).std()
    vol_ratio_20_60 = vol_20d / vol_60d
    skew_60d = ret_1d.rolling(60).skew()

    ma_dist_20d = sec_close / sec_close.rolling(20).mean() - 1.0
    ma_dist_60d = sec_close / sec_close.rolling(60).mean() - 1.0
    dd_252d     = sec_close / sec_close.rolling(252, min_periods=60).max() - 1.0

    dvol = (sec_close * daily_volume[SECTOR_ETFS]).replace(0, np.nan)
    log_dvol_60d = np.log(dvol).rolling(60).mean()
    mu = log_dvol_60d.rolling(252, min_periods=60).mean()
    sd = log_dvol_60d.rolling(252, min_periods=60).std().replace(0, np.nan)
    dvol_z_60d = (log_dvol_60d - mu) / sd

    spy_ret_1d  = spy_close.pct_change()
    spy_ret_20d = spy_close.pct_change(20)
    spy_ret_60d = spy_close.pct_change(60)

    rs_spy_20d = ret_20d.sub(spy_ret_20d, axis=0)
    rs_spy_60d = ret_60d.sub(spy_ret_60d, axis=0)

    spy_var_60d = spy_ret_1d.rolling(60).var()
    beta_60d_dict, idio_vol_60d_dict = {}, {}
    for t in SECTOR_ETFS:
        cov_t = ret_1d[t].rolling(60).cov(spy_ret_1d)
        bt = cov_t / spy_var_60d
        beta_60d_dict[t] = bt
        resid = ret_1d[t] - bt * spy_ret_1d
        idio_vol_60d_dict[t] = resid.rolling(60).std()
    beta_60d     = pd.DataFrame(beta_60d_dict)
    idio_vol_60d = pd.DataFrame(idio_vol_60d_dict)

    disp_5d  = ret_5d.std(axis=1)
    disp_20d = ret_20d.std(axis=1)
    disp_60d = ret_60d.std(axis=1)

    spy_vol_60d = spy_ret_1d.rolling(60).std()
    spy_dd_252d = spy_close / spy_close.rolling(252, min_periods=60).max() - 1.0
    vix_level   = daily_macro['VIX']
    vix_mu      = vix_level.rolling(60).mean()
    vix_sd      = vix_level.rolling(60).std().replace(0, np.nan)
    vix_z_60d   = (vix_level - vix_mu) / vix_sd
    d_vix_20d   = vix_level.diff(20)
    ust10y_level = daily_macro['USGG10YR']
    ust10y_mu = ust10y_level.rolling(60).mean()
    ust10y_sd = ust10y_level.rolling(60).std().replace(0, np.nan)
    ust10y_z_60d = (ust10y_level - ust10y_mu) / ust10y_sd
    d_ust10y_20d = ust10y_level.diff(20)

    fwd_ret = sec_close.pct_change(target_fwd_days).shift(-target_fwd_days)
    spy_fwd = spy_close.pct_change(target_fwd_days).shift(-target_fwd_days)
    y_5d_excess = fwd_ret.sub(spy_fwd, axis=0)

    fwd_ret_20 = sec_close.pct_change(20).shift(-20)
    spy_fwd_20 = spy_close.pct_change(20).shift(-20)
    y_20d_excess = fwd_ret_20.sub(spy_fwd_20, axis=0)

    per_ticker = {
        'ret_1d': ret_1d, 'ret_5d': ret_5d, 'ret_20d': ret_20d, 'ret_60d': ret_60d,
        'ret_120d': ret_120d, 'mom_240_20': mom_240_20,
        'vol_20d': vol_20d, 'vol_60d': vol_60d, 'vol_ratio_20_60': vol_ratio_20_60,
        'skew_60d': skew_60d,
        'ma_dist_20d': ma_dist_20d, 'ma_dist_60d': ma_dist_60d, 'dd_252d': dd_252d,
        'log_dvol_60d': log_dvol_60d, 'dvol_z_60d': dvol_z_60d,
        'rs_spy_20d': rs_spy_20d, 'rs_spy_60d': rs_spy_60d,
        'beta_60d': beta_60d, 'idio_vol_60d': idio_vol_60d,
        'y_5d_excess': y_5d_excess,
        'y_20d_excess': y_20d_excess,
    }
    date_level = {
        'disp_5d': disp_5d, 'disp_20d': disp_20d, 'disp_60d': disp_60d,
        'spy_ret_20d': spy_ret_20d, 'spy_vol_60d': spy_vol_60d, 'spy_dd_252d': spy_dd_252d,
        'vix_level': vix_level, 'vix_z_60d': vix_z_60d, 'd_vix_20d': d_vix_20d,
        'ust10y_level': ust10y_level, 'd_ust10y_20d': d_ust10y_20d, 'ust10y_z_60d': ust10y_z_60d,
    }

    long = None
    for name, wide in per_ticker.items():
        ll = _wide_to_long(wide, name)
        long = ll if long is None else long.merge(ll, on=['date', 'ticker'], how='outer')
    for name, series in date_level.items():
        ll = _date_series_to_long(series, name)
        long = long.merge(ll, on=['date', 'ticker'], how='left')

    if fred_wide is not None and not fred_wide.empty:
        fred_feat = build_fred_features(fred_wide, daily_close.index)
        for name in fred_feat.columns:
            ll = _date_series_to_long(fred_feat[name], name)
            long = long.merge(ll, on=['date', 'ticker'], how='left')
        for col in FRED_FEATURES:
            if col in long.columns:
                long[col] = long[col].fillna(0.0)

    for t in SECTOR_ETFS:
        long[f'is_{t}'] = (long['ticker'] == t).astype(float)

    long['inter_vixz_x_mom60d']    = long['vix_z_60d'] * long['ret_60d']
    long['inter_dust10y_x_beta60d'] = long['d_ust10y_20d'] * long['beta_60d']
    long['inter_disp20_x_mom60d']  = long['disp_20d'] * long['ret_60d']

    # FRED x feature-type interactions (it2 parity with it1 style).
    # Each pairs a macro signal with a feature type (beta/momentum/dispersion)
    # whose response is economically motivated by that macro regime.
    if 't10y2y_z_60d' in long.columns:
        long['inter_t10y2yz_x_beta60d'] = long['t10y2y_z_60d'] * long['beta_60d']
    if 'hyoas_z_60d' in long.columns:
        long['inter_hyoasz_x_mom60d']   = long['hyoas_z_60d']  * long['ret_60d']
    if 'crude_ret_60d' in long.columns:
        long['inter_crude60_x_disp20']  = long['crude_ret_60d'] * long['disp_20d']
    if 'be10y_z_60d' in long.columns:
        long['inter_be10yz_x_beta60d']  = long['be10y_z_60d']  * long['beta_60d']
    if 'usd_ret_20d' in long.columns:
        long['inter_usd20_x_mom60d']    = long['usd_ret_20d']  * long['ret_60d']

    long = long.sort_values(['date', 'ticker']).reset_index(drop=True)
    return long

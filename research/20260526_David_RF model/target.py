from __future__ import annotations

import pandas as pd

from config import SECTOR_ETFS, SPY_TICKER


def compute_frs_4(close: pd.DataFrame) -> pd.DataFrame:
    """1-week FORWARD excess return over SPY for each sector ETF.

    At Wednesday t, frs_4(t) uses close at t+1 week. Adjacent Wednesdays'
    labels cover disjoint future windows (0% overlap).
    """
    fwd_ret = close.pct_change().shift(-1)
    spy_fwd = fwd_ret[SPY_TICKER]
    return fwd_ret[SECTOR_ETFS].sub(spy_fwd, axis=0)


def compute_h_step_frs(close: pd.DataFrame, h: int) -> pd.DataFrame:
    """h-week forward excess return over SPY (h=1 reduces to frs_4)."""
    fwd_ret = close.pct_change(h).shift(-h)
    spy_fwd = fwd_ret[SPY_TICKER]
    return fwd_ret[SECTOR_ETFS].sub(spy_fwd, axis=0)


def rank_zscore_within_week(y_long: pd.DataFrame, y_col: str = 'y') -> pd.DataFrame:
    """Replace y in-place with cross-sectional rank-z within each date.
    Ranks 1..N are computed per (date), then z-scored. Equivalent in spirit to
    optimising Spearman IC under MSE loss.
    """
    out = y_long.copy()

    def _rz(s: pd.Series) -> pd.Series:
        r = s.rank(method='average')
        if r.std() == 0 or r.notna().sum() < 2:
            return r * 0.0
        return (r - r.mean()) / r.std(ddof=0)

    out[y_col] = out.groupby('date')[y_col].transform(_rz)
    return out

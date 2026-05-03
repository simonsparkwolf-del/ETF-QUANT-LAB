"""
operators.py — vectorised implementations of all functions defined in
Kakushadze (2015), Appendix A.1 (Functions and Operators).

Every function accepts and returns a pandas DataFrame of shape
(dates × tickers).  Rolling windows use minimum-periods = 1 unless
stated otherwise so early rows are filled where data permits.

Non-integer window arguments are silently floor()'d, following the paper.
"""

import numpy as np
import pandas as pd


# ── helpers ──────────────────────────────────────────────────────────────────

def _w(d: float) -> int:
    """Floor a potentially-fractional window argument."""
    return max(1, int(d))


# ── standard math ─────────────────────────────────────────────────────────────

def abs_val(x: pd.DataFrame) -> pd.DataFrame:
    return x.abs()


def log(x: pd.DataFrame) -> pd.DataFrame:
    """Natural log; guard against non-positive values."""
    return np.log(x.abs().clip(lower=1e-9))


def sign(x: pd.DataFrame) -> pd.DataFrame:
    return np.sign(x)


def signedpower(x: pd.DataFrame, a: float) -> pd.DataFrame:
    """sign(x) * |x|^a  (preserves sign for odd integer a)."""
    return np.sign(x) * (x.abs() ** a)


# ── cross-sectional operators ─────────────────────────────────────────────────

def rank(x: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional percentile rank within each row (0 < rank ≤ 1)."""
    return x.rank(axis=1, pct=True, na_option="keep")


def scale(x: pd.DataFrame, a: float = 1.0) -> pd.DataFrame:
    """Rescale each row so that sum(|x|) == a."""
    row_abs_sum = x.abs().sum(axis=1).replace(0, np.nan)
    return x.div(row_abs_sum, axis=0).mul(a)


# ── time-series operators ─────────────────────────────────────────────────────

def delay(x: pd.DataFrame, d: float) -> pd.DataFrame:
    return x.shift(_w(d))


def delta(x: pd.DataFrame, d: float) -> pd.DataFrame:
    d = _w(d)
    return x - x.shift(d)


def correlation(x: pd.DataFrame, y: pd.DataFrame, d: float) -> pd.DataFrame:
    """Rolling time-series Pearson correlation, column by column.
    Inf values (zero-variance windows) are replaced with NaN."""
    d = _w(d)
    result = pd.DataFrame(np.nan, index=x.index, columns=x.columns)
    for col in x.columns:
        r = x[col].rolling(d, min_periods=max(2, d // 2)).corr(y[col])
        result[col] = r.replace([np.inf, -np.inf], np.nan)
    return result


def covariance(x: pd.DataFrame, y: pd.DataFrame, d: float) -> pd.DataFrame:
    """Rolling time-series covariance, column by column."""
    d = _w(d)
    result = pd.DataFrame(np.nan, index=x.index, columns=x.columns)
    for col in x.columns:
        result[col] = x[col].rolling(d, min_periods=max(2, d // 2)).cov(y[col])
    return result


def stddev(x: pd.DataFrame, d: float) -> pd.DataFrame:
    d = _w(d)
    return x.rolling(d, min_periods=max(2, d // 2)).std()


def rolling_sum(x: pd.DataFrame, d: float) -> pd.DataFrame:
    d = _w(d)
    return x.rolling(d, min_periods=1).sum()


def product(x: pd.DataFrame, d: float) -> pd.DataFrame:
    d = _w(d)
    return x.rolling(d, min_periods=1).apply(np.prod, raw=True)


def ts_min(x: pd.DataFrame, d: float) -> pd.DataFrame:
    d = _w(d)
    return x.rolling(d, min_periods=1).min()


def ts_max(x: pd.DataFrame, d: float) -> pd.DataFrame:
    d = _w(d)
    return x.rolling(d, min_periods=1).max()


def ts_argmax(x: pd.DataFrame, d: float) -> pd.DataFrame:
    """Index (0-based, oldest=0) of the maximum within the rolling window."""
    d = _w(d)
    return x.rolling(d, min_periods=1).apply(np.argmax, raw=True)


def ts_argmin(x: pd.DataFrame, d: float) -> pd.DataFrame:
    d = _w(d)
    return x.rolling(d, min_periods=1).apply(np.argmin, raw=True)


def ts_rank(x: pd.DataFrame, d: float) -> pd.DataFrame:
    """Percentile rank of the most-recent value within the rolling window."""
    d = _w(d)

    def _pct_rank(arr):
        if len(arr) == 0:
            return np.nan
        return (arr[-1] >= arr).mean()

    return x.rolling(d, min_periods=1).apply(_pct_rank, raw=True)


def decay_linear(x: pd.DataFrame, d: float) -> pd.DataFrame:
    """Weighted moving average with linearly decaying weights (d, d-1, …, 1)."""
    d = _w(d)
    raw_weights = np.arange(1, d + 1, dtype=float)
    weights = raw_weights / raw_weights.sum()

    def _wma(arr):
        n = len(arr)
        w = weights[-n:]
        w = w / w.sum()
        return np.dot(arr, w)

    return x.rolling(d, min_periods=1).apply(_wma, raw=True)


# ── element-wise min/max across two DataFrames ────────────────────────────────

def df_min(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        np.minimum(a.values, b.values), index=a.index, columns=a.columns
    )


def df_max(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        np.maximum(a.values, b.values), index=a.index, columns=a.columns
    )


# ── adv helper ────────────────────────────────────────────────────────────────

def adv(dollar_volume: pd.DataFrame, d: float) -> pd.DataFrame:
    """Average daily dollar volume over past d days."""
    d = _w(d)
    return dollar_volume.rolling(d, min_periods=1).mean()

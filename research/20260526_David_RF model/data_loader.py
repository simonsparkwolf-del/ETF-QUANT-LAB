from __future__ import annotations

import sqlite3
import pandas as pd

from config import DB, SECTOR_ETFS, SPY_TICKER, VIX_TICKER, UST10Y_TICKER


def _load_wide(conn: sqlite3.Connection, table: str, tickers: list[str], col: str) -> pd.DataFrame:
    ph = ",".join("?" * len(tickers))
    sql = f"SELECT date, ticker, {col} FROM {table} WHERE ticker IN ({ph}) ORDER BY date, ticker"
    df = pd.read_sql_query(sql, conn, params=tickers)
    df['date'] = pd.to_datetime(df['date'])
    return df.pivot(index='date', columns='ticker', values=col).sort_index()


def load_weekly_close() -> pd.DataFrame:
    with sqlite3.connect(str(DB)) as conn:
        return _load_wide(conn, 'weekly_bar', SECTOR_ETFS + [SPY_TICKER], 'close')


def load_weekly_volume() -> pd.DataFrame:
    with sqlite3.connect(str(DB)) as conn:
        return _load_wide(conn, 'weekly_bar', SECTOR_ETFS, 'volume')


def load_daily_close() -> pd.DataFrame:
    with sqlite3.connect(str(DB)) as conn:
        return _load_wide(conn, 'daily_bar', SECTOR_ETFS + [SPY_TICKER], 'close')


def load_daily_volume() -> pd.DataFrame:
    with sqlite3.connect(str(DB)) as conn:
        return _load_wide(conn, 'daily_bar', SECTOR_ETFS, 'volume')


def load_daily_macro() -> pd.DataFrame:
    """Return daily date-indexed DataFrame with columns [VIX, USGG10YR, SPY_close]."""
    with sqlite3.connect(str(DB)) as conn:
        spy = _load_wide(conn, 'daily_bar', [SPY_TICKER], 'close')[SPY_TICKER]
        vix = _load_wide(conn, 'daily_bar', [VIX_TICKER], 'close')[VIX_TICKER]
        us10 = _load_wide(conn, 'daily_bar', [UST10Y_TICKER], 'close')[UST10Y_TICKER]
    return pd.DataFrame({'VIX': vix, 'USGG10YR': us10, 'SPY_close': spy})


def load_macro_weekly() -> pd.DataFrame:
    """Return weekly date-indexed DataFrame with columns [SPY_ret, VIX, dUS10Y]
    aligned to the weekly_bar Wednesday calendar."""
    with sqlite3.connect(str(DB)) as conn:
        spy = _load_wide(conn, 'weekly_bar', [SPY_TICKER], 'close')[SPY_TICKER]
        try:
            vix = _load_wide(conn, 'weekly_bar', [VIX_TICKER], 'close')[VIX_TICKER]
        except Exception:
            vix = pd.Series(index=spy.index, dtype=float)
        try:
            us10 = _load_wide(conn, 'weekly_bar', [UST10Y_TICKER], 'close')[UST10Y_TICKER]
        except Exception:
            us10 = pd.Series(index=spy.index, dtype=float)
    df = pd.DataFrame({
        'SPY_ret': spy.pct_change(),
        'VIX': vix,
        'dUS10Y': us10.diff(),
    })
    return df

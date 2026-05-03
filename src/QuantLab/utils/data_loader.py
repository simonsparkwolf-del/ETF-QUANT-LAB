"""
data_loader.py — loads the processed CSV and returns a tidy panel dict.

Usage
-----
from QuantLab.utils import load_panel

panel = load_panel("data/processed/data.csv")
# panel["close"]   -> DataFrame(dates × 11 tickers)
# panel["open"]    -> ...
# panel["vwap"]    -> approximated as (open+high+low+close)/4
# panel["returns"] -> pct_change(close)
# panel["dv"]      -> daily dollar volume = close * volume
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

# The 11 SPDR sector ETF tickers present in the data
TICKERS: list[str] = [
    "XLB", "XLC", "XLE", "XLF", "XLI",
    "XLK", "XLP", "XLU", "XLV", "XLRE", "XLY",
]

_FIELD_SUFFIX: dict[str, str] = {
    "close":  "PX_LAST",
    "open":   "PX_OPEN",
    "high":   "PX_HIGH",
    "low":    "PX_LOW",
    "volume": "PX_VOLUME",
    "tri":    "TOT_RETURN_INDEX_GROSS_DVDS",
}


def _col(ticker: str, suffix: str) -> str:
    return f"{ticker} US Equity {suffix}"


def load_panel(csv_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Read a processed CSV and return a panel of DataFrames, one per field.

    Parameters
    ----------
    csv_path : path to data/processed/data.csv

    Returns
    -------
    dict with keys:
        close, open, high, low, volume, tri,
        returns, vwap, dv
    All DataFrames have shape (n_dates, 11) with TICKERS as columns.
    """
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

    panel: dict[str, pd.DataFrame] = {}

    for field, suffix in _FIELD_SUFFIX.items():
        cols = [_col(t, suffix) for t in TICKERS]
        sub = df[cols].copy()
        sub.columns = TICKERS
        sub = sub.apply(pd.to_numeric, errors="coerce")
        panel[field] = sub

    # Derived fields -----------------------------------------------------------
    # Returns: daily close-to-close percentage change
    panel["returns"] = panel["close"].pct_change()

    # VWAP approximation: typical price weighted by session endpoints
    # Best available proxy without intraday tick data:
    #   vwap ≈ (open + high + low + close) / 4
    panel["vwap"] = (
        panel["open"] + panel["high"] + panel["low"] + panel["close"]
    ) / 4.0

    # Daily dollar volume (used to compute adv{d})
    panel["dv"] = panel["close"] * panel["volume"]

    return panel


_AGG_MAP: dict[str, str] = {
    "open": "first", "high": "max", "low": "min",
    "close": "last", "volume": "sum", "tri": "last",
}

_BAR_FIELDS = ("open", "high", "low", "close", "volume", "tri")


def save_panel_as_bars(
    panel: dict[str, pd.DataFrame],
    conn: sqlite3.Connection,
) -> None:
    """
    Write per-ticker daily and weekly bars from panel to SQLite.

    Populates tables: asset, daily_bar, weekly_bar.
    Existing rows are replaced on each call.
    """
    bar_fields = [f for f in _BAR_FIELDS if f in panel]
    daily_records: list[pd.DataFrame] = []
    weekly_records: list[pd.DataFrame] = []

    for ticker in TICKERS:
        ticker_df = pd.DataFrame({f: panel[f][ticker] for f in bar_fields})
        ticker_df = ticker_df.dropna(subset=["close"])

        # Daily
        d = ticker_df.copy()
        d.index.name = "date"
        d = d.reset_index()
        d["date"] = d["date"].dt.strftime("%Y-%m-%d")
        d["ticker"] = ticker
        daily_records.append(d)

        # Weekly (W-WED resample)
        current_agg = {k: v for k, v in _AGG_MAP.items() if k in ticker_df.columns}
        w = ticker_df.resample("W-WED").agg(current_agg)
        w.index.name = "date"
        w = w.reset_index()
        w["date"] = w["date"].dt.strftime("%Y-%m-%d")
        w["ticker"] = ticker
        weekly_records.append(w)

    cols = ["date", "ticker"] + bar_fields
    daily_all  = pd.concat(daily_records,  ignore_index=True)[cols]
    weekly_all = pd.concat(weekly_records, ignore_index=True)[cols]

    # Seed asset table (full catalog: ETF + Benchmark + Index)
    from .db import seed_assets  # lazy import — avoids top-level circular dependency
    seed_assets(conn)

    # Write bars
    conn.execute("DELETE FROM daily_bar")
    daily_all.to_sql("daily_bar", conn, if_exists="append", index=False)

    conn.execute("DELETE FROM weekly_bar")
    weekly_all.to_sql("weekly_bar", conn, if_exists="append", index=False)

    conn.commit()
    print(f"Bars saved: {len(daily_all)} daily rows, {len(weekly_all)} weekly rows → SQLite")


def combine_panels(
    train_path: str | Path,
    test_path: str | Path,
) -> dict[str, pd.DataFrame]:
    """Concatenate train + test panels (useful for full-sample backtests)."""
    train = load_panel(train_path)
    test = load_panel(test_path)
    return {
        field: pd.concat([train[field], test[field]])
        for field in train
    }

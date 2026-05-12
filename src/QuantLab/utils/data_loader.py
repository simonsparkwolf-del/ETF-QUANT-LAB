"""
data_loader.py — loads the processed CSV and returns a tidy panel dict.

Usage
-----
from QuantLab.utils import load_panel, save_panel_as_bars, save_non_etf_bars

panel = load_panel("data/processed/data.csv")
conn  = init_db("datapool.db")
save_panel_as_bars(panel, conn)        # ETF daily + weekly bars
save_non_etf_bars(data_path, conn)     # Benchmark / Index bars (appended)
# Alpha / FRS computations use TICKERS (ETF-only) — non-ETF rows ignored automatically
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

TICKERS: list[str] = [
    "XLB", "XLC", "XLE", "XLF", "XLI",
    "XLK", "XLP", "XLU", "XLV", "XLRE", "XLY",
]

# Macro tickers needed by mac-group alphas (102-107)
_MACRO_CLOSE_COLS: dict[str, str] = {
    "SPY":      "SPY US Equity PX_LAST",
    "VIX":      "VIX Index PX_LAST",
    "USGG10YR": "USGG10YR Index PX_LAST",
}

_FIELD_SUFFIX: dict[str, str] = {
    "close":  "PX_LAST",
    "open":   "PX_OPEN",
    "high":   "PX_HIGH",
    "low":    "PX_LOW",
    "volume": "PX_VOLUME",
    "tri":    "TOT_RETURN_INDEX_GROSS_DVDS",
}

# USGG10YR: Bloomberg spreads OHLC/TRI across USGG10YR–14YR ticker columns
_USGG_COL_MAP: dict[str, str] = {
    "USGG10YR Index PX_LAST":                     "close",
    "USGG11YR Index PX_OPEN":                     "open",
    "USGG12YR Index PX_HIGH":                     "high",
    "USGG13YR Index PX_LOW":                      "low",
    "USGG14YR Index TOT_RETURN_INDEX_GROSS_DVDS":  "tri",
}

_AGG_MAP: dict[str, str] = {
    "open": "first", "high": "max", "low": "min",
    "close": "last", "volume": "sum", "tri": "last",
}

_BAR_FIELDS = ("open", "high", "low", "close", "volume", "tri")


# ── Private helpers ────────────────────────────────────────────────────────────

def _col(ticker: str, suffix: str) -> str:
    return f"{ticker} US Equity {suffix}"


def _to_bar_rows(sub: pd.DataFrame, ticker: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (daily_df, weekly_df) with date + ticker columns added."""
    sub = sub.copy()
    sub.index.name = "date"

    d = sub.reset_index()
    d["date"] = d["date"].dt.strftime("%Y-%m-%d")
    d["ticker"] = ticker

    agg = {k: v for k, v in _AGG_MAP.items() if k in sub.columns}
    w = sub.resample("W-WED").agg(agg)
    w.index.name = "date"
    w = w.reset_index()
    w["date"] = w["date"].dt.strftime("%Y-%m-%d")
    w["ticker"] = ticker

    return d, w


# ── Public API ─────────────────────────────────────────────────────────────────

def load_panel(csv_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Read processed CSV → panel dict keyed by field name.

    Keys: close, open, high, low, volume, tri, returns, vwap, dv
    All DataFrames: shape (n_dates, 11), columns = TICKERS.
    """
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    panel: dict[str, pd.DataFrame] = {}

    for field, suffix in _FIELD_SUFFIX.items():
        sub = df[[_col(t, suffix) for t in TICKERS]].copy()
        sub.columns = TICKERS
        panel[field] = sub.apply(pd.to_numeric, errors="coerce")

    panel["returns"] = panel["close"].pct_change()
    panel["vwap"]    = (panel["open"] + panel["high"] + panel["low"] + panel["close"]) / 4.0
    panel["dv"]      = panel["close"] * panel["volume"]

    # Index close for mac-group alphas (102-107): SPY / VIX / USGG10YR
    index_close = {
        ticker: pd.to_numeric(df[col], errors="coerce")
        for ticker, col in _MACRO_CLOSE_COLS.items()
        if col in df.columns
    }
    if index_close:
        panel["index"] = pd.DataFrame(index_close, index=df.index)

    return panel


def save_panel_as_bars(
    panel: dict[str, pd.DataFrame],
    conn: sqlite3.Connection,
) -> None:
    """Write ETF daily + weekly bars to SQLite. Also seeds the asset table."""
    from .db import seed_assets

    bar_fields = [f for f in _BAR_FIELDS if f in panel]
    daily_all_list, weekly_all_list = [], []

    for ticker in TICKERS:
        sub = pd.DataFrame({f: panel[f][ticker] for f in bar_fields}).dropna(subset=["close"])
        d, w = _to_bar_rows(sub, ticker)
        daily_all_list.append(d)
        weekly_all_list.append(w)

    cols = ["date", "ticker"] + bar_fields
    daily_all  = pd.concat(daily_all_list,  ignore_index=True)[cols]
    weekly_all = pd.concat(weekly_all_list, ignore_index=True)[cols]

    seed_assets(conn)
    conn.execute("DELETE FROM daily_bar")
    daily_all.to_sql("daily_bar", conn, if_exists="append", index=False)
    conn.execute("DELETE FROM weekly_bar")
    weekly_all.to_sql("weekly_bar", conn, if_exists="append", index=False)
    conn.commit()
    print(f"ETF bars saved: {len(daily_all)} daily, {len(weekly_all)} weekly rows → SQLite")


def save_non_etf_bars(
    csv_path: str | Path,
    conn: sqlite3.Connection,
) -> None:
    """
    Append Benchmark / Index bars from data.csv to daily_bar / weekly_bar.
    Call AFTER save_panel_as_bars. Alpha/FRS computations use TICKERS (ETF-only)
    so non-ETF rows are ignored automatically — no extra filtering needed.
    """
    from .db import ASSET_CATALOG

    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    daily_records, weekly_records = [], []

    # SPY / SPX / VIX: column = "{security_name} {bloomberg_suffix}"
    for ticker, meta in ASSET_CATALOG.items():
        if meta["category"] == "ETF" or ticker == "USGG10YR":
            continue
        prefix = meta["security_name"]
        rename = {f"{prefix} {s}": f for f, s in _FIELD_SUFFIX.items()
                  if f"{prefix} {s}" in df.columns}
        if "close" not in rename.values():
            print(f"  {ticker}: no close column found, skipping.")
            continue
        sub = (df[list(rename)].rename(columns=rename)
               .apply(pd.to_numeric, errors="coerce").dropna(subset=["close"]))
        d, w = _to_bar_rows(sub, ticker)
        daily_records.append(d)
        weekly_records.append(w)

    # USGG10YR: Bloomberg spread layout (USGG10YR–14YR columns)
    usgg_cols = {c: f for c, f in _USGG_COL_MAP.items() if c in df.columns}
    if usgg_cols:
        usgg = (df[list(usgg_cols)].rename(columns=usgg_cols)
                .apply(pd.to_numeric, errors="coerce").dropna(subset=["close"]))
        d, w = _to_bar_rows(usgg, "USGG10YR")
        daily_records.append(d)
        weekly_records.append(w)

    if not daily_records:
        print("  No non-ETF bar data found in CSV.")
        return

    pd.concat(daily_records,  ignore_index=True).to_sql("daily_bar",  conn, if_exists="append", index=False)
    pd.concat(weekly_records, ignore_index=True).to_sql("weekly_bar", conn, if_exists="append", index=False)
    conn.commit()
    loaded = [r["ticker"].iloc[0] for r in daily_records]
    print(f"Non-ETF bars appended: {loaded} → SQLite")


def combine_panels(
    train_path: str | Path,
    test_path: str | Path,
) -> dict[str, pd.DataFrame]:
    """Concatenate train + test panels (useful for full-sample backtests)."""
    train = load_panel(train_path)
    test  = load_panel(test_path)
    return {field: pd.concat([train[field], test[field]]) for field in train}

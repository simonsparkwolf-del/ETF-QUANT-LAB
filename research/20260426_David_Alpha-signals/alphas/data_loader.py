"""
data_loader.py — loads the processed CSVs and returns a tidy panel dict.

Usage
-----
from alphas.data_loader import load_panel

panel = load_panel("data/processed/train_raw_data.csv")
# panel["close"]   -> DataFrame(dates × 11 tickers)
# panel["open"]    -> ...
# panel["vwap"]    -> approximated as (open+high+low+close)/4
# panel["returns"] -> pct_change(close)
# panel["dv"]      -> daily dollar volume = close * volume
"""

from __future__ import annotations

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
    csv_path : path to train_raw_data.csv or test_raw_data.csv

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

"""
db.py — SQLite schema and connection management for QuantLab datapool.

Tables
------
asset        — ticker master (ticker, security_name, category)
alpha        — alpha factor definitions (alpha_id, alpha_name, applicable)
frs          — FRS metric definitions (frs_id, note)
daily_bar    — daily OHLCV + TRI per ticker
weekly_bar   — W-WED resampled OHLCV + TRI per ticker
weekly_alpha — alpha values, long format (date, ticker, alpha_id, value)
weekly_frs   — FRS labels per ticker (date, ticker, frs1, frs2, frs3)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# ── Asset catalogue ────────────────────────────────────────────────────────────
# category:
#   "ETF"       — SPDR sector ETFs (investment universe, alpha/FRS targets)
#   "Benchmark" — broad-market reference (SPY / SPX)
#   "Index"     — macro / risk indicators (VIX, 10-yr yield)
ASSET_CATALOG: dict[str, dict] = {
    # SPDR Sector ETFs — investment universe
    "XLB":      {"security_name": "XLB US Equity",  "category": "ETF"},
    "XLC":      {"security_name": "XLC US Equity",  "category": "ETF"},
    "XLE":      {"security_name": "XLE US Equity",  "category": "ETF"},
    "XLF":      {"security_name": "XLF US Equity",  "category": "ETF"},
    "XLI":      {"security_name": "XLI US Equity",  "category": "ETF"},
    "XLK":      {"security_name": "XLK US Equity",  "category": "ETF"},
    "XLP":      {"security_name": "XLP US Equity",  "category": "ETF"},
    "XLU":      {"security_name": "XLU US Equity",  "category": "ETF"},
    "XLV":      {"security_name": "XLV US Equity",  "category": "ETF"},
    "XLRE":     {"security_name": "XLRE US Equity", "category": "ETF"},
    "XLY":      {"security_name": "XLY US Equity",  "category": "ETF"},
    # Benchmarks — broad-market reference
    "SPY":      {"security_name": "SPY US Equity",  "category": "Benchmark"},
    "SPX":      {"security_name": "SPX Index",      "category": "Benchmark"},
    # Macro / risk indices
    "VIX":      {"security_name": "VIX Index",      "category": "Index"},
    "USGG10YR": {"security_name": "USGG10YR Index", "category": "Index"},
}

_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS asset (
    ticker        TEXT PRIMARY KEY,
    security_name TEXT NOT NULL UNIQUE,
    category      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alpha (
    alpha_id   INTEGER PRIMARY KEY,
    alpha_name TEXT NOT NULL,
    applicable TEXT
);

CREATE TABLE IF NOT EXISTS frs (
    frs_id INTEGER PRIMARY KEY,
    note     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_bar (
    date    TEXT NOT NULL,
    ticker  TEXT NOT NULL REFERENCES asset(ticker),
    open    REAL,
    high    REAL,
    low     REAL,
    close   REAL NOT NULL,
    volume  REAL,
    tri     REAL,
    PRIMARY KEY (date, ticker)
);

CREATE TABLE IF NOT EXISTS weekly_bar (
    date    TEXT NOT NULL,
    ticker  TEXT NOT NULL REFERENCES asset(ticker),
    open    REAL,
    high    REAL,
    low     REAL,
    close   REAL NOT NULL,
    volume  REAL,
    tri     REAL,
    PRIMARY KEY (date, ticker)
);

CREATE TABLE IF NOT EXISTS weekly_alpha (
    date     TEXT    NOT NULL,
    ticker   TEXT    NOT NULL REFERENCES asset(ticker),
    alpha_id INTEGER NOT NULL REFERENCES alpha(alpha_id),
    value    REAL,
    PRIMARY KEY (date, ticker, alpha_id)
);

CREATE TABLE IF NOT EXISTS weekly_frs (
    date     TEXT    NOT NULL,
    ticker   TEXT    NOT NULL REFERENCES asset(ticker),
    frs_id INTEGER NOT NULL REFERENCES frs(frs_id),
    value    REAL,
    PRIMARY KEY (date, ticker, frs_id)
);
"""


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Open (or create) the SQLite database and return a connection."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """
    Create the datapool database schema (tables created if not already present).
    Returns an open connection ready for use.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    conn.executescript(_SCHEMA)
    conn.commit()
    print(f"Database ready: {db_path}")
    return conn


def seed_assets(conn: sqlite3.Connection) -> None:
    """
    Populate the asset table from ASSET_CATALOG.
    Replaces all existing rows on each call.
    """
    import pandas as pd

    rows = [
        {"ticker": ticker, **meta}
        for ticker, meta in ASSET_CATALOG.items()
    ]
    asset_df = pd.DataFrame(rows)[["ticker", "security_name", "category"]]
    conn.execute("DELETE FROM asset")
    asset_df.to_sql("asset", conn, if_exists="append", index=False)
    conn.commit()

    etf_n   = sum(1 for m in ASSET_CATALOG.values() if m["category"] == "ETF")
    bench_n = sum(1 for m in ASSET_CATALOG.values() if m["category"] == "Benchmark")
    idx_n   = sum(1 for m in ASSET_CATALOG.values() if m["category"] == "Index")
    print(f"Assets seeded: {etf_n} ETF, {bench_n} Benchmark, {idx_n} Index → {len(rows)} total")

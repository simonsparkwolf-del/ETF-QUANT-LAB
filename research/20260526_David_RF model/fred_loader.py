"""
fred_loader.py — load 5 FRED macro series from local CSV files.

Files expected in `New_Strategy/data/fred/`:
  T10Y2Y.csv         10Y - 2Y Treasury spread          (from 2021-01-04)
  BAMLH0A0HYM2.csv   ICE BofA US HY OAS                (from 2023-05-22 - short history!)
  DTWEXBGS.csv       Trade-weighted USD broad index    (from 2021-01-04)
  DCOILWTICO.csv     WTI crude oil spot                (from 2021-01-04)
  T10YIE.csv         10-year breakeven inflation       (from 2021-01-04)

CSV format (FRED export):
  observation_date,<series_id>
  2021-01-04,0.82
  ...

The loader also upserts the data into the existing SQLite database
(`Refinement_revised-old/ML001_data/datapool.db`, table `daily_macro_fred`)
for downstream use, and **trims to our training/testing window**
(2021-03-01 → 2026-03-31) so we keep only the dates that matter.

BAMLH0A0HYM2's short history (starts 2023-05-22) is documented downstream
in `daily_features.build_fred_features` where NaNs before that date are
filled with 0 after z-scoring — i.e. the feature is "off" before its
first observation and "on" afterwards.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from config import DB, ROOT


FRED_DIR = ROOT / "data" / "fred"

FRED_SERIES = ['T10Y2Y', 'BAMLH0A0HYM2', 'DTWEXBGS', 'DCOILWTICO', 'T10YIE']

# Trim to our pipeline window plus a small lookback buffer for rolling features.
WINDOW_START = '2020-09-01'
WINDOW_END   = '2026-03-31'


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_macro_fred (
            date      TEXT NOT NULL,
            series_id TEXT NOT NULL,
            value     REAL,
            PRIMARY KEY (date, series_id)
        )
    """)
    conn.commit()


def _load_csv(series_id: str) -> pd.DataFrame:
    path = FRED_DIR / f"{series_id}.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing FRED CSV: {path}")
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    date_col = 'observation_date' if 'observation_date' in df.columns else df.columns[0]
    val_col  = [c for c in df.columns if c != date_col][0]
    df = df.rename(columns={date_col: 'date', val_col: 'value'})
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df = df.dropna(subset=['value'])
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df = df[(df['date'] >= WINDOW_START) & (df['date'] <= WINDOW_END)]
    df['series_id'] = series_id
    return df[['date', 'series_id', 'value']].reset_index(drop=True)


def load_and_cache(force: bool = False) -> None:
    """Read all 5 CSVs and upsert into the SQLite cache, restricted to
    the pipeline window."""
    if not FRED_DIR.exists():
        raise FileNotFoundError(f"FRED CSV directory missing: {FRED_DIR}")

    with sqlite3.connect(str(DB)) as conn:
        _ensure_table(conn)
        cur = conn.cursor()
        cur.execute("DELETE FROM daily_macro_fred")
        conn.commit()

        for sid in FRED_SERIES:
            df = _load_csv(sid)
            df.to_sql('daily_macro_fred', conn, if_exists='append', index=False)
            print(f"  loaded {sid:14s}  n={len(df):>5}  "
                  f"range {df['date'].min()} -> {df['date'].max()}")


def load_fred_wide() -> pd.DataFrame:
    """Return cached FRED data as a date-indexed wide DataFrame
    (columns = series_ids), already trimmed to the pipeline window.
    Missing rows are NOT forward-filled here; the panel-builder handles
    alignment to the trading-day calendar.
    """
    with sqlite3.connect(str(DB)) as conn:
        df = pd.read_sql_query(
            "SELECT date, series_id, value FROM daily_macro_fred", conn
        )
    if df.empty:
        return pd.DataFrame()
    df['date'] = pd.to_datetime(df['date'])
    wide = df.pivot(index='date', columns='series_id', values='value').sort_index()
    return wide


if __name__ == "__main__":
    load_and_cache()
    wide = load_fred_wide()
    print("\ncache summary:")
    for sid in FRED_SERIES:
        if sid in wide.columns:
            col = wide[sid].dropna()
            print(f"  {sid:14s} n={len(col):>5}  "
                  f"range {col.index.min().date()} -> {col.index.max().date()}  "
                  f"min={col.min():.3f}  max={col.max():.3f}")

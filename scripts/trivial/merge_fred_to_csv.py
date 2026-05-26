"""
merge_fred_to_csv.py — append FRED macro series to data/processed/data.csv

Adds 5 columns (close-only, named "{series_id} Index PX_LAST") so they flow
through dataset_builder.ipynb → save_non_etf_bars → daily_bar / weekly_bar.

FRED series added:
  T10Y2Y        10Y-2Y Treasury spread
  BAMLH0A0HYM2  ICE BofA US HY OAS      (starts 2023-05-22; earlier rows = NaN)
  DTWEXBGS      Trade-weighted USD broad index
  DCOILWTICO    WTI crude oil spot
  T10YIE        10-year breakeven inflation

Source CSVs: research/20260526_David_RF model/data/fred/
  Format: observation_date, <series_id>
  NaN cells (federal holidays when FRED does not publish) are forward-filled
  onto the trading-day calendar taken from data.csv.

Run once to update the CSV; re-run whenever FRED data is refreshed.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
DATA_CSV = ROOT / "data" / "processed" / "data.csv"
FRED_DIR = ROOT / "research" / "20260526_David_RF model" / "data" / "fred"

FRED_SERIES = [
    "T10Y2Y",
    "BAMLH0A0HYM2",
    "DTWEXBGS",
    "DCOILWTICO",
    "T10YIE",
]


def _load_fred(series_id: str) -> pd.Series:
    path = FRED_DIR / f"{series_id}.csv"
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    date_col = "observation_date" if "observation_date" in df.columns else df.columns[0]
    val_col = [c for c in df.columns if c != date_col][0]
    s = (
        df.set_index(date_col)[val_col]
        .pipe(lambda x: x.replace(".", float("nan")))
        .pipe(pd.to_numeric, errors="coerce")
    )
    s.index = pd.to_datetime(s.index)
    s.name = series_id
    return s


def main() -> None:
    print(f"Reading {DATA_CSV}")
    df = pd.read_csv(DATA_CSV, index_col=0, parse_dates=True)
    print(f"  {len(df)} trading days, {len(df.columns)} columns")

    new_cols: dict[str, pd.Series] = {}
    for series_id in FRED_SERIES:
        col_name = f"{series_id} Index PX_LAST"
        fred = _load_fred(series_id)
        aligned = fred.reindex(df.index, method="ffill")
        new_cols[col_name] = aligned
        n_valid = aligned.notna().sum()
        n_nan = aligned.isna().sum()
        print(f"  {series_id:16s} → '{col_name}'  valid={n_valid}  nan={n_nan}")

    # Drop any existing FRED columns before re-adding (idempotent re-run).
    drop = [c for c in new_cols if c in df.columns]
    if drop:
        df = df.drop(columns=drop)
    df = pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)

    df.to_csv(DATA_CSV)
    print(f"\nSaved → {DATA_CSV}  ({len(df.columns)} columns total)")


if __name__ == "__main__":
    main()

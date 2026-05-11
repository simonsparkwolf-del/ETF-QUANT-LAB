"""
load_ml_input.py — build ML feature table from SQLite.

Design constraints (project conventions)
--------------------------------------
- ML reads ONLY: weekly_bar + weekly_alpha
- weekly_alpha is long format (date, ticker, alpha_id, value)
- We keep SQL simple (long-table queries) and pivot to wide in pandas.
- required config name is `required` (not "panel").

Required config format
----------------------
required = {
    "bars":  ["tri", "close", "volume"],   # columns from weekly_bar (date,ticker always included)
    "alpha": [1, 2, 3, 4],                 # alpha_id list to include (pivoted to columns alpha_1..alpha_4)
}
"""

from __future__ import annotations

import sqlite3
from typing import Any

import pandas as pd


def load_ml_panel(conn: sqlite3.Connection, required: dict[str, Any]) -> pd.DataFrame:
    """
    Load an ML "big table" for all tickers/dates.

    Returns a DataFrame with at least columns:
      - date (datetime64[ns])
      - ticker (str)
    plus:
      - requested weekly_bar columns
      - requested alpha columns as alpha_{id}
    """
    bars_cols = list(required.get("bars") or [])
    alpha_ids = list(required.get("alpha") or [])

    # Ensure date/ticker present
    bar_select_cols = ["date", "ticker"] + [c for c in bars_cols if c not in ("date", "ticker")]
    bar_sql = f"SELECT {', '.join(bar_select_cols)} FROM weekly_bar"
    bar_df = pd.read_sql(bar_sql, conn, parse_dates=["date"])

    if not alpha_ids:
        return bar_df

    placeholders = ",".join(["?"] * len(alpha_ids))
    alpha_sql = (
        "SELECT date, ticker, alpha_id, value "
        "FROM weekly_alpha "
        f"WHERE alpha_id IN ({placeholders})"
    )
    alpha_long = pd.read_sql(alpha_sql, conn, params=alpha_ids, parse_dates=["date"])

    # Pivot: (date,ticker) × alpha_id → alpha_{id} columns
    alpha_wide = (
        alpha_long.pivot_table(
            index=["date", "ticker"],
            columns="alpha_id",
            values="value",
            aggfunc="first",
        )
        .rename(columns=lambda c: f"alpha_{int(c)}")
        .reset_index()
    )

    big = bar_df.merge(alpha_wide, on=["date", "ticker"], how="left")
    return big


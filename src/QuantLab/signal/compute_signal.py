"""
compute_signal.py — orchestration for signal computation.

Key conventions
---------------
- Adding new signal indicators MUST NOT require editing any __init__.py.
  This module auto-imports:
    - QuantLab.signal.signal_metrics (non-ML)
    - all modules under QuantLab.signal.ml (ML)

- External compute interface for registered indicators is Series → Series:
    fn(p: pd.Series, *, ticker: str, **kwargs) -> pd.Series

- ML authoring interface (decorated function) returns a long DataFrame:
    panel_fn(big: pd.DataFrame, **kwargs) -> DataFrame[ticker,date,pred]
  The strong decorator wraps it into the standard Series interface.

DB tables populated
------------------
- signal        (signal_id, note, category)   — registry (incremental insert)
- weekly_signal (date, ticker, signal_id, value)
"""

from __future__ import annotations

import importlib
import pkgutil
import sqlite3
from typing import Any

import pandas as pd

from QuantLab.utils.load_ml_input import load_ml_panel

from .signal_registry import SIGNAL_REGISTRY, get_registry_df


ETFS: list[str] = [
    "XLB", "XLC", "XLE", "XLF", "XLI",
    "XLK", "XLP", "XLU", "XLV", "XLRE", "XLY",
]


def _auto_import_signals() -> None:
    """Import signal modules so decorators populate SIGNAL_REGISTRY."""
    import QuantLab.signal.signal_metrics  # noqa: F401
    import QuantLab.signal.ml as ml_pkg

    for m in pkgutil.iter_modules(ml_pkg.__path__):
        if m.name.startswith("_"):
            continue
        importlib.import_module(f"{ml_pkg.__name__}.{m.name}")


def _ensure_signal_registry_in_db(conn: sqlite3.Connection) -> None:
    """Insert only new signal_ids into the signal table (do not delete existing)."""
    reg = get_registry_df()
    if reg.empty:
        return

    existing = pd.read_sql("SELECT signal_id FROM signal", conn)
    existing_ids = set(existing["signal_id"].astype(int).tolist()) if not existing.empty else set()
    to_add = reg[~reg["signal_id"].isin(existing_ids)]
    if not to_add.empty:
        to_add.to_sql("signal", conn, if_exists="append", index=False)


def save_signal_results(
    conn: sqlite3.Connection,
    *,
    etfs: list[str] = ETFS,
    **kwargs: Any,
) -> None:
    """
    Compute all registered signals and write to SQLite weekly_signal.

    Strategy:
    - signal registry table: incremental insert (only missing signal_id)
    - weekly_signal values: for each signal_id, delete existing rows for that id, then append recomputed rows
      (preserves other signals' data).
    """
    _auto_import_signals()
    _ensure_signal_registry_in_db(conn)

    # Cache weekly TRI series for p input (Series → Series interface)
    weekly_tri = pd.read_sql(
        "SELECT date, ticker, tri FROM weekly_bar WHERE tri IS NOT NULL",
        conn,
        parse_dates=["date"],
    ).sort_values(["ticker", "date"])

    if weekly_tri.empty:
        print("No weekly_bar TRI found; skip signals.")
        return

    for sid in sorted(SIGNAL_REGISTRY.keys()):
        meta = SIGNAL_REGISTRY[sid]
        fn = meta.fn

        # Build required big table once per signal (even non-ML, to supply extra required series)
        big = load_ml_panel(conn, meta.required)

        panel_df: pd.DataFrame | None = None
        if meta.panel_fn is not None:
            panel_df = meta.panel_fn(big, **kwargs)

        out_rows: list[pd.DataFrame] = []
        for t in etfs:
            g = weekly_tri[weekly_tri["ticker"] == t]
            if g.empty:
                continue
            p = g.set_index("date")["tri"]

            # Non-ML may request extra columns; build per-ticker Series kwargs aligned to p.index
            extra: dict[str, Any] = {}
            if meta.panel_fn is None:
                bg = big[big["ticker"] == t].set_index("date").sort_index()
                if not isinstance(bg.index, pd.DatetimeIndex):
                    bg.index = pd.to_datetime(bg.index)

                bars_cols = list((meta.required or {}).get("bars") or [])
                for c in bars_cols:
                    if c in ("date", "ticker", "tri"):
                        continue
                    if c in bg.columns:
                        extra[c] = bg[c].reindex(p.index)

                alpha_ids = list((meta.required or {}).get("alpha") or [])
                for aid in alpha_ids:
                    col = f"alpha_{int(aid)}"
                    if col in bg.columns:
                        extra[col] = bg[col].reindex(p.index)

            s = fn(p, ticker=t, _panel_df=panel_df, **extra, **kwargs)
            if s is None:
                continue

            tmp = s.dropna().reset_index()
            tmp.columns = ["date", "value"]
            tmp["date"] = tmp["date"].dt.strftime("%Y-%m-%d")
            tmp["ticker"] = t
            tmp["signal_id"] = sid
            out_rows.append(tmp)

        # Replace rows for this signal_id only
        conn.execute("DELETE FROM weekly_signal WHERE signal_id = ?", (sid,))
        if out_rows:
            long = pd.concat(out_rows, ignore_index=True)[["date", "ticker", "signal_id", "value"]]
            long.to_sql("weekly_signal", conn, if_exists="append", index=False)
        conn.commit()

    print(f"Signal complete → SQLite weekly_signal table (signals={len(SIGNAL_REGISTRY)})")


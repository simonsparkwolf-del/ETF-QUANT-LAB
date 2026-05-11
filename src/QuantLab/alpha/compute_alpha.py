"""
compute_alpha.py — orchestration for alpha computation.

Usage in notebook:
    from QuantLab.alpha import compute_all_alphas, save_alpha_results
    conn    = init_db("datapool.db")
    results = compute_all_alphas(panel)
    save_alpha_results(results, conn)
"""

import warnings
import sqlite3
import pandas as pd

from . import alpha_metrics          # triggers all @register_alpha decorators
from .alpha_registry import ALPHA_REGISTRY, get_mapping_df


def compute_all_alphas(panel: dict) -> dict[int, pd.DataFrame]:
    """Run all registered alphas. Returns {alpha_id: DataFrame(dates × tickers)}."""
    results: dict[int, pd.DataFrame] = {}
    for aid, meta in ALPHA_REGISTRY.items():
        try:
            results[aid] = meta["fn"](panel)
        except Exception as exc:
            warnings.warn(f"Alpha#{aid} failed: {exc}")
    return results


def save_alpha_results(
    results: dict[int, pd.DataFrame],
    conn: sqlite3.Connection,
) -> pd.DataFrame:
    """
    Write alpha results to SQLite.

    Populates tables: alpha (registry), weekly_alpha (long-format values).
    Existing rows are replaced on each call.

    Returns the combined wide-format DataFrame (Date × Ticker index,
    Alpha_* columns) for quick inspection.
    """
    # Build wide DataFrame (Date × Ticker index, integer alpha_id columns)
    all_dfs = []
    for aid in sorted(results.keys()):
        stacked = results[aid].stack()
        stacked.name = aid
        all_dfs.append(stacked)

    combined = pd.concat(all_dfs, axis=1)
    combined.index.names = ["date", "ticker"]

    # Long format: (date, ticker, alpha_id, value) — drop NaN rows
    long = (
        combined.reset_index()
        .melt(id_vars=["date", "ticker"], var_name="alpha_id", value_name="value")
        .dropna(subset=["value"])
    )
    long["date"] = long["date"].astype(str)
    long["alpha_id"] = long["alpha_id"].astype(int)

    # Seed alpha registry
    mapping = get_mapping_df().rename(columns={"desc": "alpha_name", "group": "applicable"})
    mapping = mapping[["alpha_id", "alpha_name", "applicable"]]
    existing = pd.read_sql("SELECT alpha_id FROM alpha", conn)
    existing_ids = set(existing["alpha_id"].astype(int).tolist()) if not existing.empty else set()
    to_add = mapping[~mapping["alpha_id"].isin(existing_ids)]
    if not to_add.empty:
        to_add.to_sql("alpha", conn, if_exists="append", index=False)

    # Write weekly_alpha
    conn.execute("DELETE FROM weekly_alpha")
    long.to_sql("weekly_alpha", conn, if_exists="append", index=False)
    conn.commit()

    print(f"Saved: {len(long)} rows to weekly_alpha, {len(mapping)} alphas to alpha table")

    # Rename columns for readable display
    combined.columns = [f"Alpha_{c}" for c in combined.columns]
    combined.index.names = ["Date", "Ticker"]
    return combined

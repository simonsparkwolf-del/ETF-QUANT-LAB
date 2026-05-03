"""
compute_frs.py — orchestration for FRS metric computation.

Usage in notebook:
    from QuantLab.frs import save_frs_results, ETFS
    conn = init_db("datapool.db")
    save_frs_results(conn, etfs=ETFS)
"""

import sqlite3
import pandas as pd

from . import frs_metrics          # triggers all @register_frs decorators
from .frs_registry import FRS_REGISTRY, get_mapping_df

ETFS: list[str] = [
    "XLB", "XLC", "XLE", "XLF", "XLI",
    "XLK", "XLP", "XLU", "XLV", "XLRE", "XLY",
]


def compute_frs_for_etf(p: pd.Series, **kwargs) -> pd.DataFrame:
    """Run all registered FRS metrics on a weekly TRI price series."""
    cols = {name: meta["fn"](p, **kwargs) for name, meta in FRS_REGISTRY.items()}
    return pd.DataFrame(cols, index=p.index).dropna(how="all")


def save_frs_results(
    conn: sqlite3.Connection,
    etfs: list[str] = ETFS,
    **kwargs,
) -> None:
    """
    Compute FRS metrics from SQLite weekly_bar table and write results to weekly_frs.

    Populates tables: frs (registry), weekly_frs.
    Existing rows are replaced on each call.
    Reads weekly TRI data from the weekly_bar table (populated by save_panel_as_bars).
    """
    # Read weekly TRI data from DB
    weekly_df = pd.read_sql(
        "SELECT date, ticker, tri FROM weekly_bar WHERE tri IS NOT NULL",
        conn,
        parse_dates=["date"],
    ).set_index("date")

    frs_records: list[pd.DataFrame] = []
    for etf in etfs:
        etf_data = weekly_df[weekly_df["ticker"] == etf]
        if etf_data.empty:
            print(f"  Warning: no weekly_bar data for {etf}, skipping.")
            continue

        res = compute_frs_for_etf(etf_data["tri"], **kwargs)
        res.columns = [c.lower() for c in res.columns]   # FRS1 → frs1
        res["ticker"] = etf
        res.index.name = "date"
        res = res.reset_index()
        res["date"] = res["date"].dt.strftime("%Y-%m-%d")
        frs_records.append(res)
        print(f"  {etf}: {len(res)} rows, metrics={[c for c in res.columns if c not in ('date','ticker')]}")

    if not frs_records:
        print("  No FRS data computed — check that weekly_bar is populated first.")
        return

    frs_all = pd.concat(frs_records, ignore_index=True)
    cols = ["date", "ticker"] + [c for c in frs_all.columns if c not in ("date", "ticker")]
    frs_all = frs_all[cols]

    # Seed frs registry from registered metrics
    mapping = get_mapping_df()
    frs_reg = pd.DataFrame({
        "frs_code": mapping["frs_id"].str.extract(r"(\d+)")[0].astype(int).values,
        "note":     mapping["description"].values,
    })
    conn.execute("DELETE FROM frs")
    frs_reg.to_sql("frs", conn, if_exists="append", index=False)

    # Write weekly_frs
    conn.execute("DELETE FROM weekly_frs")
    frs_all.to_sql("weekly_frs", conn, if_exists="append", index=False)
    conn.commit()

    print(f"\nFRS complete → SQLite weekly_frs table ({len(frs_all)} rows)")

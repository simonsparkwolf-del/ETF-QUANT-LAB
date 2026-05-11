"""回测用的「行情终端」：仿真日历 + datapool 只读查询。"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd


def _dates(x) -> pd.Series:
    # Keep typing loose: pandas stubs make read_sql_query columns "Unknown".
    return pd.to_datetime(x, errors="coerce").dt.date


class QuoteTerminal:
    def __init__(self, db_path: Path) -> None:
        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")
        self._path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._day: date | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    @property
    def day(self) -> date:
        if self._day is None:
            raise RuntimeError("call QuoteTerminal.at(d) first")
        return self._day

    def at(self, d: date) -> None:
        self._day = d

    def close(self) -> None:
        self._conn.close()

    def range_ok(self, start: date, end: date) -> None:
        b = pd.read_sql_query(
            "SELECT MIN(date) AS lo, MAX(date) AS hi FROM weekly_bar", self._conn
        )
        lo, hi = _dates(b["lo"]).iloc[0], _dates(b["hi"]).iloc[0]
        assert lo <= start <= hi, f"start out of range [{lo}, {hi}]"
        assert lo <= end <= hi, f"end out of range [{lo}, {hi}]"

    def bars(self, start: date, end: date) -> pd.DataFrame:
        """ETF weekly rows merged with applicable alpha (wide), clipped to [start, end]."""
        q_b = """
        SELECT w.date, w.ticker, w.open, w.high, w.low, w.close, w.volume, w.tri
        FROM weekly_bar w JOIN asset a ON w.ticker = a.ticker
        WHERE a.category = 'ETF'
        """
        bars = pd.read_sql_query(q_b, self._conn)
        bars["date"] = _dates(bars["date"])

        q_a = """
        SELECT wa.date, wa.ticker, wa.alpha_id, wa.value FROM weekly_alpha wa
        WHERE wa.alpha_id IN (SELECT alpha_id FROM alpha WHERE applicable = 'A')
        """
        alpha = pd.read_sql_query(q_a, self._conn)
        alpha["date"] = _dates(alpha["date"])
        wide = alpha.pivot_table(
            index=["date", "ticker"], columns="alpha_id", values="value"
        )
        wide.columns = [f"alpha_{int(c)}" for c in wide.columns]
        wide = wide.reset_index()

        out = bars.merge(wide, how="left", on=["date", "ticker"])
        return out.loc[(out["date"] >= start) & (out["date"] <= end), :]

    def quote(self, ticker: str) -> pd.Series:
        d = self.day
        q = """
        SELECT date, ticker, open, high, low, close, volume, tri FROM weekly_bar
        WHERE ticker = ? AND date = ?
        """
        row = pd.read_sql_query(q, self._conn, params=[ticker, d.isoformat()])
        if row.empty:
            return pd.Series(dtype=float)
        row["date"] = _dates(row["date"])
        return row.iloc[0]

    def signals(self) -> pd.DataFrame:
        d = self.day
        long_df = pd.read_sql_query(
            "SELECT date, ticker, signal_id, value FROM weekly_signal", self._conn
        )
        long_df["date"] = _dates(long_df["date"])
        long_df = long_df.loc[long_df["date"] <= d, :]
        if long_df.empty:
            return pd.DataFrame(columns=["date", "ticker"])
        w = long_df.pivot_table(
            index=["date", "ticker"], columns="signal_id", values="value"
        )
        w.columns = [f"signal_{int(c)}" for c in w.columns]
        return w.reset_index()

    def etfs(self) -> pd.DataFrame:
        return self._bars_cat("ETF")

    def indices(self) -> pd.DataFrame:
        return self._bars_cat("Index")

    def benchmarks(self) -> pd.DataFrame:
        return self._bars_cat("Benchmark")

    def today_etfs(self) -> pd.DataFrame:
        """All ETF ``weekly_bar`` rows on ``day`` (cross-section for the broadcast date)."""
        d = self.day
        q = """
        SELECT w.date, w.ticker, w.open, w.high, w.low, w.close, w.volume, w.tri
        FROM weekly_bar w JOIN asset a ON w.ticker = a.ticker
        WHERE a.category = 'ETF' AND w.date = ?
        """
        df = pd.read_sql_query(q, self._conn, params=[d.isoformat()])
        df["date"] = _dates(df["date"])
        return df

    def _bars_cat(self, category: str) -> pd.DataFrame:
        d = self.day
        q = """
        SELECT w.date, w.ticker, w.open, w.high, w.low, w.close, w.volume, w.tri
        FROM weekly_bar w JOIN asset a ON w.ticker = a.ticker
        WHERE a.category = ?
        """
        df = pd.read_sql_query(q, self._conn, params=[category])
        df["date"] = _dates(df["date"])
        return df.loc[df["date"] <= d, :].copy()

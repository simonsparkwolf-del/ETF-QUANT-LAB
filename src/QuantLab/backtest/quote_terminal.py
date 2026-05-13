"""回测用的「行情终端」：仿真日历 + datapool 只读查询。

接口约定
--------
- 无参数方法（etfs / indices / benchmarks / quote / signals / alphas）：
  只返回 terminal.day 当日截面，严格无 look-ahead。
- trading_dates(start, end)：仅返回日期列表，供引擎迭代，不拉行情数据。
- benchmark_history(start, end)：全量历史，仅供 BacktestAnalyzer 回测后使用。
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd


def _dates(x) -> pd.Series:
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
        assert lo <= end   <= hi, f"end out of range [{lo}, {hi}]"

    # ── engine utility ─────────────────────────────────────────────────────

    def trading_dates(self, start: date, end: date) -> list[date]:
        """Sorted list of dates in weekly_bar within [start, end]. No OHLCV data."""
        df = pd.read_sql_query(
            "SELECT DISTINCT date FROM weekly_bar WHERE date >= ? AND date <= ? ORDER BY date",
            self._conn,
            params=[start.isoformat(), end.isoformat()],
        )
        return _dates(df["date"]).tolist()

    # ── current-day cross-sections ─────────────────────────────────────────

    def etfs(self) -> pd.DataFrame:
        """All ETF OHLCV rows for terminal.day."""
        return self._snapshot("ETF")

    def indices(self) -> pd.DataFrame:
        """All Index OHLCV rows for terminal.day."""
        return self._snapshot("Index")

    def benchmarks(self) -> pd.DataFrame:
        """All Benchmark OHLCV rows for terminal.day."""
        return self._snapshot("Benchmark")

    def quote(self, ticker: str) -> pd.Series:
        """Single ticker OHLCV for terminal.day."""
        d = self.day
        row = pd.read_sql_query(
            "SELECT date, ticker, open, high, low, close, volume, tri FROM weekly_bar "
            "WHERE ticker = ? AND date = ?",
            self._conn,
            params=[ticker, d.isoformat()],
        )
        if row.empty:
            return pd.Series(dtype=float)
        row["date"] = _dates(row["date"])
        return row.iloc[0]

    def signals(self) -> pd.DataFrame:
        """Signal values (wide) for terminal.day."""
        d = self.day
        long_df = pd.read_sql_query(
            "SELECT date, ticker, signal_id, value FROM weekly_signal", self._conn
        )
        long_df["date"] = _dates(long_df["date"])
        long_df = long_df.loc[long_df["date"] == d]
        if long_df.empty:
            return pd.DataFrame(columns=["date", "ticker"])
        w = long_df.pivot_table(index=["date", "ticker"], columns="signal_id", values="value")
        w.columns = [f"signal_{int(c)}" for c in w.columns]
        return w.reset_index()

    def alphas(self, alpha_ids: tuple[int, ...] | None = None) -> pd.DataFrame:
        """
        Alpha values (wide) for terminal.day.
        Pass alpha_ids to restrict columns and reduce DB IO.
        """
        d = self.day
        if alpha_ids:
            placeholders = ",".join("?" * len(alpha_ids))
            q = (
                f"SELECT ticker, alpha_id, value FROM weekly_alpha "
                f"WHERE date = ? AND alpha_id IN ({placeholders})"
            )
            params: list = [d.isoformat(), *alpha_ids]
        else:
            q = "SELECT ticker, alpha_id, value FROM weekly_alpha WHERE date = ?"
            params = [d.isoformat()]

        df = pd.read_sql_query(q, self._conn, params=params)
        if df.empty:
            return pd.DataFrame(columns=["ticker"])
        wide = df.pivot_table(index="ticker", columns="alpha_id", values="value", aggfunc="first")
        wide.columns = [f"alpha_{int(c)}" for c in wide.columns]
        return wide.reset_index()

    # ── analysis only ──────────────────────────────────────────────────────

    def benchmark_history(self, start: date, end: date) -> pd.DataFrame:
        """
        Full Benchmark OHLCV series over [start, end].
        For use by BacktestAnalyzer after the backtest completes — not for strategies.
        """
        df = pd.read_sql_query(
            "SELECT w.date, w.ticker, w.open, w.high, w.low, w.close, w.volume, w.tri "
            "FROM weekly_bar w JOIN asset a ON w.ticker = a.ticker "
            "WHERE a.category = 'Benchmark' AND w.date >= ? AND w.date <= ?",
            self._conn,
            params=[start.isoformat(), end.isoformat()],
        )
        df["date"] = _dates(df["date"])
        return df

    # ── private ────────────────────────────────────────────────────────────

    def _snapshot(self, category: str) -> pd.DataFrame:
        """OHLCV cross-section for a given asset category on terminal.day."""
        d = self.day
        df = pd.read_sql_query(
            "SELECT w.date, w.ticker, w.open, w.high, w.low, w.close, w.volume, w.tri "
            "FROM weekly_bar w JOIN asset a ON w.ticker = a.ticker "
            "WHERE a.category = ? AND w.date = ?",
            self._conn,
            params=[category, d.isoformat()],
        )
        df["date"] = _dates(df["date"])
        return df

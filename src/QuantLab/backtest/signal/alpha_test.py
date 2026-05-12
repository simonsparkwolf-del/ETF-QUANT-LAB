"""Alpha-only backtest signal — scores from ``QuoteTerminal.bars()`` ``alpha_*`` columns."""

from __future__ import annotations

from collections import OrderedDict
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from QuantLab.backtest.signal.basic import Signal

if TYPE_CHECKING:
    from QuantLab.backtest.quote_terminal import QuoteTerminal

# Same subset as QuantLab.signal.ml.signal_1 REQUIRED["alpha"].
ALPHA_IDS: tuple[int, ...] = (
    6,
    10,
    14,
    16,
    18,
    19,
    20,
    22,
    23,
    24,
    26,
    30,
    31,
    32,
    34,
    37,
    40,
    44,
    51,
    53,
    54,
    57,
    61,
    64,
    66,
    72,
    83,
    95,
    101,
    108,
    110,
    116,
    118,
    123,
    125,
    127,
    128,
    130,
    135,
    136,
)


class AlphaBacktestSignal(Signal):
    """Cross-section scores from premerged ``alpha_{id}`` in ``terminal.bars()``."""

    def __init__(self, alpha_id: int, start_date: date, end_date: date) -> None:
        super().__init__(f"alpha_{alpha_id}")
        self._alpha_id = int(alpha_id)
        self._start = start_date
        self._end = end_date
        self._bars: pd.DataFrame | None = None
        self._col = f"alpha_{self._alpha_id}"

    def bind(self, terminal: QuoteTerminal) -> None:
        super().bind(terminal)
        self._bars = terminal.bars(self._start, self._end)

    def analyze(self) -> OrderedDict[str, float]:
        assert self.terminal is not None
        assert self._bars is not None
        today = self.terminal.day
        if self._col not in self._bars.columns:
            tickers = sorted(self.terminal.today_etfs()["ticker"].unique().tolist())
            return OrderedDict((tk, 0.0) for tk in tickers)

        day_rows = self._bars.loc[self._bars["date"] == today, ["ticker", self._col]]
        scores: dict[str, float] = {}
        for _, row in self.terminal.today_etfs().iterrows():
            tk = str(row["ticker"])
            m = day_rows.loc[day_rows["ticker"] == tk, self._col]
            if m.empty or pd.isna(m.iloc[0]):
                scores[tk] = 0.0
            else:
                scores[tk] = float(m.iloc[0])
        return OrderedDict(sorted(scores.items()))

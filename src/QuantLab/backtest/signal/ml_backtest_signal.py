"""MLBacktestSignal — wraps QuantLab.signal.ml.signal_N as a backtest Signal.

Panel is built inside bind() using the engine's own QuoteTerminal, so no
separate DB connection is opened.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING

import pandas as pd

from QuantLab.backtest.schema.signal import Scores, symmetric
from QuantLab.backtest.signal.basic import Signal

if TYPE_CHECKING:
    from QuantLab.backtest.quote_terminal import QuoteTerminal


class MLBacktestSignal(Signal):
    """Backtest Signal backed by a pre-computed ML signal column in weekly_signal.

    The signal name is derived from the DB column convention (signal_{id}).
    signal_id in [1..N] — the set of available IDs is queried from the DB via
    QuoteTerminal.signal_ids(), not hardcoded here.
    """

    def __init__(self, signal_id: int) -> None:
        super().__init__(f"signal_{signal_id}")
        self._signal_id = signal_id
        self._panel_df: pd.DataFrame | None = None


    # ── per-bar ────────────────────────────────────────────────────────────

    def analyze(self) -> Scores|None:
        assert self.terminal is not None
        signal_name = f"signal_{self._signal_id}"
        try:
            signals = self.terminal.signals()[["ticker", signal_name]]
        except KeyError:
            return None
        tickers = sorted(signals["ticker"].unique().tolist())
        scores: dict[str, float] = {}
        for ticker in tickers:
            row = signals.loc[signals["ticker"] == ticker, signal_name]
            scores[ticker] = float(row.iloc[0]) if not row.empty else 0.0
        return symmetric(OrderedDict(scores))
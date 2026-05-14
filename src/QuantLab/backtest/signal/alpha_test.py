"""Alpha-only backtest signal — scores from terminal.alphas() on terminal.day."""

from __future__ import annotations

from collections import OrderedDict

import pandas as pd

from QuantLab.backtest.schema.signal import Scores, symmetric
from QuantLab.backtest.signal.basic import Signal


class AlphaBacktestSignal(Signal):
    """Cross-section scores from a single pre-computed alpha on terminal.day."""

    def __init__(self, alpha_id: int) -> None:
        super().__init__(f"alpha_{alpha_id}")
        self._alpha_id = int(alpha_id)

    def analyze(self) -> Scores:
        assert self.terminal is not None
        col = f"alpha_{self._alpha_id}"
        tickers = sorted(self.terminal.etfs()["ticker"].unique().tolist())

        df = self.terminal.alphas(alpha_ids=(self._alpha_id,))
        if df.empty or col not in df.columns:
            return symmetric(OrderedDict((t, 0.0) for t in tickers))

        indexed = df.set_index("ticker")[col]
        scores: dict[str, float] = {}
        for t in tickers:
            if t in indexed.index:
                val = indexed.loc[t]
                scores[t] = 0.0 if pd.isna(val) else float(val)
            else:
                scores[t] = 0.0
        return symmetric(OrderedDict(sorted(scores.items())))

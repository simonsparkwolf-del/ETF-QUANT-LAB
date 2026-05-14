"""DualHeadAlphaSignal — independent alpha factors for the long and short books."""

from __future__ import annotations

from collections import OrderedDict

import pandas as pd

from QuantLab.backtest.schema.signal import Scores
from QuantLab.backtest.signal.basic import Signal


class LongShortAlphaSignal(Signal):
    """Two independent alpha factors: one drives long ranking, one drives short ranking.

    The ``"long"`` and ``"short"`` keys of the returned Scores are computed
    from separate alpha IDs, so each side of the book can be optimised
    independently without forcing a single signal to serve both purposes.

    Parameters
    ----------
    long_alpha_id:
        Alpha ID used to rank ETFs for the long book (higher score → better long).
    short_alpha_id:
        Alpha ID used to rank ETFs for the short book (lower score → better short,
        i.e. the strategy should short the bottom-ranked ETFs).
    """

    def __init__(self, long_alpha_id: int, short_alpha_id: int) -> None:
        super().__init__(f"ls_alpha_l{long_alpha_id}_s{short_alpha_id}")
        self._long_id = int(long_alpha_id)
        self._short_id = int(short_alpha_id)

    def _fetch(self, alpha_id: int) -> OrderedDict[str, float]:
        assert self.terminal is not None
        col = f"alpha_{alpha_id}"
        tickers = sorted(self.terminal.etfs()["ticker"].unique().tolist())
        df = self.terminal.alphas(alpha_ids=(alpha_id,))
        if df.empty or col not in df.columns:
            return OrderedDict((t, 0.0) for t in tickers)
        indexed = df.set_index("ticker")[col]
        scores: dict[str, float] = {}
        for t in tickers:
            if t in indexed.index:
                val = indexed.loc[t]
                scores[t] = 0.0 if pd.isna(val) else float(val)
            else:
                scores[t] = 0.0
        return OrderedDict(sorted(scores.items()))

    def analyze(self) -> Scores:
        return {
            "long": self._fetch(self._long_id),
            "short": self._fetch(self._short_id),
        }

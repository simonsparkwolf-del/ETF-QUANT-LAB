from __future__ import annotations

import random
from collections import OrderedDict

from QuantLab.backtest.schema.signal import Scores, symmetric
from QuantLab.backtest.signal.basic import Signal


class DebugSignal(Signal):
    def analyze(self) -> Scores:
        assert self.terminal is not None
        tickers = self.terminal.etfs()["ticker"].unique().tolist()
        random.shuffle(tickers)
        ranking: OrderedDict[str, float] = OrderedDict(
            (ticker, random.random()) for ticker in tickers
        )
        return symmetric(ranking)

from __future__ import annotations

import random
from collections import OrderedDict
from typing import TYPE_CHECKING

from QuantLab.backtest.signal.basic import Signal

if TYPE_CHECKING:
    pass


class DebugSignal(Signal):
    def analyze(self) -> OrderedDict[str, float]:
        assert self.terminal is not None
        t = self.terminal.today_etfs()
        tickers = t["ticker"].unique().tolist()
        random.shuffle(tickers)
        ranking: OrderedDict[str, float] = OrderedDict()
        for ticker in tickers:
            ranking[ticker] = random.random()
        return ranking

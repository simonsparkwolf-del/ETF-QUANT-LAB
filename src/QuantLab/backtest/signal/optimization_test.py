from __future__ import annotations

from collections import OrderedDict

from QuantLab.backtest.schema.signal import Scores, symmetric
from QuantLab.backtest.signal.basic import Signal


class OptimizationTestSignal(Signal):
    """
    Test signal for softmax optimization: every ETF in ``terminal.etfs()``
    gets the same score ``1.0`` (equal weights after softmax).
    """

    def analyze(self) -> Scores:
        assert self.terminal is not None
        tickers = sorted(self.terminal.etfs()["ticker"].unique().tolist())
        return symmetric(OrderedDict((tk, 1.0) for tk in tickers))

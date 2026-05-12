from __future__ import annotations

from collections import OrderedDict

from QuantLab.backtest.signal.basic import Signal


class OptimizationTestSignal(Signal):
    """
    Test signal for softmax optimization: every ETF in ``terminal.today_etfs()``
    gets the same score ``1.0`` (equal weights after softmax).
    """

    def analyze(self) -> OrderedDict[str, float]:
        assert self.terminal is not None
        t = self.terminal.today_etfs()
        tickers = sorted(t["ticker"].unique().tolist())
        return OrderedDict((tk, 1.0) for tk in tickers)

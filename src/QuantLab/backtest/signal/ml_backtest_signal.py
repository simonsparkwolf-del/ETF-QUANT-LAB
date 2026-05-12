"""MLBacktestSignal — wraps QuantLab.signal.ml.signal_N as a backtest Signal.

Panel is built inside bind() using the engine's own QuoteTerminal, so no
separate DB connection is opened.
"""

from __future__ import annotations

import importlib
from collections import OrderedDict
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from QuantLab.backtest.signal.basic import Signal

if TYPE_CHECKING:
    from QuantLab.backtest.quote_terminal import QuoteTerminal


_SIGNAL_NAMES: dict[int, str] = {
    1: "ml1_LightGBM_frs3",
    2: "ml2_Ensemble_RankAvg_frs1",
    3: "ml3_XGBoost_frs3",
    4: "ml4_PCA_Ridge_frs3",
    5: "ml5_MLP_frs2",
}


class MLBacktestSignal(Signal):
    """Backtest Signal backed by a QuantLab.signal.ml.signal_{N} panel function.

    signal_id in [1..5].  Date range must match the BacktestConfig so that
    terminal.bars() covers every rebalance date.

    Panel is computed once in bind() — reusing the engine's terminal — and
    cached for O(1) lookup per analyze() call.
    """

    def __init__(self, signal_id: int) -> None:
        super().__init__(_SIGNAL_NAMES.get(signal_id, f"ml_signal_{signal_id}"))
        self._signal_id = signal_id
        self._panel_df: pd.DataFrame | None = None


    # ── per-bar ────────────────────────────────────────────────────────────

    def analyze(self) -> OrderedDict[str, float]:
        assert self.terminal is not None 
        today = self.terminal.day
        etfs = self.terminal.today_etfs()
        signal_name = f"signal_{self._signal_id}"
        signals = self.terminal.signals()
        signals = signals[["ticker",signal_name ]]
        tickers = sorted(signals["ticker"].unique().tolist())
        scores: dict[str, float] = {}
        for ticker in tickers:
            row = signals.loc[signals["ticker"]==ticker,signal_name]
            scores[ticker] = float(row.iloc[0]) if not row.empty else 0.0
        return OrderedDict(scores)
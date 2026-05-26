from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from QuantLab.backtest.schema.signal import Scores

if TYPE_CHECKING:
    from QuantLab.backtest.quote_terminal import QuoteTerminal


class Signal(ABC):
    def __init__(self, name: str):
        self.name = name
        self.terminal: QuoteTerminal | None = None

    def bind(self, terminal: QuoteTerminal) -> None:
        self.terminal = terminal

    @abstractmethod
    def analyze(self) -> Scores|None:
        """Per-ETF scores at terminal.day.

        Returns a dict with keys ``"long"`` and ``"short"``, each mapping
        ticker → float score.  Single-head signals return the same OrderedDict
        under both keys (via ``symmetric()``); dual-head signals return
        independent dicts.
        """

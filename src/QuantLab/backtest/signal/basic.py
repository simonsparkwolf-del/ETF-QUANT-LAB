from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from QuantLab.backtest.quote_terminal import QuoteTerminal


class Signal(ABC):
    def __init__(self, name: str):
        self.name = name
        self.terminal: QuoteTerminal | None = None

    def bind(self, terminal: QuoteTerminal) -> None:
        self.terminal = terminal

    @abstractmethod
    def analyze(self) -> OrderedDict[str, float]:
        """Ranking / scores for ETFs at ``terminal.day``."""

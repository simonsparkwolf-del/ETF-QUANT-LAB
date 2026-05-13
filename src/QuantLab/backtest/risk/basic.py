from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from QuantLab.backtest.schema.backtest import Action
from QuantLab.backtest.schema.risk import (
    EndTrade,
    MaxPosition,
    NoTrade,
    PositionChange,
    RiskAction,
    YesTrade,
)

if TYPE_CHECKING:
    from QuantLab.backtest.quote_terminal import QuoteTerminal


class Risk(ABC):
    def __init__(self, name: str):
        self.name = name
        self.terminal: QuoteTerminal | None = None
        self._risk_actions: list[RiskAction] = []

    def bind(self, terminal: QuoteTerminal) -> None:
        self.terminal = terminal

    def load_account(self, account) -> None:
        pass

    def act(self, actions: list[Action]) -> tuple[list[Action], list[RiskAction]]:
        """
        Engine entrypoint.

        - Clears previous risk actions
        - Calls `on_action()` to filter/transform actions
        - Returns (actions, risk_actions) so Strategy can respond
        """
        self._risk_actions = []
        filtered = self.on_action(actions)
        return filtered, list(self._risk_actions)

    # ---- RiskAction helpers (emit from subclasses) ----
    def scale(self, ratio: float, reason: str = "") -> None:
        assert self.terminal is not None
        self._risk_actions.append(
            PositionChange(ratio=ratio, update_at=self.terminal.day, reason=reason)
        )

    def max_pos(self, max_weight: float, reason: str = "") -> None:
        assert self.terminal is not None
        self._risk_actions.append(
            MaxPosition(max_weight=max_weight, update_at=self.terminal.day, reason=reason)
        )

    def stop(self, direction: str, reason: str = "") -> None:
        assert self.terminal is not None
        self._risk_actions.append(
            NoTrade(direction=direction, update_at=self.terminal.day, reason=reason)
        )

    def allow(self, direction: str, reason: str = "") -> None:
        assert self.terminal is not None
        self._risk_actions.append(
            YesTrade(direction=direction, update_at=self.terminal.day, reason=reason)
        )

    def end(self, reason: str = "") -> None:
        assert self.terminal is not None
        self._risk_actions.append(EndTrade(update_at=self.terminal.day, reason=reason))

    @abstractmethod
    def on_action(self, actions: list[Action]) -> list[Action]:
        ...

from __future__ import annotations

from QuantLab.backtest.schema.backtest import Action
from QuantLab.backtest.risk.basic import Risk


class DebugRisk(Risk):
    def on_action(self, actions: list[Action]) -> list[Action]:
        return actions

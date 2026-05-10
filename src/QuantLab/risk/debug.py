from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from abc import ABC,abstractmethod
from collections import OrderedDict
from QuantLab.risk.basic import Risk
if TYPE_CHECKING:
    from datetime import datetime
    import pandas as pd

class DebugRisk(Risk):
    def __init__(self, name: str):
        self.name = name
        self.bar: pd.DataFrame|None = None

    def on_bar(self, bar: pd.DataFrame):
        self.bar = bar

    def on_action(self, actions: list[Action]) -> list[Action]:
        return actions


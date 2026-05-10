from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from abc import ABC,abstractmethod
from collections import OrderedDict
from QuantLab.schema.backtest import Action
from QuantLab.schema.backtest import Account
import random
if TYPE_CHECKING:
    from datetime import datetime
    import pandas as pd
    from QuantLab.signal.basic import Signal
    from QuantLab.schema.backtest_config import BacktestConfig
    from datetime import date

class Strategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.signal: Signal
        self.bar: pd.DataFrame|None = None
        self.date: date|None = None
        self.account: Account|None = None
    
    def on_bar(self, bar: pd.DataFrame):
        self.bar = bar
        self.date = bar["date"].iloc[0]
    
    def load_account(self, account: Account):
        self.account = account

    @abstractmethod
    def on_ranking(self, ranking: OrderedDict[str,float]) -> list[Action]:
        """
        analyze the ranking and generate actions
        """
    @abstractmethod
    def on_holding(self)-> list[Action]:
        """
        deal with the holding of the account
        """
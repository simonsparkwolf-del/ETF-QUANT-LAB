from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from abc import ABC,abstractmethod
from collections import OrderedDict
import random
from QuantLab.signal.basic import Signal
if TYPE_CHECKING:
    from datetime import datetime
    import pandas as pd

class DebugSignal(Signal):
    def __init__(self, name: str):
        self.name = name
        self.bar: pd.DataFrame|None = None
    
    def on_bar(self, bar: pd.DataFrame):
        self.bar = bar
    
    def analyze(self) -> OrderedDict[str,float]:
        """
        Analyze the signal, return the ranking,score and other metrics of the ETFs 
        """
        tickers = self.bar["ticker"].unique().tolist()
        random.shuffle(tickers)
        ranking = OrderedDict()
        for ticker in tickers:
            ranking[ticker] = random.random()
        return ranking

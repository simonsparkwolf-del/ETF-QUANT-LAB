from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from abc import ABC,abstractmethod
from collections import OrderedDict
import random
if TYPE_CHECKING:
    from datetime import datetime
    import pandas as pd

class Signal(ABC):
    def __init__(self, name: str):
        self.name = name
        self.bar: pd.DataFrame|None = None
    
    def on_bar(self, bar: pd.DataFrame):
        self.bar = bar
    
    @abstractmethod
    def analyze(self) -> OrderedDict[str,float]:
        """
        Analyze the signal, return the ranking,score and other metrics of the ETFs 
        """

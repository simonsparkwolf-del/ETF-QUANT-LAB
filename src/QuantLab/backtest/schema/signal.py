from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from datetime import date

EPS = 1e-6

@dataclass(frozen=True)
class Signal:
    ticker: str
    score:float

@dataclass
class Ranking:
    board: list[Signal]

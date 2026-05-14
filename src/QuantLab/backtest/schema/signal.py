from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

EPS = 1e-6

# Keys used in the Scores dict returned by Signal.analyze().
LONG_KEY: Literal["long"] = "long"
SHORT_KEY: Literal["short"] = "short"

# Type alias for the dual-head score map produced by every Signal.
Scores = dict[str, OrderedDict[str, float]]


def symmetric(scores: OrderedDict[str, float]) -> Scores:
    """Wrap a single score dict into both long and short keys (same object)."""
    return {LONG_KEY: scores, SHORT_KEY: scores}


@dataclass(frozen=True)
class Signal:
    ticker: str
    score_name: str
    score: float

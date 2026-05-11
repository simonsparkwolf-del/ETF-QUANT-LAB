from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from datetime import datetime
if TYPE_CHECKING:
    from datetime import date

# Typed union for engine/module interactions.
RiskAction = "PositionChange | MaxPosition | NoTrade | YesTrade | EndTrade"

@dataclass(frozen=True)
class PositionChange:
    ratio: float
    update_at: date
    reason: str
    severity:int = 0

@dataclass(frozen=True)
class MaxPosition:
    """
    Max position weight cap per ticker, expressed as a fraction of NAV.

    Example: max_weight=0.10 means each ticker's absolute exposure should not exceed 10% of NAV.
    """
    max_weight: float
    update_at: date
    reason: str
    severity: int = 0

@dataclass(frozen=True)
class NoTrade:
    """
    now new trade will be opened
    """
    direction: Literal["long", "short"]
    update_at: date
    reason: str
    severity:int = 1

@dataclass(frozen=True)
class YesTrade:
    direction: Literal["long", "short"]
    update_at: date
    reason: str
    severity:int = 1

@dataclass(frozen=True)
class EndTrade:
    update_at: date
    reason: str
    severity:int = 2


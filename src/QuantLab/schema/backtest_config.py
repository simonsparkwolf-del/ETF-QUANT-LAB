
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from signal.basic import Signal
    from pathlib import Path
    from strategy.basic import Strategy
    from risk.basic import Risk
    from datetime import date
    from schema.backtest import Account

@dataclass(frozen=True)
class BacktestConfig:
    name: str
    start_date: date
    end_date: date
    db_path: Path
    save_path: Path
    signal: Signal
    strategy: Strategy
    risk: Risk
    account: Account
    long_cost: float = 0.0
    short_cost_per_day: float = 0.0
    base_slippage: float = 0.0
    long_enabled: bool = True
    short_enabled: bool = True
    save_eval_artifacts: bool = True
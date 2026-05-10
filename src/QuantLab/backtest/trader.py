from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from abc import ABC,abstractmethod
from collections import OrderedDict
from QuantLab.schema.backtest import Action,Trade,Security,Liability
from QuantLab.schema.backtest_config import BacktestConfig

class Trader:
    def __init__(self, config: BacktestConfig):
        self.config = config

    def on_action(self,action: Action) -> Trade|None:
        """
        assuming all action are executed
        """
        if action.direction == "long":
            if action.side == "buy":
                volume = action.volume
                price = action.price
                fee = self.config.long_cost * volume * price
                slippage = self.config.base_slippage
                target = Security(
                    ticker=action.ticker,
                    volume=volume,
                    price=price,
                    market_price=price
                )
                return Trade(
                    direction=action.direction,
                    side=action.side,
                    ticker=action.ticker,
                    volume=volume,
                    price=price,
                    fee=fee,
                    slippage=slippage,
                    date=action.date,
                    target=target
                )
            elif action.side == "sell":
                volume = action.volume
                price = action.price
                fee = self.config.long_cost * volume * price
                slippage = self.config.base_slippage
                target = Security(
                    ticker=action.ticker,
                    volume=volume,
                    price=price,
                    market_price=price
                )
                return Trade(direction=action.direction,
                    side=action.side,
                    ticker=action.ticker,
                    volume=volume,
                    price=price,
                    fee=fee,
                    slippage=slippage,
                    date=action.date,
                    target=target
                )
        elif action.direction == "short":
            if action.side == "sell":
                volume = action.volume
                price = action.price
                fee = 0
                slippage = self.config.base_slippage
                target = Liability(
                    ticker=action.ticker,
                    volume=volume,
                    price=price,
                    market_price=price,
                    start_date=action.date
                )
                return Trade(
                    direction=action.direction,
                    side=action.side,
                    ticker=action.ticker,
                    volume=volume,
                    price=price,
                    fee=fee,
                    slippage=slippage,
                    date=action.date,
                    target=target
                )
            elif action.side == "buy":
                volume = action.volume
                price = action.price
                assert action.short_start_date is not None, "Short start date is required"
                assert action.short_value is not None, "Short value is required"
                days = (action.date - action.short_start_date).days
                fee = self.config.short_cost_per_day * days * action.short_value
                slippage = self.config.base_slippage
                target = Liability(
                    ticker=action.ticker,
                    volume=volume,
                    price=price,
                    market_price=price,
                    start_date=action.short_start_date
                )
                return Trade(
                    direction=action.direction,
                    side=action.side,
                    ticker=action.ticker,
                    volume=volume,
                    price=price,
                    fee=fee,
                    slippage=slippage,
                    date=action.date,
                    target=target
                )
            
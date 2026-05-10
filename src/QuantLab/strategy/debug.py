from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from abc import ABC,abstractmethod
from collections import OrderedDict
from QuantLab.schema.backtest import Action
from QuantLab.schema.backtest import Account
import random
from QuantLab.strategy.basic import Strategy
if TYPE_CHECKING:
    from datetime import datetime
    import pandas as pd
    from QuantLab.signal.basic import Signal
    from QuantLab.schema.backtest_config import BacktestConfig
    from datetime import date

class DebugStrategy(Strategy):
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

    def on_ranking(self, ranking: OrderedDict[str,float]) -> list[Action]:
        """
        Run the strategy
        """
        actions = []
        tickers = list(ranking.keys())
        ticker = tickers[0]
        price = self.bar[self.bar["ticker"] == ticker]["close"].iloc[0]
        action = Action(
            direction="long",
            side="buy",
            ticker=ticker,
            price=price,
            volume=random.uniform(0.0,0.01*self.account.cash)/price,
            date=self.date
        )
        actions.append(action)
        ticker = tickers[-1]
        price = self.bar[self.bar["ticker"] == ticker]["close"].iloc[0]
        action = Action(
            direction="short",
            side="sell",
            ticker=ticker,
            price=price,
            volume=random.uniform(0.0,0.01*self.account.cash)/price,
            date=self.date
        )
        actions.append(action)
        return actions

    def on_holding(self)-> list[Action]:
        actions = []
        if self.account.securities.keys():
            for ticker in self.account.securities.keys():
                if random.random() < 0.5:
                    security = self.account.securities[ticker]
                    action = Action(
                        direction="long",
                        side="sell",
                        ticker=ticker,
                        price=security.market_price,
                        volume=security.volume,
                        date=self.date
                    )
                    actions.append(action)
        if self.account.liabilities.keys():
            for ticker in self.account.liabilities.keys():
                if random.random() < 0.5:
                    liability = self.account.liabilities[ticker]
                    action = Action(
                        direction="short",
                        side="buy",
                        ticker=ticker,
                        price=liability.market_price,
                        volume=liability.volume,
                        date=self.date,
                        short_start_date=liability.start_date,
                        short_value=liability.volume*liability.price
                    )
                    actions.append(action)
        return actions
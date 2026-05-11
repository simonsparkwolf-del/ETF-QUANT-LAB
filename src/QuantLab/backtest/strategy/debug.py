from __future__ import annotations

import random
from collections import OrderedDict

from QuantLab.backtest.schema.backtest import Account, Action
from QuantLab.backtest.strategy.basic import Strategy


class DebugStrategy(Strategy):
    def on_ranking(self, ranking: OrderedDict[str, float]) -> list[Action]:
        assert self.terminal is not None and self.account is not None
        actions: list[Action] = []
        tickers = list(ranking.keys())
        ticker = tickers[0]
        q = self.terminal.quote(ticker)
        price = float(q.loc["close"]) if not q.empty else 0.0
        actions.append(
            Action(
                direction="long",
                side="buy",
                ticker=ticker,
                price=price,
                volume=random.uniform(0.0, 0.01 * self.account.cash) / price
                if price > 0
                else 0.0,
                date=self.terminal.day,
            )
        )
        ticker = tickers[-1]
        q = self.terminal.quote(ticker)
        price = float(q.loc["close"]) if not q.empty else 0.0
        actions.append(
            Action(
                direction="short",
                side="sell",
                ticker=ticker,
                price=price,
                volume=random.uniform(0.0, 0.01 * self.account.cash) / price
                if price > 0
                else 0.0,
                date=self.terminal.day,
            )
        )
        return actions

    def on_holding(self) -> list[Action]:
        assert self.terminal is not None and self.account is not None
        actions: list[Action] = []
        for ticker in list(self.account.securities.keys()):
            if random.random() < 0.5:
                security = self.account.securities[ticker]
                actions.append(
                    Action(
                        direction="long",
                        side="sell",
                        ticker=ticker,
                        price=security.market_price,
                        volume=security.volume,
                        date=self.terminal.day,
                    )
                )
        for ticker in list(self.account.liabilities.keys()):
            if random.random() < 0.5:
                liability = self.account.liabilities[ticker]
                actions.append(
                    Action(
                        direction="short",
                        side="buy",
                        ticker=ticker,
                        price=liability.market_price,
                        volume=liability.volume,
                        date=self.terminal.day,
                        short_start_date=liability.start_date,
                        short_value=liability.volume * liability.price,
                    )
                )
        return actions

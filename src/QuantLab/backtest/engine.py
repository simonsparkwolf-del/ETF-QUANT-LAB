from __future__ import annotations
from typing import TYPE_CHECKING
from QuantLab.backtest.db_helper import dblite
from datetime import timedelta
from QuantLab.schema.backtest import Action,Trade
from QuantLab.backtest.trader import Trader
from QuantLab.backtest.analyzer import BacktestAnalyzer
from tqdm import tqdm
import pandas as pd
if TYPE_CHECKING:
    from QuantLab.schema.backtest import Account
    from QuantLab.schema.backtest_config import BacktestConfig

class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.account = self.config.account
        self.signal = self.config.signal
        self.strategy = self.config.strategy
        self.strategy.load_account(self.account)
        self.risk = self.config.risk
        self.db_helper = dblite(self.config.db_path)
        self.bars = self._build_bars()
        self.trader = Trader(self.config)
        self.bar = None
        

    def _build_bars(self) -> pd.DataFrame:
        bars: pd.DataFrame = self.db_helper.load_table()
        start = bars["date"].min()
        end = bars["date"].max()
        assert start <= self.config.start_date <= end, "Start date is out of range"
        assert start <= self.config.end_date <= end, "End date is out of range"
        bars = bars.loc[bars["date"] >= self.config.start_date,:]
        bars = bars.loc[bars["date"] <= self.config.end_date,:]
        bars["close"] = bars["close"].ffill().bfill()
        return bars
    
    def on_actions(self,actions: list[Action]) -> list[Trade]:
        """
        assuming all action are executed
        """
        trades = []
        for action in actions:
            if action.direction == "long" and self.config.long_enabled:
                pass
            elif action.direction == "short" and self.config.short_enabled:
                pass
            else:
                continue
            trade = self.trader.on_action(action)
            trades.append(trade)
        return trades

    
    def _set_market_price(self,account: Account,bar: pd.DataFrame):
        for ticker in account.securities.keys():
            security = account.securities[ticker]
            prices = bar.loc[bar["ticker"] == ticker, "close"]
            if not prices.empty:
                security.market_price = float(prices.iloc[0])
        for ticker in account.liabilities.keys():
            liability = account.liabilities[ticker]
            prices = bar.loc[bar["ticker"] == ticker, "close"]
            if not prices.empty:
                liability.market_price = float(prices.iloc[0])

    
    def _on_bar(self,bar: pd.DataFrame):
        assert not bar.empty, "Bar is empty"
        self.signal.on_bar(bar)
        self.strategy.on_bar(bar)
        self.risk.on_bar(bar)
        self._set_market_price(self.account,bar)
        self.bar = bar

    def run(self):
        start_date = self.config.start_date
        end_date = self.config.end_date
        days = self.bars.loc[(self.bars["date"] >= start_date)&(self.bars["date"]<=end_date),"date"].unique().tolist()
        days.sort()
        for today in tqdm(days):
            bar = self.bars.loc[self.bars["date"] == today,:]
            self._on_bar(bar)

            ranking = self.signal.analyze()

            actions = self.strategy.on_ranking(ranking)
            actions.extend(self.strategy.on_holding())
            actions = self.risk.on_action(actions)

            if actions:
                trades = self.on_actions(actions)
                self.account.on_trades(trades)

            self.account.snapshot(today)
            today += timedelta(days=1)

    def evaluate(self) -> dict[str, float | int]:
        analyzer = BacktestAnalyzer(
            self.config.save_path,
            self.config.name,
            save_artifacts=self.config.save_eval_artifacts,
        )
        return analyzer.evaluate(self.account.value_history, self.account.holding_history)
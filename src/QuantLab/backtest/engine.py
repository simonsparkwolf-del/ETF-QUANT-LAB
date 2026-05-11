from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pandas as pd
from tqdm import tqdm

from QuantLab.backtest.analyzer import BacktestAnalyzer
from QuantLab.backtest.quote_terminal import QuoteTerminal
from QuantLab.backtest.trader import Trader
from QuantLab.backtest.schema.backtest import Action, Trade

if TYPE_CHECKING:
    from QuantLab.backtest.schema.backtest import Account
    from QuantLab.backtest.schema.backtest_config import BacktestConfig


class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.account = self.config.account
        self.signal = self.config.signal
        self.strategy = self.config.strategy
        self.strategy.load_account(self.account)
        self.risk = self.config.risk

        self.terminal = QuoteTerminal(self.config.db_path)
        self.terminal.range_ok(self.config.start_date, self.config.end_date)
        for m in (self.signal, self.strategy, self.risk):
            m.bind(self.terminal)

        self.bars = self._build_bars()
        self.trader = Trader(self.config)
        self.bar = None

    def _build_bars(self) -> pd.DataFrame:
        bars: pd.DataFrame = self.terminal.bars(
            self.config.start_date, self.config.end_date
        )
        bars["close"] = bars["close"].ffill().bfill()
        return bars

    def on_actions(self, actions: list[Action]) -> list[Trade]:
        """Assuming all actions are executed."""
        trades: list[Trade] = []
        for action in actions:
            if action.direction == "long" and self.config.long_enabled:
                pass
            elif action.direction == "short" and self.config.short_enabled:
                pass
            else:
                continue
            trade = self.trader.on_action(action)
            if trade is not None:
                trades.append(trade)
        return trades

    def _set_market_price(self, account: Account) -> None:
        """Sync account marks with ``terminal.quote`` on ``terminal.day``."""
        for ticker in account.securities.keys():
            security = account.securities[ticker]
            q = self.terminal.quote(ticker)
            if not q.empty:
                security.market_price = float(q.loc["close"])
        for ticker in account.liabilities.keys():
            liability = account.liabilities[ticker]
            q = self.terminal.quote(ticker)
            if not q.empty:
                liability.market_price = float(q.loc["close"])

    def _step(self, bar: pd.DataFrame) -> None:
        assert not bar.empty, "Bar is empty"
        self._set_market_price(self.account)
        self.bar = bar

    def run(self) -> None:
        start_date = self.config.start_date
        end_date = self.config.end_date
        days = (
            self.bars.loc[
                (self.bars["date"] >= start_date) & (self.bars["date"] <= end_date),
                "date",
            ]
            .unique()
            .tolist()
        )
        days.sort()
        for today in tqdm(days):
            self.terminal.at(today)
            bar = self.bars.loc[self.bars["date"] == today, :]
            self._step(bar)
            self.strategy.on_day_start()

            ranking = self.signal.analyze()

            actions = self.strategy.on_ranking(ranking)
            actions.extend(self.strategy.on_holding())
            actions, risk_actions = self.risk.act(actions)
            actions = self.strategy.apply_risk_actions(actions, risk_actions)

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
        return analyzer.evaluate(
            self.account.value_history,
            self.account.holding_history,
            self.terminal,
        )

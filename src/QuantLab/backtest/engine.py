from __future__ import annotations

from typing import TYPE_CHECKING

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
        self.strategy.long_cost = self.config.long_cost
        self.strategy.base_slippage = self.config.base_slippage
        self.risk = self.config.risk
        self.risk.load_account(self.account)

        self.terminal = QuoteTerminal(self.config.db_path)
        self.terminal.range_ok(self.config.start_date, self.config.end_date)
        for m in (self.signal, self.strategy, self.risk):
            m.bind(self.terminal)

        self._trading_days = self.terminal.trading_dates(
            self.config.start_date, self.config.end_date
        )
        self.trader = Trader(self.config)

    def on_actions(self, actions: list[Action]) -> list[Trade]:
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
        """Sync account marks with terminal.quote on terminal.day."""
        for ticker in account.securities:
            q = self.terminal.quote(ticker)
            if not q.empty:
                account.securities[ticker].market_price = float(q.loc["close"])
        for ticker in account.liabilities:
            q = self.terminal.quote(ticker)
            if not q.empty:
                account.liabilities[ticker].market_price = float(q.loc["close"])

    def run(self) -> None:
        for today in tqdm(self._trading_days):
            self.terminal.at(today)
            self._set_market_price(self.account)
            self.strategy.on_day_start()

            ranking = self.signal.analyze()
            actions = self.strategy.on_ranking(ranking)
            actions.extend(self.strategy.on_holding())
            actions, risk_actions = self.risk.act(actions)
            actions = self.strategy.apply_risk_actions(actions, risk_actions)

            if actions:
                trades = self.on_actions(actions)
                sell_trades = [t for t in trades if t.side == "sell"]
                buy_trades  = [t for t in trades if t.side == "buy"]
                self.account.on_trades(sell_trades)
                self.account.on_trades(buy_trades)

            self.account.snapshot(today)

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

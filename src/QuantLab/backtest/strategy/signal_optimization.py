from __future__ import annotations

import math
from collections import OrderedDict

from QuantLab.backtest.schema.backtest import Action
from QuantLab.backtest.strategy.basic import Strategy

# ``Account.on_trade`` uses strict ``cash < need``; float noise on last leg can differ by ~1e-13.
_CASH_FUDGE = 1e-7


def _stable_softmax(values: list[float]) -> list[float]:
    if not values:
        return []
    m = max(values)
    exps = [math.exp(v - m) for v in values]
    s = sum(exps)
    if s <= 0.0:
        n = len(values)
        return [1.0 / n] * n
    return [e / s for e in exps]


def _sell_cash_credit(
    action_px: float,
    volume: float,
    *,
    long_cost: float,
    base_slippage: float,
) -> float:
    """Cash delta from one long sell, matching ``Trade`` + ``Account.on_trade``."""
    px = float(action_px)
    vol = float(volume)
    slip = float(base_slippage)
    lc = float(long_cost)
    exec_px = px - slip
    fee = lc * px * vol
    return exec_px * vol - fee


def _buy_cash_out(
    action_px: float,
    volume: float,
    *,
    long_cost: float,
    base_slippage: float,
) -> float:
    """Cash delta (positive = outflow) for one long buy, matching ``Trade`` + ``Account``."""
    px = float(action_px)
    vol = float(volume)
    slip = float(base_slippage)
    lc = float(long_cost)
    exec_px = px + slip
    fee = lc * px * vol
    return exec_px * vol + fee


def _buy_volume_for_dollars(
    dollars: float,
    action_px: float,
    *,
    long_cost: float,
    base_slippage: float,
) -> float:
    """Volume so that ``_buy_cash_out(px, vol, ...) == dollars`` (when friction linear in vol)."""
    px = float(action_px)
    if px <= 0.0 or dollars <= 0.0:
        return 0.0
    slip = float(base_slippage)
    lc = float(long_cost)
    per_unit = (px + slip) + lc * px
    if per_unit <= 0.0:
        return 0.0
    return dollars / per_unit


def _max_buy_volume_for_cash(
    action_px: float,
    cash: float,
    *,
    long_cost: float,
    base_slippage: float,
) -> float:
    """Largest ``vol >= 0`` with ``_buy_cash_out(px, vol, ...) <= cash`` (same linear model as ``Account``)."""
    px = float(action_px)
    c = max(0.0, float(cash) - _CASH_FUDGE)
    if px <= 0.0 or c <= 0.0:
        return 0.0
    slip = float(base_slippage)
    lc = float(long_cost)
    per_unit = (px + slip) + lc * px
    if per_unit <= 0.0:
        return 0.0
    return c / per_unit


class SiganlOptimizationStrategy(Strategy):
    """
    Long-only: **all long sells first**, then softmax-weight **buys**.

    Buy notionals are sized off **cash projected after all sells**, using the same
    price / fee / slippage rules as ``Trader`` → ``Trade`` → ``Account.on_trade``.
    Pass ``long_cost`` and ``base_slippage`` **identical** to ``BacktestConfig`` so
    the batch never asks ``Account`` for more cash than will exist after sells.

    Sell / buy **action prices** use the bar **close** from ``terminal.quote`` when
    available (same as typical marks), so sell and reload use one price source.
    """

    def __init__(
        self,
        name: str,
        *,
        long_cost: float = 0.0,
        base_slippage: float = 0.0,
    ) -> None:
        super().__init__(name)
        self.long_cost = float(long_cost)
        self.base_slippage = float(base_slippage)

    def _quote_close(self, ticker: str, *, fallback: float) -> float:
        assert self.terminal is not None
        q = self.terminal.quote(ticker)
        if q.empty:
            return float(fallback)
        px = float(q.loc["close"])
        return px if px > 0.0 else float(fallback)

    def on_ranking(self, ranking: OrderedDict[str, float]) -> list[Action]:
        assert self.terminal is not None and self.account is not None
        account = self.account
        day = self.terminal.day
        lc, slip = self.long_cost, self.base_slippage

        tickers: list[str] = []
        scores: list[float] = []
        prices: list[float] = []

        for ticker, score in ranking.items():
            fb = (
                float(account.securities[ticker].market_price)
                if ticker in account.securities
                else 0.0
            )
            px = self._quote_close(ticker, fallback=fb)
            if px <= 0.0:
                continue
            tickers.append(ticker)
            scores.append(float(score))
            prices.append(px)

        # 1) Flatten: sells use same close as signal / buy leg.
        sells: list[Action] = []
        deployable = float(account.cash)
        for ticker, sec in list(account.securities.items()):
            if sec.volume <= 0.0:
                continue
            px = self._quote_close(ticker, fallback=float(sec.market_price))
            if px <= 0.0:
                continue
            vol = float(sec.volume)
            sells.append(
                Action(
                    direction="long",
                    side="sell",
                    ticker=ticker,
                    price=px,
                    volume=vol,
                    date=day,
                )
            )
            deployable += _sell_cash_credit(px, vol, long_cost=lc, base_slippage=slip)

        self.remaining_amount = max(deployable, 0.0)

        if not tickers:
            return sells

        if deployable <= 0.0:
            return sells

        weights = _stable_softmax(scores)
        n = len(tickers)

        # 2) Buys: softmax slice of ``deployable``, then cap each leg so running cash
        #    never exceeds what ``Account.on_trade`` would allow (forward simulation).
        buys: list[Action] = []
        cash_run = deployable
        remaining_slice = deployable
        for i in range(n):
            t, w, px = tickers[i], weights[i], prices[i]
            if px <= 0.0:
                continue
            if i < n - 1:
                dollars = deployable * w
            else:
                dollars = max(0.0, remaining_slice)
            want = _buy_volume_for_dollars(
                dollars, px, long_cost=lc, base_slippage=slip
            )
            cap = _max_buy_volume_for_cash(
                px, cash_run, long_cost=lc, base_slippage=slip
            )
            vol = min(want, cap)
            if vol > 0.0:
                out = _buy_cash_out(px, vol, long_cost=lc, base_slippage=slip)
                buys.append(
                    Action(
                        direction="long",
                        side="buy",
                        ticker=t,
                        price=px,
                        volume=vol,
                        date=day,
                    )
                )
                cash_run -= out
            if i < n - 1:
                remaining_slice -= deployable * w

        return sells + buys

    def on_holding(self) -> list[Action]:
        return []

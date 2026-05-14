from __future__ import annotations

import math
from collections import OrderedDict
from typing import Literal

from QuantLab.backtest.schema.backtest import Action
from QuantLab.backtest.schema.signal import Scores
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
    px = float(action_px)
    vol = float(volume)
    exec_px = px - float(base_slippage)
    fee = float(long_cost) * px * vol
    return exec_px * vol - fee


def _buy_cash_out(
    action_px: float,
    volume: float,
    *,
    long_cost: float,
    base_slippage: float,
) -> float:
    px = float(action_px)
    vol = float(volume)
    exec_px = px + float(base_slippage)
    fee = float(long_cost) * px * vol
    return exec_px * vol + fee


def _buy_volume_for_dollars(
    dollars: float,
    action_px: float,
    *,
    long_cost: float,
    base_slippage: float,
) -> float:
    px = float(action_px)
    if px <= 0.0 or dollars <= 0.0:
        return 0.0
    per_unit = (px + float(base_slippage)) + float(long_cost) * px
    return dollars / per_unit if per_unit > 0.0 else 0.0


def _max_buy_volume_for_cash(
    action_px: float,
    cash: float,
    *,
    long_cost: float,
    base_slippage: float,
) -> float:
    px = float(action_px)
    c = max(0.0, float(cash) - _CASH_FUDGE)
    if px <= 0.0 or c <= 0.0:
        return 0.0
    per_unit = (px + float(base_slippage)) + float(long_cost) * px
    return c / per_unit if per_unit > 0.0 else 0.0


class SiganlOptimizationStrategy(Strategy):
    """
    Long-only or short-only softmax-weighted strategy.

    mode="long":  flatten all longs → re-buy with softmax(scores).
    mode="short": flatten all shorts → re-short with softmax(-scores).

    Long sizing mirrors projected cash after sells.
    Short sizing uses current NAV as total notional.
    """

    def __init__(
        self,
        name: str,
        *,
        mode: Literal["long", "short"] = "long",
        long_cost: float = 0.0,
        base_slippage: float = 0.0,
    ) -> None:
        super().__init__(name)
        self.mode = mode
        self.long_cost = float(long_cost)
        self.base_slippage = float(base_slippage)

    def _quote_close(self, ticker: str, *, fallback: float) -> float:
        assert self.terminal is not None
        q = self.terminal.quote(ticker)
        if q.empty:
            return float(fallback)
        px = float(q.loc["close"])
        return px if px > 0.0 else float(fallback)

    # ── long ───────────────────────────────────────────────────────────────

    def _on_ranking_long(self, ranking: OrderedDict[str, float]) -> list[Action]:
        assert self.terminal is not None and self.account is not None
        account = self.account
        day = self.terminal.day
        lc, slip = self.long_cost, self.base_slippage

        tickers, scores, prices = [], [], []
        for ticker, score in ranking.items():
            fb = float(account.securities[ticker].market_price) if ticker in account.securities else 0.0
            px = self._quote_close(ticker, fallback=fb)
            if px <= 0.0:
                continue
            tickers.append(ticker)
            scores.append(float(score))
            prices.append(px)

        sells: list[Action] = []
        deployable = float(account.cash)
        for ticker, sec in list(account.securities.items()):
            if sec.volume <= 0.0:
                continue
            px = self._quote_close(ticker, fallback=float(sec.market_price))
            if px <= 0.0:
                continue
            vol = float(sec.volume)
            sells.append(Action(direction="long", side="sell",
                                ticker=ticker, price=px, volume=vol, date=day))
            deployable += _sell_cash_credit(px, vol, long_cost=lc, base_slippage=slip)

        self.remaining_amount = max(deployable, 0.0)

        if not tickers or deployable <= 0.0:
            return sells

        weights = _stable_softmax(scores)
        buys: list[Action] = []
        cash_run = deployable
        remaining_slice = deployable
        n = len(tickers)
        for i in range(n):
            t, w, px = tickers[i], weights[i], prices[i]
            if px <= 0.0:
                continue
            dollars = deployable * w if i < n - 1 else max(0.0, remaining_slice)
            want = _buy_volume_for_dollars(dollars, px, long_cost=lc, base_slippage=slip)
            cap  = _max_buy_volume_for_cash(px, cash_run, long_cost=lc, base_slippage=slip)
            vol  = min(want, cap)
            if vol > 0.0:
                buys.append(Action(direction="long", side="buy",
                                   ticker=t, price=px, volume=vol, date=day))
                cash_run -= _buy_cash_out(px, vol, long_cost=lc, base_slippage=slip)
            if i < n - 1:
                remaining_slice -= deployable * w

        return sells + buys

    # ── short ──────────────────────────────────────────────────────────────

    def _on_ranking_short(self, ranking: OrderedDict[str, float]) -> list[Action]:
        assert self.terminal is not None and self.account is not None
        account = self.account
        day = self.terminal.day

        tickers, scores, prices = [], [], []
        for ticker, score in ranking.items():
            fb = float(account.liabilities[ticker].market_price) if ticker in account.liabilities else 0.0
            px = self._quote_close(ticker, fallback=fb)
            if px <= 0.0:
                continue
            tickers.append(ticker)
            scores.append(float(score))
            prices.append(px)

        covers: list[Action] = []
        for ticker, liab in list(account.liabilities.items()):
            if liab.volume <= 0.0:
                continue
            px = self._quote_close(ticker, fallback=float(liab.market_price))
            if px <= 0.0:
                continue
            covers.append(Action(
                direction="short", side="buy",
                ticker=ticker, price=px, volume=float(liab.volume), date=day,
                short_start_date=liab.start_date,
                short_value=float(liab.volume * liab.price),
            ))

        if not tickers:
            return covers

        # softmax(-score): higher weight → lower-ranked (worse) ETFs
        weights = _stable_softmax([-s for s in scores])
        deployable = float(account.total_value)

        shorts: list[Action] = []
        for t, w, px in zip(tickers, weights, prices):
            notional = deployable * w
            vol = notional / px
            if vol > 0.0:
                shorts.append(Action(
                    direction="short", side="sell",
                    ticker=t, price=px, volume=vol, date=day,
                    short_start_date=day,
                    short_value=notional,
                ))

        return covers + shorts

    # ── Strategy interface ─────────────────────────────────────────────────

    def on_ranking(self, scores: Scores) -> list[Action]:
        if self.mode == "short":
            return self._on_ranking_short(scores["short"])
        return self._on_ranking_long(scores["long"])

    def on_holding(self) -> list[Action]:
        return []

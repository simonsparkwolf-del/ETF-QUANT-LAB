"""AsymmetricLSStrategy — long and short books ranked by independent signals."""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING

import pandas as pd

from QuantLab.backtest.schema.backtest import Action
from QuantLab.backtest.schema.signal import Scores
from QuantLab.backtest.strategy.basic import Strategy

if TYPE_CHECKING:
    from QuantLab.backtest.quote_terminal import QuoteTerminal


class DualSignalStrategy(Strategy):
    """Long-Short sector ETF rotation with independent signals per side.

    - Long:  top ``n_long`` ETFs ranked by ``scores["long"]``, equal weight.
    - Short: bottom ``n_short`` ETFs ranked by ``scores["short"]``, equal weight,
             filtered by alpha_110 (12-week return) < 0.
    - Conflict: if a ticker appears in both target sets, the long side takes
                priority and the ticker is dropped from target_shorts.
    - Stickiness: an existing long is kept while its long-rank <= n_long + threshold;
                  an existing short is kept while its short-rank >= boundary AND
                  alpha_110 < 0.
    - Momentum flip: a held short whose alpha_110 turns >= 0 is force-covered
                     regardless of stickiness.

    When both ``scores["long"]`` and ``scores["short"]`` are identical (e.g. a
    single-head signal wrapped with ``symmetric()``), behaviour is equivalent
    to ``BaselineStrategy``.
    """

    def __init__(
        self,
        name: str,
        n_long: int = 3,
        n_short: int = 3,
        stickiness_threshold: int = 2,
        long_cost: float = 0.0,
        base_slippage: float = 0.0,
    ) -> None:
        super().__init__(name)
        self.n_long = n_long
        self.n_short = n_short
        self.stickiness_threshold = stickiness_threshold
        self.long_cost = long_cost
        self.base_slippage = base_slippage
        self._alpha_cache: dict[str, float] = {}
        self._alpha_cache_day = None

    # ── helpers ────────────────────────────────────────────────────────────

    def _quote_close(self, ticker: str, fallback: float = 0.0) -> float:
        assert self.terminal is not None
        q = self.terminal.quote(ticker)
        if q.empty:
            return float(fallback)
        px = float(q.loc["close"])
        return px if px > 0.0 else float(fallback)

    def _alpha110(self, ticker: str) -> float:
        """12-week cumulative return for ticker on terminal.day. Cached per day."""
        assert self.terminal is not None
        today = self.terminal.day
        if self._alpha_cache_day != today:
            df = self.terminal.alphas(alpha_ids=(110,))
            self._alpha_cache_day = today
            self._alpha_cache = {}
            if not df.empty and "alpha_110" in df.columns:
                for _, row in df.iterrows():
                    v = row["alpha_110"]
                    self._alpha_cache[str(row["ticker"])] = (
                        float(v) if not pd.isna(v) else float("nan")
                    )
        return self._alpha_cache.get(ticker, float("nan"))

    # ── target selection ───────────────────────────────────────────────────

    def _target_longs(self, long_ranking: OrderedDict[str, float]) -> list[str]:
        assert self.account is not None
        ordered = sorted(long_ranking.items(), key=lambda x: x[1], reverse=True)
        all_tickers = [t for t, _ in ordered]
        rank_map = {t: i + 1 for i, t in enumerate(all_tickers)}
        boundary = self.n_long + self.stickiness_threshold

        kept = [
            t for t in self.account.securities
            if rank_map.get(t, len(all_tickers) + 1) <= boundary
        ]
        target = list(kept)
        for t in all_tickers:
            if len(target) >= self.n_long:
                break
            if t not in target:
                target.append(t)
        return target

    def _target_shorts(
        self,
        short_ranking: OrderedDict[str, float],
        exclude: set[str],
    ) -> list[str]:
        """Select short candidates from ``short_ranking``, excluding ``exclude``.

        ``exclude`` contains tickers already claimed by the long book so that
        contradictory positions are never opened.
        """
        assert self.account is not None
        ordered = sorted(short_ranking.items(), key=lambda x: x[1], reverse=True)
        all_tickers = [t for t, _ in ordered]
        n_total = len(all_tickers)
        rank_map = {t: i + 1 for i, t in enumerate(all_tickers)}
        boundary = n_total - self.n_short + 1 - self.stickiness_threshold

        kept = [
            t for t in self.account.liabilities
            if t not in exclude
            and rank_map.get(t, 0) >= boundary
            and self._alpha110(t) < 0
        ]
        target = list(kept)
        for t in reversed(all_tickers):
            if len(target) >= self.n_short:
                break
            if t not in target and t not in exclude and self._alpha110(t) < 0:
                target.append(t)
        return target

    # ── Strategy interface ─────────────────────────────────────────────────

    def on_ranking(self, scores: Scores) -> list[Action]:
        assert self.terminal is not None and self.account is not None
        long_ranking  = scores["long"]
        short_ranking = scores["short"]
        if not long_ranking and not short_ranking:
            return []

        day = self.terminal.day
        nav = self.account.total_value

        target_longs  = set(self._target_longs(long_ranking))
        # Long takes priority: exclude its tickers from the short candidate pool.
        target_shorts = set(self._target_shorts(short_ranking, exclude=target_longs))

        current_longs  = set(self.account.securities.keys())
        current_shorts = set(self.account.liabilities.keys())
        actions: list[Action] = []

        # ── exits ──────────────────────────────────────────────────────────
        for t in current_longs - target_longs:
            sec = self.account.securities[t]
            px = self._quote_close(t, fallback=float(sec.market_price))
            if px > 0 and sec.volume > 0:
                actions.append(Action(
                    direction="long", side="sell",
                    ticker=t, price=px, volume=float(sec.volume), date=day,
                ))

        for t in current_shorts - target_shorts:
            liab = self.account.liabilities[t]
            px = self._quote_close(t, fallback=float(liab.market_price))
            if px > 0 and liab.volume > 0:
                actions.append(Action(
                    direction="short", side="buy",
                    ticker=t, price=px, volume=float(liab.volume), date=day,
                    short_start_date=liab.start_date,
                    short_value=float(liab.volume * liab.price),
                ))

        # ── entries ────────────────────────────────────────────────────────
        if nav > 0:
            per_long  = nav / self.n_long
            per_short = nav / self.n_short

            for t in target_longs - current_longs:
                px = self._quote_close(t)
                if px > 0:
                    actions.append(Action(
                        direction="long", side="buy",
                        ticker=t, price=px, volume=per_long / px, date=day,
                    ))

            for t in target_shorts - current_shorts:
                px = self._quote_close(t)
                if px > 0:
                    actions.append(Action(
                        direction="short", side="sell",
                        ticker=t, price=px, volume=per_short / px, date=day,
                        short_start_date=day,
                        short_value=per_short,
                    ))

        return actions

    def on_holding(self) -> list[Action]:
        return []

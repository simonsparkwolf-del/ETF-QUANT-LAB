from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import TYPE_CHECKING

from QuantLab.backtest.schema.backtest import Account, Action
from QuantLab.backtest.schema.risk import (
    EndTrade,
    MaxPosition,
    NoTrade,
    PositionChange,
    RiskAction,
    YesTrade,
)

if TYPE_CHECKING:
    from QuantLab.backtest.quote_terminal import QuoteTerminal


class Strategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.terminal: QuoteTerminal | None = None
        self.account: Account | None = None
        # How much notional (cash amount) the strategy can still deploy today.
        self.remaining_amount: float = 0.0
        # Max absolute position weight per ticker (fraction of NAV). Risk can tighten this.
        self.max_weight: float = 1.0

    def bind(self, terminal: QuoteTerminal) -> None:
        self.terminal = terminal

    def load_account(self, account: Account) -> None:
        self.account = account

    def on_day_start(self) -> None:
        """
        Called by the engine once per period after mark-to-market, before Signal/Strategy/Risk.
        Default behavior: reset available amount to current cash and clear max weight to 1.0.
        """
        assert self.account is not None
        self.remaining_amount = float(self.account.cash)
        self.max_weight = 1.0

    def apply_risk_actions(
        self, actions: list[Action], risk_actions: list[RiskAction]
    ) -> list[Action]:
        """
        Default implementation for Strategy to react to RiskAction.

        - `NoTrade(direction)`: blocks new openings for that direction
        - `PositionChange(ratio)`: scales *proposed* action volumes by ratio
        - `EndTrade`: force-close all current positions (creates actions)
        """
        assert self.terminal is not None and self.account is not None

        if not risk_actions:
            return actions

        # Collect directives.
        scale_ratio: float | None = None
        max_weight: float | None = None
        no_trade: set[str] = set()
        end_trade = False

        for ra in risk_actions:
            if isinstance(ra, PositionChange):
                scale_ratio = ra.ratio
            elif isinstance(ra, MaxPosition):
                max_weight = ra.max_weight
            elif isinstance(ra, NoTrade):
                no_trade.add(ra.direction)
            elif isinstance(ra, EndTrade):
                end_trade = True

        out: list[Action] = []

        # Apply max position cap from risk (if provided).
        if max_weight is not None:
            self.max_weight = float(max_weight)

        # 1) Filter openings (NoTrade) and scale volumes (PositionChange), then enforce max position.
        for a in actions:
            # "Opening" conventions:
            # - long buy opens/increases long exposure
            # - short sell opens/increases short exposure
            if a.direction == "long" and a.side == "buy" and "long" in no_trade:
                continue
            if a.direction == "short" and a.side == "sell" and "short" in no_trade:
                continue

            if scale_ratio is not None:
                a = Action(
                    direction=a.direction,
                    side=a.side,
                    ticker=a.ticker,
                    price=a.price,
                    volume=a.volume * scale_ratio,
                    date=a.date,
                    short_start_date=a.short_start_date,
                    short_value=a.short_value,
                )
            out.append(a)

        out = self._enforce_max_position(out)

        # 2) Force close positions (EndTrade).
        if end_trade:
            d = self.terminal.day
            # Close longs.
            for ticker, sec in self.account.securities.items():
                if sec.volume > 0:
                    out.append(
                        Action(
                            direction="long",
                            side="sell",
                            ticker=ticker,
                            price=sec.market_price,
                            volume=sec.volume,
                            date=d,
                        )
                    )
            # Close shorts.
            for ticker, liab in self.account.liabilities.items():
                if liab.volume > 0:
                    out.append(
                        Action(
                            direction="short",
                            side="buy",
                            ticker=ticker,
                            price=liab.market_price,
                            volume=liab.volume,
                            date=d,
                            short_start_date=liab.start_date,
                            short_value=liab.volume * liab.price,
                        )
                    )

        return out

    def _enforce_max_position(self, actions: list[Action]) -> list[Action]:
        """
        Enforce per-ticker max position weight (abs exposure <= max_weight * NAV).

        - Applies to "opening" actions (long buy / short sell).
        - Also enforces `remaining_amount` for long buys (cash notional budget).
        """
        assert self.terminal is not None and self.account is not None

        nav = float(self.account.total_value)
        if nav <= 0:
            return actions

        cap_value = max(0.0, float(self.max_weight)) * nav

        # Current exposures by ticker (positive long exposure, negative short exposure).
        cur: dict[str, float] = {}
        for t, sec in self.account.securities.items():
            cur[t] = cur.get(t, 0.0) + float(sec.volume) * float(sec.market_price)
        for t, liab in self.account.liabilities.items():
            cur[t] = cur.get(t, 0.0) - float(liab.volume) * float(liab.market_price)

        out: list[Action] = []
        for a in actions:
            # Only cap new openings/increases.
            is_open_long = a.direction == "long" and a.side == "buy"
            is_open_short = a.direction == "short" and a.side == "sell"
            if not (is_open_long or is_open_short):
                out.append(a)
                continue

            px = float(a.price)
            if px <= 0:
                continue

            signed_add = float(a.volume) * px * (1.0 if is_open_long else -1.0)
            cur_exp = float(cur.get(a.ticker, 0.0))
            target_exp = cur_exp + signed_add

            # Clamp by per-ticker cap.
            if cap_value > 0:
                target_exp = max(-cap_value, min(cap_value, target_exp))

            allowed_add = target_exp - cur_exp

            # Apply remaining_amount for long buys (simple notional budget).
            if is_open_long:
                allowed_add = min(allowed_add, float(self.remaining_amount))

            # If allowed_add doesn't increase exposure in the intended direction, skip.
            if is_open_long and allowed_add <= 0:
                continue
            if is_open_short and allowed_add >= 0:
                continue

            new_vol = abs(allowed_add) / px

            if new_vol <= 0:
                continue

            # Update budgets/exposures.
            if is_open_long:
                self.remaining_amount -= float(new_vol) * px
            cur[a.ticker] = cur_exp + (new_vol * px * (1.0 if is_open_long else -1.0))

            out.append(
                Action(
                    direction=a.direction,
                    side=a.side,
                    ticker=a.ticker,
                    price=a.price,
                    volume=new_vol,
                    date=a.date,
                    short_start_date=a.short_start_date,
                    short_value=a.short_value,
                )
            )

        return out

    @abstractmethod
    def on_ranking(self, ranking: OrderedDict[str, float]) -> list[Action]:
        """Turn signal ranking into actions."""

    @abstractmethod
    def on_holding(self) -> list[Action]:
        """Adjust or exit existing positions."""

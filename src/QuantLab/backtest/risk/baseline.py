from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import pandas as pd

from QuantLab.backtest.risk.basic import Risk
from QuantLab.backtest.schema.backtest import Action

if TYPE_CHECKING:
    from QuantLab.backtest.schema.backtest import Account


class DefenseState(Enum):
    NORMAL = "NORMAL"
    LIGHT  = "LIGHT"
    HEAVY  = "HEAVY"


class BaselineRisk(Risk):
    """
    Three-state drawdown-based risk control.

    State machine:
        NORMAL ──(DD≥dd_light)──► LIGHT ──(DD≥dd_heavy)──► HEAVY
           ▲                          ▲
           │ DD<dd_recovery, N wks    │ ≥heavy_recovery_min_pos Top-N longs
           └──────────────────────────┘   have alpha_110>0, N wks

    Position multipliers:
        NORMAL → 1.0x  |  LIGHT → 0.5x  |  HEAVY → 0x (all cash)

    Alpha values are read via terminal.alphas() — no pre-loading,
    no date range required, no look-ahead.
    """

    def __init__(
        self,
        name: str,
        dd_light: float = 0.10,
        dd_heavy: float = 0.15,
        dd_recovery: float = 0.08,
        recovery_weeks: int = 2,
        heavy_recovery_min_pos: int = 2,
    ) -> None:
        super().__init__(name)
        self.dd_light = dd_light
        self.dd_heavy = dd_heavy
        self.dd_recovery = dd_recovery
        self.recovery_weeks = recovery_weeks
        self.heavy_recovery_min_pos = heavy_recovery_min_pos

        self._state = DefenseState.NORMAL
        self._recovery_counter = 0
        self._account: Account | None = None
        self._alpha_cache: dict[str, float] = {}
        self._alpha_cache_day = None

    def load_account(self, account: Account) -> None:
        self._account = account

    # ── helpers ────────────────────────────────────────────────────────────

    def _drawdown(self) -> float:
        if self._account is None:
            return 0.0
        history = self._account.value_history
        peak = max(
            (v["total_value"] for v in history),
            default=float(self._account.initial_cash),
        )
        peak = max(peak, self._account.total_value)
        if peak <= 0:
            return 0.0
        return max(0.0, (peak - self._account.total_value) / peak)

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

    # ── state machine ──────────────────────────────────────────────────────

    def _update_state(self, actions: list[Action]) -> None:
        dd = self._drawdown()

        if self._state == DefenseState.NORMAL:
            if dd >= self.dd_heavy:
                self._state = DefenseState.HEAVY
                self._recovery_counter = 0
            elif dd >= self.dd_light:
                self._state = DefenseState.LIGHT
                self._recovery_counter = 0

        elif self._state == DefenseState.LIGHT:
            if dd >= self.dd_heavy:
                self._state = DefenseState.HEAVY
                self._recovery_counter = 0
            elif dd < self.dd_recovery:
                self._recovery_counter += 1
                if self._recovery_counter >= self.recovery_weeks:
                    self._state = DefenseState.NORMAL
                    self._recovery_counter = 0
            else:
                self._recovery_counter = 0

        elif self._state == DefenseState.HEAVY:
            # Proposed long buys = current Top-N candidates from strategy.
            # Strategy always generates proposals regardless of risk state.
            proposed_longs = [
                a.ticker for a in actions
                if a.direction == "long" and a.side == "buy"
            ]
            n_positive = sum(1 for t in proposed_longs if self._alpha110(t) > 0)
            if n_positive >= self.heavy_recovery_min_pos:
                self._recovery_counter += 1
                if self._recovery_counter >= self.recovery_weeks:
                    self._state = DefenseState.LIGHT
                    self._recovery_counter = 0
            else:
                self._recovery_counter = 0

    # ── Risk interface ─────────────────────────────────────────────────────

    def on_action(self, actions: list[Action]) -> list[Action]:
        self._update_state(actions)

        if self._state == DefenseState.LIGHT:
            self.scale(0.5, reason=f"DD>{self.dd_light:.0%}: light defensive")

        elif self._state == DefenseState.HEAVY:
            self.end(reason=f"DD>{self.dd_heavy:.0%}: heavy defensive, all cash")
            self.stop("long",  reason="HEAVY: no new longs")
            self.stop("short", reason="HEAVY: no new shorts")

        return actions

    @property
    def state(self) -> DefenseState:
        return self._state

"""LongShortBlendSignal — independent blended alpha signals for long and short books."""

from __future__ import annotations

from collections import OrderedDict

import pandas as pd

from QuantLab.backtest.schema.signal import Scores
from QuantLab.backtest.signal.basic import Signal


class LongShortBlendSignal(Signal):
    """Two independent linear-blend signals: one for the long book, one for the short book.

    Each side is a weighted combination of alpha factors, optimised independently
    in Step 2 LP/SP Bayesian blending.  Both weight dicts are normalised internally.

    Parameters
    ----------
    lp_weights:
        Mapping of ``alpha_id`` → raw weight for the long-side blend.
        Higher composite score → better long candidate.
    sp_weights:
        Mapping of ``alpha_id`` → raw weight for the short-side blend.
        Lower composite score → better short candidate
        (strategy shorts bottom-ranked ETFs).

    Example
    -------
    signal = LongShortBlendSignal(
        lp_weights={24: 0.610, 19: 0.304, 23: 0.073, 31: 0.010, 57: 0.003},
        sp_weights={53: 0.387, 57: 0.375, 19: 0.205, 31: 0.024, 23: 0.009},
    )
    scores = signal.analyze()
    # scores["long"]  — LP blend score per ticker
    # scores["short"] — SP blend score per ticker
    """

    def __init__(
        self,
        lp_weights: dict[int, float],
        sp_weights: dict[int, float],
    ) -> None:
        lp_ids = sorted(lp_weights)
        sp_ids = sorted(sp_weights)
        super().__init__(
            "ls_blend_lp" + "_".join(str(i) for i in lp_ids)
            + "_sp" + "_".join(str(i) for i in sp_ids)
        )

        lp_total = sum(lp_weights.values())
        sp_total = sum(sp_weights.values())
        if lp_total <= 0 or sp_total <= 0:
            raise ValueError("LongShortBlendSignal: both weight dicts must sum to > 0")

        self._lp_weights: dict[int, float] = {k: v / lp_total for k, v in lp_weights.items()}
        self._sp_weights: dict[int, float] = {k: v / sp_total for k, v in sp_weights.items()}

    @property
    def lp_weights(self) -> dict[int, float]:
        return dict(self._lp_weights)

    @property
    def sp_weights(self) -> dict[int, float]:
        return dict(self._sp_weights)

    def analyze(self) -> Scores:
        assert self.terminal is not None

        all_ids = tuple(set(self._lp_weights) | set(self._sp_weights))
        tickers = sorted(self.terminal.etfs()["ticker"].unique().tolist())

        df = self.terminal.alphas(alpha_ids=all_ids)
        indexed = df.set_index("ticker") if not df.empty else pd.DataFrame()

        lp_blend: dict[str, float] = {t: 0.0 for t in tickers}
        sp_blend: dict[str, float] = {t: 0.0 for t in tickers}

        for alpha_id, weight in self._lp_weights.items():
            col = f"alpha_{alpha_id}"
            if indexed.empty or col not in indexed.columns:
                continue
            for t in tickers:
                if t in indexed.index:
                    val = indexed.loc[t, col]
                    if not pd.isna(val):
                        lp_blend[t] += weight * float(val)

        for alpha_id, weight in self._sp_weights.items():
            col = f"alpha_{alpha_id}"
            if indexed.empty or col not in indexed.columns:
                continue
            for t in tickers:
                if t in indexed.index:
                    val = indexed.loc[t, col]
                    if not pd.isna(val):
                        sp_blend[t] += weight * float(val)

        return {
            "long":  OrderedDict(sorted(lp_blend.items())),
            "short": OrderedDict(sorted(sp_blend.items())),
        }

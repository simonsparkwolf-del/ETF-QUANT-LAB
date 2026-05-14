"""Linearly-blended alpha signal for Step 2 signal optimisation."""

from __future__ import annotations

from collections import OrderedDict

import pandas as pd

from QuantLab.backtest.schema.signal import Scores, symmetric
from QuantLab.backtest.signal.basic import Signal


class AlphaBlendSignal(Signal):
    """Cross-section scores from a weighted linear blend of alpha factors.

    Parameters
    ----------
    weights:
        Mapping of ``alpha_id`` → raw weight.  Weights are normalised to
        sum to 1 internally; they do **not** need to be pre-normalised.
        All values must be >= 0.

    Example
    -------
    signal = AlphaBlendSignal({57: 0.5, 19: 0.3, 31: 0.1, 23: 0.1})
    scores = signal.analyze()   # symmetric Scores wrapping the blend
    """

    def __init__(self, weights: dict[int, float]) -> None:
        ids = sorted(weights)
        super().__init__("blend_" + "_".join(str(i) for i in ids))

        total = sum(weights.values())
        if total <= 0:
            raise ValueError("AlphaBlendSignal: weights must sum to > 0")
        self._weights: dict[int, float] = {k: v / total for k, v in weights.items()}

    @property
    def weights(self) -> dict[int, float]:
        """Normalised weights (read-only)."""
        return dict(self._weights)

    def analyze(self) -> Scores:
        assert self.terminal is not None
        alpha_ids = tuple(self._weights)
        tickers = sorted(self.terminal.etfs()["ticker"].unique().tolist())

        df = self.terminal.alphas(alpha_ids=alpha_ids)

        blend: dict[str, float] = {t: 0.0 for t in tickers}
        for alpha_id, weight in self._weights.items():
            col = f"alpha_{alpha_id}"
            if df.empty or col not in df.columns:
                continue
            indexed = df.set_index("ticker")[col]
            for t in tickers:
                if t in indexed.index:
                    val = indexed.loc[t]
                    if not pd.isna(val):
                        blend[t] += weight * float(val)

        return symmetric(OrderedDict(sorted(blend.items())))

"""
signal_metrics.py — non-ML signal definitions.

Add new non-ML signals here (Series → Series), and declare `required`.
"""

from __future__ import annotations

import pandas as pd

from .signal_registry import series_signal

### EXAMPLE
# @series_signal(
#     signal_id=1,
#     note="demo(non-ML): 4-week forward return (same shape as FRS1)",
#     category="composite",
#     required={"bars": ["tri"], "alpha": []},
# )
# def sig_1_fwd4w(tri: pd.Series, **kwargs) -> pd.Series:
#     return (tri.shift(-4) / tri) - 1


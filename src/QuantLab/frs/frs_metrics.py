"""
frs_metrics.py — Forward Return Score metric definitions.

Each function is registered via @register_frs and will be picked up
automatically by compute_frs.py.  Add new metrics here.

Current metrics (4-week horizon, Wednesday-to-Wednesday):
    FRS1 — Total return
    FRS2 — Sharpe ratio proxy
    FRS3 — Volatility-penalised return
"""

import numpy as np
import pandas as pd

from .frs_registry import register_frs


@register_frs("FRS1", description="4-week total return: (P_t+4 / P_t) - 1",
              required_cols=["tri"])
def frs1(p: pd.Series, **kwargs) -> pd.Series:
    return (p.shift(-4) / p) - 1


@register_frs("FRS2", description="4-week Sharpe ratio proxy: avg(r) / std(r)",
              required_cols=["tri"])
def frs2(p: pd.Series, **kwargs) -> pd.Series:
    r = p.pct_change().shift(-1)
    avg = r.rolling(4).mean().shift(-3)
    std = r.rolling(4).std().shift(-3)
    return avg / std.replace(0, np.nan)


@register_frs("FRS3",
              description="4-week volatility-penalised return: FRS1 - beta * std(r)",
              required_cols=["tri"])
def frs3(p: pd.Series, beta: float = 2.0, **kwargs) -> pd.Series:
    r = p.pct_change().shift(-1)
    total_ret = (p.shift(-4) / p) - 1
    std = r.rolling(4).std().shift(-3)
    return total_ret - (beta * std)


# ── Add new FRS metrics below ─────────────────────────────────────────────────
# Example:
# @register_frs("FRS4", description="4-week Sortino ratio", required_cols=["tri"])
# def frs4(p: pd.Series, **kwargs) -> pd.Series:
#     r = p.pct_change().shift(-1)
#     avg = r.rolling(4).mean().shift(-3)
#     downside = r.clip(upper=0).rolling(4).std().shift(-3)
#     return avg / downside.replace(0, np.nan)

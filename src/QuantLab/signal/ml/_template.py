"""
ML signal template.

Contract:
- Declare REQUIRED = {"bars":[...], "alpha":[...]}
- Implement a panel function returning DataFrame with columns: ticker, date, pred
- Decorate with @series_signal(...). The compute layer injects _panel_df and the
  wrapper extracts a per-ticker Series aligned to p.index.
"""

from __future__ import annotations

import pandas as pd

from ..signal_registry import series_signal


REQUIRED = {"bars": ["tri", "close", "volume"], "alpha": [1, 2, 3, 4]}


@series_signal(
    signal_id=9001,
    note="demo(ML): cross-sectional rank of TRI as pred",
    category="ML",
    required=REQUIRED,
)
def ml_9001_demo(big: pd.DataFrame, **kwargs) -> pd.DataFrame:
    df = big[["date", "ticker", "tri"]].copy()
    df["pred"] = df.groupby("date")["tri"].rank(pct=True)
    return df[["ticker", "date", "pred"]]


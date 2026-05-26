"""Signal 6 — RF_tuned daily panel (frs_4 proxy).

Source: research/20260526_David_RF model/outputs/daily/rf_tuned/walk_forward_predictions.csv
Model:  RandomForest, quarterly walk-forward refit, inner-CV tuning (max_depth × min_samples_leaf)
Target: 5-trading-day forward excess return over SPY (daily analogue of frs_4)
OOS:    2023-07-03 → 2026-03-12 (138 Wednesday periods)

OOS performance (Wednesday-sampled, evaluated on weekly frs_4):
  Spearman IC mean = 0.033 | IC-IR = 0.077 | Hit rate = 54.6%

Date alignment:
  Daily predictions are forward-filled onto weekly_bar Wednesday dates so that
  holiday Wednesdays (where the closest prior trading day's prediction is used)
  are handled correctly.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from QuantLab.utils import load_pathes

from ..signal_registry import series_signal

REQUIRED = {"bars": [], "alpha": []}

_PREDS_REL = (
    Path("research")
    / "20260526_David_RF model"
    / "outputs"
    / "daily"
    / "rf_tuned"
    / "walk_forward_predictions.csv"
)


def _load_preds() -> pd.DataFrame:
    path = load_pathes()["ROOT"] / _PREDS_REL
    df = pd.read_csv(path, parse_dates=["date"], usecols=["date", "ticker", "y_pred"])
    return df.rename(columns={"y_pred": "pred"})


@series_signal(
    signal_id=6,
    note="ML: RF_tuned daily panel frs_4 (OOS weeklyIC=0.033, ICIR=0.077)",
    category="ML",
    required=REQUIRED,
)
def ml_6_rf_tuned(big: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Align daily RF predictions to weekly_bar Wednesday dates and return
    a long (ticker, date, pred) DataFrame for injection into weekly_signal."""
    preds = _load_preds()

    # Wednesday dates from weekly_bar (via load_ml_panel → big).
    weekly_dates = pd.DatetimeIndex(sorted(big["date"].unique()))

    # Pivot to wide (date × ticker) so all tickers are aligned in one shot.
    preds_wide = (
        preds.pivot(index="date", columns="ticker", values="pred")
        .sort_index()
    )

    # Reindex onto Wednesday calendar; forward-fill covers holiday Wednesdays
    # where the prior trading day's prediction is the closest available signal.
    aligned = preds_wide.reindex(weekly_dates, method="ffill")

    result = (
        aligned.stack()
        .dropna()
        .rename("pred")
        .reset_index()
    )
    result.columns = ["date", "ticker", "pred"]
    return result[["ticker", "date", "pred"]]

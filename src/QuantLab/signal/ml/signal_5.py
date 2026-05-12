"""Signal 5 — MLP (frs_2). val NDCG@3 = 0.596."""
from __future__ import annotations

import pandas as pd

from ..signal_registry import series_signal
from .utils.inference_utils import load_model, per_date_transform

REQUIRED = {
    "bars": [],
    "alpha": [1, 10, 16, 17, 18, 19, 22, 23, 24, 25, 26, 28, 30, 31, 32,
              34, 35, 38, 40, 42, 44, 53, 54, 55, 57, 61, 66, 71, 83, 84,
              86, 94, 95, 101, 114, 125, 129, 130, 135, 136],
}


@series_signal(
    signal_id=5,
    note="ML: MLP frs_2 predictor (valNDCG3=0.596)",
    category="ML",
    required=REQUIRED,
)
def ml_5_mlp(big: pd.DataFrame, **kwargs) -> pd.DataFrame:
    artifact = load_model(5)
    feats = artifact["selected_features"]

    df = per_date_transform(big, feats)
    preds = artifact["model"].predict(df[feats].to_numpy())
    df = df[["date", "ticker"]].assign(pred=preds)
    return df[["ticker", "date", "pred"]]
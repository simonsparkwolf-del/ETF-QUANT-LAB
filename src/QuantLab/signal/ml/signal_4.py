"""Signal 4 — PCA_Ridge (frs_3). val NDCG@3 = 0.622."""
from __future__ import annotations

import pandas as pd

from ..signal_registry import series_signal
from .utils.inference_utils import load_model, per_date_transform

REQUIRED = {
    "bars": [],
    "alpha": [6, 10, 14, 16, 18, 19, 20, 22, 23, 24, 26, 30, 31, 32, 34,
              37, 40, 44, 51, 53, 54, 57, 61, 64, 66, 72, 83, 95, 101,
              108, 110, 116, 118, 123, 125, 127, 128, 130, 135, 136],
}


@series_signal(
    signal_id=4,
    note="ML: PCA_Ridge frs_3 predictor (valNDCG3=0.622)",
    category="ML",
    required=REQUIRED,
)
def ml_4_pca_ridge(big: pd.DataFrame, **kwargs) -> pd.DataFrame:
    artifact = load_model(4)
    feats = artifact["selected_features"]

    df = per_date_transform(big, feats)
    preds = artifact["model"].predict(df[feats].to_numpy())
    df = df[["date", "ticker"]].assign(pred=preds)
    return df[["ticker", "date", "pred"]]
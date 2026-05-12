"""Signal 2 — Ensemble_RankAvg (frs_1). val NDCG@3 = 0.632."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..signal_registry import series_signal
from .utils.inference_utils import load_model, per_date_transform

REQUIRED = {
    "bars": [],
    "alpha": [2, 6, 8, 10, 14, 18, 19, 25, 26, 28, 30, 31, 34, 35, 38,
              40, 42, 44, 49, 53, 54, 57, 61, 66, 71, 72, 83, 84, 86, 101,
              108, 117, 119, 125, 127, 128, 129, 130, 135, 136],
}


@series_signal(
    signal_id=2,
    note="ML: Ensemble_RankAvg frs_1 predictor (valNDCG3=0.632)",
    category="ML",
    required=REQUIRED,
)
def ml_2_ensemble_rankavg(big: pd.DataFrame, **kwargs) -> pd.DataFrame:
    artifact = load_model(2)
    feats = artifact["selected_features"]

    df = per_date_transform(big, feats)
    X = df[feats].to_numpy()

    base_preds = np.stack(
        [m.predict(X) for m in artifact["base_models"].values()], axis=1
    )

    # Cross-sectional rank each base model's predictions per date, then average
    out = df[["date", "ticker"]].copy()
    out["_raw_pred"] = np.zeros(len(df))

    date_col = df["date"]
    for col_idx in range(base_preds.shape[1]):
        col_preds = pd.Series(base_preds[:, col_idx], index=df.index)
        ranked = col_preds.groupby(date_col).transform(lambda s: s.rank(pct=True))
        out["_raw_pred"] += ranked.values

    out["pred"] = out["_raw_pred"] / base_preds.shape[1]
    return out[["ticker", "date", "pred"]]
"""
inference_utils.py
==================
Shared inference utilities for ML signal modules under QuantLab.signal.ml.

Provides:
  - per_date_transform : cross-sectional fillna -> winsorize -> z-score
  - load_model         : load a patched signal pkl from the weights/ directory

The weights/ directory lives at:
  src/QuantLab/signal/ml/weights/signal_{signal_id}.pkl

Pkls must be produced by patch_selected_features.py (in the deploy_by_model
source folder) which translates ext_* feature names to alpha_N names so the
inference path reads directly from weekly_alpha without any runtime mapping.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

WEIGHTS_DIR = Path(__file__).parent.parent / "weights"


def per_date_transform(
    df: pd.DataFrame,
    feature_cols: list[str],
    winsor: tuple[float, float] = (0.05, 0.95),
) -> pd.DataFrame:
    """
    Cross-sectional preprocessing within each date:
        fillna(median) -> winsorize(5 %, 95 %) -> z-score(mean, std).

    Stateless — no fit state carried between calls. Safe to apply at
    inference time with the same result as training.
    """
    out = df.copy()
    for _, grp in out.groupby("date", sort=False):
        idx = grp.index
        b = out.loc[idx, feature_cols].copy()
        b = b.fillna(b.median())
        lo = b.quantile(winsor[0])
        hi = b.quantile(winsor[1])
        b = b.clip(lower=lo, upper=hi, axis=1)
        mu = b.mean()
        sd = b.std().replace(0, 1.0)
        b = (b - mu) / sd
        out.loc[idx, feature_cols] = b.values
    out[feature_cols] = out[feature_cols].fillna(0.0)
    return out


def load_model(signal_id: int) -> dict:
    """
    Load a patched ML001 artifact from the weights directory.

    The artifact dict contains at minimum:
      model_type        : str
      frs_target        : str
      selected_features : list[str]  -- already translated to alpha_N names
      model             : fitted estimator  (single-model artifacts)
      base_models       : dict[str, estimator]  (Ensemble_RankAvg only)
      metadata          : dict
    """
    path = WEIGHTS_DIR / f"ML_Signal_{signal_id}.pkl"
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {path}\n"
            "Run patch_selected_features.py in simon_test/deploy_by_model/ first."
        )
    with open(path, "rb") as f:
        return pickle.load(f)

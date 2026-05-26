"""
daily_model.py — daily-cadence walk-forward for LightGBM, RandomForest, ElasticNet.

CV: purged TimeSeriesSplit (5-trading-day gap between train and validation)
inside GridSearchCV for ElasticNet only. Tree models use fixed, strongly-
regularised hyperparameters (no inner CV; the daily panel has ~140 effective
independent weeks, which is too few for reliable inner tuning of tree depth
and learning rate).

Outer walk-forward: quarterly refit, expanding window.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from lightgbm import LGBMRegressor
    HAVE_LGBM = True
except Exception:
    HAVE_LGBM = False

from config import (
    EN_ALPHA_GRID, EN_L1RATIO_GRID, INNER_CV_SPLITS,
    INITIAL_TRAIN_END, RANDOM_SEED,
    RF_MAX_DEPTH_GRID, RF_MIN_SAMPLES_LEAF_GRID,
    RF_N_ESTIMATORS_FIXED, RF_INNER_CV_SPLITS, RF_INNER_CV_GAP_ROWS,
)
from model import make_weekly_ic_scorer


# ---------------------------------------------------------------------------
# Purged TimeSeriesSplit
# ---------------------------------------------------------------------------
class PurgedTimeSeriesSplit:
    """TimeSeriesSplit with a fixed gap (in rows) between train and validation
    to avoid leakage from overlapping forward-return labels.
    Assumes X is sorted chronologically. Always yields exactly n_splits folds
    if (n - gap) >= n_splits + 1; sklearn requires get_n_splits and split to
    agree on the count.
    """
    def __init__(self, n_splits: int = 3, gap: int = 5):
        self.n_splits = n_splits
        self.gap = gap

    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_splits

    def split(self, X, y=None, groups=None):
        n = len(X)
        fold_size = max(1, (n - self.gap) // (self.n_splits + 1))
        for i in range(self.n_splits):
            train_end = (i + 1) * fold_size
            val_start = train_end + self.gap
            val_end   = min(val_start + fold_size, n)
            if val_start >= n or train_end <= 0:
                val_start = n - 1
                val_end   = n
                train_end = max(1, val_start - self.gap)
            train_idx = np.arange(0, train_end)
            val_idx   = np.arange(val_start, val_end)
            yield train_idx, val_idx


# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------
def make_lightgbm() -> LGBMRegressor:
    return LGBMRegressor(
        objective='regression_l2',
        n_estimators=400,
        learning_rate=0.03,
        num_leaves=8,
        max_depth=4,
        min_data_in_leaf=200,
        feature_fraction=0.7,
        bagging_fraction=0.8,
        bagging_freq=5,
        reg_lambda=0.1,
        random_state=RANDOM_SEED,
        n_jobs=1,
        verbose=-1,
    )


def make_rf(max_depth: int = 6,
            min_samples_leaf: int = 200,
            n_estimators: int = RF_N_ESTIMATORS_FIXED) -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        max_features='sqrt',
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )


def fit_rf_cv(X_tr: pd.DataFrame, y_tr: pd.Series,
              dates_tr: pd.Series) -> tuple:
    """Inner-CV hyperparameter tuning for Random Forest.

    Grid (9 candidates): max_depth x min_samples_leaf.
    n_estimators fixed at RF_N_ESTIMATORS_FIXED (trees do not overfit by count).
    Scoring: mean weekly Spearman IC via make_weekly_ic_scorer.
    CV: PurgedTimeSeriesSplit(n_splits=RF_INNER_CV_SPLITS, gap=RF_INNER_CV_GAP_ROWS).

    Returns (best_estimator, best_params).
    """
    grid = [(d, l) for d in RF_MAX_DEPTH_GRID for l in RF_MIN_SAMPLES_LEAF_GRID]
    cv = PurgedTimeSeriesSplit(n_splits=RF_INNER_CV_SPLITS, gap=RF_INNER_CV_GAP_ROWS)

    X_arr = X_tr.reset_index(drop=True)
    y_arr = y_tr.reset_index(drop=True)
    dates_arr = pd.to_datetime(dates_tr.reset_index(drop=True)).to_numpy()
    scorer_fn = make_weekly_ic_scorer(dates_arr)

    best_score = -np.inf
    best_params = None
    for d, l in grid:
        fold_scores = []
        for tr_idx, va_idx in cv.split(X_arr):
            est = RandomForestRegressor(
                n_estimators=RF_N_ESTIMATORS_FIXED,
                max_depth=d, min_samples_leaf=l,
                max_features='sqrt',
                random_state=RANDOM_SEED, n_jobs=-1,
            )
            est.fit(X_arr.iloc[tr_idx], y_arr.iloc[tr_idx])
            score = scorer_fn(est, X_arr.iloc[va_idx], y_arr.iloc[va_idx])
            fold_scores.append(score)
        mean = float(np.mean(fold_scores))
        if mean > best_score:
            best_score = mean
            best_params = {'max_depth': d, 'min_samples_leaf': l}

    final = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS_FIXED,
        max_depth=best_params['max_depth'],
        min_samples_leaf=best_params['min_samples_leaf'],
        max_features='sqrt',
        random_state=RANDOM_SEED, n_jobs=-1,
    )
    final.fit(X_arr, y_arr)
    best_params['inner_cv_ic'] = best_score
    return final, best_params


def make_elasticnet() -> Pipeline:
    return Pipeline([
        ('scaler', StandardScaler()),
        ('en', ElasticNet(max_iter=20000, random_state=RANDOM_SEED, positive=False)),
    ])


def fit_elasticnet_cv(X_tr: pd.DataFrame, y_tr: pd.Series) -> tuple:
    pipe = make_elasticnet()
    grid = {
        'en__alpha':    EN_ALPHA_GRID,
        'en__l1_ratio': EN_L1RATIO_GRID,
    }
    cv = PurgedTimeSeriesSplit(n_splits=INNER_CV_SPLITS, gap=5)
    gs = GridSearchCV(pipe, grid, scoring='neg_mean_squared_error',
                      cv=cv, n_jobs=1, refit=True)
    gs.fit(X_tr.reset_index(drop=True), y_tr.reset_index(drop=True))
    return gs.best_estimator_, gs.best_params_


# ---------------------------------------------------------------------------
# Walk-forward (quarterly refit, expanding window)
# ---------------------------------------------------------------------------
def walk_forward_daily(panel: pd.DataFrame,
                       feature_cols: list[str],
                       target_col: str,
                       model_kind: str,
                       use_sector_fe: bool = True,
                       tune_rf: bool = True) -> pd.DataFrame:
    """Expanding-window walk-forward at daily cadence.
    - Initial train: panel['date'] <= INITIAL_TRAIN_END
    - Quarterly refit; predict that quarter's daily rows.
    - `model_kind` in {'lightgbm', 'rf', 'elasticnet'}.
    - `use_sector_fe` demeans y by ticker on the train set (independent of
      sector dummy features); ticker mean is added back at predict.
    """
    df = panel.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=[target_col] + feature_cols).reset_index(drop=True)
    df = df.sort_values(['date', 'ticker']).reset_index(drop=True)

    initial_cutoff = pd.Timestamp(INITIAL_TRAIN_END)
    quarters = (
        df.loc[df['date'] > initial_cutoff, 'date']
          .dt.to_period('Q').drop_duplicates().sort_values().tolist()
    )

    records = []
    for fold_id, q in enumerate(quarters):
        q_start = q.start_time
        q_end   = q.end_time
        train_mask = df['date'] < q_start
        pred_mask  = (df['date'] >= q_start) & (df['date'] <= q_end)
        if train_mask.sum() == 0 or pred_mask.sum() == 0:
            continue

        X_tr = df.loc[train_mask, feature_cols]
        y_tr_raw = df.loc[train_mask, target_col]
        t_tr = df.loc[train_mask, 'ticker']
        X_pr = df.loc[pred_mask, feature_cols]
        t_pr = df.loc[pred_mask, 'ticker']

        if use_sector_fe:
            ticker_mean = y_tr_raw.groupby(t_tr).mean()
            y_tr = y_tr_raw - t_tr.map(ticker_mean).values
        else:
            ticker_mean = None
            y_tr = y_tr_raw

        if model_kind == 'lightgbm':
            est = make_lightgbm()
            est.fit(X_tr, y_tr)
            best_params = {'n_est': est.n_estimators, 'leaves': est.num_leaves}
        elif model_kind == 'rf':
            if tune_rf:
                d_tr_series = df.loc[train_mask, 'date']
                est, best_params = fit_rf_cv(X_tr, y_tr, d_tr_series)
            else:
                est = make_rf()
                est.fit(X_tr, y_tr)
                best_params = {'n_est': est.n_estimators, 'depth': est.max_depth}
        elif model_kind == 'elasticnet':
            est, best_params = fit_elasticnet_cv(X_tr, y_tr)
        else:
            raise ValueError(f"unknown model_kind={model_kind}")

        y_hat_resid = est.predict(X_pr)
        if use_sector_fe:
            y_hat = y_hat_resid + t_pr.map(ticker_mean).values
        else:
            y_hat = y_hat_resid

        out = df.loc[pred_mask, ['date', 'ticker', target_col]].copy()
        out = out.rename(columns={target_col: 'y_true'})
        out['y_pred'] = y_hat
        out['fold_id'] = fold_id
        out['fold_quarter'] = str(q)
        records.append(out)
        print(f"  [{model_kind:10s}] fold {fold_id:02d} {q}: "
              f"n_tr={train_mask.sum()} n_pr={pred_mask.sum()} {best_params}")

    if not records:
        return pd.DataFrame(columns=['date', 'ticker', 'y_true', 'y_pred', 'fold_id'])
    return pd.concat(records, ignore_index=True)


def feature_importance_lgbm(panel: pd.DataFrame,
                            feature_cols: list[str],
                            target_col: str) -> pd.DataFrame:
    """Fit one LightGBM on the full panel and return feature importances by gain.
    Used for diagnostics only — NOT for selection or for evaluation.
    """
    df = panel.dropna(subset=[target_col] + feature_cols).copy()
    est = make_lightgbm()
    est.fit(df[feature_cols], df[target_col])
    imp = pd.DataFrame({
        'feature': feature_cols,
        'gain_importance': est.booster_.feature_importance(importance_type='gain'),
        'split_importance': est.booster_.feature_importance(importance_type='split'),
    }).sort_values('gain_importance', ascending=False).reset_index(drop=True)
    return imp

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from config import (
    EN_ALPHA_GRID, EN_L1RATIO_GRID, INNER_CV_SPLITS,
    INITIAL_TRAIN_END, QUARTERLY_REFIT, RANDOM_SEED,
)


def _mean_weekly_spearman_ic(y_true: np.ndarray, y_pred: np.ndarray,
                             dates: np.ndarray) -> float:
    df = pd.DataFrame({'y': y_true, 'p': y_pred, 'd': dates})
    rhos = []
    for _, grp in df.groupby('d'):
        if grp['y'].nunique() < 2 or grp['p'].nunique() < 2:
            continue
        rho, _ = spearmanr(grp['p'], grp['y'])
        if not np.isnan(rho):
            rhos.append(rho)
    if not rhos:
        return -10.0
    return float(np.mean(rhos))


def make_weekly_ic_scorer(dates_train: np.ndarray):
    """sklearn scorer that computes mean weekly Spearman IC over the rows
    being scored, looked up against the supplied date vector."""
    def scorer(estimator, X, y):
        try:
            idx = X.index.to_numpy() if hasattr(X, 'index') else np.arange(len(X))
        except Exception:
            idx = np.arange(len(X))
        d = dates_train[idx] if len(idx) <= len(dates_train) else dates_train[: len(X)]
        y_pred = estimator.predict(X)
        return _mean_weekly_spearman_ic(np.asarray(y), np.asarray(y_pred), np.asarray(d))
    return scorer


def fit_elasticnet_cv(X_tr: pd.DataFrame, y_tr: pd.Series,
                      dates_tr: pd.Series,
                      positive: bool = True) -> Pipeline:
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('en', ElasticNet(max_iter=20000, random_state=RANDOM_SEED,
                          positive=positive)),
    ])
    grid = {
        'en__alpha':    EN_ALPHA_GRID,
        'en__l1_ratio': EN_L1RATIO_GRID,
    }
    X_tr_idx = X_tr.reset_index(drop=True)
    dates_arr = pd.to_datetime(dates_tr.reset_index(drop=True)).to_numpy()
    scorer = make_weekly_ic_scorer(dates_arr)
    cv = TimeSeriesSplit(n_splits=INNER_CV_SPLITS)
    gs = GridSearchCV(pipe, grid, scoring=scorer, cv=cv, n_jobs=1, refit=True)
    gs.fit(X_tr_idx, y_tr.reset_index(drop=True))
    return gs.best_estimator_, gs.best_params_, gs.best_score_


def walk_forward(panel: pd.DataFrame, feature_cols: list[str],
                 target_col: str = 'y',
                 use_sector_fe: bool = True,
                 positive: bool = True) -> pd.DataFrame:
    """Expanding-window walk-forward with sector fixed effects.
    - Initial train: panel['date'] <= INITIAL_TRAIN_END
    - Then refit at the start of each calendar quarter, predicting that quarter's rows.
    - If use_sector_fe: demean y by ticker on the train set; add ticker mean back at predict.
    - If positive: enforces non-negative ElasticNet coefficients (sign-constrained).
    """
    df = panel.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['date', 'ticker']).reset_index(drop=True)

    initial_cutoff = pd.Timestamp(INITIAL_TRAIN_END)
    all_quarters = (
        df.loc[df['date'] > initial_cutoff, 'date']
          .dt.to_period('Q').drop_duplicates().sort_values().tolist()
    )

    records = []
    for fold_id, q in enumerate(all_quarters):
        q_start = q.start_time
        q_end   = q.end_time
        train_mask = df['date'] < q_start
        pred_mask  = (df['date'] >= q_start) & (df['date'] <= q_end)
        if train_mask.sum() == 0 or pred_mask.sum() == 0:
            continue
        X_tr = df.loc[train_mask, feature_cols]
        y_tr_raw = df.loc[train_mask, target_col]
        d_tr = df.loc[train_mask, 'date']
        t_tr = df.loc[train_mask, 'ticker']
        X_pr = df.loc[pred_mask, feature_cols]
        t_pr = df.loc[pred_mask, 'ticker']

        if use_sector_fe:
            ticker_mean = y_tr_raw.groupby(t_tr).mean()
            y_tr = y_tr_raw - t_tr.map(ticker_mean).values
        else:
            ticker_mean = None
            y_tr = y_tr_raw

        est, best_params, best_score = fit_elasticnet_cv(
            X_tr, y_tr, d_tr, positive=positive)
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
        out['en_alpha']    = best_params.get('en__alpha')
        out['en_l1_ratio'] = best_params.get('en__l1_ratio')
        out['val_ic_inner'] = best_score
        records.append(out)
        n_nonzero = int(np.sum(np.abs(est.named_steps['en'].coef_) > 1e-12))
        print(f"  fold {fold_id:02d} {q}: train_end<{q_start.date()} "
              f"n_tr={train_mask.sum()} n_pr={pred_mask.sum()} "
              f"alpha={best_params['en__alpha']} l1={best_params['en__l1_ratio']} "
              f"nz={n_nonzero}/{len(feature_cols)} inner_IC={best_score:.4f}")

    if not records:
        return pd.DataFrame(columns=['date','ticker','y_true','y_pred','fold_id'])
    return pd.concat(records, ignore_index=True)

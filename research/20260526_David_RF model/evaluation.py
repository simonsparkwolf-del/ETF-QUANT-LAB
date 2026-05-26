from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from config import BOOTSTRAP_BLOCK_WEEKS, BOOTSTRAP_N, NDCG_PERMUTATIONS, RANDOM_SEED


def weekly_spearman_ic(df: pd.DataFrame) -> pd.Series:
    out = {}
    for d, grp in df.groupby('date'):
        if grp['y_true'].nunique() < 2 or grp['y_pred'].nunique() < 2:
            continue
        rho, _ = spearmanr(grp['y_pred'], grp['y_true'])
        if not np.isnan(rho):
            out[d] = rho
    return pd.Series(out).sort_index()


def _ndcg_at_k(y_true: np.ndarray, y_pred: np.ndarray, k: int = 3) -> float:
    n = len(y_true)
    if n == 0:
        return float('nan')
    order_pred = np.argsort(-y_pred)
    rel = y_true[order_pred][:k]
    discounts = 1.0 / np.log2(np.arange(2, k + 2))
    dcg = float(np.sum(rel * discounts))
    rel_ideal = np.sort(y_true)[::-1][:k]
    idcg = float(np.sum(rel_ideal * discounts))
    if idcg == 0:
        return float('nan')
    return dcg / idcg


def ndcg_per_week(df: pd.DataFrame, k: int = 3) -> pd.Series:
    out = {}
    for d, grp in df.groupby('date'):
        out[d] = _ndcg_at_k(grp['y_true'].to_numpy(), grp['y_pred'].to_numpy(), k=k)
    return pd.Series(out).dropna().sort_index()


def top_k_precision(df: pd.DataFrame, k: int = 3) -> pd.Series:
    out = {}
    for d, grp in df.groupby('date'):
        n = len(grp)
        if n < k:
            continue
        top_pred = set(grp.nlargest(k, 'y_pred')['ticker'])
        top_true = set(grp.nlargest(k, 'y_true')['ticker'])
        out[d] = len(top_pred & top_true) / k
    return pd.Series(out).sort_index()


def hit_rate(df: pd.DataFrame) -> float:
    g = df.groupby('date')
    correct = total = 0
    for _, grp in g:
        y_med = grp['y_true'].median()
        p_med = grp['y_pred'].median()
        for _, r in grp.iterrows():
            yd = r['y_true'] - y_med
            pd_ = r['y_pred'] - p_med
            if yd == 0 or pd_ == 0:
                continue
            total += 1
            if (yd > 0) == (pd_ > 0):
                correct += 1
    return float(correct / total) if total else float('nan')


def r2_global(df: pd.DataFrame) -> float:
    y = df['y_true'].to_numpy()
    p = df['y_pred'].to_numpy()
    ss_res = float(np.sum((y - p) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')


def block_bootstrap_ic(ic_by_week: pd.Series,
                       block_len: int = BOOTSTRAP_BLOCK_WEEKS,
                       n_iter: int = BOOTSTRAP_N,
                       seed: int = RANDOM_SEED) -> dict:
    rng = np.random.default_rng(seed)
    vals = ic_by_week.dropna().to_numpy()
    n = len(vals)
    if n == 0:
        return {'mean': float('nan'), 'ci_low': float('nan'),
                'ci_high': float('nan'), 'ir_mean': float('nan'),
                'ir_ci_low': float('nan'), 'ir_ci_high': float('nan')}
    n_blocks = int(np.ceil(n / block_len))
    boot_means, boot_irs = [], []
    for _ in range(n_iter):
        starts = rng.integers(0, max(1, n - block_len + 1), size=n_blocks)
        chunks = [vals[s:s + block_len] for s in starts]
        sample = np.concatenate(chunks)[:n]
        boot_means.append(sample.mean())
        sd = sample.std(ddof=1)
        boot_irs.append(sample.mean() / sd if sd > 0 else 0.0)
    boot_means = np.asarray(boot_means)
    boot_irs   = np.asarray(boot_irs)
    return {
        'mean':     float(vals.mean()),
        'ci_low':   float(np.percentile(boot_means, 2.5)),
        'ci_high':  float(np.percentile(boot_means, 97.5)),
        'ir_mean':  float(vals.mean() / vals.std(ddof=1)) if vals.std(ddof=1) > 0 else float('nan'),
        'ir_ci_low':  float(np.percentile(boot_irs, 2.5)),
        'ir_ci_high': float(np.percentile(boot_irs, 97.5)),
    }


def ndcg_permutation_null(df: pd.DataFrame, k: int = 3,
                          n_perm: int = NDCG_PERMUTATIONS,
                          seed: int = RANDOM_SEED) -> dict:
    rng = np.random.default_rng(seed)
    obs = ndcg_per_week(df, k=k).mean()
    null_means = np.empty(n_perm)
    df2 = df[['date','ticker','y_true','y_pred']].copy()
    for i in range(n_perm):
        df2['y_pred_perm'] = (df2.groupby('date')['y_pred']
                                  .transform(lambda s: s.sample(frac=1.0,
                                                                random_state=int(rng.integers(0, 2**31)))
                                                       .to_numpy()))
        out = {}
        for d, grp in df2.groupby('date'):
            out[d] = _ndcg_at_k(grp['y_true'].to_numpy(),
                                grp['y_pred_perm'].to_numpy(), k=k)
        null_means[i] = pd.Series(out).dropna().mean()
    p_val = float((null_means >= obs).mean())
    return {
        'observed': float(obs),
        'null_mean': float(null_means.mean()),
        'null_std':  float(null_means.std(ddof=1)),
        'p_value':   p_val,
    }


def yearly_ic(df: pd.DataFrame) -> pd.DataFrame:
    ic = weekly_spearman_ic(df)
    ic.index = pd.to_datetime(ic.index)
    return ic.groupby(ic.index.year).agg(['mean', 'std', 'count']).rename_axis('year')


def regime_ic(df: pd.DataFrame, regime: pd.Series) -> pd.Series:
    """regime: Series indexed by date with category labels."""
    ic = weekly_spearman_ic(df)
    reg = regime.reindex(ic.index)
    return ic.groupby(reg).mean()


def vol_vs_return_check(df: pd.DataFrame) -> dict:
    y = df['y_true'].to_numpy()
    p = df['y_pred'].to_numpy()
    abs_y = np.abs(y)
    cy = float(np.corrcoef(p, y)[0, 1]) if np.std(p) > 0 and np.std(y) > 0 else float('nan')
    cay = float(np.corrcoef(p, abs_y)[0, 1]) if np.std(p) > 0 and np.std(abs_y) > 0 else float('nan')
    return {
        'corr_pred_y':     cy,
        'corr_pred_absy':  cay,
        'ratio_return_over_risk': float(abs(cy) / abs(cay)) if cay not in (0, float('nan')) else float('nan'),
    }


def monthly_snapshot(preds: pd.DataFrame) -> pd.DataFrame:
    """Return predictions filtered to the last trading day of each month."""
    df = preds.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['_ym'] = df['date'].dt.to_period('M')
    last_day_per_month = df.groupby('_ym')['date'].transform('max')
    out = df[df['date'] == last_day_per_month].copy()
    return out.drop(columns=['_ym']).reset_index(drop=True)


def monthly_smoothed(preds: pd.DataFrame, span: int = 5) -> pd.DataFrame:
    """Return exponentially-weighted month-aggregated predictions and targets.

    For each (year-month, ticker) pair, compute weighted average of
    daily y_pred and y_true across all trading days in the month, with
    most recent days weighted highest (exponential decay, span trading days).

    Returns DataFrame with one row per (month-end-date, ticker):
      date  ticker  y_true  y_pred  (and any other input columns averaged)
    """
    alpha = 2.0 / (span + 1.0)
    df = preds.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['_ym']  = df['date'].dt.to_period('M')
    df = df.sort_values(['ticker', 'date']).reset_index(drop=True)

    rows = []
    for (ym, t), grp in df.groupby(['_ym', 'ticker']):
        grp = grp.sort_values('date')
        n = len(grp)
        if n == 0:
            continue
        # i from 0..n-1; weight = (1-alpha)^(n-1-i), so the LAST day has weight 1
        # (relative), earliest day has weight (1-alpha)^(n-1).
        w = (1.0 - alpha) ** np.arange(n - 1, -1, -1)
        w = w / w.sum()
        y_true_w = float(np.dot(w, grp['y_true'].to_numpy()))
        y_pred_w = float(np.dot(w, grp['y_pred'].to_numpy()))
        rows.append({
            'date':   grp['date'].iloc[-1],
            'ticker': t,
            'y_true': y_true_w,
            'y_pred': y_pred_w,
        })
    out = pd.DataFrame(rows)
    return out.sort_values(['date', 'ticker']).reset_index(drop=True)

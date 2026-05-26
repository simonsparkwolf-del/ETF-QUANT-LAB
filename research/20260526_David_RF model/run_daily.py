"""
run_daily.py — daily-cadence pipeline entry point (Iteration 2).

Builds the daily long panel (~13.8k rows, 57 features = 45 prior + 12 FRED
macro), then runs **Random Forest with inner-CV hyperparameter tuning**.

Inner-CV tuning grid (9 candidates): max_depth x min_samples_leaf, scored
by weekly Spearman IC via PurgedTimeSeriesSplit(3, gap=5).

Evaluated at TWO cadences:
  * daily   — full OOS picture, every trading day in 2023-Q3..2026-Q1
  * weekly  — Wednesday-only filter, apples-to-apples with prior weekly runs
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from config import OUT, INITIAL_TRAIN_END, RF_N_ESTIMATORS_FIXED, RANDOM_SEED
from data_loader import (
    load_daily_close, load_daily_volume, load_daily_macro,
    load_weekly_close,
)
from daily_features import build_daily_panel, ALL_FEATURES, FRED_FEATURES
from daily_model import walk_forward_daily
from fred_loader import load_fred_wide
from target import compute_frs_4
from evaluation import (
    weekly_spearman_ic, ndcg_per_week, top_k_precision, hit_rate, r2_global,
    block_bootstrap_ic, vol_vs_return_check, yearly_ic,
)


DAILY_OUT = OUT / "daily"
DAILY_OUT.mkdir(parents=True, exist_ok=True)


def build():
    print("[1/4] load daily data + FRED macros")
    dc = load_daily_close()
    dv = load_daily_volume()
    dm = load_daily_macro()
    fred = load_fred_wide()
    print(f"      daily close={dc.shape}, daily vol={dv.shape}, daily macro={dm.shape}")
    print(f"      FRED wide={fred.shape}, columns={list(fred.columns)}")

    print("[2/4] build daily panel + 5d-forward target")
    panel = build_daily_panel(dc, dv, dm, fred_wide=fred, target_fwd_days=5)
    panel.to_parquet(DAILY_OUT / "feature_panel.parquet", index=False)
    print(f"      panel shape: {panel.shape}, columns={list(panel.columns)[:8]}...")

    feat_cols = [c for c in ALL_FEATURES if c in panel.columns]
    print(f"      {len(feat_cols)} features used")
    return panel, feat_cols


def _block_metrics(df: pd.DataFrame, label: str) -> dict:
    ic = weekly_spearman_ic(df)
    ic_stats = block_bootstrap_ic(ic)
    ndcg_series = ndcg_per_week(df, k=3)
    tk_series = top_k_precision(df, k=3)
    vr = vol_vs_return_check(df)
    return {
        f'{label}__n_periods_with_valid_ic': int(ic.shape[0]),
        f'{label}__spearman_ic_mean':        float(ic.mean()) if len(ic) else float('nan'),
        f'{label}__spearman_ic_std':         float(ic.std(ddof=1)) if len(ic) > 1 else float('nan'),
        f'{label}__spearman_ic_ir':          ic_stats['ir_mean'],
        f'{label}__ic_ci95_low':             ic_stats['ci_low'],
        f'{label}__ic_ci95_high':            ic_stats['ci_high'],
        f'{label}__ndcg_at_3_mean':          float(ndcg_series.mean()) if len(ndcg_series) else float('nan'),
        f'{label}__top3_precision_mean':     float(tk_series.mean()) if len(tk_series) else float('nan'),
        f'{label}__hit_rate':                hit_rate(df),
        f'{label}__r2_global':               r2_global(df),
        f'{label}__sanity_corr_pred_y':      vr['corr_pred_y'],
        f'{label}__sanity_corr_pred_absy':   vr['corr_pred_absy'],
        f'{label}__sanity_ratio':            vr['ratio_return_over_risk'],
    }


def evaluate(model_name: str, preds: pd.DataFrame) -> dict:
    out_dir = DAILY_OUT / model_name
    out_dir.mkdir(parents=True, exist_ok=True)
    preds.to_csv(out_dir / "walk_forward_predictions.csv", index=False)

    weekly_close = load_weekly_close()
    weekly_frs4 = compute_frs_4(weekly_close).stack().rename('weekly_frs4').reset_index()
    weekly_frs4.columns = ['date', 'ticker', 'weekly_frs4']
    weekly_frs4['date'] = pd.to_datetime(weekly_frs4['date'])

    wed_preds = preds.merge(weekly_frs4, on=['date', 'ticker'], how='inner')
    wed_preds = wed_preds.dropna(subset=['weekly_frs4']).copy()
    wed_preds_eval = wed_preds[['date', 'ticker', 'weekly_frs4', 'y_pred']].rename(
        columns={'weekly_frs4': 'y_true'}
    )

    summary = {
        'model': model_name,
        'n_daily_oos_rows':    int(len(preds)),
        'n_daily_oos_periods': int(preds['date'].nunique()),
        'n_weekly_oos_rows':   int(len(wed_preds_eval)),
        'n_weekly_oos_periods': int(wed_preds_eval['date'].nunique()),
        'oos_period':          f"{preds['date'].min().date()} to {preds['date'].max().date()}",
    }
    summary.update(_block_metrics(preds, 'daily'))
    summary.update(_block_metrics(wed_preds_eval, 'weekly_on_frs4'))

    yic_daily = yearly_ic(preds)
    yic_daily.to_csv(out_dir / "yearly_ic_daily.csv")
    yic_weekly = yearly_ic(wed_preds_eval)
    yic_weekly.to_csv(out_dir / "yearly_ic_weekly_on_frs4.csv")

    with open(out_dir / "metrics_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    pd.DataFrame([summary]).to_csv(out_dir / "metrics_summary.csv", index=False)
    return summary


def rf_importance_full_panel(panel: pd.DataFrame, feat_cols: list[str]) -> pd.DataFrame:
    df = panel.dropna(subset=feat_cols + ['y_5d_excess']).copy()
    est = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS_FIXED, max_depth=6, min_samples_leaf=200,
        max_features='sqrt', random_state=RANDOM_SEED, n_jobs=-1,
    )
    est.fit(df[feat_cols], df['y_5d_excess'])
    return pd.DataFrame({
        'feature': feat_cols,
        'rf_importance': est.feature_importances_,
    }).sort_values('rf_importance', ascending=False).reset_index(drop=True)


def main():
    t0 = time.time()
    panel, feat_cols = build()

    print("[3/4] RF feature-importance diagnostic (single full-panel fit, fixed depth=6/leaf=200)")
    imp = rf_importance_full_panel(panel, feat_cols)
    imp.to_csv(DAILY_OUT / "rf_feature_importance_full_panel.csv", index=False)
    print("      top 20 features:")
    print(imp.head(20).to_string(index=False))
    fred_top = imp[imp['feature'].isin(FRED_FEATURES)].head(5)
    print(f"\n      FRED features in top 20: "
          f"{[c for c in FRED_FEATURES if c in imp.head(20)['feature'].tolist()]}")

    print("\n[4/4] RF walk-forward with inner-CV tuning (initial train end "
          f"{INITIAL_TRAIN_END}, quarterly refit)")

    preds = walk_forward_daily(
        panel, feature_cols=feat_cols,
        target_col='y_5d_excess',
        model_kind='rf',
        use_sector_fe=True,
        tune_rf=True,
    )
    if preds.empty:
        print("[stop] no walk-forward predictions produced")
        return
    summary = evaluate('rf_tuned', preds)

    print("\n=== HEADLINE METRICS (RF tuned, 57 features incl. 12 FRED macros) ===")
    keys = [
        'n_weekly_oos_rows', 'n_weekly_oos_periods',
        'weekly_on_frs4__spearman_ic_mean', 'weekly_on_frs4__spearman_ic_ir',
        'weekly_on_frs4__ic_ci95_low', 'weekly_on_frs4__ic_ci95_high',
        'weekly_on_frs4__top3_precision_mean', 'weekly_on_frs4__hit_rate',
        'weekly_on_frs4__sanity_corr_pred_y', 'weekly_on_frs4__sanity_corr_pred_absy',
        'daily__spearman_ic_mean', 'daily__spearman_ic_ir',
        'daily__ic_ci95_low', 'daily__ic_ci95_high',
    ]
    for k in keys:
        v = summary.get(k, float('nan'))
        if isinstance(v, float):
            print(f"  {k:50s}: {v: .4f}")
        else:
            print(f"  {k:50s}: {v}")

    print("\n=== COMPARISON TO PRIOR (Wed-on-frs_4 IC) ===")
    print(f"  Prior 10-feat ElasticNet baseline                 : +0.018")
    print(f"  Prior 45-feat RF (fixed hyperparams)              : +0.0451  CI [-0.027, +0.107]")
    print(f"  Current 57-feat RF (tuned, FRED macros)           : "
          f"{summary['weekly_on_frs4__spearman_ic_mean']: .4f}  CI ["
          f"{summary['weekly_on_frs4__ic_ci95_low']: .4f}, "
          f"{summary['weekly_on_frs4__ic_ci95_high']: .4f}]")

    print(f"\n[done] {time.time() - t0:.1f}s")


def print_table(summaries: dict, keys: list[str]) -> None:
    labels = list(summaries.keys())
    header = f"  {'metric':45s} " + " ".join(f"{l:>14s}" for l in labels)
    print(header)
    for k in keys:
        row = f"  {k:45s} "
        for lab in labels:
            v = summaries[lab].get(k, float('nan'))
            row += f" {v: >14.4f}" if isinstance(v, float) else f" {str(v):>14s}"
        print(row)


if __name__ == "__main__":
    main()

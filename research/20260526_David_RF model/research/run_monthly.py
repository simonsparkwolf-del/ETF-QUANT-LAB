"""
run_monthly.py — Iteration 3 entry point: monthly cadence evaluation.

Trains the SAME daily-cadence RF (tuned via inner CV, 57 features) but with:
  - Target horizon = 20 trading days forward (≈ 1 month) instead of 5.
  - Inner-CV purge gap = 20 days (to match the new label horizon).

Then evaluates at monthly cadence in TWO parallel views:
  Variant A — Snapshot:    last trading day of each month.
  Variant B — Smoothed:    exponentially-weighted average across each month
                           (span=5 trading days; recent days weighted highest).

Block-bootstrap CI uses block_size=1 for snapshot, block_size=3 for smoothed
(the larger block is the statistical correction for the autocorrelation
that smoothing introduces between adjacent months).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

# This script lives in New_Strategy/research/. Add New_Strategy/ to sys.path
# so imports of config, data_loader, daily_features, etc. work unchanged.
_HERE = Path(__file__).resolve().parent
_NEW_STRATEGY = _HERE.parent
sys.path.insert(0, str(_NEW_STRATEGY))

import config as CFG
from config import (
    OUT, INITIAL_TRAIN_END, RF_N_ESTIMATORS_FIXED, RANDOM_SEED,
    MONTHLY_EWMA_SPAN,
    MONTHLY_BOOTSTRAP_BLOCK_SNAPSHOT, MONTHLY_BOOTSTRAP_BLOCK_SMOOTHED,
    RF_INNER_CV_GAP_ROWS_MONTHLY,
)
from data_loader import (
    load_daily_close, load_daily_volume, load_daily_macro,
    load_weekly_close,
)
from daily_features import build_daily_panel, ALL_FEATURES, FRED_FEATURES
import daily_model as DM
from fred_loader import load_fred_wide
from evaluation import (
    weekly_spearman_ic, ndcg_per_week, top_k_precision, hit_rate, r2_global,
    block_bootstrap_ic, vol_vs_return_check, yearly_ic,
    monthly_snapshot, monthly_smoothed,
)


MONTHLY_OUT = OUT / "research" / "rf_monthly"
MONTHLY_OUT.mkdir(parents=True, exist_ok=True)


def build():
    print("[1/4] load daily data + FRED macros")
    dc = load_daily_close()
    dv = load_daily_volume()
    dm = load_daily_macro()
    fred = load_fred_wide()
    print(f"      daily close={dc.shape}, vol={dv.shape}, macro={dm.shape}, FRED={fred.shape}")

    print("[2/4] build daily panel + 20d-forward target")
    panel = build_daily_panel(dc, dv, dm, fred_wide=fred, target_fwd_days=5)
    panel.to_parquet(MONTHLY_OUT / "feature_panel.parquet", index=False)
    print(f"      panel shape: {panel.shape}")
    print(f"      target columns present: "
          f"{[c for c in ['y_5d_excess','y_20d_excess'] if c in panel.columns]}")

    feat_cols = [c for c in ALL_FEATURES if c in panel.columns]
    print(f"      {len(feat_cols)} features used")
    return panel, feat_cols


def _eval_block(df: pd.DataFrame, label: str, block_len: int) -> dict:
    ic = weekly_spearman_ic(df)
    ic_stats = block_bootstrap_ic(ic, block_len=block_len)
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
        f'{label}__bootstrap_block_months':  block_len,
    }


def evaluate(preds: pd.DataFrame) -> dict:
    preds.to_csv(MONTHLY_OUT / "walk_forward_predictions_daily.csv", index=False)

    snap = monthly_snapshot(preds)
    smth = monthly_smoothed(preds, span=MONTHLY_EWMA_SPAN)
    snap.to_csv(MONTHLY_OUT / "monthly_snapshot_preds.csv", index=False)
    smth.to_csv(MONTHLY_OUT / "monthly_smoothed_preds.csv", index=False)

    summary = {
        'n_daily_oos_rows':       int(len(preds)),
        'n_daily_oos_periods':    int(preds['date'].nunique()),
        'n_snapshot_months':      int(snap['date'].nunique()),
        'n_smoothed_months':      int(smth['date'].nunique()),
        'oos_period':             f"{preds['date'].min().date()} to {preds['date'].max().date()}",
        'ewma_span':              MONTHLY_EWMA_SPAN,
    }
    summary.update(_eval_block(snap, 'snapshot', block_len=MONTHLY_BOOTSTRAP_BLOCK_SNAPSHOT))
    summary.update(_eval_block(smth, 'smoothed', block_len=MONTHLY_BOOTSTRAP_BLOCK_SMOOTHED))

    yearly_ic(snap).to_csv(MONTHLY_OUT / "yearly_ic_snapshot.csv")
    yearly_ic(smth).to_csv(MONTHLY_OUT / "yearly_ic_smoothed.csv")

    with open(MONTHLY_OUT / "metrics_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    pd.DataFrame([summary]).to_csv(MONTHLY_OUT / "metrics_summary.csv", index=False)
    return summary


def main():
    t0 = time.time()
    panel, feat_cols = build()

    # Switch RF inner-CV purge gap to 20 (monthly horizon) BEFORE walk-forward.
    print(f"\n[3/4] switching RF inner-CV purge gap to {RF_INNER_CV_GAP_ROWS_MONTHLY} days "
          f"(was {CFG.RF_INNER_CV_GAP_ROWS}) for the 20-day target horizon")
    DM.RF_INNER_CV_GAP_ROWS = RF_INNER_CV_GAP_ROWS_MONTHLY

    print(f"\n[4/4] RF walk-forward, target=y_20d_excess, gap={RF_INNER_CV_GAP_ROWS_MONTHLY}, "
          f"initial train end {INITIAL_TRAIN_END}, quarterly refit")
    preds = DM.walk_forward_daily(
        panel, feature_cols=feat_cols,
        target_col='y_20d_excess',
        model_kind='rf',
        use_sector_fe=True,
        tune_rf=True,
    )
    if preds.empty:
        print("[stop] no predictions")
        return

    summary = evaluate(preds)

    print("\n=== HEADLINE METRICS (RF tuned, monthly cadence, 57 features) ===")
    keys = [
        'n_snapshot_months', 'n_smoothed_months',
        'snapshot__spearman_ic_mean',   'snapshot__spearman_ic_ir',
        'snapshot__ic_ci95_low',        'snapshot__ic_ci95_high',
        'snapshot__top3_precision_mean','snapshot__hit_rate',
        'snapshot__sanity_corr_pred_y', 'snapshot__sanity_corr_pred_absy',
        'snapshot__bootstrap_block_months',
        'smoothed__spearman_ic_mean',   'smoothed__spearman_ic_ir',
        'smoothed__ic_ci95_low',        'smoothed__ic_ci95_high',
        'smoothed__top3_precision_mean','smoothed__hit_rate',
        'smoothed__sanity_corr_pred_y', 'smoothed__sanity_corr_pred_absy',
        'smoothed__bootstrap_block_months',
    ]
    for k in keys:
        v = summary.get(k, float('nan'))
        if isinstance(v, float):
            print(f"  {k:50s}: {v: .4f}")
        else:
            print(f"  {k:50s}: {v}")

    print("\n=== COMPARISON TO PRIOR (Wed-on-frs_4 IC) ===")
    print("  Prior 45-feat RF (weekly, fixed hyper)         : +0.0451  CI [-0.027, +0.107]")
    print("  Prior 57-feat RF (weekly, tuned + FRED)        : +0.0393  CI [-0.028, +0.101]")
    print(f"  This run: 57-feat RF (MONTHLY snapshot)        : "
          f"{summary['snapshot__spearman_ic_mean']: .4f}  CI ["
          f"{summary['snapshot__ic_ci95_low']: .4f}, {summary['snapshot__ic_ci95_high']: .4f}]")
    print(f"  This run: 57-feat RF (MONTHLY smoothed, EWMA5) : "
          f"{summary['smoothed__spearman_ic_mean']: .4f}  CI ["
          f"{summary['smoothed__ic_ci95_low']: .4f}, {summary['smoothed__ic_ci95_high']: .4f}]")

    print(f"\n[done] {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()

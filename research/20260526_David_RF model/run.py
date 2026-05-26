from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from config import OUT, INITIAL_TRAIN_END, DECAY_HORIZONS_WEEKS, SECTOR_ETFS
from data_loader import (
    load_weekly_close, load_weekly_volume, load_macro_weekly,
    load_daily_close,
)
from target import compute_frs_4, compute_h_step_frs, rank_zscore_within_week
from features import (
    BASE_FEATURES, DAILY_FEATURES, DISPERSION_FEATURES, MACRO_FEATURES, ALL_FEATURES,
    SIGN_FLIPS,
    build_base_features, build_daily_features, build_dispersion_features,
    build_macro_features, attach_macro_interactions,
    per_date_zscore, apply_sign_flips,
)
from model import walk_forward
from evaluation import (
    weekly_spearman_ic, ndcg_per_week, top_k_precision, hit_rate, r2_global,
    block_bootstrap_ic, ndcg_permutation_null, yearly_ic, regime_ic,
    vol_vs_return_check,
)


def build_panel():
    print("[1/6] load data")
    close   = load_weekly_close()
    volume  = load_weekly_volume()
    daily_c = load_daily_close()
    macro   = load_macro_weekly()
    print(f"      weekly close={close.shape}, weekly volume={volume.shape}")
    print(f"      daily close={daily_c.shape}, macro={macro.shape}")
    print(f"      weekly date range: {close.index.min().date()} -> {close.index.max().date()}")
    print(f"      daily  date range: {daily_c.index.min().date()} -> {daily_c.index.max().date()}")

    print("[2/6] compute target frs_4 and rank-z within each week")
    frs4_wide = compute_frs_4(close)
    y_long_raw = frs4_wide.stack().rename('y_raw').reset_index()
    y_long_raw.columns = ['date', 'ticker', 'y_raw']
    y_long = y_long_raw.rename(columns={'y_raw': 'y'})
    y_long = rank_zscore_within_week(y_long, y_col='y')

    print("[3/6] build features")
    base_long  = build_base_features(close, volume)
    daily_long = build_daily_features(daily_c, weekly_dates=close.index, window=60)
    disp_long  = build_dispersion_features(close)
    macro_z    = build_macro_features(macro)
    macro_z = macro_z.rename(columns={macro_z.columns[0]: 'date'}) if 'date' not in macro_z.columns else macro_z
    macro_z['date'] = pd.to_datetime(macro_z['date'])

    for df_ in (base_long, daily_long, disp_long):
        df_['date'] = pd.to_datetime(df_['date'])

    feats = base_long.merge(daily_long, on=['date','ticker'], how='outer') \
                     .merge(disp_long,  on=['date','ticker'], how='outer')
    feats = attach_macro_interactions(feats, macro_z)
    print(f"      feature columns: {[c for c in feats.columns if c not in ('date','ticker')]}")

    print("[4/6] merge with target; per-date z-score base+daily; flip signs")
    panel = feats.merge(y_long[['date','ticker','y']], on=['date','ticker'], how='inner')
    panel = panel.merge(y_long_raw, on=['date','ticker'], how='left')
    panel = panel.dropna(subset=['y']).reset_index(drop=True)

    zscore_cols = BASE_FEATURES + DAILY_FEATURES
    panel = per_date_zscore(panel, zscore_cols)
    for c in DISPERSION_FEATURES + MACRO_FEATURES:
        if c in panel.columns:
            panel[c] = panel[c].fillna(0.0)
    panel = apply_sign_flips(panel, SIGN_FLIPS)

    print(f"      panel shape: {panel.shape}")
    print(f"      tickers: {sorted(panel['ticker'].unique())}")
    print(f"      n weeks: {panel['date'].nunique()}")
    panel.to_parquet(OUT / "feature_panel.parquet", index=False)
    print(f"      wrote {OUT / 'feature_panel.parquet'}")
    return panel, close


def run_walk_forward(panel: pd.DataFrame, positive: bool, out_dir: Path) -> pd.DataFrame:
    label = 'A_constrained' if positive else 'B_unconstrained'
    print(f"[5/6] walk-forward ElasticNet (positive={positive}) "
          f"+ sector FE (initial train end {INITIAL_TRAIN_END}, quarterly refit) "
          f"[{label}]")
    feature_cols = [c for c in ALL_FEATURES if c in panel.columns]
    print(f"      using {len(feature_cols)} features")
    preds = walk_forward(panel, feature_cols=feature_cols, target_col='y',
                         use_sector_fe=True, positive=positive)
    if not preds.empty and 'y_raw' in panel.columns:
        preds = preds.merge(panel[['date','ticker','y_raw']],
                            on=['date','ticker'], how='left')
    out_dir.mkdir(parents=True, exist_ok=True)
    preds.to_csv(out_dir / "walk_forward_predictions.csv", index=False)
    print(f"      wrote {out_dir / 'walk_forward_predictions.csv'} "
          f"({len(preds)} rows, {preds['date'].nunique() if len(preds) else 0} weeks)")
    return preds


def evaluate(preds: pd.DataFrame, close: pd.DataFrame, out_dir: Path, label: str) -> dict:
    print(f"[6/6] aggregate ML metrics [{label}]")

    preds_rank = preds[['date','ticker','y_true','y_pred']].copy()

    preds_raw = preds[['date','ticker','y_raw','y_pred']].copy() if 'y_raw' in preds.columns else None
    if preds_raw is not None:
        preds_raw = preds_raw.rename(columns={'y_raw': 'y_true'}).dropna(subset=['y_true'])

    def _eval_block(df: pd.DataFrame, label: str) -> dict:
        ic = weekly_spearman_ic(df)
        ic_stats = block_bootstrap_ic(ic)
        ndcg_series = ndcg_per_week(df, k=3)
        tk_series = top_k_precision(df, k=3)
        return {
            f'{label}__n_oos_weeks_with_valid_ic': int(ic.shape[0]),
            f'{label}__weekly_spearman_ic_mean':   float(ic.mean()) if len(ic) else float('nan'),
            f'{label}__weekly_spearman_ic_std':    float(ic.std(ddof=1)) if len(ic) > 1 else float('nan'),
            f'{label}__weekly_spearman_ic_ir':     ic_stats['ir_mean'],
            f'{label}__ic_ci95_low':               ic_stats['ci_low'],
            f'{label}__ic_ci95_high':              ic_stats['ci_high'],
            f'{label}__ic_ir_ci95_low':            ic_stats['ir_ci_low'],
            f'{label}__ic_ir_ci95_high':           ic_stats['ir_ci_high'],
            f'{label}__ndcg_at_3_mean':            float(ndcg_series.mean()) if len(ndcg_series) else float('nan'),
            f'{label}__top3_precision_mean':       float(tk_series.mean()) if len(tk_series) else float('nan'),
            f'{label}__top3_precision_random':     3.0 / 11.0,
            f'{label}__hit_rate':                  hit_rate(df),
            f'{label}__r2_global':                 r2_global(df),
        }

    summary = {
        'n_oos_weeks_total': int(preds['date'].nunique()),
        'oos_period':        f"{preds['date'].min().date()} to {preds['date'].max().date()}",
    }
    summary.update(_eval_block(preds_rank, 'on_rank_target'))
    if preds_raw is not None:
        summary.update(_eval_block(preds_raw, 'on_raw_excess_return'))

    print("[eval] NDCG@3 permutation null on raw-return ranking (n_perm=200)")
    target_for_perm = preds_raw if preds_raw is not None else preds_rank
    perm = ndcg_permutation_null(target_for_perm, k=3, n_perm=200)
    summary.update({
        'ndcg_at_3_observed_raw': perm['observed'],
        'ndcg_at_3_null_mean':    perm['null_mean'],
        'ndcg_at_3_null_std':     perm['null_std'],
        'ndcg_at_3_p_value':      perm['p_value'],
    })

    print("[eval] decay curve on raw forward excess return")
    decay_rows = []
    for h in DECAY_HORIZONS_WEEKS:
        y_h_wide = compute_h_step_frs(close, h)
        y_h = y_h_wide.stack().rename('y_h').reset_index()
        y_h.columns = ['date', 'ticker', 'y_h']
        y_h['date'] = pd.to_datetime(y_h['date'])
        m = preds[['date','ticker','y_pred']].merge(y_h, on=['date','ticker'], how='inner')
        m = m.dropna(subset=['y_h']).rename(columns={'y_h': 'y_true'})
        if m.empty:
            decay_rows.append({'horizon_weeks': h, 'ic_mean': float('nan')})
            continue
        ic_h = weekly_spearman_ic(m)
        decay_rows.append({'horizon_weeks': h, 'ic_mean': float(ic_h.mean())})
    pd.DataFrame(decay_rows).to_csv(out_dir / "decay_curve.csv", index=False)

    print("[eval] sub-period stability (on raw-return IC)")
    eval_df_for_subperiod = preds_raw if preds_raw is not None else preds_rank
    yic = yearly_ic(eval_df_for_subperiod)
    yic.to_csv(out_dir / "subperiod_ic_yearly.csv")

    macro = load_macro_weekly()
    vix = macro['VIX'].copy()
    vix_med = vix.median()
    vix_regime = pd.Series(np.where(vix >= vix_med, 'high_VIX', 'low_VIX'), index=vix.index)
    d10 = macro['dUS10Y'].copy()
    rates_regime = pd.Series(np.where(d10 >= 0, 'rising_rates', 'falling_rates'), index=d10.index)
    reg_vix = regime_ic(eval_df_for_subperiod, vix_regime)
    reg_rt  = regime_ic(eval_df_for_subperiod, rates_regime)
    pd.DataFrame({
        'regime':         list(reg_vix.index) + list(reg_rt.index),
        'mean_weekly_ic': list(reg_vix.values) + list(reg_rt.values),
        'kind':           ['vix']*len(reg_vix) + ['rates']*len(reg_rt),
    }).to_csv(out_dir / "subperiod_ic_regime.csv", index=False)

    print("[eval] vol-vs-return sanity check (raw-return target)")
    vr = vol_vs_return_check(preds_raw if preds_raw is not None else preds_rank)
    summary.update({
        'sanity_corr_pred_y':    vr['corr_pred_y'],
        'sanity_corr_pred_absy': vr['corr_pred_absy'],
        'sanity_ratio':          vr['ratio_return_over_risk'],
    })

    with open(out_dir / "metrics_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    pd.DataFrame([summary]).to_csv(out_dir / "metrics_summary.csv", index=False)
    print(f"      wrote {out_dir / 'metrics_summary.json'}")
    print(f"\n=== HEADLINE METRICS [{label}] ===")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"  {k:48s}: {v: .4f}")
        else:
            print(f"  {k:48s}: {v}")
    return summary


def main():
    t0 = time.time()
    panel, close = build_panel()
    summaries = {}
    for positive_flag, label in [(True, 'A_constrained'), (False, 'B_unconstrained')]:
        out_dir = OUT / label
        preds = run_walk_forward(panel, positive=positive_flag, out_dir=out_dir)
        if preds.empty:
            print(f"[stop:{label}] no walk-forward predictions produced")
            continue
        summaries[label] = evaluate(preds, close, out_dir=out_dir, label=label)

    if summaries:
        rows = []
        for lab, s in summaries.items():
            row = {'variant': lab}
            row.update(s)
            rows.append(row)
        pd.DataFrame(rows).to_csv(OUT / "comparison_AB.csv", index=False)
        print(f"\nwrote {OUT / 'comparison_AB.csv'}")
        print("\n=== SIDE-BY-SIDE (key metrics) ===")
        keys = [
            'on_rank_target__weekly_spearman_ic_mean',
            'on_rank_target__weekly_spearman_ic_ir',
            'on_rank_target__ic_ci95_low',
            'on_rank_target__ic_ci95_high',
            'on_raw_excess_return__weekly_spearman_ic_mean',
            'on_raw_excess_return__weekly_spearman_ic_ir',
            'on_raw_excess_return__top3_precision_mean',
            'on_raw_excess_return__hit_rate',
            'ndcg_at_3_p_value',
            'sanity_corr_pred_y',
            'sanity_corr_pred_absy',
        ]
        labels = list(summaries.keys())
        header = f"  {'metric':50s} " + " ".join(f"{l:>18s}" for l in labels)
        print(header)
        for k in keys:
            row = f"  {k:50s} "
            for lab in labels:
                v = summaries[lab].get(k, float('nan'))
                row += f" {v: >18.4f}" if isinstance(v, float) else f" {str(v):>18s}"
            print(row)
    print(f"\n[done] {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()

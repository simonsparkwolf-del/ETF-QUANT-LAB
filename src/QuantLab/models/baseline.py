"""
Baseline Model — Long-Only Version (Fixed)
====================================
Simplified strategy that only goes long the top 3 sectors.

Key features:
  1. Decision point  : Wednesday close (signal calculated on Wed TRI)
  2. Execution point : Thursday close  (position takes effect at Thu close TRI)
  3. Return period   : Thursday close TRI → next Thursday close TRI
  4. No open prices  : entire pipeline uses TOT_RETURN_INDEX_GROSS_DVDS only
  5. No transaction costs or slippage
  6. Absolute momentum filter: if MOM < 0, ETF excluded from long candidates
  7. LONG-ONLY: No short positions, only long the top 3 sectors
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
from QuantLab.utils.config import load_pathes
warnings.filterwarnings("ignore")
pathes = load_pathes()
# ── Output directory ──────────────────────────────────────────────────────────
OUT = f"{pathes['reports_path']}/baseline/output"
os.makedirs(OUT, exist_ok=True)

# ── Universe ──────────────────────────────────────────────────────────────────
ETFS = ["XLB", "XLC", "XLE", "XLF", "XLI",
        "XLK", "XLP", "XLU", "XLV", "XLRE", "XLY"]

# =============================================================================
# 1. DATA LOADING
# =============================================================================

def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.dropna(subset=["Dates"]).copy()
    df["date"] = pd.to_datetime(df["Dates"])
    df = df.sort_values("date").set_index("date")
    return df


def extract_tri(df: pd.DataFrame) -> pd.DataFrame:
    """Extract Total Return Index for all ETFs + SPX."""
    cols = {}
    for t in ETFS:
        cols[t] = df[f"{t} US Equity TOT_RETURN_INDEX_GROSS_DVDS"].astype(float)
    cols["SPX"] = df["SPX Index TOT_RETURN_INDEX_GROSS_DVDS"].astype(float)
    return pd.DataFrame(cols)


# =============================================================================
# 2. SIGNAL CONSTRUCTION
# =============================================================================

def multi_window_momentum(tri: pd.DataFrame,
                           windows=(20, 40, 60),
                           weights=(0.2, 0.3, 0.5)) -> pd.DataFrame:
    mom = pd.DataFrame(0.0, index=tri.index, columns=tri.columns)
    for w, wt in zip(windows, weights):
        mom += wt * (tri / tri.shift(w) - 1)
    return mom


def relative_strength_zscore(mom_etf: pd.DataFrame,
                               mom_spx: pd.Series,
                               window: int = 252) -> pd.DataFrame:
    rs = mom_etf.apply(lambda col: (1 + col) / (1 + mom_spx) - 1)
    rs_mean = rs.rolling(window, min_periods=60).mean()
    rs_std  = rs.rolling(window, min_periods=60).std()
    return (rs - rs_mean) / rs_std.replace(0, np.nan).fillna(1.0) # [FIX] 避免除0後仍有NaN


def vol_adjusted_momentum(tri: pd.DataFrame,
                           windows=(20, 40, 60),
                           weights=(0.2, 0.3, 0.5)) -> pd.DataFrame:
    daily_ret = tri.pct_change()
    mom = multi_window_momentum(tri, windows, weights)

    comp_vol = pd.DataFrame(0.0, index=tri.index, columns=tri.columns)
    for w, wt in zip(windows, weights):
        comp_vol += wt * daily_ret.rolling(w, min_periods=max(5, w // 2)).std() * np.sqrt(252)

    va = mom / comp_vol.replace(0, np.nan).fillna(1.0) # [FIX] 避免除0後仍有NaN
    va = va.where(mom >= 0, -va.abs())
    return va


def zscore_cross_section(df: pd.DataFrame) -> pd.DataFrame:
    mu  = df.mean(axis=1)
    sig = df.std(axis=1).replace(0, np.nan).fillna(1.0)
    return df.subtract(mu, axis=0).divide(sig, axis=0)


def compute_composite(tri_etf: pd.DataFrame,
                       tri_spx: pd.Series) -> pd.DataFrame:
    mom     = multi_window_momentum(tri_etf)
    spx_mom = multi_window_momentum(pd.DataFrame({"SPX": tri_spx}))["SPX"]
    rs_z    = relative_strength_zscore(mom, spx_mom)
    va_mom  = vol_adjusted_momentum(tri_etf)

    z_mom = zscore_cross_section(mom)
    z_rs  = zscore_cross_section(rs_z)
    z_va  = zscore_cross_section(va_mom)

    return (z_mom + z_rs + z_va) / 3.0


# =============================================================================
# 3. PORTFOLIO CONSTRUCTION
# =============================================================================

def inv_vol_weights(tickers: list, daily_ret: pd.DataFrame,
                    ref_date, window: int = 20) -> dict:
    """
    Inverse-volatility weights for a basket of tickers.
    [FIXED] Removed 25% cap due to Top-3 math conflict.
    [FIXED] Properly allocate target sum to leave uninvested cash if len(tickers) < 3.
    """
    if not tickers:
        return {}
        
    loc   = daily_ret.index.get_loc(ref_date)
    start = max(0, loc - window)
    vols  = daily_ret.iloc[start:loc + 1][tickers].std()
    inv   = (1.0 / vols.replace(0, np.nan)).fillna(0)
    total = inv.sum()
    
    # 每個入圍的 ETF 代表 1/3 的總倉位。不足 3 個則剩餘為現金。
    target_sum = len(tickers) / 3.0

    if total == 0:
        return {t: target_sum / len(tickers) for t in tickers}
        
    # 根據反波動率分配 target_sum
    wts = (inv / total) * target_sum
    return wts.to_dict()


def build_weekly_weights(tri_etf: pd.DataFrame,
                          tri_spx: pd.Series,
                          hold_threshold: int = 2) -> pd.DataFrame:
    composite  = compute_composite(tri_etf, tri_spx)
    raw_mom    = multi_window_momentum(tri_etf)
    daily_ret  = tri_etf.pct_change()

    weekly_comp = composite.resample("W-WED").last()
    weekly_mom  = raw_mom.resample("W-WED").last()

    prev_longs  = []
    records     = []

    for wed, scores in weekly_comp.iterrows():
        if scores.isna().all():
            continue

        mom_row = weekly_mom.loc[wed] if wed in weekly_mom.index else pd.Series(dtype=float)
        ranked  = scores.dropna().sort_values(ascending=False)
        all_etfs = list(ranked.index)

        # ── Absolute momentum filter for long candidates ──────────────────
        if not mom_row.empty:
            valid_long = [t for t in all_etfs if mom_row.get(t, -1) > 0]
        else:
            valid_long = all_etfs

        # ── Rank stickiness (FIXED: strictly enforce valid_long) ──────────
        def sticky(new_set, prev_set, full_list, valid_pool):
            if not prev_set:
                return new_set
            for t in prev_set:
                # [FIXED] 強制換倉條件 1：原有持倉已經不符合絕對動量 > 0 
                if t not in valid_pool:
                    return new_set
                # 強制換倉條件 2：排名跌出緩衝區
                old_r = prev_set.index(t)
                new_r = full_list.index(t) if t in full_list else len(full_list)
                if abs(new_r - old_r) > hold_threshold:
                    return new_set
            return prev_set

        top3_candidates = [t for t in all_etfs if t in valid_long][:3]
        if len(top3_candidates) < 3:
            # 不滿 3 個，直接全上，不用黏性機制
            top3 = top3_candidates
        else:
            # 傳入 valid_long 確保黏性不會挽救負動量的 ETF
            top3 = sticky(top3_candidates, prev_longs, all_etfs, valid_long)

        prev_longs = top3

        # ── Find nearest available date in daily index ────────────────────
        avail = daily_ret.index[daily_ret.index <= wed]
        if len(avail) == 0:
            continue
        ref = avail[-1]

        # ── Inv-vol weights (LONG ONLY) ───────────────────────────────────
        weights = {t: 0.0 for t in ETFS}

        if top3:
            lw = inv_vol_weights(top3, daily_ret, ref)
            for t, w in lw.items():
                weights[t] = w

        records.append({"signal_date": wed, **weights})

    return pd.DataFrame(records).set_index("signal_date")


# =============================================================================
# 4. BACKTEST ENGINE
# =============================================================================

def run_backtest(weights_df: pd.DataFrame,
                 tri_etf: pd.DataFrame) -> tuple:
    thursdays = tri_etf[tri_etf.index.dayofweek == 3]
    rets, dates = [], []

    for wed in weights_df.index:
        exec_thurs = thursdays.index[thursdays.index > wed]
        if len(exec_thurs) == 0:
            break
        t0 = exec_thurs[0]

        next_thurs = thursdays.index[thursdays.index > t0]
        if len(next_thurs) == 0:
            break
        t1 = next_thurs[0]

        tgt = weights_df.loc[wed].reindex(ETFS).fillna(0.0)

        tri_t0 = tri_etf.loc[t0, ETFS]
        tri_t1 = tri_etf.loc[t1, ETFS]
        period_ret_etf = (tri_t1 / tri_t0 - 1).fillna(0.0)

        period_ret = (tgt * period_ret_etf).sum()
        rets.append(period_ret)
        dates.append(t0)   

    strat = pd.Series(rets, index=pd.DatetimeIndex(dates), name="strategy")

    wts_aligned = weights_df.reindex(columns=ETFS).fillna(0.0)
    turnover_series = wts_aligned.diff().abs().sum(axis=1)
    turnover_series.index.name = None
    thu_dates = []
    for wed in wts_aligned.index:
        exec_thurs = tri_etf[tri_etf.index.dayofweek == 3].index
        nxt = exec_thurs[exec_thurs > wed]
        thu_dates.append(nxt[0] if len(nxt) else pd.NaT)
    turnover_series = pd.Series(
        turnover_series.values,
        index=pd.DatetimeIndex(thu_dates),
        name="turnover"
    ).dropna()

    return strat, turnover_series


def spx_weekly_returns(tri_spx: pd.Series) -> pd.Series:
    spx_thu = tri_spx[tri_spx.index.dayofweek == 3]
    return spx_thu.pct_change().shift(-1).dropna().rename("SPX")


def eq_weight_weekly_returns(tri_etf: pd.DataFrame) -> pd.Series:
    thu = tri_etf[ETFS][tri_etf.index.dayofweek == 3]
    return thu.pct_change().shift(-1).mean(axis=1).rename("EqWeight")


# =============================================================================
# 5. PERFORMANCE METRICS
# =============================================================================

def metrics(ret: pd.Series, bench: pd.Series,
            weights_df: pd.DataFrame = None,
            rf: float = 0.05) -> dict:
    ret  = ret.dropna()
    wpy  = 52
    rf_w = (1 + rf) ** (1 / wpy) - 1

    total  = (1 + ret).prod() - 1
    n_yr   = len(ret) / wpy
    cagr   = (1 + total) ** (1 / n_yr) - 1 if n_yr > 0 else np.nan
    vol    = ret.std() * np.sqrt(wpy)
    exc    = ret - rf_w
    sharpe = exc.mean() / exc.std() * np.sqrt(wpy) if exc.std() > 0 else np.nan

    down     = ret[ret < rf_w]
    sort_d   = down.std() * np.sqrt(wpy)
    sortino  = (ret.mean() - rf_w) * wpy / sort_d if sort_d > 0 else np.nan

    cum    = (1 + ret).cumprod()
    mdd    = ((cum - cum.cummax()) / cum.cummax()).min()
    calmar = cagr / abs(mdd) if mdd != 0 else np.nan
    win    = (ret > 0).mean()

    bm     = bench.reindex(ret.index).dropna()
    common = ret.reindex(bm.index).dropna()
    if len(common) > 5:
        active = common - bm.reindex(common.index)
        ir     = active.mean() / active.std() * np.sqrt(wpy) if active.std() > 0 else np.nan
        alpha  = active.mean() * wpy
    else:
        ir, alpha = np.nan, np.nan

    if weights_df is not None:
        wts = weights_df.reindex(columns=ETFS).fillna(0.0)
        weekly_one_way = wts.diff().abs().sum(axis=1) / 2.0
        ann_turnover   = weekly_one_way.mean() * wpy
        avg_exposure   = wts.clip(lower=0).sum(axis=1).mean()
    else:
        ann_turnover = np.nan
        avg_exposure = np.nan

    return {
        "Total Return"    : total,
        "CAGR"            : cagr,
        "Ann. Volatility" : vol,
        "Sharpe Ratio"    : sharpe,
        "Sortino Ratio"   : sortino,
        "Calmar Ratio"    : calmar,
        "Max Drawdown"    : mdd,
        "Win Rate"        : win,
        "Ann. Alpha"      : alpha,
        "Info Ratio"      : ir,
        "Ann. Turnover"   : ann_turnover,
        "Avg Exposure"    : avg_exposure,
    }


def print_metrics(strat_m, bench_m, label):
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    print(f"  {'Metric':<22} {'Strategy':>16} {'SPY Benchmark':>14}")
    print(f"  {'─'*54}")
    pct_keys = {"Total Return", "CAGR", "Ann. Volatility",
                "Max Drawdown", "Win Rate", "Ann. Alpha",
                "Ann. Turnover", "Avg Exposure"}
    for k, v in strat_m.items():
        sv = f"{v:.2%}" if k in pct_keys else f"{v:.3f}"
        bv_raw = bench_m.get(k, np.nan)
        bv = f"{bv_raw:.2%}" if k in pct_keys else f"{bv_raw:.3f}"
        print(f"  {k:<22} {sv:>16} {bv:>14}")

def save_metrics(strat_m, bench_m, label, fname: str):
    with open(fname, "w") as f:
        f.write(f"  {label}\n")
        f.write(f"{'─'*60}\n")
        f.write(f"  {'Metric':<22} {'Strategy':>16} {'SPY Benchmark':>14}\n")
        f.write(f"  {'─'*54}\n")
        pct_keys = {"Total Return", "CAGR", "Ann. Volatility",
                "Max Drawdown", "Win Rate", "Ann. Alpha",
                "Ann. Turnover", "Avg Exposure"}
        for k, v in strat_m.items():
            sv = f"{v:.2%}" if k in pct_keys else f"{v:.3f}"
            bv_raw = bench_m.get(k, np.nan)
            bv = f"{bv_raw:.2%}" if k in pct_keys else f"{bv_raw:.3f}"
            f.write(f"  {k:<22} {sv:>16} {bv:>14}\n")
        f.write(f"{'─'*60}\n")
    print(f"  Saved: {fname}")


# =============================================================================
# 6. VISUALISATION
# =============================================================================

def plot_performance(strat: pd.Series, bench: pd.Series, eq: pd.Series,
                     title: str, fname: str):
    fig = plt.figure(figsize=(13, 11))
    gs  = fig.add_gridspec(3, 1, height_ratios=[3, 1.3, 1.3], hspace=0.35)
    fig.suptitle(title, fontsize=13, fontweight="bold")

    ax1 = fig.add_subplot(gs[0])
    cum_s = (1 + strat.dropna()).cumprod()
    cum_b = (1 + bench.reindex(strat.index).fillna(0)).cumprod()
    cum_e = (1 + eq.reindex(strat.index).fillna(0)).cumprod()

    ax1.plot(cum_s, label="Strategy",     color="#1f77b4", lw=2)
    ax1.plot(cum_b, label="SPY Benchmark",color="#d62728", lw=1.5, ls="--")
    ax1.plot(cum_e, label="Equal Weight", color="#2ca02c", lw=1.5, ls=":")
    ax1.set_ylabel("Cumulative Return (Base = 1.0)")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.2f}x"))
    ax1.legend(fontsize=9)
    ax1.grid(alpha=0.3)

    ax2 = fig.add_subplot(gs[1])
    dd = cum_s / cum_s.cummax() - 1
    ax2.fill_between(dd.index, dd, 0, color="#1f77b4", alpha=0.4)
    ax2.plot(dd, color="#1f77b4", lw=1)
    ax2.set_ylabel("Drawdown")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax2.grid(alpha=0.3)

    ax3 = fig.add_subplot(gs[2])
    roll_sh = strat.rolling(26).apply(
        lambda x: x.mean() / x.std() * np.sqrt(52) if x.std() > 0 else np.nan
    )
    ax3.plot(roll_sh, color="#1f77b4", lw=1.2)
    ax3.axhline(0, color="black", lw=0.8, ls="--")
    ax3.axhline(1, color="green", lw=0.8, ls=":", alpha=0.6)
    ax3.set_ylabel("Rolling 26W Sharpe")
    ax3.grid(alpha=0.3)

    plt.savefig(fname, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Saved: {fname}")


def plot_monthly_heatmap(ret: pd.Series, title: str, fname: str):
    monthly = ret.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    df = monthly.to_frame("r")
    df["year"]  = df.index.year
    df["month"] = df.index.month
    pivot = df.pivot(index="year", columns="month", values="r")
    pivot.columns = ["Jan","Feb","Mar","Apr","May","Jun",
                     "Jul","Aug","Sep","Oct","Nov","Dec"]

    fig, ax = plt.subplots(figsize=(13, max(3, len(pivot) * 0.75)))
    fig.suptitle(title, fontsize=12, fontweight="bold")

    vals = pivot.values[~np.isnan(pivot.values)]
    vmax = max(abs(vals).max(), 0.01) if len(vals) else 0.05

    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto",
                   vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(12))
    ax.set_xticklabels(pivot.columns, fontsize=9)
    ax.set_yticks(range(len(pivot)))
    ax.set_yticklabels(pivot.index, fontsize=9)

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.1%}", ha="center", va="center",
                        fontsize=7.5, color="black")

    plt.colorbar(im, ax=ax,
                 format=mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))
    plt.tight_layout()
    plt.savefig(fname, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Saved: {fname}")


def plot_weights(weights_df: pd.DataFrame, title: str, fname: str):
    fig, ax = plt.subplots(figsize=(13, 4))
    fig.suptitle(title, fontsize=12, fontweight="bold")

    colors = plt.cm.tab20.colors
    ec = {e: colors[i] for i, e in enumerate(ETFS)}

    longs  = weights_df.clip(lower=0)

    for e in ETFS:
        if e in longs.columns:
            ax.fill_between(longs.index, 0, longs[e],
                             color=ec[e], alpha=0.85, label=e)
    ax.set_ylabel("Long Weight")
    ax.set_ylim(0, 1.05)
    ax.legend(ncol=6, fontsize=7.5, loc="upper right")
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(fname, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Saved: {fname}")


def plot_etf_usage(weights_df: pd.DataFrame, title: str, fname: str):
    long_counts  = (weights_df.clip(lower=0) > 0.01).sum()

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle(title, fontsize=12, fontweight="bold")

    x = range(len(ETFS))
    ax.bar(x, long_counts[ETFS],  label="Long",  color="#1f77b4", alpha=0.85)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(ETFS, fontsize=10)
    ax.set_ylabel("Number of Weeks Selected")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    total_weeks = len(weights_df)
    ax.text(0.01, 0.97, f"Total weeks: {total_weeks}",
            transform=ax.transAxes, fontsize=8,
            va="top", color="grey")

    plt.tight_layout()
    plt.savefig(fname, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"  Saved: {fname}")


# =============================================================================
# 7. PIPELINE
# =============================================================================

def pipeline(df: pd.DataFrame, label: str) -> dict:
    print(f"\n{'='*60}")
    print(f"  {label}  (Long-Only)")
    print(f"{'='*60}")

    tri     = extract_tri(df)
    tri_etf = tri[ETFS]
    tri_spx = tri["SPX"]

    print("  Building weekly signals (Wednesday close)...")
    wts = build_weekly_weights(tri_etf, tri_spx, hold_threshold=2)

    print("  Simulating portfolio (Thursday close TRI)...")
    strat, turnover_s = run_backtest(wts, tri_etf)
    bench = spx_weekly_returns(tri_spx)
    eq    = eq_weight_weekly_returns(tri_etf)
    sm = metrics(strat, bench, weights_df=wts)
    bm = metrics(bench.reindex(strat.index).dropna(),
                 bench.reindex(strat.index).dropna())
    print_metrics(sm, bm, label)
    save_metrics(sm, bm, label, f"{OUT}/{label}_metrics.txt")
    tag  = label.replace(" ", "_").replace("/", "-").replace("(","").replace(")","")
    plot_performance(strat, bench, eq,
                     title=f"Cumulative Returns — {label} [Long-Only]",
                     fname=f"{OUT}/{tag}_LO_cumulative.png")
    plot_monthly_heatmap(strat,
                         title=f"Monthly Returns — {label} [Long-Only]",
                         fname=f"{OUT}/{tag}_LO_heatmap.png")
    plot_weights(wts,
                 title=f"Weekly Sector Weights — {label} [Long-Only]",
                 fname=f"{OUT}/{tag}_LO_weights.png")
    plot_etf_usage(wts,
                   title=f"ETF Selection Frequency — {label} [Long-Only]",
                   fname=f"{OUT}/{tag}_LO_etf_usage.png")
    return {"strat": strat, "bench": bench, "eq": eq,
            "weights": wts, "turnover": turnover_s,
            "metrics": sm, "bm_metrics": bm}


# =============================================================================
# 8. MAIN
# =============================================================================

if __name__ == "__main__":
    from QuantLab.utils.config import load_pathes
    pathes = load_pathes()
    print("Loading data...")
    df_train = load_and_clean(f"{pathes['data_path']}/processed/train_raw_data.csv")
    df_test  = load_and_clean(f"{pathes['data_path']}/processed/test_raw_data.csv")

    # ── In-sample (2021-2024) ─────────────────────────────────────────────
    train_lo = pipeline(df_train, "In-Sample 2021-2024")

    # ── Out-of-sample (2024-2026) ─────────────────────────────────────────
    test_lo  = pipeline(df_test,  "Out-of-Sample 2024-2026")

    print(f"\n\nAll outputs saved to: {OUT}")
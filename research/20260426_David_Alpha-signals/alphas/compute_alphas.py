"""
compute_alphas.py — end-to-end runner.

Usage (from repo root):
    python -m alphas.compute_alphas
    python -m alphas.compute_alphas --split train   # train only
    python -m alphas.compute_alphas --split test    # test only
    python -m alphas.compute_alphas --split full    # train+test concatenated

Outputs
-------
alphas/output/alpha_values_<split>.csv
    Wide CSV: index=Dates, columns=MultiIndex(alpha_id, ticker)

alphas/output/alpha_summary_<split>.csv
    One row per (alpha, ticker) with: mean, std, IC_vs_next_ret, t_stat.

alphas/output/alpha_signals.md
    Human-readable summary (overwritten on each run).
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from alphas.data_loader import load_panel, combine_panels, TICKERS
from alphas.alpha_library import compute_all_alphas, GROUP_A, GROUP_B, NOT_IMPLEMENTED

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR  = Path(__file__).resolve().parents[3] / "data" / "processed"
OUT_DIR   = REPO_ROOT / "alphas" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── IC helper ────────────────────────────────────────────────────────────────

def information_coefficient(
    signal: pd.Series, fwd_return: pd.Series, periods: int = 5
) -> tuple[float, float]:
    """
    Spearman IC between today's signal and the forward `periods`-day return.
    Returns (ic, t_stat).
    """
    s = signal.dropna()
    r = fwd_return.shift(-periods).dropna()
    common = s.index.intersection(r.index)
    if len(common) < 30:
        return np.nan, np.nan
    ic, _ = scipy_stats.spearmanr(s.loc[common], r.loc[common])
    t = ic * np.sqrt((len(common) - 2) / (1 - ic ** 2 + 1e-12))
    return ic, t


# ── main ─────────────────────────────────────────────────────────────────────

def run_all(split: str = "train") -> dict[int, pd.DataFrame]:
    train_path = DATA_DIR / "train_raw_data.csv"
    test_path  = DATA_DIR / "test_raw_data.csv"

    if split == "train":
        panel = load_panel(train_path)
    elif split == "test":
        panel = load_panel(test_path)
    else:  # full
        panel = combine_panels(train_path, test_path)

    print(f"[compute_alphas] split={split}  dates={len(panel['close'])}  tickers={len(TICKERS)}")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        alphas = compute_all_alphas(panel)

    print(f"[compute_alphas] computed {len(alphas)}/82 alphas successfully")
    return alphas, panel


def save_results(alphas: dict[int, pd.DataFrame], panel: dict, split: str = "train") -> None:
    # ── wide CSV ─────────────────────────────────────────────────────────────
    frames = []
    for aid, df in sorted(alphas.items()):
        tmp = df.copy()
        tmp.columns = pd.MultiIndex.from_tuples(
            [(aid, t) for t in tmp.columns], names=["alpha", "ticker"]
        )
        frames.append(tmp)

    wide = pd.concat(frames, axis=1)
    wide_path = OUT_DIR / f"alpha_values_{split}.csv"
    wide.to_csv(wide_path)
    print(f"[compute_alphas] saved -> {wide_path}")

    # ── summary CSV (IC, mean, std, t-stat) ──────────────────────────────────
    fwd_ret = panel["close"].pct_change().shift(-5)  # 5-day fwd return
    rows = []
    for aid, df in sorted(alphas.items()):
        group = "A" if aid in GROUP_A else "B"
        for ticker in TICKERS:
            sig = df[ticker].dropna()
            fr  = fwd_ret[ticker]
            ic, t = information_coefficient(sig, fr, 5)
            rows.append(
                dict(
                    alpha=aid,
                    group=group,
                    ticker=ticker,
                    mean=sig.mean(),
                    std=sig.std(),
                    ic_5d=ic,
                    t_stat=t,
                )
            )
    summary = pd.DataFrame(rows)
    summary_path = OUT_DIR / f"alpha_summary_{split}.csv"
    summary.to_csv(summary_path, index=False)
    print(f"[compute_alphas] saved -> {summary_path}")

    # ── markdown summary ─────────────────────────────────────────────────────
    write_markdown_summary(alphas, summary, split)


def write_markdown_summary(
    alphas: dict[int, pd.DataFrame],
    summary: pd.DataFrame,
    split: str,
) -> None:
    md_path = OUT_DIR / "alpha_signals.md"

    agg = (
        summary.groupby(["alpha", "group"])
        .agg(mean_ic=("ic_5d", "mean"), mean_t=("t_stat", "mean"))
        .reset_index()
        .sort_values("mean_ic", ascending=False)
    )

    lines: list[str] = [
        "# Alpha Signals — Computed Results",
        "",
        f"**Data split:** `{split}` &nbsp;|&nbsp; "
        f"**Alphas computed:** {len(alphas)} / 82 implementable (101 total)",
        "",
        "## Summary Table",
        "",
        "| Alpha | Group | Mean IC (5d) | Mean t-stat | Notes |",
        "|------:|:-----:|-------------:|------------:|:------|",
    ]

    for _, row in agg.iterrows():
        aid   = int(row["alpha"])
        grp   = row["group"]
        mic   = f"{row['mean_ic']:.4f}" if not np.isnan(row["mean_ic"]) else "—"
        mt    = f"{row['mean_t']:.2f}"  if not np.isnan(row["mean_t"])  else "—"
        note  = "vwap≈(O+H+L+C)/4" if grp == "B" else ""
        lines.append(f"| {aid:3d} | {grp} | {mic} | {mt} | {note} |")

    lines += [
        "",
        "## Not-Implemented Alphas (19)",
        "",
        "| Alpha | Reason |",
        "|------:|:-------|",
        "| 48 | Requires `IndNeutralize(subindustry)` — not meaningful for sector-ETF universe |",
        "| 56 | Requires market cap (`cap`) — not available in dataset |",
        "| 58 | Requires `IndNeutralize(sector)` + exact vwap |",
        "| 59 | Requires `IndNeutralize(industry)` + exact vwap |",
        "| 63 | Requires `IndNeutralize(industry)` + exact vwap |",
        "| 67 | Requires `IndNeutralize(sector, subindustry)` + exact vwap |",
        "| 69 | Requires `IndNeutralize(industry)` + exact vwap |",
        "| 70 | Requires `IndNeutralize(industry)` + exact vwap |",
        "| 76 | Requires `IndNeutralize(sector)` + exact vwap |",
        "| 79 | Requires `IndNeutralize(sector)` + exact vwap |",
        "| 80 | Requires `IndNeutralize(industry)` |",
        "| 82 | Requires `IndNeutralize(sector)` |",
        "| 87 | Requires `IndNeutralize(industry)` + exact adv81/vwap |",
        "| 89 | Requires `IndNeutralize(industry)` + exact vwap |",
        "| 90 | Requires `IndNeutralize(subindustry)` |",
        "| 91 | Requires `IndNeutralize(industry)` + exact vwap |",
        "| 93 | Requires `IndNeutralize(industry)` + exact vwap |",
        "| 97 | Requires `IndNeutralize(industry)` + exact vwap |",
        "| 100 | Requires `IndNeutralize(subindustry)` twice |",
        "",
        "## Files",
        "",
        "| File | Description |",
        "|:-----|:------------|",
        f"| `alphas/output/alpha_values_{split}.csv` | Raw daily alpha values (dates × alpha×ticker MultiIndex) |",
        f"| `alphas/output/alpha_summary_{split}.csv` | Per-alpha-per-ticker IC, t-stat, mean, std |",
        "| `alphas/alpha_library.py` | All 82 alpha implementations |",
        "| `alphas/operators.py` | Operator primitives (rank, ts_rank, decay_linear, …) |",
        "| `alphas/data_loader.py` | Panel data loader + vwap approximation |",
        "| `alphas/tests/test_alphas.py` | Unit tests |",
        "| `implementability_report.md` | Full per-alpha assessment |",
        "",
    ]

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[compute_alphas] saved -> {md_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="train", choices=["train", "test", "full"])
    args = parser.parse_args()

    alphas, panel = run_all(args.split)
    save_results(alphas, panel, args.split)
    print("[compute_alphas] done.")

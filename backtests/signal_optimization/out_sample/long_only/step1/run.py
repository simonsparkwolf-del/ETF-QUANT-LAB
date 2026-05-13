"""
Step 1 — Single signal quality pre-screening (optimization.md §4 Step 1).

Backtests six signals through SiganlOptimizationStrategy:
  Signal 0 : equal-weight baseline  (OptimizationTestSignal, all scores = 1.0)
  Signal 1 : ML LightGBM_frs3       (val NDCG@3 = 0.639)
  Signal 2 : ML Ensemble_RankAvg_frs1 (val NDCG@3 = 0.632)
  Signal 3 : ML XGBoost_frs3        (val NDCG@3 = 0.623)
  Signal 4 : ML PCA_Ridge_frs3      (val NDCG@3 = 0.622)
  Signal 5 : ML MLP_frs2            (val NDCG@3 = 0.596)

Phase 1 — Screening: all 6 signals run without saving artifacts; metrics are
  collected and compared.

Phase 2 — Best signal: the highest-Sharpe ML signal is re-run with full
  artifacts (all_in_one_panel.png, CSVs, JSON, md) saved under
  outputs/best_signal_{id}/.

Outputs written to  backtests/signal_optimization/step1/outputs/:
  step1_comparison.md   — side-by-side metric table for all 6 signals
  step1_summary.json    — full metrics dict for programmatic use
  best_signal_{id}/     — full BacktestAnalyzer artifacts for the winner
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.debug import DebugRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.ml_backtest_signal import MLBacktestSignal
from QuantLab.backtest.signal.optimization_test import OptimizationTestSignal
from QuantLab.backtest.strategy.signal_optimization import SiganlOptimizationStrategy
from QuantLab.utils.config import load_pathes


# ── constants ──────────────────────────────────────────────────────────────

from typing import Literal

MODE: Literal["long", "short"] = "long"

START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 3, 1)
INITIAL_NAV = 10_000.0

_SIGNAL_LABELS: dict[int, str] = {
    0: "EqualWeight (baseline)",
    1: "LightGBM_frs3",
    2: "Ensemble_RankAvg_frs1",
    3: "XGBoost_frs3",
    4: "PCA_Ridge_frs3",
    5: "MLP_frs2",
}


# ── helpers ────────────────────────────────────────────────────────────────

def _build_signal(signal_id: int):
    if signal_id == 0:
        return OptimizationTestSignal("equal_weight_baseline")
    return MLBacktestSignal(signal_id)


def _run_one(
    signal,
    run_name: str,
    db_path: Path,
    save_path: Path,
    *,
    save_artifacts: bool,
    mode: Literal["long", "short"] = MODE,
) -> dict:
    strategy = SiganlOptimizationStrategy(run_name, mode=mode, long_cost=0.0, base_slippage=0.0)
    config = BacktestConfig(
        name=run_name,
        start_date=START_DATE,
        end_date=END_DATE,
        db_path=db_path,
        save_path=save_path,
        signal=signal,
        strategy=strategy,
        risk=DebugRisk(f"{run_name}_risk"),
        account=Account(INITIAL_NAV),
        long_cost=0.0,
        short_cost_per_day=0.0,
        base_slippage=0.0,
        long_enabled=(mode == "long"),
        short_enabled=(mode == "short"),
        save_eval_artifacts=save_artifacts,
    )
    engine = BacktestEngine(config)
    engine.run()
    return engine.evaluate()


def _objective(m: dict) -> float:
    return float(m.get("sharpe", 0.0))
   


# ── report formatting ──────────────────────────────────────────────────────

def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def _f2(v: float) -> str:
    return f"{v:.3f}"


def _delta(candidate: float, baseline: float, as_pct: bool = False) -> str:
    d = candidate - baseline
    s = _pct(d) if as_pct else _f2(d)
    return f"+{s}" if d >= 0 else s


def _build_report(
    all_metrics: dict[int, dict],
    best_id: int,
    baseline_id: int = 0,
) -> str:
    bm = all_metrics[baseline_id]
    lines = [
        "# Step 1 — Signal Screening Report",
        "",
        f"Date range: {START_DATE} → {END_DATE}  |  "
        f"Initial NAV: {INITIAL_NAV:,.0f}",
        "",
        "## Comparison Table",
        "",
        "| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. | Δ Sharpe vs §0 |",
        "|--------|:------:|:-----------:|:--------:|:------:|:-------------:|:--------------:|",
    ]
    for sid in sorted(all_metrics):
        m = all_metrics[sid]
        label = _SIGNAL_LABELS[sid]
        tag = " ★" if sid == best_id else ""
        sharpe = float(m.get("sharpe", 0.0))
        ann_ret = float(m.get("annual_return", 0.0))
        ann_vol = float(m.get("annual_volatility", 0.0))
        max_dd = float(m.get("max_drawdown", 0.0))
        to_ann = float(m.get("turnover_annualized", 0.0))
        d_sharpe = _delta(sharpe, float(bm.get("sharpe", 0.0)))
        lines.append(
            f"| {label}{tag} | {_f2(sharpe)} | {_pct(ann_ret)} | {_pct(ann_vol)} | "
            f"{_pct(max_dd)} | {_pct(to_ann)} | {d_sharpe} |"
        )

    lines += [
        "",
        f"> ★ best ML signal by Sharpe",
        "",
        "## Verdict",
        "",
        f"Best ML signal: **{_SIGNAL_LABELS[best_id]}** (Signal {best_id})",
        f"- Sharpe: {_f2(float(all_metrics[best_id].get('sharpe', 0.0)))}",
        "",
        "Full artifacts saved in `outputs/best_signal_{}/`.".format(best_id),
    ]
    return "\n".join(lines)


# ── main ───────────────────────────────────────────────────────────────────

def main() -> None:
    paths = load_pathes()
    root = paths["ROOT"]
    db_path = root / "simon_test" /  "datapool.db"
    outputs = root / "backtests" / "signal_optimization"/ "out_sample"/"long_only" / "step1" / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    # ── Phase 1: screen all 6 signals (no artifact I/O) ──────────────────
    all_metrics: dict[int, dict] = {}
    for sid in range(0, 6):
        label = _SIGNAL_LABELS[sid]
        print(f"\n{'=' * 60}")
        print(f"  Signal {sid}: {label}")
        print(f"{'=' * 60}")
        signal = _build_signal(sid)
        metrics = _run_one(
            signal,
            run_name=f"step1_sig{sid}",
            db_path=db_path,
            save_path=outputs,
            save_artifacts=False,
        )
        all_metrics[sid] = metrics
        print(
            f"  Sharpe={metrics.get('sharpe', 0):.3f}  "
            f"AnnRet={metrics.get('annual_return', 0) * 100:.2f}%  "
            f"MaxDD={metrics.get('max_drawdown', 0) * 100:.2f}%  "
            f"TO_ann={metrics.get('turnover_annualized', 0) * 100:.2f}%"
        )

    # ── Phase 2: select best ML signal by objective ──────────────────────
    best_id = max(range(1, 6), key=lambda sid: _objective(all_metrics[sid]))
    best_label = _SIGNAL_LABELS[best_id]
    print(f"\n>>> Best ML signal: {best_id} ({best_label}), Sharpe={_objective(all_metrics[best_id]):.3f}")

    # ── Phase 3: save comparison report ──────────────────────────────────
    report_md = _build_report(all_metrics, best_id)
    (outputs / "step1_comparison.md").write_text(report_md, encoding="utf-8")
    print(f"\n--- Comparison ---\n{report_md}\n")

    with open(outputs / "step1_summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_signal_id": best_id,
                "best_signal_label": best_label,
                "all_metrics": {str(k): v for k, v in all_metrics.items()},
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    # ── Phase 4: re-run best signal with full artifacts ──────────────────
    best_save = outputs / f"best_signal_{best_id}"
    best_save.mkdir(parents=True, exist_ok=True)
    print(f"\n{'=' * 60}")
    print(f"  Re-running best signal {best_id} ({best_label}) with full artifacts")
    print(f"{'=' * 60}")
    signal_best = _build_signal(best_id)
    best_metrics = _run_one(
        signal_best,
        run_name=f"step1_best_signal_{best_id}",
        db_path=db_path,
        save_path=best_save,
        save_artifacts=True,
    )
    print(
        f"\n  [BEST] Sharpe={best_metrics.get('sharpe', 0):.3f}  "
        f"AnnRet={best_metrics.get('annual_return', 0) * 100:.2f}%  "
        f"MaxDD={best_metrics.get('max_drawdown', 0) * 100:.2f}%"
    )
    print(f"\nArtifacts saved to: {best_save}")
    print("Done.")


if __name__ == "__main__":
    main()

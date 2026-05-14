"""
Alpha screening — short-only mode, same alpha id set as signal_1 LightGBM features.

Each ``alpha_id`` in ``ALPHA_IDS`` is backtested via ``SiganlOptimizationStrategy``
(mode="short"); sizing uses softmax(-score) so the worst-ranked ETFs get the
highest short weight.

Outputs:  backtests/signal_optimization/short_only/alphas/outputs/
  alpha_comparison.md
  alpha_summary.json
  best_alpha_{id}/
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Literal

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.debug import DebugRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.alpha_test import AlphaBacktestSignal
from QuantLab.backtest.signal.optimization_test import OptimizationTestSignal
from QuantLab.backtest.strategy.signal_optimization import SiganlOptimizationStrategy
from QuantLab.utils.config import load_pathes

ALPHA_IDS: tuple[int, ...] = (
    6, 10, 14, 16, 18, 19, 20, 22, 23, 24, 26, 30, 31, 32, 34, 37, 40, 44,
    51, 53, 54, 57, 61, 64, 66, 72, 83, 95, 101,
    108, 110, 116, 118, 123, 125, 127, 128, 130, 135, 136,
)

MODE: Literal["long", "short"] = "short"

START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 3, 1)
INITIAL_NAV = 10_000.0


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


def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def _f2(v: float) -> str:
    return f"{v:.3f}"


def _build_alpha_report(all_metrics: dict[int, dict], best_aid: int, baseline_metrics: dict) -> str:
    bm_sharpe = float(baseline_metrics.get("sharpe", 0.0))
    lines = [
        "# Alpha screening — Short-Only (signal_1 feature subset)",
        "",
        f"Date range: {START_DATE} → {END_DATE}  |  Initial NAV: {INITIAL_NAV:,.0f}",
        "",
        "## Benchmark (Equal-Weight Short)",
        "",
        "| Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |",
        "|:------:|:-----------:|:--------:|:------:|:-------------:|",
        f"| {_f2(bm_sharpe)} | {_pct(float(baseline_metrics.get('annual_return', 0.0)))} "
        f"| {_pct(float(baseline_metrics.get('annual_volatility', 0.0)))} "
        f"| {_pct(float(baseline_metrics.get('max_drawdown', 0.0)))} "
        f"| {_pct(float(baseline_metrics.get('turnover_annualized', 0.0)))} |",
        "",
        "## Comparison",
        "",
        "| alpha_id | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. | Δ Sharpe vs EW |",
        "|----------|:------:|:-----------:|:--------:|:------:|:-------------:|:--------------:|",
    ]
    for aid in sorted(all_metrics):
        m = all_metrics[aid]
        tag = " ★" if aid == best_aid else ""
        sharpe = float(m.get("sharpe", 0.0))
        ann_ret = float(m.get("annual_return", 0.0))
        ann_vol = float(m.get("annual_volatility", 0.0))
        max_dd = float(m.get("max_drawdown", 0.0))
        to_ann = float(m.get("turnover_annualized", 0.0))
        d = sharpe - bm_sharpe
        d_str = f"+{_f2(d)}" if d >= 0 else _f2(d)
        lines.append(
            f"| {aid}{tag} | {_f2(sharpe)} | {_pct(ann_ret)} | {_pct(ann_vol)} | "
            f"{_pct(max_dd)} | {_pct(to_ann)} | {d_str} |"
        )
    lines += [
        "",
        f"> ★ best by Sharpe: **alpha_id {best_aid}** ({_f2(float(all_metrics[best_aid].get('sharpe', 0.0)))})",
        "",
        f"Artifacts: `outputs/best_alpha_{best_aid}/`",
    ]
    return "\n".join(lines)


def main() -> None:
    paths = load_pathes()
    root = paths["ROOT"]
    db_path = root / "simon_test" / "datapool.db"
    outputs = root / "backtests" / "signal_optimization" /"out_sample" / "short_only" / "alphas" / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    # ── Equal-weight baseline ─────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("  Equal-Weight Baseline (Short)")
    print(f"{'=' * 60}")
    baseline_metrics = _run_one(
        OptimizationTestSignal("ew_baseline"),
        run_name="short_alpha_ew_baseline",
        db_path=db_path,
        save_path=outputs,
        save_artifacts=False,
    )
    print(
        f"  Sharpe={baseline_metrics.get('sharpe', 0):.3f}  "
        f"AnnRet={baseline_metrics.get('annual_return', 0) * 100:.2f}%  "
        f"MaxDD={baseline_metrics.get('max_drawdown', 0) * 100:.2f}%"
    )

    all_metrics: dict[int, dict] = {}
    for aid in ALPHA_IDS:
        print(f"\n{'=' * 60}")
        print(f"  alpha_id={aid}")
        print(f"{'=' * 60}")
        signal = AlphaBacktestSignal(aid)
        metrics = _run_one(
            signal,
            run_name=f"short_alpha_screen_{aid}",
            db_path=db_path,
            save_path=outputs,
            save_artifacts=False,
        )
        all_metrics[aid] = metrics
        print(
            f"  Sharpe={metrics.get('sharpe', 0):.3f}  "
            f"AnnRet={metrics.get('annual_return', 0) * 100:.2f}%  "
            f"MaxDD={metrics.get('max_drawdown', 0) * 100:.2f}%  "
            f"TO_ann={metrics.get('turnover_annualized', 0) * 100:.2f}%"
        )

    best_aid = max(all_metrics, key=lambda a: _objective(all_metrics[a]))
    print(f"\n>>> Best alpha_id: {best_aid}, Sharpe={_objective(all_metrics[best_aid]):.3f}")

    (outputs / "alpha_comparison.md").write_text(
        _build_alpha_report(all_metrics, best_aid, baseline_metrics), encoding="utf-8"
    )

    with open(outputs / "alpha_summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_alpha_id": best_aid,
                "baseline_metrics": baseline_metrics,
                "all_metrics": {str(k): v for k, v in all_metrics.items()},
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    best_save = outputs / f"best_alpha_{best_aid}"
    best_save.mkdir(parents=True, exist_ok=True)
    print(f"\n{'=' * 60}")
    print(f"  Re-running best alpha_id={best_aid} with full artifacts")
    print(f"{'=' * 60}")
    best_metrics = _run_one(
        AlphaBacktestSignal(best_aid),
        run_name=f"short_alpha_best_{best_aid}",
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

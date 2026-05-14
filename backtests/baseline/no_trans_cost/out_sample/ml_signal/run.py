"""
Baseline Long-Short — ML signal screening (out-of-sample).

Each ML signal (1–5) is backtested via BaselineStrategy + BaselineRisk.

Outputs:  backtests/baseline/out_sample/ml_signal/outputs/
  comparison.md
  summary.json
  best_signal_{id}/
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.baseline import BaselineRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.ml_backtest_signal import MLBacktestSignal
from QuantLab.backtest.strategy.baseline import BaselineStrategy
from QuantLab.utils.config import load_pathes

START_DATE  = date(2025, 1, 1)
END_DATE    = date(2026, 3, 1)
INITIAL_NAV = 10_000.0

SIGNAL_IDS: tuple[int, ...] = (1, 2, 3, 4, 5)

_SIGNAL_LABELS: dict[int, str] = {
    1: "LightGBM_frs3",
    2: "Ensemble_RankAvg_frs1",
    3: "XGBoost_frs3",
    4: "PCA_Ridge_frs3",
    5: "MLP_frs2",
}


def _run_one(
    signal,
    run_name: str,
    db_path: Path,
    save_path: Path,
    *,
    save_artifacts: bool,
) -> dict:
    strategy = BaselineStrategy(run_name)
    risk     = BaselineRisk(f"{run_name}_risk")
    config = BacktestConfig(
        name=run_name,
        start_date=START_DATE,
        end_date=END_DATE,
        db_path=db_path,
        save_path=save_path,
        signal=signal,
        strategy=strategy,
        risk=risk,
        account=Account(INITIAL_NAV),
        long_cost=0.0,
        short_cost_per_day=0.0,
        base_slippage=0.0,
        long_enabled=True,
        short_enabled=True,
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


def _build_report(all_metrics: dict[int, dict], best_id: int) -> str:
    lines = [
        "# Baseline Long-Short — ML Signal Comparison (Out-of-Sample)",
        "",
        f"Date range: {START_DATE} → {END_DATE}  |  Initial NAV: {INITIAL_NAV:,.0f}",
        "",
        "## Comparison",
        "",
        "| Signal | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |",
        "|--------|:------:|:-----------:|:--------:|:------:|:-------------:|",
    ]
    for sid in sorted(all_metrics):
        m = all_metrics[sid]
        tag = " ★" if sid == best_id else ""
        lines.append(
            f"| {_SIGNAL_LABELS[sid]}{tag} "
            f"| {_f2(float(m.get('sharpe', 0.0)))} "
            f"| {_pct(float(m.get('annual_return', 0.0)))} "
            f"| {_pct(float(m.get('annual_volatility', 0.0)))} "
            f"| {_pct(float(m.get('max_drawdown', 0.0)))} "
            f"| {_pct(float(m.get('turnover_annualized', 0.0)))} |"
        )
    lines += [
        "",
        f"> ★ best by Sharpe: **{_SIGNAL_LABELS[best_id]}** ({_f2(_objective(all_metrics[best_id]))})",
        "",
        f"Artifacts: `outputs/best_signal_{best_id}/`",
    ]
    return "\n".join(lines)


def main() -> None:
    paths = load_pathes()
    db_path = paths["ROOT"] / "simon_test" / "datapool.db"
    outputs = paths["ROOT"] / "backtests" / "baseline" / "out_sample" / "ml_signal" / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    all_metrics: dict[int, dict] = {}
    for sid in SIGNAL_IDS:
        print(f"\n{'=' * 60}")
        print(f"  Signal {sid}: {_SIGNAL_LABELS[sid]}")
        print(f"{'=' * 60}")
        metrics = _run_one(
            MLBacktestSignal(sid),
            run_name=f"os_baseline_sig{sid}",
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

    best_id = max(all_metrics, key=lambda sid: _objective(all_metrics[sid]))
    print(f"\n>>> Best signal: {best_id} ({_SIGNAL_LABELS[best_id]}), "
          f"Sharpe={_objective(all_metrics[best_id]):.3f}")

    (outputs / "comparison.md").write_text(
        _build_report(all_metrics, best_id), encoding="utf-8"
    )

    with open(outputs / "summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_signal_id": best_id,
                "best_signal_label": _SIGNAL_LABELS[best_id],
                "all_metrics": {str(k): v for k, v in all_metrics.items()},
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    best_save = outputs / f"best_signal_{best_id}"
    best_save.mkdir(parents=True, exist_ok=True)
    print(f"\n{'=' * 60}")
    print(f"  Re-running Signal {best_id} ({_SIGNAL_LABELS[best_id]}) with full artifacts")
    print(f"{'=' * 60}")
    best_metrics = _run_one(
        MLBacktestSignal(best_id),
        run_name=f"os_baseline_best_signal_{best_id}",
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

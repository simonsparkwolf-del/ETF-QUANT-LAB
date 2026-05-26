"""
Baseline Long-Short — Alpha signal screening (out-of-sample).

Each alpha in ALPHA_IDS is backtested via BaselineStrategy + BaselineRisk.

Outputs:  backtests/baseline/out_sample/alpha/outputs/
  comparison.md
  summary.json
  best_alpha_{id}/
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.baseline import BaselineRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.alpha_test import AlphaBacktestSignal
from QuantLab.backtest.strategy.baseline import BaselineStrategy
from QuantLab.utils.config import get_db_path

START_DATE  = date(2025, 1, 1)
END_DATE    = date(2026, 3, 1)
INITIAL_NAV = 10_000.0

ALPHA_IDS: tuple[int, ...] = (
    6, 10, 14, 16, 18, 19, 20, 22, 23, 24, 26, 30, 31, 32, 34, 37, 40, 44,
    51, 53, 54, 57, 61, 64, 66, 72, 83, 95, 101,
    108, 110, 116, 118, 123, 125, 127, 128, 130, 135, 136,
)


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


def _build_report(all_metrics: dict[int, dict], best_aid: int) -> str:
    lines = [
        "# Baseline Long-Short — Alpha Comparison (Out-of-Sample)",
        "",
        f"Date range: {START_DATE} → {END_DATE}  |  Initial NAV: {INITIAL_NAV:,.0f}",
        "",
        "## Comparison",
        "",
        "| alpha_id | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |",
        "|----------|:------:|:-----------:|:--------:|:------:|:-------------:|",
    ]
    for aid in sorted(all_metrics):
        m = all_metrics[aid]
        tag = " ★" if aid == best_aid else ""
        lines.append(
            f"| {aid}{tag} "
            f"| {_f2(float(m.get('sharpe', 0.0)))} "
            f"| {_pct(float(m.get('annual_return', 0.0)))} "
            f"| {_pct(float(m.get('annual_volatility', 0.0)))} "
            f"| {_pct(float(m.get('max_drawdown', 0.0)))} "
            f"| {_pct(float(m.get('turnover_annualized', 0.0)))} |"
        )
    lines += [
        "",
        f"> ★ best by Sharpe: **alpha_id {best_aid}** ({_f2(_objective(all_metrics[best_aid]))})",
        "",
        f"Artifacts: `outputs/best_alpha_{best_aid}/`",
    ]
    return "\n".join(lines)


def main() -> None:
    db_path = get_db_path()
    outputs = Path(__file__).parent / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    all_metrics: dict[int, dict] = {}
    for aid in ALPHA_IDS:
        print(f"\n{'=' * 60}")
        print(f"  alpha_id={aid}")
        print(f"{'=' * 60}")
        metrics = _run_one(
            AlphaBacktestSignal(aid),
            run_name=f"os_baseline_alpha_{aid}",
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

    (outputs / "comparison.md").write_text(
        _build_report(all_metrics, best_aid), encoding="utf-8"
    )

    with open(outputs / "summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_alpha_id": best_aid,
                "all_metrics": {str(k): v for k, v in all_metrics.items()},
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    best_save = outputs / f"best_alpha_{best_aid}"
    best_save.mkdir(parents=True, exist_ok=True)
    print(f"\n{'=' * 60}")
    print(f"  Re-running alpha_id={best_aid} with full artifacts")
    print(f"{'=' * 60}")
    best_metrics = _run_one(
        AlphaBacktestSignal(best_aid),
        run_name=f"os_baseline_best_alpha_{best_aid}",
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

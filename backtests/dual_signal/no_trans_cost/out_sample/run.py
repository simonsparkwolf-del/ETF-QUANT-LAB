"""
Dual-Signal L/S — Alpha pair grid (out-of-sample).

Tests LongShortAlphaSignal(long_alpha_id, short_alpha_id) with DualSignalStrategy
+ BaselineRisk across all combinations of LONG_ALPHAS × SHORT_ALPHAS.

Symmetric pairs (long == short) reproduce the single-alpha BaselineStrategy result
and serve as the per-alpha baseline within this run.

Outputs:  backtests/dual_signal/no_trans_cost/out_sample/outputs/
  comparison.md
  summary.json
  best_l{long_id}_s{short_id}/   (full artifacts for the top Sharpe pair)

Candidate pools (from Step 1 IS LP/SP ranking):
  LONG_ALPHAS  — top 4 IS LP performers
  SHORT_ALPHAS — top 5 IS SP performers
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.baseline import BaselineRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.dual_head_alpha_signal import LongShortAlphaSignal
from QuantLab.backtest.strategy.asymmetric_ls import DualSignalStrategy
from QuantLab.utils.config import get_db_path

START_DATE  = date(2025, 1, 1)
END_DATE    = date(2026, 3, 1)
INITIAL_NAV = 10_000.0

# Top 4 IS LP alpha pool (by IS LP Sharpe: #24 1.122, #66 0.744, #101 0.732, #64 0.726).
LONG_ALPHAS: tuple[int, ...] = (24, 66, 101, 64)

# Top 5 IS SP alpha pool (by IS SP Sharpe: #24 -0.420, #57 -0.559, #19 -0.593, #51 -0.621, #66 -0.630).
SHORT_ALPHAS: tuple[int, ...] = (24, 57, 19, 51, 66)


def _pair_key(long_id: int, short_id: int) -> str:
    return f"l{long_id}_s{short_id}"


def _run_one(
    long_id: int,
    short_id: int,
    db_path: Path,
    save_path: Path,
    *,
    save_artifacts: bool,
) -> dict:
    key = _pair_key(long_id, short_id)
    run_name = f"os_dual_{key}"
    signal   = LongShortAlphaSignal(long_id, short_id)
    strategy = DualSignalStrategy(run_name)
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


def _build_report(
    all_metrics: dict[tuple[int, int], dict],
    best_pair: tuple[int, int],
) -> str:
    bl, bs = best_pair
    lines = [
        "# Dual-Signal L/S — Alpha Pair Grid (Out-of-Sample)",
        "",
        f"Date range: {START_DATE} → {END_DATE}  |  Initial NAV: {INITIAL_NAV:,.0f}",
        "",
        f"Long pool:  {LONG_ALPHAS}",
        f"Short pool: {SHORT_ALPHAS}",
        "",
        "> Symmetric pairs (long == short) reproduce single-alpha BaselineStrategy results.",
        "",
        "## Comparison",
        "",
        "| Long α | Short α | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |",
        "|:------:|:-------:|:------:|:-----------:|:--------:|:------:|:-------------:|",
    ]
    for (lid, sid) in sorted(all_metrics):
        m = all_metrics[(lid, sid)]
        tag = " ★" if (lid, sid) == best_pair else ""
        sym = " (sym)" if lid == sid else ""
        lines.append(
            f"| #{lid}{sym} | #{sid}{sym} "
            f"| {_f2(float(m.get('sharpe', 0.0)))}{tag} "
            f"| {_pct(float(m.get('annual_return', 0.0)))} "
            f"| {_pct(float(m.get('annual_volatility', 0.0)))} "
            f"| {_pct(float(m.get('max_drawdown', 0.0)))} "
            f"| {_pct(float(m.get('turnover_annualized', 0.0)))} |"
        )
    lines += [
        "",
        f"> ★ best by Sharpe: **long=#{bl} / short=#{bs}**"
        f" ({_f2(_objective(all_metrics[best_pair]))})",
        "",
        f"Artifacts: `outputs/best_{_pair_key(bl, bs)}/`",
    ]
    return "\n".join(lines)


def main() -> None:
    db_path = get_db_path()
    outputs = Path(__file__).parent / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    pairs = [
        (lid, sid)
        for lid in LONG_ALPHAS
        for sid in SHORT_ALPHAS
    ]

    all_metrics: dict[tuple[int, int], dict] = {}
    for lid, sid in pairs:
        key = _pair_key(lid, sid)
        print(f"\n{'=' * 60}")
        print(f"  long=#{lid}  short=#{sid}  ({key})")
        print(f"{'=' * 60}")
        metrics = _run_one(
            lid, sid,
            db_path=db_path,
            save_path=outputs,
            save_artifacts=False,
        )
        all_metrics[(lid, sid)] = metrics
        print(
            f"  Sharpe={metrics.get('sharpe', 0):.3f}  "
            f"AnnRet={metrics.get('annual_return', 0) * 100:.2f}%  "
            f"MaxDD={metrics.get('max_drawdown', 0) * 100:.2f}%  "
            f"TO_ann={metrics.get('turnover_annualized', 0) * 100:.2f}%"
        )

    best_pair = max(all_metrics, key=lambda p: _objective(all_metrics[p]))
    bl, bs = best_pair
    print(
        f"\n>>> Best pair: long=#{bl} / short=#{bs},"
        f" Sharpe={_objective(all_metrics[best_pair]):.3f}"
    )

    (outputs / "comparison.md").write_text(
        _build_report(all_metrics, best_pair), encoding="utf-8"
    )

    with open(outputs / "summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_long_alpha_id": bl,
                "best_short_alpha_id": bs,
                "all_metrics": {
                    f"{lid},{sid}": v for (lid, sid), v in all_metrics.items()
                },
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    best_save = outputs / f"best_{_pair_key(bl, bs)}"
    best_save.mkdir(parents=True, exist_ok=True)
    print(f"\n{'=' * 60}")
    print(f"  Re-running long=#{bl} / short=#{bs} with full artifacts")
    print(f"{'=' * 60}")
    best_metrics = _run_one(
        bl, bs,
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

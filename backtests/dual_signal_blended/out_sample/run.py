"""
Design 02 — Dual-Blend L/S: 2×2 ablation grid (out-of-sample).

Compares four configurations to isolate the contribution of replacing
single-alpha signals with Step 2 Bayesian-optimised blends on each side.

Grid
----
  l57_s23           — Design 01 best pair (single-alpha baseline)
  lp_blend_s23      — LP blend + single #23  (LP-only upgrade)
  l57_sp_blend      — single #57 + SP blend  (SP-only upgrade)
  lp_blend_sp_blend — LP blend + SP blend    (Design 02 target)

Signal class: LongShortBlendSignal
  - Single-alpha configs use degenerate weight dicts {alpha_id: 1.0}
  - All alpha IDs fetched in a single terminal.alphas() call per bar

Window: OOS only — 2025-01-01 → 2026-03-01 (61 bars)
Target: OOS Sharpe > 2.220 (Design 01 best l57_s23, no-cost)

Outputs: backtests/dual_signal_blended/out_sample/outputs/
  summary.json
  comparison.md
  l57_s23/
  lp_blend_s23/
  l57_sp_blend/
  lp_blend_sp_blend/
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.baseline import BaselineRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.dual_blend_signal import LongShortBlendSignal
from QuantLab.backtest.strategy.asymmetric_ls import DualSignalStrategy
from QuantLab.utils.config import get_db_path

START_DATE  = date(2025, 1, 1)
END_DATE    = date(2026, 3, 1)
INITIAL_NAV = 10_000.0

# ── Step 2 optimised weights — TBD: re-run Step 2 with IS-correct candidate pools ──────────
# Fill these after running:
#   backtests/signal_optimization/01 blend/long power/run.py  → LP_WEIGHTS
#   backtests/signal_optimization/01 blend/short power/run.py → SP_WEIGHTS
LP_WEIGHTS: dict[int, float] = {}  # TODO: fill after re-running long power blend
SP_WEIGHTS: dict[int, float] = {}  # TODO: fill after re-running short power blend

# ── 2×2 ablation configs ─────────────────────────────────────────────────────
CONFIGS: dict[str, tuple[dict[int, float], dict[int, float]]] = {
    "l57_s23":           ({57: 1.0}, {23: 1.0}),
    "lp_blend_s23":      (LP_WEIGHTS, {23: 1.0}),
    "l57_sp_blend":      ({57: 1.0}, SP_WEIGHTS),
    "lp_blend_sp_blend": (LP_WEIGHTS, SP_WEIGHTS),
}


# ── backtest helper ───────────────────────────────────────────────────────────

def _run_one(
    label: str,
    lp_w: dict[int, float],
    sp_w: dict[int, float],
    db_path: Path,
    save_path: Path,
) -> dict:
    run_name = f"dsb_{label}"
    signal   = LongShortBlendSignal(lp_weights=lp_w, sp_weights=sp_w)
    strategy = DualSignalStrategy(run_name)
    risk     = BaselineRisk(f"{run_name}_risk")
    config   = BacktestConfig(
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
        save_eval_artifacts=True,
    )
    engine = BacktestEngine(config)
    engine.run()
    return engine.evaluate()


def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def _f3(v: float) -> str:
    return f"{v:.3f}"


def _build_report(results: dict[str, dict]) -> str:
    lines = [
        "# Design 02 — Dual-Blend L/S: 2×2 Ablation (Out-of-Sample)",
        "",
        f"Date range: {START_DATE} → {END_DATE}  |  Initial NAV: {INITIAL_NAV:,.0f}",
        "",
        "| Config | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |",
        "|--------|:------:|:-----------:|:--------:|:------:|:-------------:|",
    ]
    for label, m in results.items():
        tag = " ★" if label == "lp_blend_sp_blend" else ""
        lines.append(
            f"| `{label}`{tag} "
            f"| {_f3(float(m.get('sharpe', 0)))} "
            f"| {_pct(float(m.get('annual_return', 0)))} "
            f"| {_pct(float(m.get('annual_volatility', 0)))} "
            f"| {_pct(float(m.get('max_drawdown', 0)))} "
            f"| {_pct(float(m.get('turnover_annualized', 0)))} |"
        )
    lines += [
        "",
        "> ★ Design 02 target: `lp_blend_sp_blend`",
        "> Baseline (Design 01 best): `l57_s23` Sharpe = 2.220",
    ]
    return "\n".join(lines)


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    db_path = get_db_path()
    outputs = Path(__file__).parent / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict] = {}
    for label, (lp_w, sp_w) in CONFIGS.items():
        print(f"\n{'=' * 60}")
        print(f"  Config: {label}")
        print(f"{'=' * 60}")
        save_dir = outputs / label
        save_dir.mkdir(parents=True, exist_ok=True)
        m = _run_one(label, lp_w, sp_w, db_path, save_dir)
        results[label] = m
        print(
            f"  Sharpe={m.get('sharpe', 0):.3f}  "
            f"AnnRet={m.get('annual_return', 0) * 100:.2f}%  "
            f"MaxDD={m.get('max_drawdown', 0) * 100:.2f}%  "
            f"TO_ann={m.get('turnover_annualized', 0) * 100:.2f}%"
        )

    (outputs / "comparison.md").write_text(
        _build_report(results), encoding="utf-8"
    )
    with open(outputs / "summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    best = max(results, key=lambda k: float(results[k].get("sharpe", 0)))
    print(f"\n>>> Best config: {best}  Sharpe={results[best].get('sharpe', 0):.3f}")
    print(f"Done. Outputs → {outputs}")


if __name__ == "__main__":
    main()

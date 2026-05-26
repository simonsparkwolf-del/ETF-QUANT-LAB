"""
Dual-Signal L/S — Key pairs, OOS, with realistic transaction costs.

Runs a focused set of pairs (not the full grid) to validate that the
no-transaction-cost OOS ranking holds under realistic market frictions
for SPDR sector ETFs.

Cost assumptions (US institutional, SPDR sector ETFs):
  long_cost        = 0.0002   — 2 bps per leg (commission + half-spread)
  short_cost_per_day = 0.003/365 ≈ 8.22e-6  — 0.30 % p.a. borrow (ETB)
  base_slippage    = 0.0      — captured in long_cost; avoid double-counting

Key pairs selected:
  l57_s23  — OOS #1 (no-cost), primary hypothesis pair
  l23_s23  — OOS #2 (sym), Alpha#23 single-signal baseline
  l57_s19  — OOS #3, robustness of #57 long signal
  l57_s57  — OOS #8 (sym), Alpha#57 single-signal baseline
  l23_s31  — IS best pair; validate whether IS winner survives costs

Outputs:  backtests/dual_signal/trans_cost/out_sample/outputs/
  comparison.md
  summary.json
  <key>/   — full artifacts for every pair
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

# Realistic transaction costs for SPDR sector ETFs (institutional).
# See docs/02_work/02_trading_opt/02_dual_signal_test.md for derivation.
LONG_COST         = 0.0002          # 2 bps per leg (commission + half bid-ask spread)
SHORT_COST_PER_DAY = 0.003 / 365    # 0.30 % p.a. borrow rate (easy-to-borrow ETF)
BASE_SLIPPAGE     = 0.0             # already captured in LONG_COST

# Focused pair list: primary + symmetric baselines + robustness checks.
# Format: (long_alpha_id, short_alpha_id)
KEY_PAIRS: tuple[tuple[int, int], ...] = (
    (57, 23),   # OOS #1 (no-cost): primary hypothesis — LP#57 × SP#23
    (23, 23),   # OOS #2 (sym):     Alpha#23 single-signal baseline
    (57, 19),   # OOS #3:           robustness of #57 long signal
    (57, 57),   # OOS #8 (sym):     Alpha#57 single-signal baseline
    (23, 31),   # IS best pair:     validate IS winner under costs
)


def _pair_key(long_id: int, short_id: int) -> str:
    return f"l{long_id}_s{short_id}"


def _run_one(
    long_id: int,
    short_id: int,
    db_path: Path,
    save_path: Path,
) -> dict:
    key = _pair_key(long_id, short_id)
    run_name = f"os_tc_dual_{key}"
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
        long_cost=LONG_COST,
        short_cost_per_day=SHORT_COST_PER_DAY,
        base_slippage=BASE_SLIPPAGE,
        long_enabled=True,
        short_enabled=True,
        save_eval_artifacts=True,
    )
    engine = BacktestEngine(config)
    engine.run()
    return engine.evaluate()


def _pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def _f2(v: float) -> str:
    return f"{v:.3f}"


def _build_report(all_metrics: dict[tuple[int, int], dict]) -> str:
    lines = [
        "# Dual-Signal L/S — Key Pairs, OOS, With Transaction Costs",
        "",
        f"Date range : {START_DATE} → {END_DATE}  |  Initial NAV: {INITIAL_NAV:,.0f}",
        "",
        f"long_cost         = {LONG_COST} ({LONG_COST * 1e4:.1f} bps per leg)",
        f"short_cost_per_day = {SHORT_COST_PER_DAY:.2e} ({SHORT_COST_PER_DAY * 365 * 100:.2f} % p.a.)",
        f"base_slippage     = {BASE_SLIPPAGE}",
        "",
        "Reference (no-cost OOS Sharpe): l57_s23 = 2.220 | l23_s23 = 2.022 | l57_s19 = 1.933",
        "",
        "| Pair | Sym | Sharpe | Ann. Return | Ann. Vol | Max DD | Turnover Ann. |",
        "|:----:|:---:|:------:|:-----------:|:--------:|:------:|:-------------:|",
    ]
    for (lid, sid) in KEY_PAIRS:
        m = all_metrics.get((lid, sid), {})
        sym = "✓" if lid == sid else ""
        lines.append(
            f"| l{lid}_s{sid} | {sym} "
            f"| {_f2(float(m.get('sharpe', 0.0)))} "
            f"| {_pct(float(m.get('annual_return', 0.0)))} "
            f"| {_pct(float(m.get('annual_volatility', 0.0)))} "
            f"| {_pct(float(m.get('max_drawdown', 0.0)))} "
            f"| {_pct(float(m.get('turnover_annualized', 0.0)))} |"
        )
    return "\n".join(lines)


def main() -> None:
    db_path = get_db_path()
    outputs = Path(__file__).parent / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    all_metrics: dict[tuple[int, int], dict] = {}
    for lid, sid in KEY_PAIRS:
        key = _pair_key(lid, sid)
        pair_save = outputs / key
        pair_save.mkdir(parents=True, exist_ok=True)

        print(f"\n{'=' * 60}")
        print(f"  long=#{lid}  short=#{sid}  ({key})")
        print(f"{'=' * 60}")

        metrics = _run_one(lid, sid, db_path=db_path, save_path=pair_save)
        all_metrics[(lid, sid)] = metrics

        print(
            f"  Sharpe={metrics.get('sharpe', 0):.3f}  "
            f"AnnRet={metrics.get('annual_return', 0) * 100:.2f}%  "
            f"MaxDD={metrics.get('max_drawdown', 0) * 100:.2f}%  "
            f"TO_ann={metrics.get('turnover_annualized', 0) * 100:.2f}%"
        )

    (outputs / "comparison.md").write_text(
        _build_report(all_metrics), encoding="utf-8"
    )

    with open(outputs / "summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "cost_params": {
                    "long_cost": LONG_COST,
                    "short_cost_per_day": SHORT_COST_PER_DAY,
                    "base_slippage": BASE_SLIPPAGE,
                },
                "all_metrics": {
                    _pair_key(lid, sid): v
                    for (lid, sid), v in all_metrics.items()
                },
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\nDone. Outputs →", outputs)


if __name__ == "__main__":
    main()

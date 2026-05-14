"""
Dual-Signal L/S — IS best pair (l23_s31) with transaction costs.

Validates whether the IS best pair from the no-cost grid retains its
performance under realistic SPDR sector ETF trading frictions.

Cost parameters mirror trans_cost/out_sample/run.py:
  long_cost         = 0.0002   (2 bps per leg)
  short_cost_per_day = 0.003/365 ≈ 8.22e-6  (0.30 % p.a. borrow)
  base_slippage     = 0.0

Reference (no-cost IS): l23_s31 Sharpe = 1.440, Ann. Return = 18.70%, Max DD = -9.14%

Outputs: backtests/dual_signal/trans_cost/in_sample/outputs/l23_s31/
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.baseline import BaselineRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.dual_head_alpha_signal import LongShortAlphaSignal
from QuantLab.backtest.strategy.asymmetric_ls import DualSignalStrategy
from QuantLab.utils.config import load_pathes

START_DATE  = date(2021, 3, 3)
END_DATE    = date(2024, 12, 31)
INITIAL_NAV = 10_000.0

LONG_ID  = 23
SHORT_ID = 31

LONG_COST          = 0.0002
SHORT_COST_PER_DAY = 0.003 / 365
BASE_SLIPPAGE      = 0.0


def main() -> None:
    paths = load_pathes()
    db_path = paths["ROOT"] / "simon_test" / "datapool.db"
    save_path = (
        paths["ROOT"]
        / "backtests" / "dual_signal" / "trans_cost" / "in_sample" / "outputs"
        / "l23_s31"
    )
    save_path.mkdir(parents=True, exist_ok=True)

    run_name = "is_tc_dual_l23_s31"
    signal   = LongShortAlphaSignal(LONG_ID, SHORT_ID)
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
    metrics = engine.evaluate()

    print(f"\n{'=' * 60}")
    print(f"  IS best pair: long=#{LONG_ID} / short=#{SHORT_ID}  [with costs]")
    print(f"{'=' * 60}")
    print(f"  Sharpe      : {metrics.get('sharpe', 0):.3f}  (no-cost: 1.440)")
    print(f"  Ann. Return : {metrics.get('annual_return', 0) * 100:.2f}%  (no-cost: 18.70%)")
    print(f"  Ann. Vol    : {metrics.get('annual_volatility', 0) * 100:.2f}%")
    print(f"  Max DD      : {metrics.get('max_drawdown', 0) * 100:.2f}%  (no-cost: -9.14%)")
    print(f"  Win Rate    : {metrics.get('win_rate', 0) * 100:.1f}%")
    print(f"  CAPM α      : {metrics.get('capm_alpha_annual_vs_spy', 0) * 100:.2f}%")
    print(f"  CAPM β      : {metrics.get('capm_beta_vs_spy', 0):.3f}")
    print(f"  Turnover    : {metrics.get('turnover_annualized', 0) * 100:.0f}% p.a.")
    print(f"\nArtifacts saved to: {save_path}")


if __name__ == "__main__":
    main()

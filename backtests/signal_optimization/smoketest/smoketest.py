"""
Smoke backtest: constant optimization signal (all scores = 1) + softmax full-flatten strategy.

Requires a populated ``datapool.db`` (see ``simon_test/backtest/debug.py`` for layout).
"""

from __future__ import annotations

from datetime import date

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.debug import DebugRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.optimization_test import OptimizationTestSignal
from QuantLab.backtest.strategy.signal_optimization import SiganlOptimizationStrategy
from QuantLab.utils.config import load_pathes


def main() -> None:
    paths = load_pathes()
    root = paths["ROOT"]
    db_path = root / "simon_test" / "ML001_data" / "datapool.db"
    save_path = root / "backtests" / "signal_optimization" / "smoketest" / "outputs"
    save_path.mkdir(parents=True, exist_ok=True)

    long_cost = 0.0
    base_slippage = 0.0
    strategy = SiganlOptimizationStrategy(
        "signal_optimization",
        long_cost=long_cost,
        base_slippage=base_slippage,
    )

    config = BacktestConfig(
        name="signal_optimization_smoketest",
        start_date=date(2025, 1, 1),
        end_date=date(2026, 1, 31),
        db_path=db_path,
        save_path=save_path,
        signal=OptimizationTestSignal("optimization_test_const"),
        strategy=strategy,
        risk=DebugRisk("smoketest_pass_through"),
        account=Account(10_000.0),
        long_cost=long_cost,
        short_cost_per_day=0.0,
        base_slippage=base_slippage,
        long_enabled=True,
        short_enabled=False,
        save_eval_artifacts=True,
    )
    engine = BacktestEngine(config)
    engine.run()
    metrics = engine.evaluate()
    print(metrics)


if __name__ == "__main__":
    main()

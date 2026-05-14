"""
Step 2 — LP Signal Blend: Bayesian optimisation (Long Power).

Searches for optimal linear weights over the Step 1 LP candidate pool
{#57, #24, #19, #31, #23} to maximise LP Sharpe on the IS-train window,
then validates on IS-val and OOS.

Windows
-------
  IS-train  2021-03-03 → 2023-12-31  (~150 bars)  optimisation target
  IS-val    2024-01-01 → 2024-12-31  (~52  bars)  overfitting check
  OOS       2025-01-01 → 2026-03-01  (61   bars)  final result

Method
------
  Sampler : TPESampler (seed=42)
  Trials  : 150
  Pruner  : MedianPruner
  Space   : u_k ~ Uniform[0, 1] for each k; normalised to simplex w_k = u_k / Σu

Reference baselines (run once, saved alongside optimised result)
----------------------------------------------------------------
  single_alpha_57/   — best Step 1 single alpha on OOS
  equal_weight_blend/ — all weights = 0.2 (null hypothesis for blending)

Outputs: backtests/signal_optimization/01 blend/long power/outputs/
  study.pkl
  best_weights.json
  summary.json
  best_blend/           full artifacts (OOS window)
  single_alpha_57/      full artifacts (OOS window)
  equal_weight_blend/   full artifacts (OOS window)
"""

from __future__ import annotations

import json
import pickle
from datetime import date
from pathlib import Path

import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
from tqdm import tqdm

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.risk.baseline import BaselineRisk
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig
from QuantLab.backtest.signal.alpha_test import AlphaBacktestSignal
from QuantLab.backtest.signal.signal_blend import AlphaBlendSignal
from QuantLab.backtest.strategy.signal_optimization import SiganlOptimizationStrategy
from QuantLab.utils.config import load_pathes

# ── windows ────────────────────────────────────────────────────────────────────
IS_TRAIN_START = date(2021,  3,  3)
IS_TRAIN_END   = date(2023, 12, 31)
IS_VAL_START   = date(2024,  1,  1)
IS_VAL_END     = date(2024, 12, 31)
OOS_START      = date(2025,  1,  1)
OOS_END        = date(2026,  3,  1)

INITIAL_NAV = 10_000.0

# ── LP candidate pool (Step 1 OOS LP ranking) ─────────────────────────────────
# #24 included: highest OOS LP (2.055); no SP constraint in LP-only optimisation.
LP_CANDIDATES: tuple[int, ...] = (57, 24, 19, 31, 23)

N_TRIALS = 150


# ── backtest helper ────────────────────────────────────────────────────────────

def _run_lp(
    signal,
    start: date,
    end: date,
    db_path: Path,
    save_path: Path,
    *,
    save_artifacts: bool = False,
    run_name: str = "lp_run",
) -> dict:
    strategy = SiganlOptimizationStrategy(run_name, mode="long")
    risk     = BaselineRisk(f"{run_name}_risk")
    config   = BacktestConfig(
        name=run_name,
        start_date=start,
        end_date=end,
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
        short_enabled=False,
        save_eval_artifacts=save_artifacts,
    )
    engine = BacktestEngine(config)
    engine.run()
    return engine.evaluate()


def _sharpe(metrics: dict) -> float:
    return float(metrics.get("sharpe", 0.0))


# ── optuna objective ───────────────────────────────────────────────────────────

def _make_objective(db_path: Path, scratch: Path):
    def objective(trial: optuna.Trial) -> float:
        raw = {aid: trial.suggest_float(f"u{aid}", 0.0, 1.0) for aid in LP_CANDIDATES}
        if sum(raw.values()) == 0.0:
            return 0.0
        signal = AlphaBlendSignal(raw)
        run_name = f"trial_{trial.number}"
        metrics = _run_lp(
            signal,
            IS_TRAIN_START, IS_TRAIN_END,
            db_path, scratch / run_name,
            run_name=run_name,
        )
        return _sharpe(metrics)
    return objective


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    paths    = load_pathes()
    db_path  = paths["ROOT"] / "simon_test" / "datapool.db"
    outputs  = (
        paths["ROOT"]
        / "backtests" / "signal_optimization" / "01 blend" / "long power" / "outputs"
    )
    scratch  = outputs / "_trials"
    outputs.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)

    # ── Bayesian optimisation ────────────────────────────────────────────────
    print(f"Running {N_TRIALS} Bayesian trials on IS-train "
          f"({IS_TRAIN_START} → {IS_TRAIN_END}) …")

    sampler = TPESampler(seed=42)
    pruner  = MedianPruner(n_startup_trials=20, n_warmup_steps=0)
    study   = optuna.create_study(
        direction="maximize",
        sampler=sampler,
        pruner=pruner,
    )
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    with tqdm(total=N_TRIALS, desc="Bayes opt", unit="trial") as pbar:
        def _cb(study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
            pbar.set_postfix(best=f"{study.best_value:.3f}", last=f"{trial.value:.3f}")
            pbar.update(1)
        study.optimize(_make_objective(db_path, scratch), n_trials=N_TRIALS, callbacks=[_cb])

    with open(outputs / "study.pkl", "wb") as f:
        pickle.dump(study, f)

    best_trial = study.best_trial
    raw_best   = {aid: best_trial.params[f"u{aid}"] for aid in LP_CANDIDATES}
    best_signal = AlphaBlendSignal(raw_best)
    best_weights = best_signal.weights   # normalised

    print(f"\nBest trial #{best_trial.number}  IS-train Sharpe = {best_trial.value:.3f}")
    print("Normalised weights:")
    for aid, w in sorted(best_weights.items(), key=lambda x: -x[1]):
        print(f"  alpha_{aid}: {w:.4f}")

    with open(outputs / "best_weights.json", "w") as f:
        json.dump({str(k): v for k, v in best_weights.items()}, f, indent=2)

    # ── evaluate key configurations on all three windows ────────────────────
    configs = {
        "best_blend":         AlphaBlendSignal(raw_best),
        "equal_weight_blend": AlphaBlendSignal({aid: 1.0 for aid in LP_CANDIDATES}),
        "single_alpha_57":    AlphaBacktestSignal(57),
    }

    # IS-train Sharpe for best_blend comes directly from the study — no re-run needed.
    # Baselines only need IS-val (overfitting reference) and OOS (final comparison).
    eval_runs = [
        (label, signal, window, start, end, window == "oos")
        for label, signal in configs.items()
        for window, start, end in [
            ("is_val", IS_VAL_START, IS_VAL_END),
            ("oos",    OOS_START,    OOS_END),
        ]
    ]

    summary: dict[str, dict] = {
        "best_blend": {"is_train_sharpe": study.best_value},
        "equal_weight_blend": {},
        "single_alpha_57": {},
    }
    with tqdm(total=len(eval_runs), desc="Evaluating", unit="run") as pbar:
        for label, signal, window, start, end, save_arts in eval_runs:
            pbar.set_postfix(config=label, window=window)
            save_dir = outputs / label
            save_dir.mkdir(parents=True, exist_ok=True)
            m = _run_lp(signal, start, end, db_path, save_dir,
                        run_name=f"{label}_{window}", save_artifacts=save_arts)
            summary[label][f"{window}_sharpe"] = _sharpe(m)
            if window == "oos":
                summary[label]["oos_annual_return"]     = m.get("annual_return")
                summary[label]["oos_annual_volatility"] = m.get("annual_volatility")
                summary[label]["oos_max_drawdown"]      = m.get("max_drawdown")
            pbar.update(1)

    for label in configs:
        s = summary[label]
        print(f"\n[{label}]")
        if "is_train_sharpe" in s:
            print(f"  IS-train Sharpe : {s['is_train_sharpe']:.3f}  (from study)")
        print(f"  IS-val   Sharpe : {s.get('is_val_sharpe', 0):.3f}")
        print(f"  OOS      Sharpe : {s.get('oos_sharpe', 0):.3f}")

    summary["best_weights"] = {str(k): v for k, v in best_weights.items()}
    with open(outputs / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nDone. Outputs → {outputs}")


if __name__ == "__main__":
    main()

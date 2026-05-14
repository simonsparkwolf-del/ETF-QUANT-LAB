"""
Step 3 — Joint L/S Blend: Bayesian optimisation on the full L/S objective.

Searches for optimal LP and SP blend weights jointly so that the combined
LongShortBlendSignal maximises the full L/S Sharpe on the IS-train window.

Unlike Step 2 (which optimised LP and SP independently on single-side
objectives), this study uses the complete DualSignalStrategy L/S backtest
as the objective — no gradient required; TPE is a black-box sampler.

Candidate pools (unchanged from Step 2)
-----------------------------------------
  LP: #57, #24, #19, #31, #23
  SP: #23, #53, #31, #19, #57

Search space: 10 parameters
  u_lp_k ~ Uniform[0, 1]  for each k in LP_CANDIDATES  → normalised to LP simplex
  u_sp_k ~ Uniform[0, 1]  for each k in SP_CANDIDATES  → normalised to SP simplex

Windows
-------
  IS-train  2021-03-03 → 2023-12-31  (~150 bars)  optimisation target
  IS-val    2024-01-01 → 2024-12-31  (~52  bars)  overfitting check
  OOS       2025-01-01 → 2026-03-01  (61   bars)  final result

Outputs: backtests/signal_optimization/02 ls_blend/outputs/
  study.pkl
  best_weights.json         {lp: {...}, sp: {...}}
  summary.json
  best_ls_blend/            full artifacts (OOS window)
  equal_weight_blend/       full artifacts (OOS window)
  l57_s23/                  full artifacts (OOS window)  — Design 01/02 baseline
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
from QuantLab.backtest.signal.dual_blend_signal import LongShortBlendSignal
from QuantLab.backtest.strategy.asymmetric_ls import DualSignalStrategy
from QuantLab.utils.config import load_pathes

# ── windows ────────────────────────────────────────────────────────────────────
IS_TRAIN_START = date(2021,  3,  3)
IS_TRAIN_END   = date(2023, 12, 31)
IS_VAL_START   = date(2024,  1,  1)
IS_VAL_END     = date(2024, 12, 31)
OOS_START      = date(2025,  1,  1)
OOS_END        = date(2026,  3,  1)

INITIAL_NAV = 10_000.0

# ── candidate pools ────────────────────────────────────────────────────────────
LP_CANDIDATES: tuple[int, ...] = (57, 24, 19, 31, 23)
SP_CANDIDATES: tuple[int, ...] = (23, 53, 31, 19, 57)

N_TRIALS = 300


# ── backtest helper ────────────────────────────────────────────────────────────

def _run_ls(
    signal,
    start: date,
    end: date,
    db_path: Path,
    save_path: Path,
    *,
    save_artifacts: bool = False,
    run_name: str = "ls_run",
) -> dict:
    strategy = DualSignalStrategy(run_name)
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
        short_enabled=True,
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
        lp_raw = {aid: trial.suggest_float(f"lp_{aid}", 0.0, 1.0) for aid in LP_CANDIDATES}
        sp_raw = {aid: trial.suggest_float(f"sp_{aid}", 0.0, 1.0) for aid in SP_CANDIDATES}
        if sum(lp_raw.values()) == 0.0 or sum(sp_raw.values()) == 0.0:
            return 0.0
        signal   = LongShortBlendSignal(lp_weights=lp_raw, sp_weights=sp_raw)
        run_name = f"trial_{trial.number}"
        metrics  = _run_ls(
            signal,
            IS_TRAIN_START, IS_TRAIN_END,
            db_path, scratch / run_name,
            run_name=run_name,
        )
        return _sharpe(metrics)
    return objective


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    paths   = load_pathes()
    db_path = paths["ROOT"] / "simon_test" / "datapool.db"
    outputs = (
        paths["ROOT"]
        / "backtests" / "signal_optimization" / "02 ls_blend" / "outputs"
    )
    scratch = outputs / "_trials"
    outputs.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)

    # ── Bayesian optimisation ────────────────────────────────────────────────
    print(f"Running {N_TRIALS} Bayesian trials on IS-train "
          f"({IS_TRAIN_START} → {IS_TRAIN_END}) …")

    sampler = TPESampler(seed=42)
    pruner  = MedianPruner(n_startup_trials=30, n_warmup_steps=0)
    study   = optuna.create_study(
        direction="maximize",
        sampler=sampler,
        pruner=pruner,
    )
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    with tqdm(total=N_TRIALS, desc="Bayes opt (L/S)", unit="trial") as pbar:
        def _cb(study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
            pbar.set_postfix(best=f"{study.best_value:.3f}", last=f"{trial.value:.3f}")
            pbar.update(1)
        study.optimize(_make_objective(db_path, scratch), n_trials=N_TRIALS, callbacks=[_cb])

    with open(outputs / "study.pkl", "wb") as f:
        pickle.dump(study, f)

    best_trial = study.best_trial
    lp_raw_best = {aid: best_trial.params[f"lp_{aid}"] for aid in LP_CANDIDATES}
    sp_raw_best = {aid: best_trial.params[f"sp_{aid}"] for aid in SP_CANDIDATES}
    best_signal  = LongShortBlendSignal(lp_weights=lp_raw_best, sp_weights=sp_raw_best)
    best_lp_w    = best_signal.lp_weights
    best_sp_w    = best_signal.sp_weights

    print(f"\nBest trial #{best_trial.number}  IS-train L/S Sharpe = {best_trial.value:.3f}")
    print("LP weights:")
    for aid, w in sorted(best_lp_w.items(), key=lambda x: -x[1]):
        print(f"  alpha_{aid}: {w:.4f}")
    print("SP weights:")
    for aid, w in sorted(best_sp_w.items(), key=lambda x: -x[1]):
        print(f"  alpha_{aid}: {w:.4f}")

    with open(outputs / "best_weights.json", "w") as f:
        json.dump(
            {"lp": {str(k): v for k, v in best_lp_w.items()},
             "sp": {str(k): v for k, v in best_sp_w.items()}},
            f, indent=2,
        )

    # ── evaluate key configurations ──────────────────────────────────────────
    configs = {
        "best_ls_blend":      LongShortBlendSignal(lp_raw_best, sp_raw_best),
        "equal_weight_blend": LongShortBlendSignal(
            {aid: 1.0 for aid in LP_CANDIDATES},
            {aid: 1.0 for aid in SP_CANDIDATES},
        ),
        "l57_s23":            LongShortBlendSignal({57: 1.0}, {23: 1.0}),
    }

    eval_runs = [
        (label, signal, window, start, end, window == "oos")
        for label, signal in configs.items()
        for window, start, end in [
            ("is_val", IS_VAL_START, IS_VAL_END),
            ("oos",    OOS_START,    OOS_END),
        ]
    ]

    summary: dict[str, dict] = {
        "best_ls_blend": {"is_train_sharpe": study.best_value},
        "equal_weight_blend": {},
        "l57_s23": {},
    }
    with tqdm(total=len(eval_runs), desc="Evaluating", unit="run") as pbar:
        for label, signal, window, start, end, save_arts in eval_runs:
            pbar.set_postfix(config=label, window=window)
            save_dir = outputs / label
            save_dir.mkdir(parents=True, exist_ok=True)
            m = _run_ls(signal, start, end, db_path, save_dir,
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

    summary["best_weights"] = {
        "lp": {str(k): v for k, v in best_lp_w.items()},
        "sp": {str(k): v for k, v in best_sp_w.items()},
    }
    with open(outputs / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nDone. Outputs → {outputs}")


if __name__ == "__main__":
    main()

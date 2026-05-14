## Overview

This backtest engine consists of 4 core modules:

- `**BacktestEngine**`: Advances the simulation clock, calls Signal/Strategy/Risk, applies fills to the account, then runs evaluation and writes artifacts.
- `**QuoteTerminal` (market data terminal)**: The single source of truth for **time + data**. The engine only does `terminal.at(today)` each period; all modules query data via `terminal`.
- `**Signal / Strategy / Risk`**: Aligned via `bind(terminal)`. They no longer depend on the engine broadcasting `bar` / `date`.
- `**BacktestAnalyzer**`: Produces metrics and the large dashboard image (with **NAV vs SPY** as panel #1).

> Key contract: **all “history” queries default to “from the beginning up to now (inclusive of today)”**, enforced by `QuoteTerminal` (e.g. `benchmarks()` / `signals()` / `etfs()` are cut off at `date <= terminal.day`).

---

## Architecture (data/control flow)

```mermaid
flowchart TB
    eng[BacktestEngine] -->|terminal.at(today)| term[QuoteTerminal]
    eng --> sgl[Signal.analyze()]
    eng --> stg[Strategy.on_ranking / on_holding]
    eng --> rsk[Risk.on_action]
    stg --> act[Action list]
    rsk --> act2[Filtered actions]
    eng --> trd[Trader.on_action -> Trade]
    trd --> acc[Account.on_trades + snapshot]
    eng --> eval[BacktestAnalyzer.evaluate]
    eval --> fig[all_in_one_panel.png (Panel #1: NAV vs SPY)]
```



### Separation of responsibilities (Signal / Strategy / Risk)

This engine deliberately splits “what to trade”, “how to trade”, and “whether we are allowed to trade”
into three modules. The boundaries are:

- **Signal (`Signal`) — *What to trade***  
Produces a **`Scores` dict** for the universe at `terminal.day`. It should be a pure data+math
component: it reads from `QuoteTerminal`, and outputs `{“long”: OrderedDict[ticker, score], “short”: OrderedDict[ticker, score]}`. It should not place orders, mutate the account, or enforce risk constraints. Single-head signals wrap their scores with `symmetric()`; dual-head signals (`LongShortAlphaSignal`) return independent dicts per side.
- **Strategy (`Strategy`) — *How to trade***  
Converts scores into **intent**: a list of `Action`s (and optionally additional holding
adjustments via `on_holding`). Strategy owns position sizing and rebalancing logic, and may read
the account state. It picks which score key(s) to consume — `scores[“long”]`, `scores[“short”]`, or both. It should not directly “block” trades for risk reasons; it proposes actions.
- **Risk (`Risk`) — *Whether we are allowed to trade***  
Acts as the final gatekeeper. It receives proposed actions and can **filter, clamp, or transform**
them (e.g. max position, max turnover, leverage limits, no-trade lists). Risk should be the only
place that enforces portfolio constraints, so constraints stay consistent across strategies.

### Why this design is necessary

- **Single source of truth for time & data**: all three modules share the same `QuoteTerminal` via
`bind(terminal)`, which prevents subtle date drift and inconsistent data loading.
- **Composability**: you can swap signals/strategies/risks independently (e.g. many-signal × many-strategy grids)
without rewriting the engine loop.
- **Testability**: each module can be unit-tested with a fake `QuoteTerminal` and a fixed `terminal.day`.
Bugs become localized: “signal math”, “strategy sizing”, or “risk constraints”.
- **No accidental look-ahead**: keeping “history queries” inside the terminal and separating signal/strategy/risk
makes it easier to enforce a consistent data cut-off policy (history up to `terminal.day`, inclusive).

---

## Developer Guide

### 1) Minimal runnable backtest (code template)

This example shows how to assemble a `BacktestConfig` and run a backtest (see also `simon_test/backtest/debug.py`).

```python
from datetime import date
from pathlib import Path

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig

from QuantLab.backtest.signal.debug import DebugSignal
from QuantLab.backtest.strategy.debug import DebugStrategy
from QuantLab.backtest.risk.debug import DebugRisk


config = BacktestConfig(
    name="demo_run",
    start_date=date(2025, 1, 1),
    end_date=date(2026, 1, 31),
    db_path=Path(r"E:\path\to\datapool.db"),
    save_path=Path(r"E:\path\to\outputs"),
    signal=DebugSignal("demo"),
    strategy=DebugStrategy("demo"),
    risk=DebugRisk("demo"),
    account=Account(10000),
    long_cost=0.00001,
    short_cost_per_day=0.00001,
    base_slippage=0.0001,
    short_enabled=False,
)

engine = BacktestEngine(config)
engine.run()
metrics = engine.evaluate()
print(metrics)
```

### 2) Alignment rule: always use `bind(terminal)`

All modules (Signal/Strategy/Risk) must obtain the same terminal instance via `bind(terminal)`:

```python
class MySignal(Signal):
    def analyze(self):
        assert self.terminal is not None
        today = self.terminal.day
        # Example: ETF cross-section on day + signal history
        today_xs = self.terminal.today_etfs()
        sig_hist_wide = self.terminal.signals()
        ...
```

```python
class MyStrategy(Strategy):
    def on_ranking(self, ranking):
        assert self.terminal is not None and self.account is not None
        q = self.terminal.quote("SPY")
        price = float(q.loc["close"]) if not q.empty else 0.0
        ...
```

> Do not implement `on_bar(bar)` or cache `self.bar/self.date` inside modules. Always use `terminal.day` and `terminal.*()` queries.

### 3) `QuoteTerminal` API contract

Common methods:

- **Time**
  - `terminal.at(day)`: set the current simulation date
  - `terminal.day`: get the current simulation date
- **Engine panel**
  - `terminal.bars(start, end)`: ETF `weekly_bar` + applicable alpha (wide), used by the engine loop
- **Queries**
  - `terminal.quote(ticker)`: one `weekly_bar` row for the given ticker on the current day
  - `terminal.today_etfs()`: ETF cross-section on the current day
  - `terminal.etfs()` / `terminal.indices()` / `terminal.benchmarks()`: history up to today (inclusive)
  - `terminal.signals()`: `weekly_signal` wide history up to today (inclusive)

### 4) Evaluation metrics & artifacts (incl. SPY)

`engine.evaluate()` writes the following under `save_path`:

- `*_metrics.json` / `*_metrics.md`
- `*_value_history.csv` / `*_holding_history.csv`
- `*_all_in_one_panel.png`

In the large dashboard `all_in_one_panel.png`, **panel #1 is always `NAV vs SPY`** (SPY data is loaded via `QuoteTerminal.benchmarks()`).

Added benchmark fields (persisted to metrics):

- `excess_return_annual_vs_spy`: annualized excess return vs SPY (annualized mean of r_p - r_{spy})
- `capm_alpha_annual_vs_spy`: CAPM regression intercept alpha, annualized (regress r_p = a + b r_{spy}, report a times periods_per_year)
- `capm_beta_vs_spy`: CAPM beta vs SPY

Win rate (`win_rate`) definition:

- **Win Rate = profitable trade weeks / total trade weeks**
- Trade week is defined as weeks where holdings market value changes vs previous week (|Delta signed_MV|>0)

---

### 5) Blueprint: grid-run across multiple Signals × Strategies (metrics JSON)

This pattern is useful for quick “many configs” runs (e.g. smoke experiments). It traverses
multiple signal objects and strategy objects, runs the engine, and aggregates `engine.evaluate()`
metrics into a single JSON file.

```python
import json
from copy import deepcopy
from datetime import date
from pathlib import Path

from QuantLab.backtest.engine import BacktestEngine
from QuantLab.backtest.schema.backtest import Account
from QuantLab.backtest.schema.backtest_config import BacktestConfig

# Replace these with your own implementations.
from QuantLab.backtest.signal.debug import DebugSignal
from QuantLab.backtest.strategy.debug import DebugStrategy
from QuantLab.backtest.risk.debug import DebugRisk


def run_grid(
    *,
    db_path: Path,
    save_root: Path,
    start_date: date,
    end_date: date,
    signals: list,
    strategies: list,
):
    results = []

    for sig in signals:
        for stg in strategies:
            run_name = f"{sig.__class__.__name__}__{stg.__class__.__name__}"
            out_dir = save_root / run_name

            # Important: create a fresh account per run.
            account = Account(10000)

            config = BacktestConfig(
                name=run_name,
                start_date=start_date,
                end_date=end_date,
                db_path=db_path,
                save_path=out_dir,
                signal=sig,
                strategy=stg,
                risk=DebugRisk("grid"),
                account=account,
                long_cost=0.00001,
                short_cost_per_day=0.00001,
                base_slippage=0.0001,
                short_enabled=False,
                save_eval_artifacts=True,
            )

            engine = BacktestEngine(config)
            engine.run()
            metrics = engine.evaluate()  # writes per-run artifacts + returns a dict

            results.append(
                {
                    "name": run_name,
                    "signal": sig.__class__.__name__,
                    "strategy": stg.__class__.__name__,
                    "metrics": metrics,
                }
            )

    save_root.mkdir(parents=True, exist_ok=True)
    (save_root / "grid_metrics.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    run_grid(
        db_path=Path(r"E:\path\to\datapool.db"),
        save_root=Path(r"E:\path\to\grid_outputs"),
        start_date=date(2025, 1, 1),
        end_date=date(2026, 1, 31),
        signals=[
            DebugSignal("sigA"),
            DebugSignal("sigB"),
        ],
        strategies=[
            DebugStrategy("stgA"),
            DebugStrategy("stgB"),
        ],
    )
```

Notes:

- For “real” grids, you’ll usually want per-run seeds and to pass parameters into constructors.
- If a strategy keeps internal state, create a new instance per run (same for signals).

---

### 6) How to implement the 3 required base classes (Signal / Strategy / Risk)

To plug into `BacktestEngine`, you typically implement these three abstractions:

- `**Signal**`: produces a ranking (or scores) each period.
- `**Strategy**`: turns ranking into `Action`s and manages existing positions.
- `**Risk**`: filters or edits actions before execution.

All three must follow the same alignment rule:

- The engine will call `**bind(terminal)**` once at initialization.
- Inside your methods, use `**self.terminal.day**` and `self.terminal.*()` to fetch data.
- Do not depend on engine-broadcast `bar` or cached `self.bar/self.date`.

#### Signal: minimal template

```python
from collections import OrderedDict

from QuantLab.backtest.schema.signal import Scores, symmetric
from QuantLab.backtest.signal.basic import Signal


class MySignal(Signal):
    def analyze(self) -> Scores:
        assert self.terminal is not None

        tickers = self.terminal.etfs()["ticker"].unique().tolist()

        # Example: equal scores (replace with your own logic)
        scores: OrderedDict[str, float] = OrderedDict((t, 0.0) for t in tickers)
        # symmetric() publishes the same dict under both "long" and "short" keys.
        return symmetric(scores)
```

For a dual-head signal that uses different scores per side:

```python
class MyDualSignal(Signal):
    def analyze(self) -> Scores:
        assert self.terminal is not None
        long_scores  = OrderedDict(...)   # higher = better long candidate
        short_scores = OrderedDict(...)   # lower  = better short candidate
        return {"long": long_scores, "short": short_scores}
```

#### Strategy: minimal template

```python
from QuantLab.backtest.schema.backtest import Action
from QuantLab.backtest.schema.signal import Scores
from QuantLab.backtest.strategy.basic import Strategy


class MyStrategy(Strategy):
    def on_ranking(self, scores: Scores) -> list[Action]:
        assert self.terminal is not None and self.account is not None

        # Consume the long-side scores (use scores["short"] for short ranking).
        ranking = scores["long"]
        tickers = list(ranking.keys())
        if not tickers:
            return []

        top = tickers[0]
        q = self.terminal.quote(top)
        if q.empty:
            return []

        px = float(q.loc["close"])
        vol = 0.01 * float(self.account.cash) / px if px > 0 else 0.0
        return [
            Action(
                direction="long",
                side="buy",
                ticker=top,
                price=px,
                volume=vol,
                date=self.terminal.day,
            )
        ]

    def on_holding(self) -> list[Action]:
        return []
```

#### Risk: minimal template

```python
from QuantLab.backtest.schema.backtest import Action
from QuantLab.backtest.risk.basic import Risk


class MyRisk(Risk):
    def on_action(self, actions: list[Action]) -> list[Action]:
        assert self.terminal is not None

        # Example: drop zero/negative volume orders
        out = [a for a in actions if a.volume > 0]
        return out
```

#### Common pitfalls

- **Stateful instances in grids**: if a class stores internal state, instantiate a new object per run.
- **Date alignment**: always use `self.terminal.day` rather than `datetime.now()` or manually tracked dates.
- **Missing quotes**: guard on `terminal.quote(ticker).empty` to avoid indexing errors.


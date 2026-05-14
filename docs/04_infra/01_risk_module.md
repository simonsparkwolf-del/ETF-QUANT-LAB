# Risk Module

Base class interface for risk management in the backtest engine.

**Current implementation:** `BaselineRisk` — see `trading_opt/01_warmup_test.md` for full design and parameters.

---

## Interface

```python
class Risk:
    def bind(self, terminal: QuoteTerminal) -> None: ...
    def on_action(self, actions: list[Action], account: Account) -> list[Action]: ...
```

`on_action()` receives the full proposed action list from the strategy and returns a (possibly modified) list. It may:
- Reduce position size (`PositionChange`)
- Block all new trades (`NoTrade`)
- Force-close all positions (`EndTrade`)
- Pass actions through unchanged

All market data queries must go through `terminal` (never direct DB access).

---

## State Machine Convention

Risk modules typically implement a state machine with explicit transitions. States are persisted across weekly calls via instance variables. Recovery conditions must be checked against `terminal.day` to avoid look-ahead.

```
NORMAL ──[trigger]──► REDUCED ──[trigger]──► OFF
  ▲                       ▲
  └──[recovery]───────────┘
```

---

## Key Constraints

- `terminal.alphas()` results are cached per `terminal.day` — safe to call multiple times within `on_action()`.
- `account.value_history` contains snapshots up to (but not including) the current period.
- `peak_nav` must use `max(value_history, current_total_value)` to include today's MTM.

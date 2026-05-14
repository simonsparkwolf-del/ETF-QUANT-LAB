# Strategy Module

Base class interface for portfolio construction in the backtest engine.

---

## Interface

```python
from QuantLab.backtest.schema.signal import Scores

class Strategy:
    def bind(self, terminal: QuoteTerminal) -> None: ...
    def on_ranking(self, scores: Scores) -> list[Action]: ...
    def on_holding(self) -> list[Action]: ...
```

- `on_ranking(scores)` — called once per rebalance period; receives the signal's `Scores` dict (keys `"long"` and `"short"`); returns a list of `Action` objects. The strategy picks which key(s) to consume.
- `on_holding()` — called after `on_ranking()` for any intra-period position adjustments. Return `[]` if all management is consolidated in `on_ranking()`.

---

## Signal Key Consumption Convention

| Strategy | Consumes | Notes |
|----------|----------|-------|
| `BaselineStrategy` | `scores["long"]` for both sides | Single unified ranking; symmetric behaviour |
| `SiganlOptimizationStrategy(mode="long")` | `scores["long"]` | LP softmax allocator |
| `SiganlOptimizationStrategy(mode="short")` | `scores["short"]` | SP softmax on negated scores |
| `DualSignalStrategy` | `scores["long"]` for longs, `scores["short"]` for shorts | Independent ranking per side |

---

## Concrete Implementations

| Class | File | Design |
|-------|------|--------|
| `BaselineStrategy` | `strategy/baseline.py` | Market-neutral L/S, rank stickiness, alpha_110 short filter, 3-state risk machine |
| `SiganlOptimizationStrategy` | `strategy/signal_optimization.py` | Long-only or short-only softmax allocator (Step 0/1 signal optimization) |
| `DualSignalStrategy` | `strategy/asymmetric_ls.py` | L/S with independent signals per side; long takes priority on conflict |

---

## Action Types

| `direction` / `side` | Effect |
|----------------------|--------|
| `long` / `buy` | Open / increase long position |
| `long` / `sell` | Close / reduce long position |
| `short` / `sell` | Open / increase short position |
| `short` / `buy` | Cover / reduce short position |

Risk layer can additionally emit `EndTrade`, `NoTrade`, `PositionChange`.

---

## Conventions

- Position sizing uses `account.total_value` (NAV after MTM) at the time of the call.
- Strategies always generate a **full** proposal regardless of current risk state; `Risk.act()` filters the list downstream.
- Rank stickiness (retaining positions near the boundary) is handled inside `on_ranking()` before emitting actions.
- `on_holding()` returns `[]` in most strategies; override only for intra-period forced exits (e.g. momentum flip).

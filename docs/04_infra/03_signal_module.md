# Signal Module

Base class interface for signal generation in the backtest engine.

Signal classes translate raw data (alpha factors, ML predictions, or any computed metric) into a per-ETF score map consumed by the strategy.

---

## Interface

```python
from QuantLab.backtest.schema.signal import Scores

class Signal:
    def bind(self, terminal: QuoteTerminal) -> None: ...
    def analyze(self) -> Scores: ...
```

`analyze()` is called once per rebalance period (after `terminal.day` is advanced) and returns a `Scores` dict:

```python
Scores = dict[str, OrderedDict[str, float]]
# always contains at minimum:
#   scores["long"]  — ticker → score for the long book (higher = better long)
#   scores["short"] — ticker → score for the short book (lower = better short)
```

The strategy decides which key(s) to consume. A signal that is indifferent to side publishes the same `OrderedDict` under both keys using the `symmetric()` helper.

---

## Score Type Helpers (`schema/signal.py`)

| Symbol | Type | Purpose |
|--------|------|---------|
| `Scores` | `dict[str, OrderedDict[str, float]]` | Return type of `analyze()` |
| `LONG_KEY` | `"long"` | Canonical key for long-book scores |
| `SHORT_KEY` | `"short"` | Canonical key for short-book scores |
| `symmetric(od)` | `Scores` | Wrap a single `OrderedDict` under both keys |

---

## Concrete Implementations

| Class | File | `"long"` / `"short"` scores | Note |
|-------|------|-----------------------------|------|
| `AlphaBacktestSignal(alpha_id)` | `signal/alpha_test.py` | Same alpha, both keys | Single-head via `symmetric()` |
| `MLBacktestSignal(signal_id)` | `signal/ml_backtest_signal.py` | Same ML prediction, both keys | Single-head via `symmetric()` |
| `OptimizationTestSignal` | `signal/optimization_test.py` | Constant 1.0, both keys | Equal-weight Step 0 baseline |
| `LongShortAlphaSignal(long_alpha_id, short_alpha_id)` | `signal/dual_head_alpha_signal.py` | Independent alphas per key | Dual-head; `"long"` ≠ `"short"` |

---

## Constraints

- All data access must go through `terminal` — never query `datapool.db` directly inside `analyze()`.
- `terminal.at(day)` is already set before `analyze()` is called; no manual date management needed.
- Results must cover **all tradable ETFs** at the current date; missing tickers are dropped by the strategy.
- Both `"long"` and `"short"` keys must always be present in the returned `Scores`.

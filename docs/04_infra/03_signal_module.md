# Signal Module

Base class interface for signal generation in the backtest engine.

Signal classes translate raw data (alpha factors, ML predictions, or any computed metric) into a per-ETF score vector consumed by the strategy.

---

## Interface

```python
class Signal:
    def bind(self, terminal: QuoteTerminal) -> None: ...
    def analyze(self) -> OrderedDict[str, float]: ...
```

`analyze()` is called once per rebalance period (after `terminal.day` is advanced) and returns an `OrderedDict[ticker, score]` sorted by score descending. Higher score = stronger long candidate; lower score = stronger short candidate.

---

## Concrete Implementations

| Class | Source | Score |
|-------|--------|-------|
| `AlphaBacktestSignal(alpha_id)` | `weekly_alpha` via `terminal.alphas()` | Raw alpha factor value |
| `MLBacktestSignal(signal_id)` | `weekly_signal` via `terminal.signals()` | ML model prediction |
| `OptimizationTestSignal` | Constant = 1.0 | Equal-weight baseline (Step 0) |

---

## Constraints

- All data access must go through `terminal` — never query `datapool.db` directly inside `analyze()`.
- `terminal.at(day)` is already set before `analyze()` is called; no manual date management needed.
- Results must cover **all tradable ETFs** at the current date; missing tickers are dropped by the strategy.

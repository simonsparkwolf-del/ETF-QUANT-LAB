# Strategy Module

Base class interface for portfolio construction in the backtest engine.

**Current implementation:** `BaselineStrategy` — see `trading_opt/01_warmup_test.md` for full design and parameters.

---

## Interface

```python
class Strategy:
    def bind(self, terminal: QuoteTerminal) -> None: ...
    def on_ranking(self, ranking: OrderedDict[str, float], account: Account) -> list[Action]: ...
    def on_holding(self, account: Account) -> list[Action]: ...
```

- `on_ranking()` — called once per rebalance period; receives the signal's ranked ETF scores; returns a list of buy/sell `Action` objects.
- `on_holding()` — called between rebalances for intra-period position management. Return `[]` if all management is consolidated in `on_ranking()`.

---

## Action Types

| Action | Effect |
|--------|--------|
| `Buy(ticker, quantity)` | Open / increase long position |
| `Sell(ticker, quantity)` | Close / reduce long position |
| `Short(ticker, quantity)` | Open / increase short position |
| `Cover(ticker, quantity)` | Close / reduce short position |
| `EndTrade` | Force-close all current positions |
| `NoTrade` | Block any new position opens this period |
| `PositionChange(ratio)` | Scale all current positions by `ratio` |

---

## Conventions

- Position sizing uses `account.nav` (net asset value after MTM) at the time of the call.
- Strategies always generate a **full** proposal regardless of current risk state; `Risk.on_action()` filters the list downstream.
- Rank stickiness (retaining positions near the boundary) is handled inside `on_ranking()` before emitting actions.

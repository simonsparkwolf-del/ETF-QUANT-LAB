"""
signal_registry.py — decorator-based registry for signals.

Conventions
-----------
- External compute interface is ALWAYS: (p: pd.Series, *, ticker: str, **kwargs) -> pd.Series
  This matches FRS-style indicators (Series → Series).

- Non-ML indicators are written directly as Series → Series.

- ML indicators are authored as:
    panel_fn(big: pd.DataFrame, **kwargs) -> pd.DataFrame
  returning a long DataFrame with columns: ticker, date, pred
  The strong decorator wraps it into the standard Series → Series interface,
  extracting by ticker/date via pandas.

- Each indicator must declare `required`:
    required = {"bars": [...], "alpha": [...]}
  used to build the ML/feature big table from weekly_bar + weekly_alpha.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


@dataclass(frozen=True)
class SignalMeta:
    signal_id: int
    note: str
    category: str  # ML | alpha | composite
    required: dict[str, Any]
    fn: Callable[..., pd.Series]  # standardized interface
    panel_fn: Optional[Callable[..., pd.DataFrame]] = None  # only for ML


SIGNAL_REGISTRY: dict[int, SignalMeta] = {}


def register_signal(
    signal_id: int,
    note: str,
    category: str,
    required: dict[str, Any],
    *,
    panel_fn: Callable[..., pd.DataFrame] | None = None,
):
    """Register a standardized signal function into SIGNAL_REGISTRY."""

    def decorator(fn: Callable[..., pd.Series]) -> Callable[..., pd.Series]:
        SIGNAL_REGISTRY[signal_id] = SignalMeta(
            signal_id=signal_id,
            note=note,
            category=category,
            required=required,
            fn=fn,
            panel_fn=panel_fn,
        )
        return fn

    return decorator


def series_signal(
    *,
    signal_id: int,
    note: str,
    category: str,
    required: dict[str, Any],
):
    """
    Strong decorator that supports TWO authoring styles.

    Style A (non-ML): decorate a Series → Series function:
        @series_signal(...)
        def my_sig(p: pd.Series, **kwargs) -> pd.Series: ...

    Style B (ML): decorate a panel function returning (ticker,date,pred):
        @series_signal(...)
        def my_model(big: pd.DataFrame, **kwargs) -> pd.DataFrame: ...

    How style is detected:
      - If the decorated function's first parameter annotation is pd.DataFrame,
        it is treated as panel_fn (ML).
      - Otherwise treated as Series → Series (non-ML).
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., pd.Series]:
        # Resolve first-param annotation, handling PEP-563 string annotations
        # (from __future__ import annotations turns all hints into strings).
        first_anno = None
        try:
            import inspect
            import typing

            sig = inspect.signature(fn)
            params = list(sig.parameters.values())
            if params:
                raw = params[0].annotation
                if isinstance(raw, str):
                    resolved = typing.get_type_hints(fn)
                    first_anno = resolved.get(params[0].name, raw)
                else:
                    first_anno = raw
        except Exception:
            pass

        if first_anno is pd.DataFrame:
            panel_fn: Callable[..., pd.DataFrame] = fn  # type: ignore[assignment]

            def wrapped(
                p: pd.Series,
                *,
                ticker: str,
                _panel_df: pd.DataFrame | None = None,
                **kwargs: Any,
            ) -> pd.Series:
                if _panel_df is None:
                    raise RuntimeError(
                        f"signal_id={signal_id}: ML path requires _panel_df injected by compute layer"
                    )
                need = {"ticker", "date", "pred"}
                if not need.issubset(_panel_df.columns):
                    raise ValueError(
                        f"signal_id={signal_id}: _panel_df must include columns {sorted(need)}; "
                        f"got {list(_panel_df.columns)}"
                    )

                sub = _panel_df.loc[_panel_df["ticker"] == ticker, ["date", "pred"]]
                if sub.empty:
                    return pd.Series(index=p.index, dtype=float)

                # Ensure date is datetime index for alignment
                s = (
                    sub.drop_duplicates(subset=["date"])
                    .set_index("date")["pred"]
                    .sort_index()
                )
                if not isinstance(s.index, pd.DatetimeIndex):
                    s.index = pd.to_datetime(s.index)
                return s.reindex(p.index)

            wrapped._required = required  # type: ignore[attr-defined]
            wrapped._panel_fn = panel_fn  # type: ignore[attr-defined]

            return register_signal(
                signal_id, note, category, required, panel_fn=panel_fn
            )(wrapped)

        # Non-ML: Series → Series
        series_fn: Callable[..., pd.Series] = fn  # type: ignore[assignment]
        series_fn._required = required  # type: ignore[attr-defined]
        series_fn._panel_fn = None  # type: ignore[attr-defined]
        return register_signal(signal_id, note, category, required, panel_fn=None)(series_fn)

    return decorator


def get_registry_df() -> pd.DataFrame:
    """Export registry to DataFrame for DB insertion (signal table)."""
    rows = [
        {"signal_id": m.signal_id, "note": m.note, "category": m.category}
        for m in SIGNAL_REGISTRY.values()
    ]
    return pd.DataFrame(rows).sort_values("signal_id").reset_index(drop=True)


"""
frs_registry.py — decorator-based registry for FRS metrics.

To add a new FRS metric:
    1. Write a function  frs_N(p: pd.Series, **kwargs) -> pd.Series
    2. Decorate it with  @register_frs("FRSN", description="...", required_cols=["tri"])
    3. Re-run the notebook cell — it will be picked up automatically.
"""

import pandas as pd

FRS_REGISTRY: dict[str, dict] = {}


def register_frs(name: str, description: str = "", required_cols: list | None = None):
    """Decorator that registers an FRS metric function into FRS_REGISTRY."""
    def decorator(fn):
        FRS_REGISTRY[name] = {
            "fn": fn,
            "description": description,
            "required_cols": required_cols or ["tri"],
        }
        return fn
    return decorator


def get_mapping_df() -> pd.DataFrame:
    """Export the registry as a DataFrame (saved to frs_mapping.csv)."""
    rows = [
        {
            "frs_id": k,
            "description": v["description"],
            "required_cols": str(v["required_cols"]),
        }
        for k, v in FRS_REGISTRY.items()
    ]
    return pd.DataFrame(rows)

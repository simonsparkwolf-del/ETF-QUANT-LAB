"""
alpha_registry.py — decorator-based registry for alpha metrics.

To add a new alpha:
    1. Write  alpha_N(panel: dict) -> pd.DataFrame  in alpha_metrics.py
    2. Decorate it with  @register_alpha(id=N, group="custom", required=[...], desc="...")
    3. Re-run the notebook cell — it will be picked up automatically.
"""

import pandas as pd

ALPHA_REGISTRY: dict[int, dict] = {}


def register_alpha(id: int, group: str, required: list, desc: str = ""):
    """Decorator that registers an alpha function into ALPHA_REGISTRY."""
    def decorator(fn):
        ALPHA_REGISTRY[id] = {
            "fn": fn,
            "group": group,
            "required": required,
            "desc": desc,
        }
        return fn
    return decorator


def get_mapping_df() -> pd.DataFrame:
    """Export the registry as a DataFrame (saved to alpha_mapping.csv)."""
    rows = [
        {
            "alpha_id": k,
            "group": v["group"],
            "required": str(v["required"]),
            "desc": v["desc"],
        }
        for k, v in ALPHA_REGISTRY.items()
    ]
    return pd.DataFrame(rows).sort_values("alpha_id").reset_index(drop=True)

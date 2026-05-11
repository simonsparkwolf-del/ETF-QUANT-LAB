# Data Instruction — Adding / Removing Metrics & Updating the Database

Developer guide: **copy-paste code templates**, lifecycle (add / remove), and how each **`save_*`** updates SQLite. Schema: `docs/01 Data Infra.md`.

---

## 1. How the database is updated (one glance)

Orchestration is normally run from `scripts/dataset_builder.ipynb` (or any script with an open `conn`).

| Step | Function | What changes in SQLite |
|------|----------|-------------------------|
| Bars | `save_panel_as_bars`, `save_non_etf_bars` | `daily_bar`, `weekly_bar` (replace-style per pipeline; see data loader) |
| Alphas | `save_alpha_results` | **`weekly_alpha`:** `DELETE` entire table, then insert from **current** `ALPHA_REGISTRY` only.<br>**`alpha`:** **append** new `alpha_id` rows only. |
| FRS | `save_frs_results` | **`weekly_frs`:** `DELETE` entire table, then insert from **current** `FRS_REGISTRY` only.<br>**`frs`:** **append** new `frs_id` rows only. |
| Signals | `save_signal_results` | **`weekly_signal`:** for each **`signal_id` still in code**, `DELETE` rows with that id, then insert. **Removed ids are not deleted** — run SQL manually.<br>**`signal`:** **append** new `signal_id` rows only. |

**Rule of thumb:** registry tables (`alpha`, `frs`, `signal`) are **insert-only** for new ids. Fact tables follow the rules above.

---

## 2. Code templates (copy-paste)

Replace `...` with your own ids, names, and logic. Imports should match your file location (relative imports below assume the standard package layout).

### 2.1 FRS template — `src/QuantLab/frs/frs_metrics.py`

`save_frs_results` maps the decorator **name** `"FRS4"` → integer **`frs_id = 4`** (digits in the string). Keep the numeric suffix consistent with what you want in the DB.

```python
import numpy as np
import pandas as pd

from .frs_registry import register_frs


@register_frs(
    "FRS4",
    description="Example: 4-week forward return (same idea as FRS1)",
    required_cols=["tri"],
)
def frs4(p: pd.Series, **kwargs) -> pd.Series:
    return (p.shift(-4) / p) - 1
```

**Update DB** (after editing code):

```python
from QuantLab.frs import save_frs_results, ETFS

save_frs_results(conn, etfs=ETFS)
```

---

### 2.2 Alpha template — `src/QuantLab/alpha/alpha_metrics.py`

Function receives **`panel`**: `dict[str, pd.DataFrame]` — each value is **wide** (index = dates, columns = tickers). Return a **wide** `DataFrame` with the **same** index/columns as the alpha universe.

Pick an integer **`id`** that is not already used in this file.

```python
import pandas as pd

from .alpha_registry import register_alpha


@register_alpha(
    id=102,
    group="custom",
    required=["close"],
    desc="Example: cross-sectional rank of close (pct, axis=1)",
)
def alpha_102(panel: dict) -> pd.DataFrame:
    c = panel["close"]
    return c.rank(axis=1, pct=True)
```

**Update DB** (needs in-memory `panel` from `load_panel`, same as notebook):

```python
from QuantLab.alpha import compute_all_alphas, save_alpha_results

results = compute_all_alphas(panel)
save_alpha_results(results, conn)
```

---

### 2.3 Signal (non-ML) template — `src/QuantLab/signal/signal_metrics.py`

- **First positional argument** at runtime is always **weekly TRI** as a `pd.Series` (date index). Name it `tri` or `p` — both work.
- Declare **`required`**: `bars` columns from `weekly_bar`, and **`alpha`** id list (pivoted to `alpha_1`, `alpha_2`, … on the big table). The compute layer passes extra series as **kwargs** (`close`, `alpha_1`, …) aligned to the TRI index.

```python
import pandas as pd

from .signal_registry import series_signal


@series_signal(
    signal_id=11,
    note="Example: blend tri momentum with alpha_1",
    category="composite",
    required={"bars": ["tri", "close"], "alpha": [1]},
)
def sig_11(
    tri: pd.Series,
    close: pd.Series | None = None,
    alpha_1: pd.Series | None = None,
    **kwargs,
) -> pd.Series:
    mom = tri.pct_change(4)
    if alpha_1 is None:
        return mom
    return mom + 0.1 * alpha_1.reindex(tri.index)
```

**Update DB:**

```python
from QuantLab.signal.compute_signal import save_signal_results
from QuantLab.frs import ETFS

save_signal_results(conn, etfs=ETFS)
```

---

### 2.4 Signal (ML) template — `src/QuantLab/signal/ml/my_model.py`

- Filename must **not** start with `_` (otherwise auto-import skips it).
- **First parameter must be annotated** `big: pd.DataFrame`.
- Return a long **`DataFrame`** with columns **`ticker`**, **`date`**, **`pred`** only.

```python
from __future__ import annotations

import pandas as pd

from ..signal_registry import series_signal


REQUIRED = {"bars": ["tri", "close"], "alpha": [1, 2]}


@series_signal(
    signal_id=9200,
    note="Example ML: cross-sectional rank of tri as pred",
    category="ML",
    required={"bars": ["tri", "close"], "alpha": [1, 2]},
)
def ml_9200(big: pd.DataFrame, **kwargs) -> pd.DataFrame:
    df = big[["date", "ticker", "tri"]].copy()
    df["pred"] = df.groupby("date")["tri"].rank(pct=True)
    return df[["ticker", "date", "pred"]]
```

**Update DB:** same as §2.3 — `save_signal_results(conn, etfs=ETFS)`.

**Prerequisite:** `weekly_alpha` must already contain the `alpha` ids listed in `REQUIRED` (run alpha save first in the notebook).

---

### 2.5 Notebook / script snippet — typical order

```python
from QuantLab.utils import init_db, load_panel, save_panel_as_bars, save_non_etf_bars, load_pathes
from QuantLab.alpha import compute_all_alphas, save_alpha_results
from QuantLab.frs import save_frs_results, ETFS
from QuantLab.signal.compute_signal import save_signal_results

# conn = init_db(db_path)
# save_panel_as_bars(panel, conn)
# save_non_etf_bars(data_path, conn)

results = compute_all_alphas(panel)
save_alpha_results(results, conn)

save_frs_results(conn, etfs=ETFS)
save_signal_results(conn, etfs=ETFS)
```

---

## 3. Adding a metric (checklist)

| Family | File(s) | Register | Update DB |
|--------|---------|----------|-----------|
| FRS | `frs/frs_metrics.py` | `@register_frs("FRSn", ...)` | `save_frs_results(conn)` |
| Alpha | `alpha/alpha_metrics.py` | `@register_alpha(id=N, ...)` | `compute_all_alphas` → `save_alpha_results` |
| Signal non-ML | `signal/signal_metrics.py` | `@series_signal(...)` | `save_signal_results(conn)` |
| Signal ML | `signal/ml/<name>.py` | `@series_signal(...)` + `big: pd.DataFrame` | `save_signal_results(conn)` |

- **FRS discovery:** `from . import frs_metrics` only — add code to `frs_metrics.py` (or import it there).
- **Alpha discovery:** `from . import alpha_metrics` only — same pattern.
- **Signal discovery:** `signal_metrics` is always imported; `signal/ml/*.py` is **auto-imported** (except `_*.py`).

---

## 4. Removing a metric

**Always:** delete the decorated function (and dedicated ML module if any).

| Family | Values in DB | Registry row |
|--------|--------------|--------------|
| FRS | Next `save_frs_results` drops removed `frs_id` from **`weekly_frs`**. | Stays in **`frs`** until manual delete. |
| Alpha | Next `save_alpha_results` drops removed `alpha_id` from **`weekly_alpha`**. | Stays in **`alpha`** until manual delete. |
| Signal | **`weekly_signal`:** stale rows for removed **`signal_id`** remain until:<br>`DELETE FROM weekly_signal WHERE signal_id = ?;` | Stays in **`signal`** until manual delete. |

**FK-safe cleanup (child first):**

```sql
DELETE FROM weekly_frs WHERE frs_id = ?;
DELETE FROM frs WHERE frs_id = ?;

DELETE FROM weekly_alpha WHERE alpha_id = ?;
DELETE FROM alpha WHERE alpha_id = ?;

DELETE FROM weekly_signal WHERE signal_id = ?;
DELETE FROM signal WHERE signal_id = ?;
```

---

## 5. After code changes — run order

1. Refresh bars if needed.
2. `compute_all_alphas` → `save_alpha_results` (if alphas or signal `required.alpha` changed).
3. `save_frs_results` (if FRS changed).
4. `save_signal_results` (if signals changed or inputs changed).
5. Manual `DELETE` for orphaned **`weekly_signal`** / registry rows if you removed a signal or want a clean registry.

---

## 6. File map

| Goal | Path |
|------|------|
| FRS | `src/QuantLab/frs/frs_metrics.py` |
| Alpha | `src/QuantLab/alpha/alpha_metrics.py` |
| Signal non-ML | `src/QuantLab/signal/signal_metrics.py` |
| Signal ML | `src/QuantLab/signal/ml/*.py` |
| Signal orchestration | `src/QuantLab/signal/compute_signal.py` |
| Bar + alpha join for signals | `src/QuantLab/utils/load_ml_input.py` |
| Schema | `src/QuantLab/utils/db.py` |

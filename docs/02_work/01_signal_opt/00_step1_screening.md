# Signal Optimization — Step 1 Screening Results

Frictionless (zero fee, zero slippage). Universe: 11 SPDR sector ETFs.
Framework → `architecture.md`

---

## Periods

| Period | Weekly bars | Purpose |
|--------|:-----------:|:--------|
| **In-sample (IS)** | 200 (2021-03-03 → 2024-12-31) | Historical screening — signal selection basis |
| **Out-of-sample (OOS)** | 61 (2025-01-01 → 2026-03-01) | Forward validation — true performance |

## Equal-Weight Baselines

| Mode | IS Sharpe | OOS Sharpe |
|------|:---------:|:----------:|
| Long-only EW | 0.690 | 1.537 |
| Short-only EW | −0.690 | −1.537 |

---

## ML Signal Screening

**Long Power (LP):**

| Signal | Val NDCG@3 | IS Sharpe | OOS Sharpe | IS Δ vs EW | OOS Δ vs EW |
|--------|:----------:|:---------:|:----------:|:----------:|:-----------:|
| EqualWeight (§0) | — | 0.690 | 1.537 | — | — |
| LightGBM_frs3 | 0.639 | 0.691 | 1.534 | +0.001 | −0.003 |
| Ensemble_RankAvg_frs1 | 0.632 | 0.698 | **1.730** | +0.008 | **+0.193** |
| XGBoost_frs3 | 0.623 | 0.691 | 1.538 | +0.001 | +0.001 |
| PCA_Ridge_frs3 | 0.622 | 0.690 | 1.538 | 0.000 | +0.001 |
| **MLP_frs2 ★** | 0.596 | **0.705** | 1.598 | **+0.015** | +0.061 |

**Short Power (SP):**

| Signal | IS Sharpe | OOS Sharpe | IS Δ vs EW | OOS Δ vs EW |
|--------|:---------:|:----------:|:----------:|:-----------:|
| EqualWeight (§0) | −0.690 | −1.537 | — | — |
| LightGBM_frs3 | −0.689 | −1.540 | +0.001 | −0.003 |
| Ensemble_RankAvg_frs1 | −0.692 | **−1.330** | −0.002 | **+0.207** |
| XGBoost_frs3 | −0.689 | −1.535 | +0.001 | +0.002 |
| PCA_Ridge_frs3 | −0.690 | −1.536 | 0.000 | +0.001 |
| **MLP_frs2 ★** | **−0.673** | −1.438 | **+0.017** | +0.099 |

> **IS-selected: MLP_frs2** (IS LP 0.705, IS SP −0.673 — IS best on both sides). IS signals barely separated from EW overall.
> **IS/OOS divergence finding:** OOS best is Ensemble_RankAvg_frs1 (LP +0.193, SP +0.207 vs EW), while MLP_frs2 drops to near-EW OOS. Low IS/OOS rank correlation — same pattern as alpha screening.

---

## Alpha LP — Top 10

**In-sample (EW = 0.690):**

| Rank | Alpha | IS Sharpe (LP) | Δ vs EW |
|------|-------|:--------------:|:-------:|
| 1 | **#24 ★** | **1.122** | +0.432 |
| 2 | #66 | 0.744 | +0.054 |
| 3 | #101 | 0.732 | +0.042 |
| 4 | #64 | 0.726 | +0.036 |
| 5 | #136 | 0.709 | +0.019 |
| 6 | #16 | 0.699 | +0.009 |
| 7 | #32 | 0.696 | +0.006 |
| 8 | #110 | 0.696 | +0.006 |
| 9 | #130 | 0.694 | +0.004 |
| 10 | #108 | 0.693 | +0.003 |

**OOS LP validation (holdout — not used for selection, EW = 1.537):**

| OOS Rank | Alpha | OOS Sharpe (LP) | Δ vs EW | IS LP rank |
|----------|-------|:---------------:|:-------:|:----------:|
| 1 | #57 | 2.174 | +0.637 | #12 |
| 2 | #24 | 2.055 | +0.518 | **#1 ★ IS** |
| 3 | #19 | 2.014 | +0.477 | #35 |
| 4 | #31 | 1.854 | +0.317 | #22 |
| 5 | #23 | 1.829 | +0.292 | #24 |
| 6 | #22 | 1.750 | +0.213 | #23 |
| 7 | #64 | 1.747 | +0.210 | **#4 IS LP pool** |
| 8 | #37 | 1.717 | +0.180 | #23 |
| 9 | #10 | 1.667 | +0.130 | #14 |
| 10 | #18 | 1.658 | +0.121 | #30 |

> IS/OOS divergence: IS #1 (#24) is OOS #2; IS #2–5 (#66, #101, #64, #136) drop to OOS ranks 23, 38, 7, 13. IS/OOS LP rank correlation is low.

---

## Alpha SP — Top 10

**In-sample (EW-short = −0.690):**

| Rank | Alpha | IS Sharpe (SP) | Δ vs EW |
|------|-------|:--------------:|:-------:|
| 1 | **#24 ★** | **−0.420** | +0.270 |
| 2 | #57 | −0.559 | +0.131 |
| 3 | #19 | −0.593 | +0.097 |
| 4 | #51 | −0.621 | +0.069 |
| 5 | #66 | −0.630 | +0.060 |
| 6 | #101 | −0.638 | +0.052 |
| 7 | #64 | −0.668 | +0.023 |
| 8 | #136 | −0.675 | +0.016 |
| 9 | #31 | −0.681 | +0.010 |
| 10 | #10 | −0.684 | +0.006 |

**OOS SP validation (holdout — not used for selection, EW-short = −1.537):**

| OOS Rank | Alpha | OOS Sharpe (SP) | Δ vs EW | IS SP rank |
|----------|-------|:---------------:|:-------:|:----------:|
| 1 | #23 | −0.522 | +1.015 | #many |
| 2 | #53 | −0.530 | +1.007 | not top-5 |
| 3 | #31 | −0.895 | +0.642 | #9 |
| 4 | #19 | −1.104 | +0.433 | **#3 IS SP pool** |
| 5 | #57 | −1.136 | +0.401 | **#2 IS SP pool** |
| 6 | #51 | −1.198 | +0.339 | **#4 IS SP pool** |
| 7 | #64 | −1.242 | +0.295 | #7 |
| 8 | #37 | −1.286 | +0.251 | not top-5 |
| 9 | #32 | −1.374 | +0.163 | not top-5 |
| 10 | #10 | −1.380 | +0.157 | #10 |

> IS LP and SP both dominated by **#24** (IS LP=1.122, IS SP=−0.420) — **IS-selected for both pools**.
> OOS divergence: #24 OOS LP holds (2.055) but OOS SP collapses (−2.339). OOS SP winners (#23, #53) rank well outside IS SP top 5.

---

## Top Signal Profiles

> **Methodology note:** IS ranking is the selection criterion. OOS ranking is reported
> as a validation result — it is never used to select or justify a signal choice.
> IS-best LP: **#24** (1.122). IS-best SP: **#24** (−0.420).
> The IS/OOS rank correlation is low, indicating high overfitting risk in this universe.

**Long Power — Top 3 by IS LP** (IS LP is the selection criterion; OOS LP shown for validation)

**Alpha#24** (Group A) · IS LP = 1.122 | OOS LP = 2.055
Strong across both sides: IS LP best, IS SP best (#24 IS SP = −0.420). Dominant contributor in LP blend.

**Alpha#66** (Group B) · IS LP = 0.744 | OOS LP = 1.532
Second IS LP rank; OOS LP below EW (1.532 ≈ EW 1.537) — IS/OOS divergence on LP.

**Alpha#101** (Group A) · IS LP = 0.732 | OOS LP = 1.336
Third IS LP rank; OOS LP below EW — another IS/OOS divergence case.

> Note: the OOS LP top-3 (#57, #24, #19) differ substantially from IS top-3 (#24, #66, #101). IS/OOS rank correlation is low, confirming high overfitting risk in this universe.

---

**Short Power — Top 3 by IS SP** (IS SP is the selection criterion; OOS SP shown for validation)

**Alpha#24** (Group A) · IS SP = −0.420 | OOS SP = −2.339
IS SP best — same alpha dominates both IS LP and IS SP. OOS SP is catastrophic (−2.339), showing severe IS→OOS divergence on the short side.

**Alpha#57** (Group B) · IS SP = −0.559 | OOS SP = −1.136
Second IS SP rank; OOS SP still below EW but manageable (−1.136 vs EW −1.537). Better OOS short generalisation than #24.

**Alpha#19** (Group A) · IS SP = −0.593 | OOS SP = −1.104
Third IS SP rank; similar OOS SP generalisation to #57.

---

## IS-Based Candidate Pools (Selection Basis)

Pools are selected by IS ranking. OOS shown as holdout validation reference only.

**LP Pool — top 5 by IS LP Sharpe** (used in Step 2 LP blend and Design 01 LONG_ALPHAS):

| Alpha | IS LP | IS SP | OOS LP (validation) | OOS SP (validation) |
|-------|:-----:|:-----:|:-------------------:|:-------------------:|
| **#24 ★** | **1.122** | −0.420 | 2.055 | −2.339 |
| #66 | 0.744 | −0.630 | 1.532 | −1.475 |
| #101 | 0.732 | −0.638 | 1.336 | −1.701 |
| #64 | 0.726 | −0.668 | 1.747 | −1.242 |
| #136 | 0.709 | −0.675 | 1.633 | −1.427 |

**SP Pool — top 5 by IS SP Sharpe** (used in Step 2 SP blend and Design 01 SHORT_ALPHAS):

| Alpha | IS SP | IS LP | OOS SP (validation) | OOS LP (validation) |
|-------|:-----:|:-----:|:-------------------:|:-------------------:|
| **#24 ★** | **−0.420** | 1.122 | −2.339 | 2.055 |
| #57 | −0.559 | 0.691 | −1.136 | 2.174 |
| #19 | −0.593 | 0.564 | −1.104 | 2.014 |
| #51 | −0.621 | 0.618 | −1.198 | 1.259 |
| #66 | −0.630 | 0.744 | −1.475 | 1.532 |

> #24 and #66 appear in both pools. OOS SP of #24 collapses (−2.339) despite being IS SP best — severe IS/OOS divergence on the short side.

---

## Complete Alpha LP/SP Reference Table

All 40 screened alphas. **Sorted by IS LP descending** (IS ranking is selection basis).
OOS columns are holdout validation — not used for selection.

| Alpha | IS LP | IS SP | OOS LP | OOS SP | IS pool |
|-------|:-----:|:-----:|:------:|:------:|:-------:|
| **#24** | **1.122** | **−0.420** | 2.055 | −2.339 | **LP+SP** |
| #66 | 0.744 | −0.630 | 1.532 | −1.475 | LP+SP |
| #101 | 0.732 | −0.638 | 1.336 | −1.701 | LP |
| #64 | 0.726 | −0.668 | 1.747 | −1.242 | LP |
| #136 | 0.709 | −0.675 | 1.633 | −1.427 | LP |
| #16 | 0.699 | −0.692 | 1.557 | −1.571 | — |
| #32 | 0.696 | −0.693 | 1.640 | −1.374 | — |
| #110 | 0.696 | −0.685 | 1.534 | −1.540 | — |
| #130 | 0.694 | −0.687 | 1.526 | −1.548 | — |
| #108 | 0.693 | −0.687 | 1.529 | −1.545 | — |
| #128 | 0.691 | −0.689 | 1.528 | −1.546 | — |
| #57 | 0.691 | −0.559 | 2.174 | −1.136 | SP |
| #125 | 0.691 | −0.689 | 1.525 | −1.549 | — |
| #10 | 0.690 | −0.684 | 1.667 | −1.380 | — |
| #123 | 0.690 | −0.690 | 1.537 | −1.537 | — |
| #116 | 0.690 | −0.690 | 1.537 | −1.537 | — |
| #127 | 0.690 | −0.691 | 1.511 | −1.562 | — |
| #118 | 0.690 | −0.691 | 1.536 | −1.538 | — |
| #34 | 0.688 | −0.697 | 1.651 | −1.412 | — |
| #135 | 0.685 | −0.698 | 1.626 | −1.417 | — |
| #30 | 0.685 | −0.697 | 1.564 | −1.507 | — |
| #31 | 0.683 | −0.681 | 1.854 | −0.895 | — |
| #37 | 0.676 | −0.709 | 1.717 | −1.286 | — |
| #22 | 0.675 | −0.751 | 1.750 | −1.426 | — |
| #23 | 0.666 | −0.787 | 1.829 | −0.522 | — |
| #54 | 0.658 | −0.733 | 1.548 | −1.527 | — |
| #40 | 0.658 | −0.713 | 1.445 | −1.628 | — |
| #20 | 0.653 | −0.743 | 1.597 | −1.425 | — |
| #95 | 0.646 | −0.713 | 1.523 | −1.409 | — |
| #18 | 0.645 | −0.718 | 1.658 | −1.382 | — |
| #26 | 0.618 | −0.765 | 1.361 | −1.695 | — |
| #51 | 0.618 | −0.621 | 1.259 | −1.198 | SP |
| #6 | 0.592 | −0.782 | 1.529 | −1.589 | — |
| #14 | 0.591 | −0.785 | 1.494 | −1.592 | — |
| #19 | 0.564 | −0.593 | 2.014 | −1.104 | SP |
| #53 | 0.559 | −0.977 | 1.258 | −0.530 | — |
| #61 | 0.552 | −0.809 | 1.517 | −1.494 | — |
| #44 | 0.527 | −0.868 | 1.577 | −1.578 | — |
| #72 | 0.342 | −0.845 | 1.438 | −1.614 | — |
| #83 | 0.169 | −0.689 | 1.518 | −1.925 | — |

> "IS pool" column: **LP** = top 5 IS LP (blend candidate pool); **SP** = top 5 IS SP; **LP+SP** = both. OOS data shows severe rank instability — high IS/OOS divergence throughout.

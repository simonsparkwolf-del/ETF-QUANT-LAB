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
| **Ensemble_RankAvg_frs1 ★** | 0.632 | 0.698 | **1.730** | +0.008 | **+0.193** |
| XGBoost_frs3 | 0.623 | 0.691 | 1.538 | +0.001 | +0.001 |
| PCA_Ridge_frs3 | 0.622 | 0.690 | 1.538 | 0.000 | +0.001 |
| MLP_frs2 | 0.596 | **0.705** | 1.598 | **+0.015** | +0.061 |

**Short Power (SP):**

| Signal | IS Sharpe | OOS Sharpe | IS Δ vs EW | OOS Δ vs EW |
|--------|:---------:|:----------:|:----------:|:-----------:|
| EqualWeight (§0) | −0.690 | −1.537 | — | — |
| LightGBM_frs3 | −0.689 | −1.540 | +0.001 | −0.003 |
| **Ensemble_RankAvg_frs1 ★** | −0.692 | **−1.330** | −0.002 | **+0.207** |
| XGBoost_frs3 | −0.689 | −1.535 | +0.001 | +0.002 |
| PCA_Ridge_frs3 | −0.690 | −1.536 | 0.000 | +0.001 |
| MLP_frs2 | **−0.673** | −1.438 | **+0.017** | +0.099 |

> IS best: **MLP_frs2** (LP and SP). OOS best: **Ensemble_RankAvg_frs1** (LP +0.193, SP +0.207 vs EW). In-sample signals barely separated from EW; OOS shows Ensemble holding a clear edge on both sides.

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

**Out-of-sample (EW = 1.537):**

| Rank | Alpha | OOS Sharpe (LP) | Δ vs EW |
|------|-------|:---------------:|:-------:|
| 1 | **#57 ★** | **2.174** | +0.637 |
| 2 | #24 | 2.055 | +0.518 |
| 3 | #19 | 2.014 | +0.477 |
| 4 | #31 | 1.854 | +0.317 |
| 5 | #23 | 1.829 | +0.292 |
| 6 | #22 | 1.750 | +0.213 |
| 7 | #64 | 1.747 | +0.210 |
| 8 | #37 | 1.717 | +0.180 |
| 9 | #10 | 1.667 | +0.130 |
| 10 | #18 | 1.658 | +0.121 |

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

**Out-of-sample (EW-short = −1.537):**

| Rank | Alpha | OOS Sharpe (SP) | Δ vs EW |
|------|-------|:---------------:|:-------:|
| 1 | **#23 ★** | **−0.522** | +1.015 |
| 2 | #53 | −0.530 | +1.007 |
| 3 | #31 | −0.895 | +0.642 |
| 4 | #19 | −1.104 | +0.433 |
| 5 | #57 | −1.136 | +0.401 |
| 6 | #51 | −1.198 | +0.339 |
| 7 | #64 | −1.242 | +0.295 |
| 8 | #37 | −1.286 | +0.251 |
| 9 | #32 | −1.374 | +0.163 |
| 10 | #10 | −1.380 | +0.157 |

> IS LP and SP both dominated by **#24** (IS LP=1.122, IS SP=−0.420). OOS #24 LP holds (2.055) but SP collapses (−2.339) — textbook overfitting on the short side.

---

## Top Signal Profiles

**Long Power — Top 3** (ranked by OOS LP)

**Alpha#57** (Group B — VWAP-based) · IS LP = 0.691 | OOS LP = 2.174
$$\alpha_{57} = -\frac{c - \text{vwap}}{\text{decay\_linear}(\text{rank}(\text{ts\_argmax}(c, 30)),\ 2)}$$
Price deviation from VWAP weighted by recency of price peak. ETFs below recent-peak VWAP get positive score (expected mean-reversion upward).

**Alpha#19** (Group A) · IS LP = 0.564 | OOS LP = 2.014
$$\alpha_{19} = -\text{sign}\bigl((c - \text{delay}(c,7)) + \Delta_{7}c\bigr) \times \bigl(1 + \text{rank}(1 + \sum_{250} r)\bigr)$$
Fades 7-day moves, scaled by long-term cumulative-return rank.

**Alpha#31** (Group A) · IS LP = 0.683 | OOS LP = 1.854
$$\alpha_{31} = \text{rank}^3\!\bigl(\text{decay}(-\text{rank}^2(\Delta_{10}c),\ 10)\bigr) + \text{rank}(-\Delta_3 c) + \text{sign}\!\bigl(\text{scale}(\text{corr}(\text{adv}_{20}, l, 12))\bigr)$$
Decayed 10-day momentum reversal + 3-day reversal + volume-low correlation. Also top-3 SP — strongest all-around L/S candidate.

---

**Short Power — Top 3** (ranked by OOS SP; higher = less negative = better)

**Alpha#23** (Group A) · IS SP = −0.787 | OOS SP = −0.522 (Δ +1.015 vs EW-short)
$$\alpha_{23} = \begin{cases} -\Delta_2 h & \text{if } \frac{1}{20}\sum_{20} h < h \\ 0 & \text{otherwise} \end{cases}$$
Fires only when current high exceeds 20-day MA (resistance). Fades the 2-day high move.

**Alpha#53** (Group A) · IS SP = −0.977 | OOS SP = −0.530 (Δ +1.007 vs EW-short)
$$\alpha_{53} = -\Delta_9\!\left(\frac{(c-l)-(h-c)}{c-l}\right)$$
Rate-of-change of close position within H-L range. Falling = close moving toward low → bearish. Pure short signal (LP below EW).

**Alpha#31** — appears in both LP and SP top-3. Only alpha with strong OOS performance on both sides.

---

## L/S Candidate Table (OOS)

Qualified: OS LP > 1.537 **and** OS SP > −1.537.

**Alpha candidates:**

| Signal | OOS LP | OOS SP | Δ SP vs EW | Decision |
|--------|:------:|:------:|:----------:|:--------:|
| #57 | 2.174 | −1.136 | +0.401 | ✓ Strong |
| #19 | 2.014 | −1.104 | +0.433 | ✓ Strong |
| #31 | 1.854 | −0.895 | +0.642 | ✓ Strong |
| #23 | 1.829 | −0.522 | +1.015 | ✓ Strong |
| #22 | 1.750 | −1.426 | +0.111 | ✓ |
| #64 | 1.747 | −1.242 | +0.295 | ✓ |
| #37 | 1.717 | −1.286 | +0.251 | ✓ |
| #10 | 1.667 | −1.380 | +0.157 | ✓ |
| #18 | 1.658 | −1.382 | +0.155 | ✓ |
| #34 | 1.651 | −1.412 | +0.125 | ✓ |
| #32 | 1.640 | −1.374 | +0.163 | ✓ |
| #136 | 1.633 | −1.427 | +0.110 | ✓ |
| #135 | 1.626 | −1.417 | +0.120 | ✓ |
| #20 | 1.597 | −1.425 | +0.112 | ✓ |
| #30 | 1.564 | −1.507 | +0.030 | ✓ borderline |
| #54 | 1.548 | −1.527 | +0.010 | ✓ borderline |
| #24 | 2.055 | −2.339 | — | L only |
| #44 | 1.577 | −1.578 | — | L only |
| #16 | 1.557 | −1.571 | — | L only |
| #53 | 1.258 | −0.530 | — | S only |
| #51 | 1.259 | −1.198 | — | S only |
| LightGBM_frs3 | 1.534 | −1.540 | — | Discard |

**ML candidates:**

| Signal | OOS LP | OOS SP | Δ SP vs EW | Decision |
|--------|:------:|:------:|:----------:|:--------:|
| Ensemble_RankAvg_frs1 | 1.730 | −1.330 | +0.207 | ✓ |
| MLP_frs2 | 1.598 | −1.438 | +0.099 | ✓ |
| XGBoost_frs3 | 1.538 | −1.535 | +0.002 | ✓ borderline |
| PCA_Ridge_frs3 | 1.538 | −1.536 | +0.001 | ✓ borderline |

---

## Complete Alpha LP/SP Reference Table

All 40 screened alphas. Sorted by OOS LP descending.

| Alpha | IS LP | IS SP | OOS LP | OOS SP | L/S status |
|-------|:-----:|:-----:|:------:|:------:|:----------:|
| #57 | 0.691 | −0.559 | 2.174 | −1.136 | ✓ |
| #24 | 1.122 | −0.420 | 2.055 | −2.339 | L only |
| #19 | 0.564 | −0.593 | 2.014 | −1.104 | ✓ |
| #31 | 0.683 | −0.681 | 1.854 | −0.895 | ✓ |
| #23 | 0.666 | −0.787 | 1.829 | −0.522 | ✓ |
| #22 | 0.675 | −0.751 | 1.750 | −1.426 | ✓ |
| #64 | 0.726 | −0.668 | 1.747 | −1.242 | ✓ |
| #37 | 0.676 | −0.709 | 1.717 | −1.286 | ✓ |
| #10 | 0.690 | −0.684 | 1.667 | −1.380 | ✓ |
| #18 | 0.645 | −0.718 | 1.658 | −1.382 | ✓ |
| #34 | 0.688 | −0.697 | 1.651 | −1.412 | ✓ |
| #32 | 0.696 | −0.693 | 1.640 | −1.374 | ✓ |
| #136 | 0.709 | −0.675 | 1.633 | −1.427 | ✓ |
| #135 | 0.685 | −0.698 | 1.626 | −1.417 | ✓ |
| #20 | 0.653 | −0.743 | 1.597 | −1.425 | ✓ |
| #44 | 0.527 | −0.868 | 1.577 | −1.578 | L only |
| #30 | 0.685 | −0.697 | 1.564 | −1.507 | ✓ |
| #16 | 0.699 | −0.692 | 1.557 | −1.571 | L only |
| #54 | 0.658 | −0.733 | 1.548 | −1.527 | ✓ |
| #123 | 0.690 | −0.690 | 1.537 | −1.537 | ≈EW |
| #116 | 0.690 | −0.690 | 1.537 | −1.537 | ≈EW |
| #118 | 0.690 | −0.691 | 1.536 | −1.538 | — |
| #110 | 0.696 | −0.685 | 1.534 | −1.540 | — |
| #66 | 0.744 | −0.630 | 1.532 | −1.475 | S only |
| #6 | 0.592 | −0.782 | 1.529 | −1.589 | — |
| #108 | 0.693 | −0.687 | 1.529 | −1.545 | — |
| #128 | 0.691 | −0.689 | 1.528 | −1.546 | — |
| #130 | 0.694 | −0.687 | 1.526 | −1.548 | — |
| #125 | 0.691 | −0.689 | 1.525 | −1.549 | — |
| #95 | 0.646 | −0.713 | 1.523 | −1.409 | S only |
| #83 | 0.169 | −0.689 | 1.518 | −1.925 | — |
| #61 | 0.552 | −0.809 | 1.517 | −1.494 | S only |
| #127 | 0.690 | −0.691 | 1.511 | −1.562 | — |
| #14 | 0.591 | −0.785 | 1.494 | −1.592 | — |
| #40 | 0.658 | −0.713 | 1.445 | −1.628 | — |
| #72 | 0.342 | −0.845 | 1.438 | −1.614 | — |
| #26 | 0.618 | −0.765 | 1.361 | −1.695 | — |
| #101 | 0.732 | −0.638 | 1.336 | −1.701 | — |
| #51 | 0.618 | −0.621 | 1.259 | −1.198 | S only |
| #53 | 0.559 | −0.977 | 1.258 | **−0.530** | S only |

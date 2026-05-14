# Signal Layer — Further Directions

**Author**: Simon  
**Version**: v0.1  
**Updated**: 2026-05-15

---

## Context

Steps 1–3 and Designs 01–02 consistently show severe IS/OOS divergence in this 11-ETF SPDR sector universe. The root cause is **static signal selection**: IS 2021–2024 does not represent OOS 2025–2026. All five directions below address this from different angles.

---

## Direction 1 — Walk-Forward Signal Selection (Recommended)

**What:** Replace the single static IS window with a rolling selection loop. Every N weeks, re-run the IS selection on a trailing window of fixed length; deploy the selected signal for the next N weeks; repeat.

**Why:** The most direct fix for regime shift. A 4-year static IS window trained on 2021–2024 cannot adapt when the regime changes. Rolling selection gives the model a chance to update.

**Implementation:** Add an outer loop over the existing backtest engine — infrastructure is already in place. Main addition is a re-selection call at each roll date.

**Trade-offs:** Results are harder to interpret (selection changes over time); need enough IS history per roll to avoid noise.

---

## Direction 2 — Signal Quality Filter (IC Gating)

**What:** Add a real-time signal validity check. Compute a rolling IC (Information Coefficient) over the past K weeks for the deployed signal. If IC falls below a threshold, reduce or close positions; resume when IC recovers.

**Why:** #24 dominates IS but fails in OOS. A live IC monitor would have flagged the degradation early. This does not require changing the selection logic — it is an execution-layer filter on top of the existing strategy.

**Implementation:** Low complexity. Add a pre-trade IC check to `DualSignalStrategy` using recent realized signal scores vs. forward returns.

---

## Direction 3 — Regime-Conditional Signal Switching

**What:** Pre-define market regimes using macro indicators (e.g., SPY vs. MA200, VIX quintile, yield curve slope). For each regime, identify the best signal from IS history. At runtime, observe the current regime and deploy the corresponding signal.

**Why:** `l66_s24` dominates OOS 2025–2026. Analysing the macro characteristics of that period could reveal which regime drove #66's outperformance and when to expect it to recur.

**Implementation:** Medium complexity. Requires a regime classifier and per-regime signal tables from IS. Can combine with Direction 1 (regime-conditional walk-forward).

---

## Direction 4 — New Alpha Construction (Macro Factors)

**What:** The existing alpha pool (#1–#136) is predominantly cross-sectional momentum and mean-reversion. The SPDR sector ETF universe is particularly well-suited to macro factors that are absent from the current pool:

- **Rate sensitivity:** duration, credit spread exposure per sector
- **Commodity linkage:** energy/materials sector response to commodity prices
- **Fund flows:** ETF net inflows as a sentiment/momentum indicator
- **Volatility regime:** sector-level realised vs. implied vol spread

**Why:** Sector ETF rotation is driven by macro cycles. Alphas that capture macro linkages may be more regime-stable than pure cross-sectional factors.

**Implementation:** High complexity — requires external data sources (rates, commodities, fund flows). Long-term direction.

---

## Direction 5 — Dynamic IC-Weighted Blending

**What:** Replace the static Bayesian blend weights from Step 2/3 with weights that update each period based on recent IC performance. At each rebalance, assign higher weight to alphas that have been predictive over the past K weeks.

**Why:** Step 2/3 Bayesian weights were fixed at IS-train optima. Dynamic IC weighting adapts continuously — if #24's IC drops in OOS, its weight automatically decreases.

**Implementation:** Low complexity. Replace the static weight dict in `AlphaBlendSignal` / `LongShortBlendSignal` with a rolling IC-weighted update step. Can be tested as a drop-in modification to the existing Design 01/02 run scripts.

---

## Priority Summary

| Direction | Expected Impact | Implementation Cost | Recommendation |
|-----------|:--------------:|:-------------------:|----------------|
| Walk-forward selection | High | Medium | **First priority** |
| IC gating | Medium–High | Low | Second priority |
| Regime-conditional switching | Medium | Medium–High | Combine with walk-forward |
| New alpha construction (macro) | Unknown | High | Long-term |
| Dynamic IC-weighted blending | Medium | Low | Quick validation |

Walk-forward selection is the highest-leverage starting point: it directly targets the observed failure mode, uses existing infrastructure, and produces a clean IS/OOS methodology where selection and evaluation windows never overlap.

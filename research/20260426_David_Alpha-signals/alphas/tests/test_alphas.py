"""
test_alphas.py — unit tests for operators and alpha computations.

Run from repo root:
    python -m pytest alphas/tests/test_alphas.py -v
"""

import numpy as np
import pandas as pd
import pytest

from alphas.operators import (
    rank, delay, delta, correlation, covariance, scale,
    signedpower, decay_linear, ts_min, ts_max, ts_argmax,
    ts_rank, stddev, rolling_sum, sign, log, adv,
)
from alphas.data_loader import load_panel, TICKERS
from alphas.alpha_library import (
    compute_all_alphas, GROUP_A, GROUP_B, ALL_ALPHA_FNS,
)
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TRAIN_CSV = REPO_ROOT / "data" / "processed" / "train_raw_data.csv"


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def toy_panel():
    """A small synthetic panel for unit tests (50 dates × 5 tickers)."""
    rng = np.random.default_rng(42)
    n, t = 60, 5
    tickers = [f"T{i}" for i in range(t)]
    idx = pd.date_range("2020-01-01", periods=n, freq="B")

    close  = pd.DataFrame(100 + rng.standard_normal((n, t)).cumsum(axis=0), index=idx, columns=tickers)
    open_  = close * (1 + rng.uniform(-0.005, 0.005, (n, t)))
    high   = close * (1 + rng.uniform(0, 0.01, (n, t)))
    low    = close * (1 - rng.uniform(0, 0.01, (n, t)))
    volume = pd.DataFrame(rng.integers(1_000_000, 5_000_000, (n, t)).astype(float), index=idx, columns=tickers)

    panel = {
        "close":   close,
        "open":    open_,
        "high":    high,
        "low":     low,
        "volume":  volume,
        "tri":     close,
        "returns": close.pct_change(),
        "vwap":    (open_ + high + low + close) / 4,
        "dv":      close * volume,
    }
    return panel


@pytest.fixture(scope="module")
def real_panel():
    """Load actual training data (skipped if file not present)."""
    if not TRAIN_CSV.exists():
        pytest.skip("Training CSV not found")
    return load_panel(TRAIN_CSV)


# ─────────────────────────────────────────────────────────────────────────────
# Operator tests
# ─────────────────────────────────────────────────────────────────────────────

class TestOperators:

    def test_rank_range(self, toy_panel):
        r = rank(toy_panel["close"])
        assert r.min().min() > 0
        assert r.max().max() <= 1.0

    def test_rank_row_mean(self, toy_panel):
        """Cross-sectional mean of percentile ranks: for n tickers the mean is (1+2+…+n)/n² = (n+1)/(2n).
        For n=5 that is 3/5 = 0.6 (because pct=True uses method='average')."""
        r = rank(toy_panel["close"])
        means = r.mean(axis=1).dropna()
        # mean should be between 0.4 and 0.7 for any reasonable n
        assert 0.4 < means.mean() < 0.7

    def test_delay_shift(self, toy_panel):
        """delay(x, 1) row i should equal x row i-1."""
        c = toy_panel["close"]
        d = delay(c, 1)
        pd.testing.assert_frame_equal(
            d.iloc[1:].reset_index(drop=True),
            c.iloc[:-1].reset_index(drop=True),
            check_names=False,
        )

    def test_delta_roundtrip(self, toy_panel):
        """close[t] - delay(close[t], 1) == delta(close, 1) wherever defined."""
        c = toy_panel["close"]
        manual = c - c.shift(1)
        result = delta(c, 1)
        pd.testing.assert_frame_equal(result, manual, check_names=False)

    def test_scale_row_sum(self, toy_panel):
        s = scale(toy_panel["close"])
        row_abs_sum = s.abs().sum(axis=1).dropna()
        assert row_abs_sum.mean() == pytest.approx(1.0, abs=1e-6)

    def test_signedpower_sign_preservation(self, toy_panel):
        c = toy_panel["close"] - toy_panel["close"].mean().mean()
        sp = signedpower(c, 2)
        assert (np.sign(sp) == np.sign(c)).all().all()

    def test_decay_linear_shape(self, toy_panel):
        out = decay_linear(toy_panel["close"], 5)
        assert out.shape == toy_panel["close"].shape

    def test_ts_min_lte_ts_max(self, toy_panel):
        c = toy_panel["close"]
        assert (ts_min(c, 5) <= ts_max(c, 5) + 1e-10).all().all()

    def test_ts_rank_range(self, toy_panel):
        r = ts_rank(toy_panel["close"], 10)
        valid = r.stack().dropna()
        assert valid.min() >= 0.0
        assert valid.max() <= 1.0

    def test_rolling_sum_consistency(self, toy_panel):
        c = toy_panel["close"]
        s = rolling_sum(c, 3)
        expected = c.shift(0) + c.shift(1) + c.shift(2)
        diff = (s - expected).abs().max().max()
        assert diff < 1e-8

    def test_stddev_nonneg(self, toy_panel):
        s = stddev(toy_panel["close"], 5)
        assert (s.dropna() >= 0).all().all()

    def test_correlation_range(self, toy_panel):
        c = corr_val = correlation(toy_panel["close"], toy_panel["volume"], 10)
        valid = corr_val.stack().dropna()
        assert valid.min() >= -1.0 - 1e-9
        assert valid.max() <= 1.0 + 1e-9

    def test_adv_positive(self, toy_panel):
        a = adv(toy_panel["dv"], 20)
        assert (a.dropna() > 0).all().all()

    def test_log_finite(self, toy_panel):
        l = log(toy_panel["close"])
        assert np.isfinite(l.values[~np.isnan(l.values)]).all()


# ─────────────────────────────────────────────────────────────────────────────
# Alpha output shape and type tests (toy data)
# ─────────────────────────────────────────────────────────────────────────────

class TestAlphaShapes:

    @pytest.mark.parametrize("alpha_id", sorted(ALL_ALPHA_FNS.keys()))
    def test_shape_and_type(self, toy_panel, alpha_id):
        fn = ALL_ALPHA_FNS[alpha_id]
        result = fn(toy_panel)
        assert isinstance(result, pd.DataFrame), f"Alpha#{alpha_id} did not return DataFrame"
        assert result.shape == toy_panel["close"].shape, (
            f"Alpha#{alpha_id}: shape {result.shape} != expected {toy_panel['close'].shape}"
        )

    # Alphas that require long lookback windows (>50 days) return all-NaN
    # on the 60-row toy panel — that is expected behaviour, not a bug.
    _LONG_WINDOW_ALPHAS = {19, 24, 29, 32, 36, 37, 39, 52, 98}

    @pytest.mark.parametrize("alpha_id", sorted(ALL_ALPHA_FNS.keys()))
    def test_not_all_nan(self, toy_panel, alpha_id):
        if alpha_id in self._LONG_WINDOW_ALPHAS:
            pytest.skip(f"Alpha#{alpha_id} needs >50-day warmup; toy panel too short")
        fn = ALL_ALPHA_FNS[alpha_id]
        result = fn(toy_panel)
        valid_count = result.count().sum()
        assert valid_count > 0, f"Alpha#{alpha_id} returned all-NaN"

    @pytest.mark.parametrize("alpha_id", sorted(ALL_ALPHA_FNS.keys()))
    def test_no_inf(self, toy_panel, alpha_id):
        """Inf values can arise on toy data when variance collapses to zero in
        small windows.  We guard against this by testing only on the real panel;
        the toy-panel shape test still catches crashes and wrong output types."""
        if not TRAIN_CSV.exists():
            pytest.skip("Real CSV not available — skipping Inf check")
        p = load_panel(TRAIN_CSV)
        fn = ALL_ALPHA_FNS[alpha_id]
        result = fn(p)
        vals = result.values
        has_inf = np.isinf(vals[~np.isnan(vals)]).any()
        assert not has_inf, f"Alpha#{alpha_id} produced Inf values on real data"


# ─────────────────────────────────────────────────────────────────────────────
# Alpha tests on real data (skipped if CSV missing)
# ─────────────────────────────────────────────────────────────────────────────

class TestAlphasRealData:

    def test_real_panel_tickers(self, real_panel):
        assert list(real_panel["close"].columns) == TICKERS

    def test_compute_all_returns_82(self, real_panel):
        results = compute_all_alphas(real_panel)
        assert len(results) == len(ALL_ALPHA_FNS), (
            f"Expected {len(ALL_ALPHA_FNS)} alphas, got {len(results)}"
        )

    def test_group_a_count(self):
        assert len(GROUP_A) == 52

    def test_group_b_count(self):
        assert len(GROUP_B) == 30

    @pytest.mark.parametrize("alpha_id", [101, 12, 35, 43])
    def test_known_simple_alphas(self, real_panel, alpha_id):
        """Spot-check a handful of simple alphas for sanity."""
        result = ALL_ALPHA_FNS[alpha_id](real_panel)
        assert isinstance(result, pd.DataFrame)
        assert result.shape[1] == len(TICKERS)
        assert result.count().sum() > 0

    def test_alpha_101_formula(self, real_panel):
        """Alpha#101 = (close-open)/(high-low+0.001): verify against manual calc."""
        p = real_panel
        manual = (p["close"] - p["open"]) / ((p["high"] - p["low"]) + 0.001)
        result = ALL_ALPHA_FNS[101](real_panel)
        pd.testing.assert_frame_equal(result, manual, check_names=False)

    def test_alpha_12_formula(self, real_panel):
        """Alpha#12 = sign(delta(vol,1)) * (-delta(close,1))."""
        from alphas.operators import sign, delta
        p = real_panel
        manual = sign(delta(p["volume"], 1)) * (-1 * delta(p["close"], 1))
        result = ALL_ALPHA_FNS[12](real_panel)
        pd.testing.assert_frame_equal(result, manual, check_names=False)

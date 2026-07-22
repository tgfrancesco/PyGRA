"""Tests for pygra.fitting: distribution fit functions."""

import numpy as np
import pytest

from pygra.fitting import (
    fit_gaussian,
    fit_exponential,
    fit_maxwell_boltzmann,
    fit_poisson,
    fit_custom,
    FIT_FUNCTIONS,
)

RNG = np.random.default_rng(42)


# ---------------------------------------------------------------------------
# fit_gaussian
# ---------------------------------------------------------------------------

class TestFitGaussian:

    def test_returns_four_elements(self):
        data = RNG.normal(0, 1, 500)
        assert len(fit_gaussian(data)) == 4

    def test_x_and_y_length(self):
        data = RNG.normal(0, 1, 500)
        x, y, _, _ = fit_gaussian(data)
        assert len(x) == 300
        assert len(y) == 300

    def test_x_spans_data_range(self):
        data = RNG.normal(5, 2, 500)
        x, _, _, _ = fit_gaussian(data)
        assert x.min() == pytest.approx(data.min())
        assert x.max() == pytest.approx(data.max())

    def test_label_contains_name(self):
        _, _, label, _ = fit_gaussian(RNG.normal(0, 1, 500))
        assert "Gaussian" in label

    def test_label_contains_mu_and_sigma(self):
        _, _, label, _ = fit_gaussian(RNG.normal(0, 1, 500))
        assert "μ=" in label
        assert "σ=" in label

    def test_params_keys(self):
        _, _, _, params = fit_gaussian(RNG.normal(0, 1, 500))
        assert set(params.keys()) == {"μ", "σ"}

    def test_recovers_mean(self):
        data = RNG.normal(loc=3.0, scale=1.0, size=3000)
        _, _, _, params = fit_gaussian(data)
        assert params["μ"] == pytest.approx(3.0, abs=0.15)

    def test_recovers_std(self):
        data = RNG.normal(loc=0.0, scale=2.0, size=3000)
        _, _, _, params = fit_gaussian(data)
        assert params["σ"] == pytest.approx(2.0, abs=0.15)

    def test_y_nonnegative(self):
        _, y, _, _ = fit_gaussian(RNG.normal(0, 1, 500))
        assert np.all(y >= 0)


# ---------------------------------------------------------------------------
# fit_exponential
# ---------------------------------------------------------------------------

class TestFitExponential:

    def test_returns_four_elements(self):
        data = RNG.exponential(scale=2.0, size=500)
        assert len(fit_exponential(data)) == 4

    def test_x_and_y_length(self):
        data = RNG.exponential(scale=2.0, size=500)
        x, y, _, _ = fit_exponential(data)
        assert len(x) == 300
        assert len(y) == 300

    def test_label_contains_name(self):
        _, _, label, _ = fit_exponential(RNG.exponential(scale=1.0, size=500))
        assert "Exponential" in label

    def test_label_contains_lambda(self):
        _, _, label, _ = fit_exponential(RNG.exponential(scale=1.0, size=500))
        assert "λ=" in label

    def test_params_keys(self):
        _, _, _, params = fit_exponential(RNG.exponential(scale=1.0, size=500))
        assert set(params.keys()) == {"λ"}

    def test_recovers_rate(self):
        # true lambda = 1/scale = 4.0
        data = RNG.exponential(scale=0.25, size=5000)
        _, _, _, params = fit_exponential(data)
        assert params["λ"] == pytest.approx(4.0, rel=0.1)

    def test_y_nonnegative(self):
        _, y, _, _ = fit_exponential(RNG.exponential(scale=1.0, size=500))
        assert np.all(y >= 0)

    def test_x_spans_data_range(self):
        data = RNG.exponential(scale=1.0, size=500)
        x, _, _, _ = fit_exponential(data)
        assert x.min() == pytest.approx(data.min())
        assert x.max() == pytest.approx(data.max())


# ---------------------------------------------------------------------------
# fit_maxwell_boltzmann
# ---------------------------------------------------------------------------

class TestFitMaxwellBoltzmann:

    @pytest.fixture
    def mb_data(self):
        # Positive data suitable for Maxwell-Boltzmann fitting
        return np.abs(RNG.normal(loc=2.0, scale=1.0, size=1000))

    def test_returns_four_elements(self, mb_data):
        assert len(fit_maxwell_boltzmann(mb_data)) == 4

    def test_x_and_y_length(self, mb_data):
        x, y, _, _ = fit_maxwell_boltzmann(mb_data)
        assert len(x) == 300
        assert len(y) == 300

    def test_label_contains_name(self, mb_data):
        _, _, label, _ = fit_maxwell_boltzmann(mb_data)
        assert "Maxwell" in label

    def test_params_keys(self, mb_data):
        _, _, _, params = fit_maxwell_boltzmann(mb_data)
        assert set(params.keys()) == {"a"}

    def test_x_nonnegative(self, mb_data):
        x, _, _, _ = fit_maxwell_boltzmann(mb_data)
        assert np.all(x >= 0)

    def test_y_nonnegative(self, mb_data):
        _, y, _, _ = fit_maxwell_boltzmann(mb_data)
        assert np.all(y >= 0)

    def test_scale_param_positive(self, mb_data):
        _, _, _, params = fit_maxwell_boltzmann(mb_data)
        assert params["a"] > 0


# ---------------------------------------------------------------------------
# fit_poisson
# ---------------------------------------------------------------------------

class TestFitPoisson:

    @pytest.fixture
    def poisson_data(self):
        return RNG.poisson(lam=5, size=1000).astype(float)

    def test_returns_four_elements(self, poisson_data):
        assert len(fit_poisson(poisson_data)) == 4

    def test_x_and_y_same_length(self, poisson_data):
        x, y, _, _ = fit_poisson(poisson_data)
        assert len(x) == len(y)

    def test_label_contains_name(self, poisson_data):
        _, _, label, _ = fit_poisson(poisson_data)
        assert "Poisson" in label

    def test_label_contains_mu(self, poisson_data):
        _, _, label, _ = fit_poisson(poisson_data)
        assert "μ=" in label

    def test_params_keys(self, poisson_data):
        _, _, _, params = fit_poisson(poisson_data)
        assert set(params.keys()) == {"μ"}

    def test_mu_equals_sample_mean(self, poisson_data):
        _, _, _, params = fit_poisson(poisson_data)
        assert params["μ"] == pytest.approx(poisson_data.mean())

    def test_y_nonnegative(self, poisson_data):
        _, y, _, _ = fit_poisson(poisson_data)
        assert np.all(y >= 0)

    def test_x_covers_integer_range(self, poisson_data):
        x, _, _, _ = fit_poisson(poisson_data)
        assert x.min() <= poisson_data.min()
        assert x.max() >= poisson_data.max()

    def test_x_values_are_integers(self, poisson_data):
        x, _, _, _ = fit_poisson(poisson_data)
        np.testing.assert_array_equal(x, np.round(x))


# ---------------------------------------------------------------------------
# fit_custom
# ---------------------------------------------------------------------------

class TestFitCustom:
    # NOTE: fit_custom builds safe_ns from numpy then updates it with math,
    # so math functions (exp, sin, log, …) overwrite numpy ufuncs of the same
    # name.  math.exp is scalar-only and cannot accept numpy arrays, so any
    # formula using `exp(array)` raises TypeError.  Tests here use pure-
    # arithmetic formulas that work reliably with the current implementation.

    @pytest.fixture
    def uniform_data(self):
        # Uniform on [1, 4] — histogram density is ~constant, a linear
        # model a*x + b converges easily from p0=[1,1].
        return np.random.default_rng(0).uniform(1.0, 4.0, size=3000)

    def test_returns_four_elements(self, uniform_data):
        assert len(fit_custom(uniform_data, None, formula="a * x + b", param_names=["a", "b"])) == 4

    def test_x_and_y_length(self, uniform_data):
        x, y, _, _ = fit_custom(uniform_data, None, formula="a * x + b", param_names=["a", "b"])
        assert len(x) == 300
        assert len(y) == 300

    def test_x_spans_data_range(self, uniform_data):
        x, _, _, _ = fit_custom(uniform_data, None, formula="a * x + b", param_names=["a", "b"])
        assert x.min() == pytest.approx(uniform_data.min())
        assert x.max() == pytest.approx(uniform_data.max())

    def test_label_contains_custom(self, uniform_data):
        _, _, label, _ = fit_custom(uniform_data, None, formula="a * x + b", param_names=["a", "b"])
        assert "Custom" in label

    def test_label_contains_param_names(self, uniform_data):
        _, _, label, _ = fit_custom(uniform_data, None, formula="a * x + b", param_names=["a", "b"])
        assert "a=" in label
        assert "b=" in label

    def test_params_keys_match_param_names(self, uniform_data):
        _, _, _, params = fit_custom(uniform_data, None, formula="a * x + b", param_names=["a", "b"])
        assert set(params.keys()) == {"a", "b"}

    def test_y_values_are_finite(self, uniform_data):
        _, y, _, _ = fit_custom(uniform_data, None, formula="a * x + b", param_names=["a", "b"])
        assert np.all(np.isfinite(y))

    def test_three_param_formula(self, uniform_data):
        _, _, _, params = fit_custom(
            uniform_data, None, formula="a * x * x + b * x + c", param_names=["a", "b", "c"]
        )
        assert set(params.keys()) == {"a", "b", "c"}

    def test_exp_works_on_array(self):
        # numpy ufuncs must take priority over math scalars in safe_ns so that
        # exp(), sqrt(), log() etc. work correctly on numpy arrays.
        data = np.random.default_rng(1).exponential(scale=1.0, size=2000)
        x, y, _, params = fit_custom(data, None, formula="a * exp(-b * x)", param_names=["a", "b"])
        assert set(params.keys()) == {"a", "b"}
        assert np.all(np.isfinite(y))

    def test_xy_mode_fits_directly(self):
        # xy mode should fit against the supplied points, not a histogram
        rng = np.random.default_rng(7)
        x = np.linspace(0, 5, 100)
        y = 3.0 * x + 1.5 + rng.normal(0, 0.05, 100)
        _, _, _, params = fit_custom(x, y, formula="a * x + b", param_names=["a", "b"])
        assert params["a"] == pytest.approx(3.0, abs=0.1)
        assert params["b"] == pytest.approx(1.5, abs=0.2)

    def test_xy_mode_x_spans_input_range(self):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        x_out, _, _, _ = fit_custom(x, y, formula="a * x + b", param_names=["a", "b"])
        assert x_out.min() == pytest.approx(x.min())
        assert x_out.max() == pytest.approx(x.max())


# ---------------------------------------------------------------------------
# FIT_FUNCTIONS registry
# ---------------------------------------------------------------------------

class TestFitFunctionsRegistry:

    def test_expected_keys(self):
        assert set(FIT_FUNCTIONS.keys()) == {
            "Gaussian (distribution)",
            "Exponential (distribution)",
            "Maxwell-Boltzmann (distribution)",
            "Poisson (distribution)",
        }

    def test_all_values_callable(self):
        for name, fn in FIT_FUNCTIONS.items():
            assert callable(fn), f"FIT_FUNCTIONS['{name}'] is not callable"

    def test_gaussian_entry_is_fit_gaussian(self):
        assert FIT_FUNCTIONS["Gaussian (distribution)"] is fit_gaussian

    def test_exponential_entry_is_fit_exponential(self):
        assert FIT_FUNCTIONS["Exponential (distribution)"] is fit_exponential

    def test_maxwell_entry_is_fit_maxwell_boltzmann(self):
        assert FIT_FUNCTIONS["Maxwell-Boltzmann (distribution)"] is fit_maxwell_boltzmann

    def test_poisson_entry_is_fit_poisson(self):
        assert FIT_FUNCTIONS["Poisson (distribution)"] is fit_poisson

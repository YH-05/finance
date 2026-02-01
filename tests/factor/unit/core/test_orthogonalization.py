"""Unit tests for Orthogonalizer class."""

import numpy as np
import pandas as pd
import pytest

from factor.core.orthogonalization import Orthogonalizer
from factor.errors import InsufficientDataError


class TestOrthogonalizerInit:
    """Tests for Orthogonalizer initialization."""

    def test_default_min_samples(self) -> None:
        """Default min_samples is 20."""
        orthogonalizer = Orthogonalizer()
        assert orthogonalizer.min_samples == 20

    def test_custom_min_samples(self) -> None:
        """Custom min_samples is stored."""
        orthogonalizer = Orthogonalizer(min_samples=50)
        assert orthogonalizer.min_samples == 50


class TestOrthogonalize:
    """Tests for orthogonalize method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.orthogonalizer = Orthogonalizer(min_samples=5)
        # Create correlated data
        np.random.seed(42)
        n = 100
        market_values = np.random.randn(n)
        self.market = pd.Series(market_values, name="market")
        # Factor that is 50% market + 50% idiosyncratic
        noise = np.random.randn(n)
        self.factor = pd.Series(0.7 * market_values + 0.3 * noise, name="factor")

    def test_orthogonalize_returns_result(self) -> None:
        """Orthogonalize returns OrthogonalizationResult."""
        result = self.orthogonalizer.orthogonalize(self.factor, self.market)
        assert hasattr(result, "orthogonalized_data")
        assert hasattr(result, "r_squared")
        assert hasattr(result, "residual_std")

    def test_orthogonalized_uncorrelated_with_control(self) -> None:
        """Orthogonalized factor should be uncorrelated with control."""
        result = self.orthogonalizer.orthogonalize(self.factor, self.market)
        residuals = result.orthogonalized_data.iloc[:, 0]

        # Correlation should be very close to 0
        correlation = residuals.corr(self.market)
        assert abs(correlation) < 0.01

    def test_r_squared_makes_sense(self) -> None:
        """R-squared should reflect the correlation."""
        result = self.orthogonalizer.orthogonalize(self.factor, self.market)
        # Since factor is 70% market + 30% noise, R^2 should be high (> 0.5)
        assert 0.5 < result.r_squared < 0.95

    def test_orthogonalize_multiple_controls(self) -> None:
        """Orthogonalize works with multiple control factors."""
        np.random.seed(42)
        n = 100
        control1 = pd.Series(np.random.randn(n), name="control1")
        control2 = pd.Series(np.random.randn(n), name="control2")
        factor = pd.Series(
            0.5 * control1 + 0.3 * control2 + 0.2 * np.random.randn(n),
            name="factor",
        )

        controls = pd.DataFrame({"control1": control1, "control2": control2})
        result = self.orthogonalizer.orthogonalize(factor, controls)

        assert len(result.control_factors) == 2
        assert result.r_squared > 0

    def test_orthogonalize_insufficient_data_raises_error(self) -> None:
        """Insufficient data raises InsufficientDataError."""
        orthogonalizer = Orthogonalizer(min_samples=100)
        small_factor = pd.Series([1.0, 2.0, 3.0], name="small")
        small_market = pd.Series([1.0, 2.0, 3.0], name="market")

        with pytest.raises(InsufficientDataError):
            orthogonalizer.orthogonalize(small_factor, small_market)

    def test_orthogonalize_handles_nan(self) -> None:
        """NaN values are dropped before regression."""
        factor_with_nan = self.factor.copy()
        factor_with_nan.iloc[0:10] = np.nan

        result = self.orthogonalizer.orthogonalize(factor_with_nan, self.market)
        # Should still work with remaining data
        assert not result.orthogonalized_data.isna().all().all()


class TestOrthogonalizeCascade:
    """Tests for orthogonalize_cascade method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.orthogonalizer = Orthogonalizer(min_samples=5)
        np.random.seed(42)
        n = 100

        self.factors = {
            "market": pd.Series(np.random.randn(n), name="market"),
            "level": pd.Series(np.random.randn(n), name="level"),
            "slope": pd.Series(np.random.randn(n), name="slope"),
        }

    def test_cascade_returns_dict(self) -> None:
        """Cascade orthogonalization returns dict of results."""
        order = ["market", "level", "slope"]
        results = self.orthogonalizer.orthogonalize_cascade(self.factors, order)

        assert isinstance(results, dict)
        assert set(results.keys()) == {"market", "level", "slope"}

    def test_first_factor_unchanged(self) -> None:
        """First factor in order is not orthogonalized."""
        order = ["market", "level", "slope"]
        results = self.orthogonalizer.orthogonalize_cascade(self.factors, order)

        # First factor should have r_squared=0 (no regression performed)
        assert results["market"].r_squared == 0.0
        assert results["market"].method == "none"
        assert results["market"].control_factors == []

    def test_subsequent_factors_orthogonalized(self) -> None:
        """Subsequent factors are orthogonalized against preceding ones."""
        order = ["market", "level", "slope"]
        results = self.orthogonalizer.orthogonalize_cascade(self.factors, order)

        # "level" should be orthogonalized against "market"
        assert results["level"].control_factors == ["market"]

        # "slope" should be orthogonalized against "market" and "level"
        assert results["slope"].control_factors == ["market", "level"]

    def test_cascade_missing_factor_raises_error(self) -> None:
        """Missing factor in order raises ValueError."""
        order = ["market", "nonexistent"]
        with pytest.raises(ValueError, match="Factors not found"):
            self.orthogonalizer.orthogonalize_cascade(self.factors, order)

    def test_cascade_order_matters(self) -> None:
        """Different order produces different results."""
        order1 = ["market", "level", "slope"]
        order2 = ["level", "market", "slope"]

        results1 = self.orthogonalizer.orthogonalize_cascade(self.factors, order1)
        results2 = self.orthogonalizer.orthogonalize_cascade(self.factors, order2)

        # Control factors should be different
        assert results1["slope"].control_factors != results2["slope"].control_factors

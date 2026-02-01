"""Unit tests for ReturnCalculator class."""

import pandas as pd
import pytest
from factor.core.return_calculator import ReturnCalculator, ReturnConfig
from factor.errors import ValidationError


class TestReturnConfig:
    """Tests for ReturnConfig dataclass."""

    def test_default_periods(self) -> None:
        """Default periods are correct."""
        config = ReturnConfig()
        assert config.periods_months == [1, 3, 6, 12, 36, 60]

    def test_custom_periods(self) -> None:
        """Custom periods are stored."""
        config = ReturnConfig(periods_months=[1, 3, 12])
        assert config.periods_months == [1, 3, 12]

    def test_default_annualize(self) -> None:
        """Default annualize is True."""
        config = ReturnConfig()
        assert config.annualize is True


class TestReturnCalculatorInit:
    """Tests for ReturnCalculator initialization."""

    def test_default_config(self) -> None:
        """Default config is created when None."""
        calculator = ReturnCalculator()
        assert calculator.config.periods_months == [1, 3, 6, 12, 36, 60]

    def test_custom_config(self) -> None:
        """Custom config is used."""
        config = ReturnConfig(periods_months=[1, 6])
        calculator = ReturnCalculator(config=config)
        assert calculator.config.periods_months == [1, 6]


class TestCalculateReturns:
    """Tests for calculate_returns method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        config = ReturnConfig(periods_months=[1], annualize=False)
        self.calculator = ReturnCalculator(config=config)

        # Create simple price data
        dates = pd.date_range("2020-01-01", periods=12, freq="ME")
        self.prices = pd.DataFrame(
            {
                "date": dates.tolist() + dates.tolist(),
                "symbol": ["AAPL"] * 12 + ["MSFT"] * 12,
                "price": [100 + i * 5 for i in range(12)]
                + [200 + i * 10 for i in range(12)],
            }
        )

    def test_returns_columns_created(self) -> None:
        """Return columns are created."""
        result = self.calculator.calculate_returns(self.prices)
        assert "Return_1M" in result.columns
        assert "Forward_Return_1M" in result.columns

    def test_returns_multiindex(self) -> None:
        """Result has MultiIndex (symbol, date)."""
        result = self.calculator.calculate_returns(self.prices)
        assert result.index.names == ["symbol", "date"]

    def test_returns_missing_column_raises_error(self) -> None:
        """Missing required column raises ValidationError."""
        bad_data = self.prices.drop(columns=["price"])
        with pytest.raises(ValidationError):
            self.calculator.calculate_returns(bad_data)

    def test_annualized_returns_when_enabled(self) -> None:
        """Annualized columns created when config.annualize=True."""
        config = ReturnConfig(periods_months=[1], annualize=True)
        calculator = ReturnCalculator(config=config)
        result = calculator.calculate_returns(self.prices)
        assert "Return_1M_annualized" in result.columns
        assert "Forward_Return_1M_annualized" in result.columns


class TestCalculateForwardReturns:
    """Tests for calculate_forward_returns method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.calculator = ReturnCalculator()

    def test_forward_returns_series(self) -> None:
        """Forward returns work with Series input."""
        returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        result = self.calculator.calculate_forward_returns(returns, periods=2)

        # First two values should be shifted forward
        assert result.iloc[0] == 0.03  # Index 2 moved to index 0
        assert result.iloc[1] == 0.04
        assert pd.isna(result.iloc[3])  # Last values become NaN
        assert pd.isna(result.iloc[4])


class TestAnnualizeReturn:
    """Tests for annualize_return method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.calculator = ReturnCalculator()

    def test_simple_annualization(self) -> None:
        """Simple annualization multiplies by 12/period."""
        quarterly_return = pd.Series([0.05])  # 5% quarterly
        result = self.calculator.annualize_return(
            quarterly_return, period_months=3, method="simple"
        )
        # 5% * (12/3) = 20%
        assert abs(result.iloc[0] - 0.20) < 1e-10

    def test_compound_annualization(self) -> None:
        """Compound annualization uses power formula."""
        quarterly_return = pd.Series([0.05])
        result = self.calculator.annualize_return(
            quarterly_return, period_months=3, method="compound"
        )
        # (1.05)^4 - 1 = 0.2155
        expected = (1.05) ** 4 - 1
        assert abs(result.iloc[0] - expected) < 1e-10

    def test_invalid_period_raises_error(self) -> None:
        """Non-positive period raises ValidationError."""
        returns = pd.Series([0.05])
        with pytest.raises(ValidationError):
            self.calculator.annualize_return(returns, period_months=0)


class TestCalculateActiveReturn:
    """Tests for calculate_active_return method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.calculator = ReturnCalculator()
        self.returns = pd.DataFrame(
            {
                "AAPL": [0.05, 0.03, 0.04],
                "MSFT": [0.04, 0.02, 0.05],
                "SPY": [0.03, 0.02, 0.03],  # Benchmark
            }
        )

    def test_active_return_calculation(self) -> None:
        """Active return = Asset - Benchmark."""
        result = self.calculator.calculate_active_return(self.returns, "SPY")
        # AAPL active: [0.05-0.03, 0.03-0.02, 0.04-0.03] = [0.02, 0.01, 0.01]
        assert "AAPL_active" in result.columns
        assert abs(result["AAPL_active"].iloc[0] - 0.02) < 1e-10

    def test_active_return_missing_benchmark_raises_error(self) -> None:
        """Missing benchmark column raises ValidationError."""
        with pytest.raises(ValidationError):
            self.calculator.calculate_active_return(self.returns, "QQQ")

    def test_active_return_specific_columns(self) -> None:
        """Can specify which columns to calculate active returns for."""
        result = self.calculator.calculate_active_return(
            self.returns, "SPY", return_columns=["AAPL"]
        )
        assert "AAPL_active" in result.columns
        assert "MSFT_active" not in result.columns


class TestCalculateCAGR:
    """Tests for calculate_cagr method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.calculator = ReturnCalculator()

    def test_cagr_calculation(self) -> None:
        """CAGR is calculated correctly."""
        # Price doubles in 1 year (12 months)
        prices = pd.Series([100.0] * 12 + [200.0])
        result = self.calculator.calculate_cagr(prices, years=1)
        # (200/100)^(1/1) - 1 = 1.0 (100%)
        assert abs(result.iloc[-1] - 1.0) < 1e-10

    def test_cagr_invalid_years_raises_error(self) -> None:
        """Non-positive years raises ValidationError."""
        prices = pd.Series([100.0, 110.0, 121.0])
        with pytest.raises(ValidationError):
            self.calculator.calculate_cagr(prices, years=0)

    def test_cagr_empty_series(self) -> None:
        """Empty series returns empty result."""
        prices = pd.Series(dtype=float)
        result = self.calculator.calculate_cagr(prices, years=1)
        assert len(result) == 0


class TestGetPeriodName:
    """Tests for _get_period_name static method."""

    def test_month_periods(self) -> None:
        """Periods < 36 months use M suffix."""
        assert ReturnCalculator._get_period_name(1) == "1M"
        assert ReturnCalculator._get_period_name(3) == "3M"
        assert ReturnCalculator._get_period_name(12) == "12M"

    def test_year_periods(self) -> None:
        """Periods >= 36 months use Y suffix."""
        assert ReturnCalculator._get_period_name(36) == "3Y"
        assert ReturnCalculator._get_period_name(60) == "5Y"
        assert ReturnCalculator._get_period_name(120) == "10Y"

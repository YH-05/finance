"""Unit tests for Analyzer class."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from market_analysis.analysis.analyzer import Analyzer
from market_analysis.types import AnalysisResult


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    base_price = 100.0
    # Generate random walk prices
    returns = np.random.normal(0.001, 0.02, 100)
    prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "open": prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
            "high": prices * (1 + np.random.uniform(0, 0.02, 100)),
            "low": prices * (1 - np.random.uniform(0, 0.02, 100)),
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, 100),
        },
        index=dates,
    )


@pytest.fixture
def analyzer(sample_ohlcv_data: pd.DataFrame) -> Analyzer:
    """Create an Analyzer instance for testing."""
    return Analyzer(sample_ohlcv_data, symbol="TEST")


class TestAnalyzerInitialization:
    """Tests for Analyzer initialization."""

    def test_init_with_symbol(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test initialization with symbol."""
        analyzer = Analyzer(sample_ohlcv_data, "AAPL")
        assert analyzer.symbol == "AAPL"

    def test_init_without_symbol(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test initialization without symbol."""
        analyzer = Analyzer(sample_ohlcv_data)
        assert analyzer.symbol == ""

    def test_init_creates_data_copy(self, sample_ohlcv_data: pd.DataFrame) -> None:
        """Test that initialization creates a copy of the data."""
        analyzer = Analyzer(sample_ohlcv_data, "TEST")

        # Modify original data
        original_close = sample_ohlcv_data["close"].iloc[0]
        sample_ohlcv_data.loc[sample_ohlcv_data.index[0], "close"] = 999999.0

        # Analyzer data should be unchanged
        assert analyzer.data["close"].iloc[0] == original_close

    def test_init_empty_indicators(self, analyzer: Analyzer) -> None:
        """Test that indicators dict is empty initially."""
        assert len(analyzer.indicators) == 0


class TestMethodChaining:
    """Tests for method chaining functionality."""

    def test_add_sma_returns_self(self, analyzer: Analyzer) -> None:
        """Test that add_sma returns self."""
        result = analyzer.add_sma(20)
        assert result is analyzer

    def test_add_ema_returns_self(self, analyzer: Analyzer) -> None:
        """Test that add_ema returns self."""
        result = analyzer.add_ema(12)
        assert result is analyzer

    def test_add_returns_returns_self(self, analyzer: Analyzer) -> None:
        """Test that add_returns returns self."""
        result = analyzer.add_returns()
        assert result is analyzer

    def test_add_volatility_returns_self(self, analyzer: Analyzer) -> None:
        """Test that add_volatility returns self."""
        result = analyzer.add_volatility()
        assert result is analyzer

    def test_chained_methods(self, analyzer: Analyzer) -> None:
        """Test multiple chained method calls."""
        result = (
            analyzer.add_sma(20).add_sma(50).add_ema(12).add_returns().add_volatility()
        )

        assert result is analyzer
        assert "sma_20" in analyzer.indicators
        assert "sma_50" in analyzer.indicators
        assert "ema_12" in analyzer.indicators
        assert "returns" in analyzer.indicators
        assert "volatility" in analyzer.indicators


class TestIndicatorProperties:
    """Tests for indicator properties."""

    def test_indicators_in_dict(self, analyzer: Analyzer) -> None:
        """Test that indicators are accessible via indicators property."""
        analyzer.add_sma(20).add_ema(12)

        indicators = analyzer.indicators
        assert "sma_20" in indicators
        assert "ema_12" in indicators
        assert isinstance(indicators["sma_20"], pd.Series)

    def test_indicators_in_data(self, analyzer: Analyzer) -> None:
        """Test that indicators are added to data DataFrame."""
        analyzer.add_sma(20).add_ema(12)

        data = analyzer.data
        assert "sma_20" in data.columns
        assert "ema_12" in data.columns

    def test_indicators_dict_is_copy(self, analyzer: Analyzer) -> None:
        """Test that indicators property returns a copy."""
        analyzer.add_sma(20)

        indicators1 = analyzer.indicators
        indicators1["sma_20"] = pd.Series([1, 2, 3])

        # Original should be unchanged
        indicators2 = analyzer.indicators
        assert len(indicators2["sma_20"]) == 100  # Original length

    def test_data_property_is_copy(self, analyzer: Analyzer) -> None:
        """Test that data property returns a copy."""
        analyzer.add_sma(20)

        data1 = analyzer.data
        data1["sma_20"] = 0

        # Original should be unchanged
        data2 = analyzer.data
        assert data2["sma_20"].iloc[-1] != 0


class TestAddSMA:
    """Tests for add_sma method."""

    def test_add_sma_default_name(self, analyzer: Analyzer) -> None:
        """Test add_sma with default column name."""
        analyzer.add_sma(20)
        assert "sma_20" in analyzer.indicators
        assert "sma_20" in analyzer.data.columns

    def test_add_sma_custom_name(self, analyzer: Analyzer) -> None:
        """Test add_sma with custom column name."""
        analyzer.add_sma(20, column_name="my_sma")
        assert "my_sma" in analyzer.indicators
        assert "my_sma" in analyzer.data.columns

    def test_add_multiple_sma(self, analyzer: Analyzer) -> None:
        """Test adding multiple SMAs."""
        analyzer.add_sma(20).add_sma(50).add_sma(200)

        assert "sma_20" in analyzer.indicators
        assert "sma_50" in analyzer.indicators
        assert "sma_200" in analyzer.indicators


class TestAddEMA:
    """Tests for add_ema method."""

    def test_add_ema_default_name(self, analyzer: Analyzer) -> None:
        """Test add_ema with default column name."""
        analyzer.add_ema(12)
        assert "ema_12" in analyzer.indicators

    def test_add_ema_custom_name(self, analyzer: Analyzer) -> None:
        """Test add_ema with custom column name."""
        analyzer.add_ema(12, column_name="short_ema")
        assert "short_ema" in analyzer.indicators


class TestAddReturns:
    """Tests for add_returns method."""

    def test_add_returns_default(self, analyzer: Analyzer) -> None:
        """Test add_returns with defaults."""
        analyzer.add_returns()
        assert "returns" in analyzer.indicators

    def test_add_returns_multiple_periods(self, analyzer: Analyzer) -> None:
        """Test add_returns with multiple periods."""
        analyzer.add_returns(periods=5, column_name="returns_5d")
        assert "returns_5d" in analyzer.indicators

    def test_add_log_returns(self, analyzer: Analyzer) -> None:
        """Test add_returns with log returns."""
        analyzer.add_returns(log_returns=True)
        assert "log_returns" in analyzer.indicators


class TestAddVolatility:
    """Tests for add_volatility method."""

    def test_add_volatility_default(self, analyzer: Analyzer) -> None:
        """Test add_volatility with defaults."""
        analyzer.add_volatility()
        assert "volatility" in analyzer.indicators

    def test_add_volatility_custom_window(self, analyzer: Analyzer) -> None:
        """Test add_volatility with custom window."""
        analyzer.add_volatility(window=60, column_name="vol_60d")
        assert "vol_60d" in analyzer.indicators

    def test_add_volatility_auto_calculates_returns(self, analyzer: Analyzer) -> None:
        """Test that add_volatility calculates returns if not present."""
        # Don't add returns first
        analyzer.add_volatility()

        # Volatility should still be calculated
        assert "volatility" in analyzer.indicators
        vol = analyzer.indicators["volatility"]
        assert vol.notna().sum() > 0


class TestAddAllIndicators:
    """Tests for add_all_indicators method."""

    def test_add_all_default(self, analyzer: Analyzer) -> None:
        """Test add_all_indicators with defaults."""
        analyzer.add_all_indicators()

        # Check default SMAs
        assert "sma_20" in analyzer.indicators
        assert "sma_50" in analyzer.indicators
        assert "sma_200" in analyzer.indicators

        # Check default EMAs
        assert "ema_12" in analyzer.indicators
        assert "ema_26" in analyzer.indicators

        # Check returns and volatility
        assert "returns" in analyzer.indicators
        assert "volatility" in analyzer.indicators

    def test_add_all_custom_windows(self, analyzer: Analyzer) -> None:
        """Test add_all_indicators with custom windows."""
        analyzer.add_all_indicators(
            sma_windows=[10, 30],
            ema_windows=[5, 10],
            volatility_window=30,
        )

        assert "sma_10" in analyzer.indicators
        assert "sma_30" in analyzer.indicators
        assert "ema_5" in analyzer.indicators
        assert "ema_10" in analyzer.indicators

        # Default windows should not be present
        assert "sma_20" not in analyzer.indicators


class TestResult:
    """Tests for result method."""

    def test_result_returns_analysis_result(self, analyzer: Analyzer) -> None:
        """Test that result returns AnalysisResult."""
        analyzer.add_sma(20).add_returns()
        result = analyzer.result()

        assert isinstance(result, AnalysisResult)

    def test_result_contains_symbol(self, analyzer: Analyzer) -> None:
        """Test that result contains symbol."""
        result = analyzer.result()
        assert result.symbol == "TEST"

    def test_result_contains_data(self, analyzer: Analyzer) -> None:
        """Test that result contains data."""
        analyzer.add_sma(20)
        result = analyzer.result()

        assert isinstance(result.data, pd.DataFrame)
        assert "sma_20" in result.data.columns

    def test_result_contains_indicators(self, analyzer: Analyzer) -> None:
        """Test that result contains indicators."""
        analyzer.add_sma(20).add_ema(12)
        result = analyzer.result()

        assert "sma_20" in result.indicators
        assert "ema_12" in result.indicators

    def test_result_contains_statistics(self, analyzer: Analyzer) -> None:
        """Test that result contains statistics."""
        analyzer.add_returns().add_volatility()
        result = analyzer.result()

        assert "mean_return" in result.statistics
        assert "std_return" in result.statistics
        assert "avg_volatility" in result.statistics

    def test_result_analyzed_at(self, analyzer: Analyzer) -> None:
        """Test that result has analyzed_at timestamp."""
        result = analyzer.result()
        assert isinstance(result.analyzed_at, datetime)


class TestOriginalDataUnchanged:
    """Tests to verify original data is not modified."""

    def test_original_df_unchanged_after_add_sma(
        self, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test that original DataFrame is unchanged after adding SMA."""
        original_columns = list(sample_ohlcv_data.columns)

        analyzer = Analyzer(sample_ohlcv_data, "TEST")
        analyzer.add_sma(20)

        # Original DataFrame should not have new columns
        assert list(sample_ohlcv_data.columns) == original_columns
        assert "sma_20" not in sample_ohlcv_data.columns

    def test_original_df_unchanged_after_all_operations(
        self, sample_ohlcv_data: pd.DataFrame
    ) -> None:
        """Test that original DataFrame is unchanged after all operations."""
        original_columns = list(sample_ohlcv_data.columns)
        original_values = sample_ohlcv_data["close"].copy()

        analyzer = Analyzer(sample_ohlcv_data, "TEST")
        analyzer.add_all_indicators()
        _ = analyzer.result()

        # Original DataFrame should be completely unchanged
        assert list(sample_ohlcv_data.columns) == original_columns
        assert (sample_ohlcv_data["close"] == original_values).all()


class TestRepr:
    """Tests for __repr__ method."""

    def test_repr(self, analyzer: Analyzer) -> None:
        """Test string representation."""
        analyzer.add_sma(20).add_ema(12)
        repr_str = repr(analyzer)

        assert "Analyzer" in repr_str
        assert "TEST" in repr_str
        assert "sma_20" in repr_str
        assert "ema_12" in repr_str

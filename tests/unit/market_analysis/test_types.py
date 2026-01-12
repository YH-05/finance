"""Tests for market_analysis.types module."""

from datetime import datetime

import pandas as pd
import pytest

from market_analysis.types import (
    AgentOutput,
    AgentOutputMetadata,
    AnalysisOptions,
    AnalysisResult,
    AssetType,
    CacheConfig,
    ChartOptions,
    CorrelationResult,
    DataSource,
    ExportOptions,
    FetchOptions,
    Interval,
    MarketDataResult,
    RetryConfig,
)


class TestDataSource:
    """Tests for DataSource enum."""

    def test_values(self) -> None:
        """Test enum values."""
        assert DataSource.YFINANCE.value == "yfinance"
        assert DataSource.FRED.value == "fred"
        assert DataSource.LOCAL.value == "local"


class TestAssetType:
    """Tests for AssetType enum."""

    def test_values(self) -> None:
        """Test enum values."""
        assert AssetType.STOCK.value == "stock"
        assert AssetType.INDEX.value == "index"
        assert AssetType.FOREX.value == "forex"
        assert AssetType.COMMODITY.value == "commodity"


class TestInterval:
    """Tests for Interval enum."""

    def test_values(self) -> None:
        """Test enum values."""
        assert Interval.DAILY.value == "1d"
        assert Interval.WEEKLY.value == "1wk"
        assert Interval.MONTHLY.value == "1mo"


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter is True

    def test_frozen(self) -> None:
        """Test config is immutable."""
        from dataclasses import FrozenInstanceError

        config = RetryConfig()
        with pytest.raises(FrozenInstanceError):
            config.max_attempts = 5


class TestCacheConfig:
    """Tests for CacheConfig dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.ttl_seconds == 3600
        assert config.max_entries == 1000
        assert config.db_path is None


class TestFetchOptions:
    """Tests for FetchOptions dataclass."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        options = FetchOptions(symbols=["AAPL"])
        assert options.symbols == ["AAPL"]
        assert options.interval == Interval.DAILY
        assert options.source == DataSource.YFINANCE

    def test_optional_fields(self) -> None:
        """Test optional fields."""
        options = FetchOptions(
            symbols=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-12-31",
            use_cache=False,
        )
        assert options.start_date == "2024-01-01"
        assert options.end_date == "2024-12-31"
        assert options.use_cache is False


class TestAnalysisOptions:
    """Tests for AnalysisOptions dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        options = AnalysisOptions()
        assert options.indicators == ["sma", "ema"]
        assert options.window_sizes == [20, 50, 200]
        assert options.include_returns is True
        assert options.annualization_factor == 252


class TestChartOptions:
    """Tests for ChartOptions dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        options = ChartOptions()
        assert options.chart_type == "line"
        assert options.width == 1200
        assert options.height == 600
        assert options.show_volume is True


class TestExportOptions:
    """Tests for ExportOptions dataclass."""

    def test_defaults(self) -> None:
        """Test default values."""
        options = ExportOptions()
        assert options.format == "csv"
        assert options.include_metadata is True


class TestMarketDataResult:
    """Tests for MarketDataResult dataclass."""

    def test_creation(self) -> None:
        """Test result creation."""
        df = pd.DataFrame({"close": [100, 101, 102]})
        result = MarketDataResult(
            symbol="AAPL",
            data=df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
        )
        assert result.symbol == "AAPL"
        assert result.from_cache is False
        assert result.row_count == 3
        assert result.is_empty is False

    def test_empty_result(self) -> None:
        """Test empty result."""
        result = MarketDataResult(
            symbol="AAPL",
            data=pd.DataFrame(),
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
        )
        assert result.is_empty is True
        assert result.row_count == 0


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_creation(self) -> None:
        """Test result creation."""
        df = pd.DataFrame({"close": [100, 101, 102]})
        result = AnalysisResult(
            symbol="AAPL",
            data=df,
            indicators={"sma_20": pd.Series([100, 100.5, 101])},
            statistics={"mean_return": 0.05},
        )
        assert result.symbol == "AAPL"
        assert "sma_20" in result.indicators
        assert result.statistics["mean_return"] == 0.05


class TestCorrelationResult:
    """Tests for CorrelationResult dataclass."""

    def test_creation(self) -> None:
        """Test result creation."""
        corr_df = pd.DataFrame(
            {"AAPL": [1.0, 0.8], "GOOGL": [0.8, 1.0]},
            index=pd.Index(["AAPL", "GOOGL"]),
        )
        result = CorrelationResult(
            symbols=["AAPL", "GOOGL"],
            correlation_matrix=corr_df,
            period="1Y",
        )
        assert result.symbols == ["AAPL", "GOOGL"]
        assert result.method == "pearson"


class TestAgentOutput:
    """Tests for AgentOutput dataclass."""

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        metadata = AgentOutputMetadata(
            generated_at=datetime(2024, 1, 15, 12, 0),
            symbols=["AAPL"],
            period="1Y",
        )
        output = AgentOutput(
            metadata=metadata,
            summary="Test summary",
            data={"key": "value"},
            recommendations=["Buy", "Hold"],
        )

        d = output.to_dict()
        assert d["summary"] == "Test summary"
        assert d["data"] == {"key": "value"}
        assert d["recommendations"] == ["Buy", "Hold"]
        assert d["metadata"]["symbols"] == ["AAPL"]

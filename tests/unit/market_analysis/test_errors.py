"""Tests for market_analysis.errors module."""

from market_analysis.errors import (
    AnalysisError,
    CacheError,
    DataFetchError,
    ErrorCode,
    ExportError,
    MarketAnalysisError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)


class TestMarketAnalysisError:
    """Tests for MarketAnalysisError base class."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = MarketAnalysisError("Test error")
        assert str(error) == "[UNKNOWN] Test error"
        assert error.code == ErrorCode.UNKNOWN
        assert error.details == {}
        assert error.cause is None

    def test_error_with_code(self) -> None:
        """Test error with specific code."""
        error = MarketAnalysisError("Network failure", code=ErrorCode.NETWORK_ERROR)
        assert "[NETWORK_ERROR]" in str(error)
        assert error.code == ErrorCode.NETWORK_ERROR

    def test_error_with_details(self) -> None:
        """Test error with details."""
        error = MarketAnalysisError(
            "Test error",
            details={"symbol": "AAPL", "count": 10},
        )
        assert "symbol='AAPL'" in str(error)
        assert "count=10" in str(error)

    def test_error_with_cause(self) -> None:
        """Test error with cause chain."""
        original = ValueError("Original error")
        error = MarketAnalysisError("Wrapped error", cause=original)
        assert "Caused by: ValueError" in str(error)
        assert error.cause is original

    def test_to_dict(self) -> None:
        """Test serialization to dict."""
        error = MarketAnalysisError(
            "Test error",
            code=ErrorCode.API_ERROR,
            details={"key": "value"},
        )
        d = error.to_dict()
        assert d["error_type"] == "MarketAnalysisError"
        assert d["code"] == "API_ERROR"
        assert d["message"] == "Test error"
        assert d["details"] == {"key": "value"}


class TestDataFetchError:
    """Tests for DataFetchError."""

    def test_basic_fetch_error(self) -> None:
        """Test basic fetch error."""
        error = DataFetchError("Failed to fetch")
        assert error.code == ErrorCode.API_ERROR

    def test_fetch_error_with_symbol(self) -> None:
        """Test fetch error with symbol."""
        error = DataFetchError(
            "Failed to fetch AAPL",
            symbol="AAPL",
            source="yfinance",
        )
        assert error.symbol == "AAPL"
        assert error.source == "yfinance"
        assert "symbol='AAPL'" in str(error)


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error(self) -> None:
        """Test validation error."""
        error = ValidationError(
            "Invalid date range",
            field="start_date",
            value="2024-13-45",
        )
        assert error.code == ErrorCode.INVALID_PARAMETER
        assert error.field == "start_date"
        assert error.value == "2024-13-45"

    def test_validation_error_with_code(self) -> None:
        """Test validation error with specific code."""
        error = ValidationError(
            "Invalid symbol",
            code=ErrorCode.INVALID_SYMBOL,
        )
        assert error.code == ErrorCode.INVALID_SYMBOL


class TestAnalysisError:
    """Tests for AnalysisError."""

    def test_analysis_error(self) -> None:
        """Test analysis error."""
        error = AnalysisError(
            "Insufficient data",
            symbol="AAPL",
            indicator="sma_200",
        )
        assert error.code == ErrorCode.ANALYSIS_ERROR
        assert error.symbol == "AAPL"
        assert error.indicator == "sma_200"


class TestExportError:
    """Tests for ExportError."""

    def test_export_error(self) -> None:
        """Test export error."""
        error = ExportError(
            "Failed to write file",
            format="csv",
            path="/data/output.csv",
        )
        assert error.code == ErrorCode.EXPORT_ERROR
        assert error.format == "csv"
        assert error.path == "/data/output.csv"


class TestCacheError:
    """Tests for CacheError."""

    def test_cache_error(self) -> None:
        """Test cache error."""
        error = CacheError(
            "Cache read failed",
            operation="get",
            key="test_key",
        )
        assert error.code == ErrorCode.CACHE_ERROR
        assert error.operation == "get"
        assert error.key == "test_key"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_rate_limit_error(self) -> None:
        """Test rate limit error."""
        error = RateLimitError(
            "Rate limit exceeded",
            retry_after=60,
            source="yfinance",
        )
        assert error.code == ErrorCode.RATE_LIMIT
        assert error.retry_after == 60
        assert "retry_after_seconds=60" in str(error)


class TestTimeoutError:
    """Tests for TimeoutError."""

    def test_timeout_error(self) -> None:
        """Test timeout error."""
        error = TimeoutError(
            "Operation timed out",
            timeout_seconds=30.0,
            operation="fetch_data",
        )
        assert error.code == ErrorCode.TIMEOUT
        assert error.timeout_seconds == 30.0
        assert error.operation == "fetch_data"

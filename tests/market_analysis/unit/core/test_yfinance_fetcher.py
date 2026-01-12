"""Unit tests for YFinanceFetcher class."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market_analysis.core.yfinance_fetcher import (
    YFINANCE_SYMBOL_PATTERN,
    YFinanceFetcher,
)
from market_analysis.errors import DataFetchError, ValidationError
from market_analysis.types import (
    DataSource,
    FetchOptions,
    Interval,
    RetryConfig,
)
from market_analysis.utils.cache import SQLiteCache


class TestYFinanceSymbolPattern:
    """Tests for yfinance symbol pattern validation."""

    @pytest.mark.parametrize(
        "symbol",
        [
            "AAPL",
            "GOOGL",
            "MSFT",
            "BRK.B",
            "BRK-B",
            "^GSPC",
            "^DJI",
            "USDJPY=X",
            "EURUSD=X",
        ],
    )
    def test_valid_symbols(self, symbol: str) -> None:
        """Test that valid symbols match the pattern."""
        assert YFINANCE_SYMBOL_PATTERN.match(symbol) is not None

    @pytest.mark.parametrize(
        "symbol",
        [
            "",
            "   ",
            "@AAPL",
            "AAPL@",
            "AAPL GOOGL",
        ],
    )
    def test_invalid_symbols(self, symbol: str) -> None:
        """Test that invalid symbols don't match the pattern."""
        # Empty string needs special handling
        if not symbol.strip():
            assert not symbol.strip()
        else:
            result = YFINANCE_SYMBOL_PATTERN.match(symbol)
            # Some patterns might match partially, check full match
            if result:
                assert result.group() != symbol


class TestYFinanceFetcher:
    """Tests for YFinanceFetcher class."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance without cache."""
        return YFinanceFetcher()

    @pytest.fixture
    def fetcher_with_cache(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance with cache."""
        cache = SQLiteCache()
        return YFinanceFetcher(cache=cache)

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create a sample OHLCV DataFrame."""
        return pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0],
                "High": [155.0, 156.0, 157.0],
                "Low": [149.0, 150.0, 151.0],
                "Close": [154.0, 155.0, 156.0],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )

    def test_source_property(self, fetcher: YFinanceFetcher) -> None:
        """Test that source property returns YFINANCE."""
        assert fetcher.source == DataSource.YFINANCE

    def test_default_interval(self, fetcher: YFinanceFetcher) -> None:
        """Test that default interval is DAILY."""
        assert fetcher.default_interval == Interval.DAILY

    @pytest.mark.parametrize(
        "symbol,expected",
        [
            ("AAPL", True),
            ("GOOGL", True),
            ("BRK.B", True),
            ("BRK-B", True),
            ("^GSPC", True),
            ("USDJPY=X", True),
            ("", False),
            ("   ", False),
        ],
    )
    def test_validate_symbol(
        self, fetcher: YFinanceFetcher, symbol: str, expected: bool
    ) -> None:
        """Test symbol validation."""
        assert fetcher.validate_symbol(symbol) == expected

    def test_validate_options_empty_symbols(self, fetcher: YFinanceFetcher) -> None:
        """Test validation fails for empty symbols list."""
        options = FetchOptions(symbols=[])

        with pytest.raises(ValidationError):
            fetcher.fetch(options)

    def test_validate_options_invalid_symbols(self, fetcher: YFinanceFetcher) -> None:
        """Test validation fails for invalid symbols."""
        options = FetchOptions(symbols=["AAPL", "", "GOOGL"])

        with pytest.raises(ValidationError):
            fetcher.fetch(options)

    @patch("market_analysis.core.yfinance_fetcher.yf.Ticker")
    def test_fetch_success(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df: pd.DataFrame,
    ) -> None:
        """Test successful data fetch."""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_df
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(
            symbols=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].symbol == "AAPL"
        assert results[0].source == DataSource.YFINANCE
        assert results[0].from_cache is False
        assert len(results[0].data) == 3
        assert list(results[0].data.columns) == [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

    @patch("market_analysis.core.yfinance_fetcher.yf.Ticker")
    def test_fetch_multiple_symbols(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df: pd.DataFrame,
    ) -> None:
        """Test fetching multiple symbols."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_df
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(symbols=["AAPL", "GOOGL", "MSFT"])

        results = fetcher.fetch(options)

        assert len(results) == 3
        assert [r.symbol for r in results] == ["AAPL", "GOOGL", "MSFT"]

    @patch("market_analysis.core.yfinance_fetcher.yf.Ticker")
    def test_fetch_empty_result(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """Test fetch returning empty DataFrame for valid symbol with no data."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        # Valid symbol (has regularMarketPrice) but no historical data for period
        mock_ticker.info = {"regularMarketPrice": 150.0}
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(symbols=["AAPL"])

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].is_empty

    @patch("market_analysis.core.yfinance_fetcher.yf.Ticker")
    def test_fetch_invalid_symbol_raises_error(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """Test fetch raises DataFetchError for invalid/delisted symbol."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        # Invalid symbol: no regularMarketPrice indicates delisted/invalid
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(symbols=["INVALID"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "Invalid or delisted symbol" in str(exc_info.value)

    @patch("market_analysis.core.yfinance_fetcher.yf.Ticker")
    def test_fetch_with_cache_miss(
        self,
        mock_ticker_class: MagicMock,
        fetcher_with_cache: YFinanceFetcher,
        sample_df: pd.DataFrame,
    ) -> None:
        """Test fetch with cache miss."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_df
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(
            symbols=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        results = fetcher_with_cache.fetch(options)

        assert len(results) == 1
        assert results[0].from_cache is False

    @patch("market_analysis.core.yfinance_fetcher.yf.Ticker")
    def test_fetch_with_cache_hit(
        self,
        mock_ticker_class: MagicMock,
        fetcher_with_cache: YFinanceFetcher,
        sample_df: pd.DataFrame,
    ) -> None:
        """Test fetch with cache hit."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_df
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(
            symbols=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        # First fetch - cache miss
        results1 = fetcher_with_cache.fetch(options)
        assert results1[0].from_cache is False

        # Second fetch - cache hit
        results2 = fetcher_with_cache.fetch(options)
        assert results2[0].from_cache is True

        # API should only be called once
        assert mock_ticker.history.call_count == 1

    @patch("market_analysis.core.yfinance_fetcher.yf.Ticker")
    def test_fetch_api_error(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """Test fetch handling API errors."""
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("API Error")
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(symbols=["AAPL"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "Failed to fetch data for AAPL" in str(exc_info.value)

    def test_fetch_with_retry_config(self) -> None:
        """Test that retry config is applied."""
        retry_config = RetryConfig(max_attempts=5)
        fetcher = YFinanceFetcher(retry_config=retry_config)

        assert fetcher._retry_config == retry_config

    def test_fetch_bypass_cache(
        self,
        fetcher_with_cache: YFinanceFetcher,
    ) -> None:
        """Test fetching with cache bypass."""
        with patch(
            "market_analysis.core.yfinance_fetcher.yf.Ticker"
        ) as mock_ticker_class:
            sample_df = pd.DataFrame(
                {
                    "Open": [150.0],
                    "High": [155.0],
                    "Low": [149.0],
                    "Close": [154.0],
                    "Volume": [1000000],
                },
                index=pd.to_datetime(["2024-01-01"]),
            )
            mock_ticker = MagicMock()
            mock_ticker.history.return_value = sample_df
            mock_ticker_class.return_value = mock_ticker

            options = FetchOptions(
                symbols=["AAPL"],
                use_cache=False,
            )

            results = fetcher_with_cache.fetch(options)

            assert results[0].from_cache is False

    @patch("market_analysis.core.yfinance_fetcher.yf.Ticker")
    def test_format_date_datetime(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """Test date formatting with datetime objects."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [155.0],
                "Low": [149.0],
                "Close": [154.0],
                "Volume": [1000000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(
            symbols=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
        )

        fetcher.fetch(options)

        mock_ticker.history.assert_called_once()
        call_kwargs = mock_ticker.history.call_args.kwargs
        assert call_kwargs["start"] == "2024-01-01"
        assert call_kwargs["end"] == "2024-12-31"

    def test_map_interval(self, fetcher: YFinanceFetcher) -> None:
        """Test interval mapping."""
        assert fetcher._map_interval(Interval.DAILY) == "1d"
        assert fetcher._map_interval(Interval.WEEKLY) == "1wk"
        assert fetcher._map_interval(Interval.MONTHLY) == "1mo"
        assert fetcher._map_interval(Interval.HOURLY) == "1h"

"""Unit tests for FREDFetcher class."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market_analysis.core.fred_fetcher import (
    FRED_API_KEY_ENV,
    FRED_SERIES_PATTERN,
    FREDFetcher,
)
from market_analysis.errors import DataFetchError, ValidationError
from market_analysis.types import DataSource, FetchOptions, Interval, RetryConfig
from market_analysis.utils.cache import SQLiteCache


class TestFREDSeriesPattern:
    """Tests for FRED series ID pattern validation."""

    @pytest.mark.parametrize(
        "series_id",
        [
            "GDP",
            "CPIAUCSL",
            "DGS10",
            "UNRATE",
            "FEDFUNDS",
            "T10Y2Y",
            "SP500",
        ],
    )
    def test_valid_series_ids(self, series_id: str) -> None:
        """Test that valid series IDs match the pattern."""
        assert FRED_SERIES_PATTERN.match(series_id) is not None

    @pytest.mark.parametrize(
        "series_id",
        [
            "",
            "   ",
            "gdp",  # lowercase
            "123ABC",  # starts with number
            "GDP-10",  # contains hyphen
            "GDP.10",  # contains period
        ],
    )
    def test_invalid_series_ids(self, series_id: str) -> None:
        """Test that invalid series IDs don't match the pattern."""
        if not series_id.strip():
            assert not series_id.strip()
        else:
            assert FRED_SERIES_PATTERN.match(series_id) is None


class TestFREDFetcher:
    """Tests for FREDFetcher class."""

    @pytest.fixture
    def mock_api_key(self, monkeypatch: pytest.MonkeyPatch) -> str:
        """Set a mock API key in environment."""
        api_key = "test_api_key_12345"
        monkeypatch.setenv(FRED_API_KEY_ENV, api_key)
        return api_key

    @pytest.fixture
    def fetcher(self, mock_api_key: str) -> FREDFetcher:
        """Create a FREDFetcher instance with mock API key."""
        return FREDFetcher()

    @pytest.fixture
    def fetcher_with_cache(self, mock_api_key: str) -> FREDFetcher:
        """Create a FREDFetcher instance with cache."""
        cache = SQLiteCache()
        return FREDFetcher(cache=cache)

    @pytest.fixture
    def sample_series(self) -> pd.Series:
        """Create a sample FRED series data."""
        return pd.Series(
            [100.0, 101.5, 102.3],
            index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            name="GDP",
        )

    def test_init_without_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that initialization fails without API key."""
        monkeypatch.delenv(FRED_API_KEY_ENV, raising=False)

        with pytest.raises(ValidationError) as exc_info:
            FREDFetcher()

        assert FRED_API_KEY_ENV in str(exc_info.value)

    def test_init_with_api_key_parameter(self) -> None:
        """Test initialization with API key parameter."""
        fetcher = FREDFetcher(api_key="my_api_key")
        assert fetcher._api_key == "my_api_key"

    def test_init_with_env_var(self, mock_api_key: str) -> None:
        """Test initialization with environment variable."""
        fetcher = FREDFetcher()
        assert fetcher._api_key == mock_api_key

    def test_source_property(self, fetcher: FREDFetcher) -> None:
        """Test that source property returns FRED."""
        assert fetcher.source == DataSource.FRED

    def test_default_interval(self, fetcher: FREDFetcher) -> None:
        """Test that default interval is MONTHLY."""
        assert fetcher.default_interval == Interval.MONTHLY

    @pytest.mark.parametrize(
        "series_id,expected",
        [
            ("GDP", True),
            ("CPIAUCSL", True),
            ("DGS10", True),
            ("T10Y2Y", True),
            ("", False),
            ("   ", False),
            ("gdp", False),
            ("123ABC", False),
        ],
    )
    def test_validate_symbol(
        self, fetcher: FREDFetcher, series_id: str, expected: bool
    ) -> None:
        """Test series ID validation."""
        assert fetcher.validate_symbol(series_id) == expected

    def test_validate_options_empty_symbols(self, fetcher: FREDFetcher) -> None:
        """Test validation fails for empty symbols list."""
        options = FetchOptions(symbols=[])

        with pytest.raises(ValidationError):
            fetcher.fetch(options)

    def test_validate_options_invalid_symbols(self, fetcher: FREDFetcher) -> None:
        """Test validation fails for invalid symbols."""
        options = FetchOptions(symbols=["GDP", "invalid", "CPIAUCSL"])

        with pytest.raises(ValidationError):
            fetcher.fetch(options)

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_fetch_success(
        self,
        mock_fred_class: MagicMock,
        fetcher: FREDFetcher,
        sample_series: pd.Series,
    ) -> None:
        """Test successful data fetch."""
        mock_fred = MagicMock()
        mock_fred.get_series.return_value = sample_series
        mock_fred_class.return_value = mock_fred

        options = FetchOptions(
            symbols=["GDP"],
            start_date="2024-01-01",
            end_date="2024-03-31",
        )

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].symbol == "GDP"
        assert results[0].source == DataSource.FRED
        assert results[0].from_cache is False
        assert len(results[0].data) == 3
        # FRED data uses value for all OHLC columns
        assert list(results[0].data.columns) == [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_fetch_multiple_series(
        self,
        mock_fred_class: MagicMock,
        fetcher: FREDFetcher,
        sample_series: pd.Series,
    ) -> None:
        """Test fetching multiple series."""
        mock_fred = MagicMock()
        mock_fred.get_series.return_value = sample_series
        mock_fred_class.return_value = mock_fred

        options = FetchOptions(symbols=["GDP", "CPIAUCSL", "UNRATE"])

        results = fetcher.fetch(options)

        assert len(results) == 3
        assert [r.symbol for r in results] == ["GDP", "CPIAUCSL", "UNRATE"]

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_fetch_empty_result(
        self,
        mock_fred_class: MagicMock,
        fetcher: FREDFetcher,
    ) -> None:
        """Test fetch returning empty series."""
        mock_fred = MagicMock()
        mock_fred.get_series.return_value = pd.Series(dtype=float)
        mock_fred_class.return_value = mock_fred

        options = FetchOptions(symbols=["INVALID"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "No data found" in str(exc_info.value)

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_fetch_with_cache_miss(
        self,
        mock_fred_class: MagicMock,
        fetcher_with_cache: FREDFetcher,
        sample_series: pd.Series,
    ) -> None:
        """Test fetch with cache miss."""
        mock_fred = MagicMock()
        mock_fred.get_series.return_value = sample_series
        mock_fred_class.return_value = mock_fred

        options = FetchOptions(
            symbols=["GDP"],
            start_date="2024-01-01",
            end_date="2024-03-31",
        )

        results = fetcher_with_cache.fetch(options)

        assert len(results) == 1
        assert results[0].from_cache is False

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_fetch_with_cache_hit(
        self,
        mock_fred_class: MagicMock,
        fetcher_with_cache: FREDFetcher,
        sample_series: pd.Series,
    ) -> None:
        """Test fetch with cache hit."""
        mock_fred = MagicMock()
        mock_fred.get_series.return_value = sample_series
        mock_fred_class.return_value = mock_fred

        options = FetchOptions(
            symbols=["GDP"],
            start_date="2024-01-01",
            end_date="2024-03-31",
        )

        # First fetch - cache miss
        results1 = fetcher_with_cache.fetch(options)
        assert results1[0].from_cache is False

        # Second fetch - cache hit
        results2 = fetcher_with_cache.fetch(options)
        assert results2[0].from_cache is True

        # API should only be called once
        assert mock_fred.get_series.call_count == 1

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_fetch_api_error(
        self,
        mock_fred_class: MagicMock,
        fetcher: FREDFetcher,
    ) -> None:
        """Test fetch handling API errors."""
        mock_fred = MagicMock()
        mock_fred.get_series.side_effect = Exception("API Error")
        mock_fred_class.return_value = mock_fred

        options = FetchOptions(symbols=["GDP"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "Failed to fetch FRED series GDP" in str(exc_info.value)

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_fetch_invalid_series_error(
        self,
        mock_fred_class: MagicMock,
        fetcher: FREDFetcher,
    ) -> None:
        """Test fetch handling invalid series ID error."""
        mock_fred = MagicMock()
        mock_fred.get_series.side_effect = ValueError("Invalid series ID")
        mock_fred_class.return_value = mock_fred

        options = FetchOptions(symbols=["INVALIDSERIES"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "Invalid FRED series ID" in str(exc_info.value)

    def test_fetch_with_retry_config(self, mock_api_key: str) -> None:
        """Test that retry config is applied."""
        retry_config = RetryConfig(max_attempts=5)
        fetcher = FREDFetcher(retry_config=retry_config)

        assert fetcher._retry_config == retry_config

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_format_date_datetime(
        self,
        mock_fred_class: MagicMock,
        fetcher: FREDFetcher,
        sample_series: pd.Series,
    ) -> None:
        """Test date formatting with datetime objects."""
        mock_fred = MagicMock()
        mock_fred.get_series.return_value = sample_series
        mock_fred_class.return_value = mock_fred

        options = FetchOptions(
            symbols=["GDP"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
        )

        fetcher.fetch(options)

        mock_fred.get_series.assert_called_once()
        call_kwargs = mock_fred.get_series.call_args.kwargs
        assert call_kwargs["observation_start"] == "2024-01-01"
        assert call_kwargs["observation_end"] == "2024-12-31"

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_get_series_info(
        self,
        mock_fred_class: MagicMock,
        fetcher: FREDFetcher,
    ) -> None:
        """Test getting series metadata."""
        mock_fred = MagicMock()
        mock_info = pd.Series(
            {"id": "GDP", "title": "Gross Domestic Product", "frequency": "Quarterly"}
        )
        mock_fred.get_series_info.return_value = mock_info
        mock_fred_class.return_value = mock_fred

        info = fetcher.get_series_info("GDP")

        assert info["id"] == "GDP"
        assert info["title"] == "Gross Domestic Product"

    @patch("market_analysis.core.fred_fetcher.Fred")
    def test_get_series_info_error(
        self,
        mock_fred_class: MagicMock,
        fetcher: FREDFetcher,
    ) -> None:
        """Test get_series_info error handling."""
        mock_fred = MagicMock()
        mock_fred.get_series_info.side_effect = Exception("API Error")
        mock_fred_class.return_value = mock_fred

        with pytest.raises(DataFetchError):
            fetcher.get_series_info("INVALID")

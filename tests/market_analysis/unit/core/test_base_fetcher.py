"""Unit tests for BaseDataFetcher abstract class."""

from datetime import datetime

import pandas as pd
import pytest

from market_analysis.core.base_fetcher import STANDARD_COLUMNS, BaseDataFetcher
from market_analysis.errors import ValidationError
from market_analysis.types import DataSource, FetchOptions, Interval, MarketDataResult


class ConcreteFetcher(BaseDataFetcher):
    """Concrete implementation of BaseDataFetcher for testing."""

    @property
    def source(self) -> DataSource:
        """Return YFINANCE as the data source."""
        return DataSource.YFINANCE

    def fetch(self, options: FetchOptions) -> list[MarketDataResult]:
        """Mock fetch implementation."""
        self._validate_options(options)
        results = []
        for symbol in options.symbols:
            df = pd.DataFrame(
                {
                    "open": [100.0, 101.0],
                    "high": [105.0, 106.0],
                    "low": [99.0, 100.0],
                    "close": [104.0, 105.0],
                    "volume": [1000000, 1100000],
                },
                index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
            )
            results.append(self._create_result(symbol, df))
        return results

    def validate_symbol(self, symbol: str) -> bool:
        """Validate that symbol is non-empty and alphanumeric."""
        return bool(symbol and symbol.replace(".", "").replace("-", "").isalnum())


class TestBaseDataFetcher:
    """Tests for BaseDataFetcher abstract class."""

    @pytest.fixture
    def fetcher(self) -> ConcreteFetcher:
        """Create a concrete fetcher for testing."""
        return ConcreteFetcher()

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create a sample DataFrame for normalization tests."""
        return pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [105.0, 106.0],
                "Low": [99.0, 100.0],
                "Close": [104.0, 105.0],
                "Volume": [1000000, 1100000],
            },
            index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
        )

    def test_source_property(self, fetcher: ConcreteFetcher) -> None:
        """Test that source property returns correct value."""
        assert fetcher.source == DataSource.YFINANCE

    def test_default_interval_property(self, fetcher: ConcreteFetcher) -> None:
        """Test that default_interval returns DAILY."""
        assert fetcher.default_interval == Interval.DAILY

    def test_validate_symbol_valid(self, fetcher: ConcreteFetcher) -> None:
        """Test validation of valid symbols."""
        assert fetcher.validate_symbol("AAPL") is True
        assert fetcher.validate_symbol("GOOGL") is True
        assert fetcher.validate_symbol("BRK.B") is True
        assert fetcher.validate_symbol("BRK-B") is True

    def test_validate_symbol_invalid(self, fetcher: ConcreteFetcher) -> None:
        """Test validation of invalid symbols."""
        assert fetcher.validate_symbol("") is False
        assert fetcher.validate_symbol("   ") is False

    def test_normalize_dataframe_standard(
        self, fetcher: ConcreteFetcher, sample_df: pd.DataFrame
    ) -> None:
        """Test normalization of standard DataFrame."""
        normalized = fetcher.normalize_dataframe(sample_df, "AAPL")

        assert list(normalized.columns) == STANDARD_COLUMNS
        assert len(normalized) == 2
        assert normalized["close"].iloc[0] == 104.0

    def test_normalize_dataframe_empty(self, fetcher: ConcreteFetcher) -> None:
        """Test normalization of empty DataFrame."""
        empty_df = pd.DataFrame()
        normalized = fetcher.normalize_dataframe(empty_df, "AAPL")

        assert list(normalized.columns) == STANDARD_COLUMNS
        assert len(normalized) == 0

    def test_normalize_dataframe_adj_close(self, fetcher: ConcreteFetcher) -> None:
        """Test normalization with Adj Close column."""
        df = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [99.0],
                "Adj Close": [104.0],
                "Volume": [1000000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        normalized = fetcher.normalize_dataframe(df, "AAPL")

        assert "close" in normalized.columns
        assert normalized["close"].iloc[0] == 104.0

    def test_normalize_dataframe_missing_volume(self, fetcher: ConcreteFetcher) -> None:
        """Test normalization when volume is missing."""
        df = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [99.0],
                "Close": [104.0],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        normalized = fetcher.normalize_dataframe(df, "AAPL")

        assert "volume" in normalized.columns
        assert pd.isna(normalized["volume"].iloc[0])

    def test_normalize_dataframe_sorted_by_date(self, fetcher: ConcreteFetcher) -> None:
        """Test that normalized DataFrame is sorted by date."""
        df = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [105.0, 106.0, 107.0],
                "Low": [99.0, 100.0, 101.0],
                "Close": [104.0, 105.0, 106.0],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=pd.to_datetime(["2024-01-03", "2024-01-01", "2024-01-02"]),
        )
        normalized = fetcher.normalize_dataframe(df, "AAPL")

        assert normalized.index[0] == pd.Timestamp("2024-01-01")
        assert normalized.index[1] == pd.Timestamp("2024-01-02")
        assert normalized.index[2] == pd.Timestamp("2024-01-03")

    def test_validate_options_empty_symbols(self, fetcher: ConcreteFetcher) -> None:
        """Test validation fails for empty symbols list."""
        options = FetchOptions(symbols=[])

        with pytest.raises(ValidationError) as exc_info:
            fetcher._validate_options(options)

        assert "At least one symbol must be provided" in str(exc_info.value)

    def test_validate_options_invalid_symbols(self, fetcher: ConcreteFetcher) -> None:
        """Test validation fails for invalid symbols."""
        options = FetchOptions(symbols=["AAPL", "", "GOOGL"])

        with pytest.raises(ValidationError) as exc_info:
            fetcher._validate_options(options)

        assert "Invalid symbols" in str(exc_info.value)

    def test_validate_options_valid(self, fetcher: ConcreteFetcher) -> None:
        """Test validation passes for valid options."""
        options = FetchOptions(
            symbols=["AAPL", "GOOGL"],
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        # Should not raise
        fetcher._validate_options(options)

    def test_create_result(self, fetcher: ConcreteFetcher) -> None:
        """Test creation of MarketDataResult."""
        df = pd.DataFrame(
            {
                "open": [100.0],
                "high": [105.0],
                "low": [99.0],
                "close": [104.0],
                "volume": [1000000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )

        result = fetcher._create_result(
            symbol="AAPL",
            data=df,
            from_cache=True,
            metadata={"extra": "info"},
        )

        assert result.symbol == "AAPL"
        assert result.source == DataSource.YFINANCE
        assert result.from_cache is True
        assert result.metadata == {"extra": "info"}
        assert result.row_count == 1
        assert isinstance(result.fetched_at, datetime)

    def test_fetch_returns_results(self, fetcher: ConcreteFetcher) -> None:
        """Test that fetch returns results for valid options."""
        options = FetchOptions(symbols=["AAPL", "GOOGL"])

        results = fetcher.fetch(options)

        assert len(results) == 2
        assert results[0].symbol == "AAPL"
        assert results[1].symbol == "GOOGL"
        assert all(isinstance(r, MarketDataResult) for r in results)


class TestStandardColumns:
    """Tests for STANDARD_COLUMNS constant."""

    def test_standard_columns_content(self) -> None:
        """Test that STANDARD_COLUMNS contains expected values."""
        assert STANDARD_COLUMNS == ["open", "high", "low", "close", "volume"]

    def test_standard_columns_immutable(self) -> None:
        """Test that STANDARD_COLUMNS is a list."""
        assert isinstance(STANDARD_COLUMNS, list)
        assert len(STANDARD_COLUMNS) == 5

"""Unit tests for mock fetcher classes."""

from datetime import datetime

import pandas as pd
import pytest

from market_analysis.core.mock_fetchers import (
    MockBloombergFetcher,
    MockFactSetFetcher,
    generate_mock_constituents,
    generate_mock_financial_data,
    generate_mock_ohlcv,
)
from market_analysis.types import (
    DataSource,
    FetchOptions,
    IdentifierType,
    Interval,
)


class TestGenerateMockOHLCV:
    """Tests for generate_mock_ohlcv function."""

    def test_generates_dataframe(self) -> None:
        """Test that function generates a DataFrame."""
        df = generate_mock_ohlcv("TEST")
        assert isinstance(df, pd.DataFrame)

    def test_has_ohlcv_columns(self) -> None:
        """Test that DataFrame has OHLCV columns."""
        df = generate_mock_ohlcv("TEST")
        expected_columns = ["open", "high", "low", "close", "volume"]
        assert list(df.columns) == expected_columns

    def test_has_datetime_index(self) -> None:
        """Test that DataFrame has DatetimeIndex."""
        df = generate_mock_ohlcv("TEST")
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_respects_date_range(self) -> None:
        """Test that DataFrame respects date range."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        df = generate_mock_ohlcv("TEST", start_date=start, end_date=end)

        # Cast index min/max to Timestamp for comparison
        min_date = pd.Timestamp(df.index.min())  # type: ignore[arg-type]
        max_date = pd.Timestamp(df.index.max())  # type: ignore[arg-type]
        assert min_date >= pd.Timestamp(start)
        assert max_date <= pd.Timestamp(end)

    def test_reproducible_with_seed(self) -> None:
        """Test that same seed produces same data."""
        df1 = generate_mock_ohlcv("TEST", seed=42)
        df2 = generate_mock_ohlcv("TEST", seed=42)

        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_different_data(self) -> None:
        """Test that different seeds produce different data."""
        df1 = generate_mock_ohlcv("TEST", seed=42)
        df2 = generate_mock_ohlcv("TEST", seed=123)

        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(df1, df2)

    def test_high_greater_than_low(self) -> None:
        """Test that high is always greater than low."""
        df = generate_mock_ohlcv("TEST", seed=42)
        assert (df["high"] >= df["low"]).all()

    @pytest.mark.parametrize(
        "interval",
        [Interval.DAILY, Interval.WEEKLY, Interval.MONTHLY],
    )
    def test_different_intervals(self, interval: Interval) -> None:
        """Test that different intervals produce data."""
        df = generate_mock_ohlcv("TEST", interval=interval)
        assert not df.empty

    def test_empty_date_range(self) -> None:
        """Test that empty date range returns empty DataFrame."""
        df = generate_mock_ohlcv(
            "TEST",
            start_date="2024-01-02",
            end_date="2024-01-01",
        )
        assert df.empty


class TestGenerateMockFinancialData:
    """Tests for generate_mock_financial_data function."""

    def test_generates_dataframe(self) -> None:
        """Test that function generates a DataFrame."""
        df = generate_mock_financial_data(
            symbols=["AAPL", "MSFT"],
            fields=["PX_LAST", "PE_RATIO"],
        )
        assert isinstance(df, pd.DataFrame)

    def test_has_correct_columns(self) -> None:
        """Test that DataFrame has correct field columns."""
        fields = ["PX_LAST", "PE_RATIO", "DIVIDEND_YIELD"]
        df = generate_mock_financial_data(
            symbols=["AAPL"],
            fields=fields,
        )
        assert list(df.columns) == fields

    def test_has_correct_index(self) -> None:
        """Test that DataFrame has correct symbol index."""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        df = generate_mock_financial_data(
            symbols=symbols,
            fields=["PX_LAST"],
        )
        assert list(df.index) == symbols

    def test_reproducible_with_seed(self) -> None:
        """Test that same seed produces same data."""
        df1 = generate_mock_financial_data(
            symbols=["AAPL"],
            fields=["PX_LAST"],
            seed=42,
        )
        df2 = generate_mock_financial_data(
            symbols=["AAPL"],
            fields=["PX_LAST"],
            seed=42,
        )
        pd.testing.assert_frame_equal(df1, df2)


class TestGenerateMockConstituents:
    """Tests for generate_mock_constituents function."""

    def test_generates_dataframe(self) -> None:
        """Test that function generates a DataFrame."""
        df = generate_mock_constituents("TEST_INDEX")
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self) -> None:
        """Test that DataFrame has required columns."""
        df = generate_mock_constituents("TEST_INDEX")
        required_columns = [
            "date",
            "P_SYMBOL",
            "SEDOL",
            "Asset ID",
            "FG_COMPANY_NAME",
            "GICS Sector",
            "GICS Industry Group",
            "Weight (%)",
            "Universe",
        ]
        for col in required_columns:
            assert col in df.columns

    def test_weights_sum_to_100(self) -> None:
        """Test that weights sum to approximately 100 per date."""
        df = generate_mock_constituents("TEST_INDEX", n_constituents=50)

        for _, group in df.groupby("date"):
            total_weight = group["Weight (%)"].sum()
            assert abs(total_weight - 100.0) < 0.01

    def test_correct_number_of_constituents(self) -> None:
        """Test that correct number of constituents generated."""
        n = 30
        df = generate_mock_constituents("TEST_INDEX", n_constituents=n)

        per_date_counts = df.groupby("date").size()
        assert all(count == n for count in per_date_counts)

    def test_reproducible_with_seed(self) -> None:
        """Test that same seed produces same data."""
        # Use fixed dates to ensure reproducibility
        df1 = generate_mock_constituents(
            "TEST",
            seed=42,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
        df2 = generate_mock_constituents(
            "TEST",
            seed=42,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )
        pd.testing.assert_frame_equal(df1, df2)


class TestMockBloombergFetcher:
    """Tests for MockBloombergFetcher class."""

    @pytest.fixture
    def fetcher(self) -> MockBloombergFetcher:
        """Create a MockBloombergFetcher instance."""
        return MockBloombergFetcher(seed=42)

    def test_source_property(self, fetcher: MockBloombergFetcher) -> None:
        """Test that source property returns BLOOMBERG."""
        assert fetcher.source == DataSource.BLOOMBERG

    def test_default_interval(self, fetcher: MockBloombergFetcher) -> None:
        """Test that default interval is DAILY."""
        assert fetcher.default_interval == Interval.DAILY

    @pytest.mark.parametrize(
        "symbol,expected",
        [
            ("AAPL US Equity", True),
            ("7203 JP Equity", True),
            ("SPX Index", True),
            ("AAPL", False),
            ("AAPL-US", False),
            ("", False),
        ],
    )
    def test_validate_symbol(
        self, fetcher: MockBloombergFetcher, symbol: str, expected: bool
    ) -> None:
        """Test symbol validation."""
        assert fetcher.validate_symbol(symbol) == expected

    def test_fetch_returns_results(self, fetcher: MockBloombergFetcher) -> None:
        """Test that fetch returns results."""
        options = FetchOptions(symbols=["AAPL US Equity"])
        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].symbol == "AAPL US Equity"
        assert not results[0].is_empty

    def test_fetch_multiple_symbols(self, fetcher: MockBloombergFetcher) -> None:
        """Test fetching multiple symbols."""
        options = FetchOptions(
            symbols=["AAPL US Equity", "MSFT US Equity", "GOOGL US Equity"]
        )
        results = fetcher.fetch(options)

        assert len(results) == 3
        for result in results:
            assert not result.is_empty

    def test_fetch_with_date_range(self, fetcher: MockBloombergFetcher) -> None:
        """Test fetching with date range."""
        options = FetchOptions(
            symbols=["AAPL US Equity"],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        results = fetcher.fetch(options)

        assert len(results) == 1
        df = results[0].data
        # Cast index min/max to Timestamp for comparison
        min_date = pd.Timestamp(df.index.min())  # type: ignore[arg-type]
        max_date = pd.Timestamp(df.index.max())  # type: ignore[arg-type]
        assert min_date >= pd.Timestamp("2024-01-01")
        assert max_date <= pd.Timestamp("2024-01-31")

    def test_fetch_financial(self, fetcher: MockBloombergFetcher) -> None:
        """Test fetching financial data."""
        df = fetcher.fetch_financial(
            symbols=["AAPL US Equity", "MSFT US Equity"],
            fields=["PX_LAST", "PE_RATIO"],
        )

        assert len(df) == 2
        assert "PX_LAST" in df.columns
        assert "PE_RATIO" in df.columns

    def test_session_context_manager(self, fetcher: MockBloombergFetcher) -> None:
        """Test mock session context manager."""
        with fetcher.session() as sess:
            assert sess is None

    def test_convert_identifier(self) -> None:
        """Test convert_identifier passthrough."""
        result = MockBloombergFetcher.convert_identifier(
            "US0378331005", IdentifierType.ISIN
        )
        assert result == "/isin/US0378331005"

    def test_reproducible_results(self) -> None:
        """Test that same seed produces same results."""
        fetcher1 = MockBloombergFetcher(seed=42)
        fetcher2 = MockBloombergFetcher(seed=42)

        options = FetchOptions(symbols=["AAPL US Equity"])

        results1 = fetcher1.fetch(options)
        results2 = fetcher2.fetch(options)

        pd.testing.assert_frame_equal(results1[0].data, results2[0].data)


class TestMockFactSetFetcher:
    """Tests for MockFactSetFetcher class."""

    @pytest.fixture
    def fetcher(self) -> MockFactSetFetcher:
        """Create a MockFactSetFetcher instance."""
        return MockFactSetFetcher(seed=42)

    def test_source_property(self, fetcher: MockFactSetFetcher) -> None:
        """Test that source property returns FACTSET."""
        assert fetcher.source == DataSource.FACTSET

    def test_default_interval(self, fetcher: MockFactSetFetcher) -> None:
        """Test that default interval is DAILY."""
        assert fetcher.default_interval == Interval.DAILY

    @pytest.mark.parametrize(
        "symbol,expected",
        [
            ("AAPL-US", True),
            ("7203-JP", True),
            ("VOD-GB", True),
            ("AAPL", False),
            ("AAPL US Equity", False),
            ("", False),
        ],
    )
    def test_validate_symbol(
        self, fetcher: MockFactSetFetcher, symbol: str, expected: bool
    ) -> None:
        """Test symbol validation."""
        assert fetcher.validate_symbol(symbol) == expected

    def test_fetch_returns_results(self, fetcher: MockFactSetFetcher) -> None:
        """Test that fetch returns results."""
        options = FetchOptions(symbols=["AAPL-US"])
        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].symbol == "AAPL-US"
        assert not results[0].is_empty

    def test_fetch_multiple_symbols(self, fetcher: MockFactSetFetcher) -> None:
        """Test fetching multiple symbols."""
        options = FetchOptions(symbols=["AAPL-US", "MSFT-US", "GOOGL-US"])
        results = fetcher.fetch(options)

        assert len(results) == 3
        for result in results:
            assert not result.is_empty

    def test_load_constituents(self, fetcher: MockFactSetFetcher) -> None:
        """Test loading mock constituents."""
        df = fetcher.load_constituents("M_US500")

        assert len(df) > 0
        assert "P_SYMBOL" in df.columns
        assert "Weight (%)" in df.columns
        assert "GICS Sector" in df.columns

    def test_load_constituents_with_dates(self, fetcher: MockFactSetFetcher) -> None:
        """Test loading constituents with date filter."""
        df = fetcher.load_constituents(
            "M_US500",
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        assert len(df) > 0

    def test_load_financial_data(self, fetcher: MockFactSetFetcher) -> None:
        """Test loading mock financial data."""
        df = fetcher.load_financial_data(["FF_ROIC", "FF_ROE"])

        assert len(df) > 0
        assert "date" in df.columns
        assert "P_SYMBOL" in df.columns
        assert "FF_ROIC" in df.columns
        assert "FF_ROE" in df.columns

    def test_reproducible_results(self) -> None:
        """Test that same seed produces same results."""
        fetcher1 = MockFactSetFetcher(seed=42)
        fetcher2 = MockFactSetFetcher(seed=42)

        options = FetchOptions(symbols=["AAPL-US"])

        results1 = fetcher1.fetch(options)
        results2 = fetcher2.fetch(options)

        pd.testing.assert_frame_equal(results1[0].data, results2[0].data)

    def test_custom_n_constituents(self) -> None:
        """Test that n_constituents parameter works."""
        fetcher = MockFactSetFetcher(n_constituents=100, seed=42)
        df = fetcher.load_constituents("M_US500")

        per_date_counts = df.groupby("date").size()
        assert all(count == 100 for count in per_date_counts)


class TestMockFetcherIntegration:
    """Integration tests for mock fetchers with DataFetcherFactory."""

    def test_factory_creates_mock_bloomberg(self) -> None:
        """Test that factory creates MockBloombergFetcher."""
        from market_analysis.core import DataFetcherFactory

        fetcher = DataFetcherFactory.create("mock_bloomberg", seed=42)
        assert isinstance(fetcher, MockBloombergFetcher)
        assert fetcher.source == DataSource.BLOOMBERG

    def test_factory_creates_mock_factset(self) -> None:
        """Test that factory creates MockFactSetFetcher."""
        from market_analysis.core import DataFetcherFactory

        fetcher = DataFetcherFactory.create("mock_factset", seed=42)
        assert isinstance(fetcher, MockFactSetFetcher)
        assert fetcher.source == DataSource.FACTSET

    def test_supported_sources_includes_mocks(self) -> None:
        """Test that supported sources includes mock fetchers."""
        from market_analysis.core import DataFetcherFactory

        sources = DataFetcherFactory.get_supported_sources()
        assert "mock_bloomberg" in sources
        assert "mock_factset" in sources

    def test_supported_sources_can_exclude_mocks(self) -> None:
        """Test that mock fetchers can be excluded."""
        from market_analysis.core import DataFetcherFactory

        sources = DataFetcherFactory.get_supported_sources(include_mock=False)
        assert "mock_bloomberg" not in sources
        assert "mock_factset" not in sources
        assert "yfinance" in sources

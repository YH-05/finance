"""Unit tests for BloombergFetcher class."""

from datetime import datetime

import pytest

from market_analysis.core.bloomberg_fetcher import (
    BLOOMBERG_EQUITY_PATTERN,
    BLOOMBERG_NON_EQUITY_PATTERN,
    BloombergFetcher,
    _is_valid_bloomberg_symbol,
)
from market_analysis.errors import DataFetchError
from market_analysis.types import (
    DataSource,
    FetchOptions,
    IdentifierType,
    Interval,
)


class TestBloombergSymbolPattern:
    """Tests for Bloomberg symbol pattern validation."""

    @pytest.mark.parametrize(
        "symbol",
        [
            "AAPL US Equity",
            "IBM US Equity",
            "7203 JP Equity",
        ],
    )
    def test_valid_equity_symbols(self, symbol: str) -> None:
        """Test that valid Equity symbols match the pattern."""
        assert BLOOMBERG_EQUITY_PATTERN.match(symbol) is not None

    @pytest.mark.parametrize(
        "symbol",
        [
            "SPX Index",
            "USDJPY Curncy",
            "CLF4 Comdty",
            "T 5 Govt",
        ],
    )
    def test_valid_non_equity_symbols(self, symbol: str) -> None:
        """Test that valid non-Equity symbols match the pattern."""
        assert BLOOMBERG_NON_EQUITY_PATTERN.match(symbol) is not None

    @pytest.mark.parametrize(
        "symbol",
        [
            "AAPL US Equity",
            "IBM US Equity",
            "7203 JP Equity",
            "SPX Index",
            "USDJPY Curncy",
            "CLF4 Comdty",
            "T 5 Govt",
        ],
    )
    def test_valid_symbols_with_helper(self, symbol: str) -> None:
        """Test that all valid symbols pass the helper function."""
        assert _is_valid_bloomberg_symbol(symbol) is True

    @pytest.mark.parametrize(
        "symbol",
        [
            "",
            "   ",
            "AAPL",  # Missing exchange and asset class
            "AAPL US",  # Missing asset class
            "AAPL Equity",  # Missing country code for Equity
            "AAPL-US",  # Wrong format (FactSet style)
        ],
    )
    def test_invalid_symbols(self, symbol: str) -> None:
        """Test that invalid symbols don't pass validation."""
        assert _is_valid_bloomberg_symbol(symbol.strip()) is False


class TestBloombergFetcher:
    """Tests for BloombergFetcher class."""

    @pytest.fixture
    def fetcher(self) -> BloombergFetcher:
        """Create a BloombergFetcher instance."""
        return BloombergFetcher()

    def test_source_property(self, fetcher: BloombergFetcher) -> None:
        """Test that source property returns BLOOMBERG."""
        assert fetcher.source == DataSource.BLOOMBERG

    def test_default_interval(self, fetcher: BloombergFetcher) -> None:
        """Test that default interval is DAILY."""
        assert fetcher.default_interval == Interval.DAILY

    @pytest.mark.parametrize(
        "symbol,expected",
        [
            ("AAPL US Equity", True),
            ("7203 JP Equity", True),
            ("SPX Index", True),
            ("USDJPY Curncy", True),
            ("AAPL", False),
            ("", False),
            ("   ", False),
            ("AAPL-US", False),  # FactSet style
        ],
    )
    def test_validate_symbol(
        self, fetcher: BloombergFetcher, symbol: str, expected: bool
    ) -> None:
        """Test symbol validation."""
        assert fetcher.validate_symbol(symbol) == expected

    def test_format_date_none(self, fetcher: BloombergFetcher) -> None:
        """Test date formatting with None input."""
        assert fetcher._format_date(None) is None

    def test_format_date_datetime(self, fetcher: BloombergFetcher) -> None:
        """Test date formatting with datetime input."""
        date = datetime(2024, 1, 15)
        assert fetcher._format_date(date) == "20240115"

    def test_format_date_string(self, fetcher: BloombergFetcher) -> None:
        """Test date formatting with string input."""
        assert fetcher._format_date("2024-01-15") == "20240115"

    @pytest.mark.parametrize(
        "interval,expected",
        [
            (Interval.DAILY, "DAILY"),
            (Interval.WEEKLY, "WEEKLY"),
            (Interval.MONTHLY, "MONTHLY"),
            (Interval.HOURLY, "DAILY"),  # Falls back to DAILY
        ],
    )
    def test_map_interval(
        self, fetcher: BloombergFetcher, interval: Interval, expected: str
    ) -> None:
        """Test interval mapping to Bloomberg format."""
        assert fetcher._map_interval(interval) == expected

    def test_convert_identifier_sedol(self) -> None:
        """Test SEDOL identifier conversion."""
        result = BloombergFetcher.convert_identifier("2046251", IdentifierType.SEDOL)
        assert result == "/sedol/2046251"

    def test_convert_identifier_cusip(self) -> None:
        """Test CUSIP identifier conversion."""
        result = BloombergFetcher.convert_identifier("037833100", IdentifierType.CUSIP)
        assert result == "/cusip/037833100"

    def test_convert_identifier_isin(self) -> None:
        """Test ISIN identifier conversion."""
        result = BloombergFetcher.convert_identifier(
            "US0378331005", IdentifierType.ISIN
        )
        assert result == "/isin/US0378331005"

    def test_convert_identifier_figi(self) -> None:
        """Test FIGI identifier conversion."""
        result = BloombergFetcher.convert_identifier(
            "BBG000B9XRY4", IdentifierType.FIGI
        )
        assert result == "/bbgid/BBG000B9XRY4"

    def test_convert_identifier_ticker(self) -> None:
        """Test ticker identifier (no conversion)."""
        result = BloombergFetcher.convert_identifier("AAPL", IdentifierType.TICKER)
        assert result == "AAPL"


class TestBloombergFetcherWithoutAPI:
    """Tests for BloombergFetcher when Bloomberg API is not available."""

    @pytest.fixture(autouse=True)
    def set_bloomberg_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch BLOOMBERG_AVAILABLE at module level."""
        import market_analysis.core.bloomberg_fetcher as bf

        monkeypatch.setattr(bf, "BLOOMBERG_AVAILABLE", False)

    def test_fetch_without_api_raises_error(self) -> None:
        """Test that fetch raises error when Bloomberg is not available."""
        fetcher = BloombergFetcher()
        options = FetchOptions(
            symbols=["AAPL US Equity"],
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "Bloomberg is not available" in str(exc_info.value)

    def test_session_without_api_raises_error(self) -> None:
        """Test that session raises error when Bloomberg is not available."""
        fetcher = BloombergFetcher()

        with pytest.raises(DataFetchError) as exc_info, fetcher.session():
            pass

        assert "Bloomberg is not available" in str(exc_info.value)


class TestBloombergFetcherValidation:
    """Tests for BloombergFetcher validation."""

    @pytest.fixture
    def fetcher(self) -> BloombergFetcher:
        """Create a BloombergFetcher instance."""
        return BloombergFetcher()

    def test_validate_options_empty_symbols_raises(
        self, fetcher: BloombergFetcher
    ) -> None:
        """Test that empty symbols list raises ValidationError."""
        from market_analysis.errors import ValidationError

        options = FetchOptions(symbols=[])

        with pytest.raises(ValidationError) as exc_info:
            fetcher._validate_options(options)

        assert "At least one symbol must be provided" in str(exc_info.value)

    def test_validate_options_invalid_symbols_raises(
        self, fetcher: BloombergFetcher
    ) -> None:
        """Test that invalid symbols raise ValidationError."""
        from market_analysis.errors import ValidationError

        options = FetchOptions(symbols=["INVALID"])

        with pytest.raises(ValidationError) as exc_info:
            fetcher._validate_options(options)

        assert "Invalid symbols" in str(exc_info.value)

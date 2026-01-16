"""Unit tests for FactSetFetcher class."""

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from market_analysis.core.factset_fetcher import (
    FACTSET_SYMBOL_PATTERN,
    FactSetFetcher,
)
from market_analysis.errors import DataFetchError
from market_analysis.types import (
    DataSource,
    FetchOptions,
    Interval,
)


class TestFactSetSymbolPattern:
    """Tests for FactSet symbol pattern validation."""

    @pytest.mark.parametrize(
        "symbol",
        [
            "AAPL-US",
            "MSFT-US",
            "7203-JP",
            "VOD-GB",
            "SAP-DE",
            "MOCK001-US",
        ],
    )
    def test_valid_symbols(self, symbol: str) -> None:
        """Test that valid FactSet symbols match the pattern."""
        assert FACTSET_SYMBOL_PATTERN.match(symbol) is not None

    @pytest.mark.parametrize(
        "symbol",
        [
            "",
            "   ",
            "AAPL",  # Missing country code
            "AAPL US Equity",  # Bloomberg style
            "AAPL-USA",  # Country code too long
            "AAPL_US",  # Wrong separator
        ],
    )
    def test_invalid_symbols(self, symbol: str) -> None:
        """Test that invalid symbols don't match the pattern."""
        result = (
            FACTSET_SYMBOL_PATTERN.match(symbol.strip()) if symbol.strip() else None
        )
        assert result is None


class TestFactSetFetcher:
    """Tests for FactSetFetcher class."""

    @pytest.fixture
    def fetcher(self) -> FactSetFetcher:
        """Create a FactSetFetcher instance without data dir."""
        return FactSetFetcher()

    @pytest.fixture
    def temp_data_dir(self, tmp_path: Path) -> Path:
        """Create a temporary data directory with sample files."""
        data_dir = tmp_path / "factset_data"
        data_dir.mkdir()
        return data_dir

    @pytest.fixture
    def temp_db(self, tmp_path: Path) -> Path:
        """Create a temporary SQLite database with sample data."""
        db_path = tmp_path / "factset.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create FG_PRICE table
        cursor.execute("""
            CREATE TABLE FG_PRICE (
                date TEXT,
                P_SYMBOL TEXT,
                variable TEXT,
                value REAL
            )
        """)

        # Insert sample data
        sample_data = [
            ("2024-01-01", "AAPL-US", "FG_PRICE", 150.0),
            ("2024-01-02", "AAPL-US", "FG_PRICE", 152.0),
            ("2024-01-03", "AAPL-US", "FG_PRICE", 151.0),
        ]

        cursor.executemany(
            "INSERT INTO FG_PRICE (date, P_SYMBOL, variable, value) VALUES (?, ?, ?, ?)",
            sample_data,
        )

        # Create sample universe table
        cursor.execute("""
            CREATE TABLE M_US500 (
                date TEXT,
                P_SYMBOL TEXT,
                SEDOL TEXT,
                "Asset ID" TEXT,
                FG_COMPANY_NAME TEXT,
                "GICS Sector" TEXT,
                "GICS Industry Group" TEXT,
                "Weight (%)" REAL
            )
        """)

        cursor.execute("""
            INSERT INTO M_US500 VALUES
            ('2024-01-31', 'AAPL-US', 'SEDOL01', 'ASSET01', 'Apple Inc',
             'Information Technology', 'Technology Hardware', 5.5)
        """)

        conn.commit()
        conn.close()

        return db_path

    def test_source_property(self, fetcher: FactSetFetcher) -> None:
        """Test that source property returns FACTSET."""
        assert fetcher.source == DataSource.FACTSET

    def test_default_interval(self, fetcher: FactSetFetcher) -> None:
        """Test that default interval is DAILY."""
        assert fetcher.default_interval == Interval.DAILY

    @pytest.mark.parametrize(
        "symbol,expected",
        [
            ("AAPL-US", True),
            ("7203-JP", True),
            ("VOD-GB", True),
            ("AAPL", False),
            ("AAPL US Equity", False),  # Bloomberg style
            ("", False),
            ("   ", False),
        ],
    )
    def test_validate_symbol(
        self, fetcher: FactSetFetcher, symbol: str, expected: bool
    ) -> None:
        """Test symbol validation."""
        assert fetcher.validate_symbol(symbol) == expected

    def test_format_date_none(self, fetcher: FactSetFetcher) -> None:
        """Test date formatting with None input."""
        assert fetcher._format_date(None) is None

    def test_format_date_datetime(self, fetcher: FactSetFetcher) -> None:
        """Test date formatting with datetime input."""
        date = datetime(2024, 1, 15)
        assert fetcher._format_date(date) == "2024-01-15"

    def test_format_date_string(self, fetcher: FactSetFetcher) -> None:
        """Test date formatting with string input."""
        assert fetcher._format_date("2024-01-15") == "2024-01-15"

    def test_fetch_without_data_source_raises(self, fetcher: FactSetFetcher) -> None:
        """Test that fetch raises error when no data source is configured."""
        options = FetchOptions(symbols=["AAPL-US"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "No data source configured" in str(exc_info.value)

    def test_fetch_from_database(self, temp_db: Path) -> None:
        """Test fetching data from database."""
        fetcher = FactSetFetcher(db_path=temp_db)
        options = FetchOptions(symbols=["AAPL-US"])

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].symbol == "AAPL-US"
        assert not results[0].is_empty
        assert results[0].source == DataSource.FACTSET

    def test_load_constituents_from_db(self, temp_db: Path) -> None:
        """Test loading constituents from database."""
        fetcher = FactSetFetcher(db_path=temp_db)

        df = fetcher.load_constituents("M_US500")

        assert len(df) > 0
        assert "P_SYMBOL" in df.columns
        assert "Weight (%)" in df.columns
        assert "GICS Sector" in df.columns

    def test_load_constituents_with_date_filter(self, temp_db: Path) -> None:
        """Test loading constituents with date filter."""
        fetcher = FactSetFetcher(db_path=temp_db)

        df = fetcher.load_constituents(
            "M_US500",
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        assert len(df) > 0

    def test_load_financial_data_no_db_raises(self, fetcher: FactSetFetcher) -> None:
        """Test that load_financial_data raises error when no db configured."""
        with pytest.raises(DataFetchError) as exc_info:
            fetcher.load_financial_data(["FF_ROIC", "FF_ROE"])

        assert "Database path not configured" in str(exc_info.value)

    def test_database_connection_context_manager(self, temp_db: Path) -> None:
        """Test database connection context manager."""
        fetcher = FactSetFetcher(db_path=temp_db)

        with fetcher.database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM FG_PRICE")
            count = cursor.fetchone()[0]
            assert count > 0

    def test_database_connection_without_path_raises(
        self, fetcher: FactSetFetcher
    ) -> None:
        """Test that database connection raises error when no path configured."""
        with (
            pytest.raises(DataFetchError) as exc_info,
            fetcher.database_connection(),
        ):
            pass

        assert "No database path configured" in str(exc_info.value)


class TestFactSetFetcherValidation:
    """Tests for FactSetFetcher validation."""

    @pytest.fixture
    def fetcher(self) -> FactSetFetcher:
        """Create a FactSetFetcher instance."""
        return FactSetFetcher()

    def test_validate_options_empty_symbols_raises(
        self, fetcher: FactSetFetcher
    ) -> None:
        """Test that empty symbols list raises ValidationError."""
        from market_analysis.errors import ValidationError

        options = FetchOptions(symbols=[])

        with pytest.raises(ValidationError) as exc_info:
            fetcher._validate_options(options)

        assert "At least one symbol must be provided" in str(exc_info.value)

    def test_validate_options_invalid_symbols_raises(
        self, fetcher: FactSetFetcher
    ) -> None:
        """Test that invalid symbols raise ValidationError."""
        from market_analysis.errors import ValidationError

        options = FetchOptions(symbols=["INVALID"])

        with pytest.raises(ValidationError) as exc_info:
            fetcher._validate_options(options)

        assert "Invalid symbols" in str(exc_info.value)


class TestFactSetFetcherFromFiles:
    """Tests for FactSetFetcher file-based fetching."""

    @pytest.fixture
    def temp_dir_with_data(self, tmp_path: Path) -> Path:
        """Create temporary directory with parquet files."""
        data_dir = tmp_path / "factset_data"
        data_dir.mkdir()

        # Create sample price data
        price_data = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
                "P_SYMBOL": ["TEST-US"] * 3,
                "value": [100.0, 101.0, 102.0],
            }
        )
        price_data.to_parquet(data_dir / "Price_2024.parquet")

        return data_dir

    def test_fetch_from_files(self, temp_dir_with_data: Path) -> None:
        """Test fetching data from parquet files."""
        fetcher = FactSetFetcher(data_dir=temp_dir_with_data)
        options = FetchOptions(symbols=["TEST-US"])

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].symbol == "TEST-US"

    def test_fetch_symbol_not_found_in_files(self, temp_dir_with_data: Path) -> None:
        """Test fetching a symbol that doesn't exist in files."""
        fetcher = FactSetFetcher(data_dir=temp_dir_with_data)
        options = FetchOptions(symbols=["NOTFOUND-US"])

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].symbol == "NOTFOUND-US"
        assert results[0].is_empty

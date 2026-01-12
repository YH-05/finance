"""Unit tests for DataExporter class."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from market_analysis.errors import ExportError
from market_analysis.export.exporter import DataExporter
from market_analysis.types import (
    AgentOutput,
    AnalysisResult,
    DataSource,
    MarketDataResult,
)


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, 30)
    prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "open": prices * (1 + np.random.uniform(-0.01, 0.01, 30)),
            "high": prices * (1 + np.random.uniform(0, 0.02, 30)),
            "low": prices * (1 - np.random.uniform(0, 0.02, 30)),
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, 30),
        },
        index=dates,
    )


@pytest.fixture
def market_data_result(sample_ohlcv_data: pd.DataFrame) -> MarketDataResult:
    """Create a MarketDataResult for testing."""
    return MarketDataResult(
        symbol="AAPL",
        data=sample_ohlcv_data,
        source=DataSource.YFINANCE,
        fetched_at=datetime(2024, 1, 31, 12, 0, 0),
        from_cache=False,
        metadata={"info": "test"},
    )


@pytest.fixture
def analysis_result(sample_ohlcv_data: pd.DataFrame) -> AnalysisResult:
    """Create an AnalysisResult for testing."""
    sma_series = pd.Series(sample_ohlcv_data["close"].rolling(20).mean())
    return AnalysisResult(
        symbol="AAPL",
        data=sample_ohlcv_data,
        indicators={"sma_20": sma_series},
        statistics={"mean_return": 0.05, "std_return": 0.02},
        analyzed_at=datetime(2024, 1, 31, 12, 0, 0),
    )


@pytest.fixture
def exporter(market_data_result: MarketDataResult) -> DataExporter:
    """Create a DataExporter for testing."""
    return DataExporter(market_data_result)


@pytest.fixture
def analysis_exporter(analysis_result: AnalysisResult) -> DataExporter:
    """Create a DataExporter with AnalysisResult for testing."""
    return DataExporter(analysis_result)


class TestDataExporterInitialization:
    """Tests for DataExporter initialization."""

    def test_init_with_market_data_result(
        self, market_data_result: MarketDataResult
    ) -> None:
        """Test initialization with MarketDataResult."""
        exporter = DataExporter(market_data_result)
        assert exporter.symbol == "AAPL"
        assert exporter.result is market_data_result

    def test_init_with_analysis_result(self, analysis_result: AnalysisResult) -> None:
        """Test initialization with AnalysisResult."""
        exporter = DataExporter(analysis_result)
        assert exporter.symbol == "AAPL"
        assert exporter.result is analysis_result

    def test_init_custom_date_format(
        self, market_data_result: MarketDataResult
    ) -> None:
        """Test initialization with custom date format."""
        exporter = DataExporter(market_data_result, date_format="%d/%m/%Y")
        assert exporter._date_format == "%d/%m/%Y"

    def test_data_property(self, exporter: DataExporter) -> None:
        """Test data property returns DataFrame."""
        data = exporter.data
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 30


class TestToJson:
    """Tests for to_json method."""

    def test_to_json_returns_string(self, exporter: DataExporter) -> None:
        """Test that to_json returns a JSON string."""
        result = exporter.to_json()
        assert isinstance(result, str)

        parsed = json.loads(result)
        assert "symbol" in parsed
        assert parsed["symbol"] == "AAPL"

    def test_to_json_contains_data(self, exporter: DataExporter) -> None:
        """Test that JSON contains data array."""
        result = exporter.to_json()
        parsed = json.loads(result)

        assert "data" in parsed
        assert len(parsed["data"]) == 30
        assert "close" in parsed["data"][0]

    def test_to_json_with_metadata(self, exporter: DataExporter) -> None:
        """Test that JSON includes metadata when requested."""
        result = exporter.to_json(include_metadata=True)
        parsed = json.loads(result)

        assert "row_count" in parsed
        assert "columns" in parsed
        assert "source" in parsed
        assert parsed["source"] == "yfinance"

    def test_to_json_without_metadata(self, exporter: DataExporter) -> None:
        """Test that JSON excludes metadata when not requested."""
        result = exporter.to_json(include_metadata=False)
        parsed = json.loads(result)

        assert "symbol" in parsed
        assert "data" in parsed
        assert "row_count" not in parsed

    def test_to_json_writes_file(self, exporter: DataExporter, temp_dir: Path) -> None:
        """Test that to_json writes to file."""
        output_path = temp_dir / "output.json"
        result = exporter.to_json(output_path=output_path)

        assert output_path.exists()
        file_content = output_path.read_text(encoding="utf-8")
        assert result == file_content

    def test_to_json_creates_parent_dirs(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """Test that to_json creates parent directories."""
        output_path = temp_dir / "nested" / "dir" / "output.json"
        exporter.to_json(output_path=output_path)

        assert output_path.exists()

    def test_to_json_custom_indent(self, exporter: DataExporter) -> None:
        """Test that to_json respects indent parameter."""
        result_indent_2 = exporter.to_json(indent=2)
        result_indent_4 = exporter.to_json(indent=4)

        assert len(result_indent_4) > len(result_indent_2)

    def test_to_json_analysis_result(self, analysis_exporter: DataExporter) -> None:
        """Test to_json with AnalysisResult."""
        result = analysis_exporter.to_json()
        parsed = json.loads(result)

        assert "analyzed_at" in parsed
        assert "statistics" in parsed
        assert "indicator_names" in parsed


class TestToCsv:
    """Tests for to_csv method."""

    def test_to_csv_returns_string(self, exporter: DataExporter) -> None:
        """Test that to_csv returns a CSV string."""
        result = exporter.to_csv()
        assert isinstance(result, str)
        assert "close" in result

    def test_to_csv_contains_all_rows(self, exporter: DataExporter) -> None:
        """Test that CSV contains all data rows."""
        result = exporter.to_csv()
        lines = result.strip().split("\n")

        assert len(lines) == 31  # Header + 30 data rows

    def test_to_csv_date_format(self, exporter: DataExporter) -> None:
        """Test that CSV uses correct date format."""
        result = exporter.to_csv(date_format="%Y/%m/%d")
        assert "2024/01/01" in result

    def test_to_csv_writes_file(self, exporter: DataExporter, temp_dir: Path) -> None:
        """Test that to_csv writes to file."""
        output_path = temp_dir / "output.csv"
        result = exporter.to_csv(output_path=output_path)

        assert output_path.exists()
        file_content = output_path.read_text(encoding="utf-8")
        assert result == file_content

    def test_to_csv_include_index(self, exporter: DataExporter) -> None:
        """Test that CSV includes date index."""
        result = exporter.to_csv(include_index=True)
        assert "date" in result.lower()
        assert "2024-01-01" in result


class TestToSqlite:
    """Tests for to_sqlite method."""

    def test_to_sqlite_creates_table(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """Test that to_sqlite creates table."""
        db_path = temp_dir / "test.db"
        rows = exporter.to_sqlite(db_path)

        assert rows == 30
        assert db_path.exists()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "market_data_aapl" in tables

    def test_to_sqlite_custom_table_name(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """Test to_sqlite with custom table name."""
        db_path = temp_dir / "test.db"
        exporter.to_sqlite(db_path, table_name="custom_table")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "custom_table" in tables

    def test_to_sqlite_upsert(self, exporter: DataExporter, temp_dir: Path) -> None:
        """Test that to_sqlite performs UPSERT correctly."""
        db_path = temp_dir / "test.db"

        rows1 = exporter.to_sqlite(db_path, if_exists="upsert")
        rows2 = exporter.to_sqlite(db_path, if_exists="upsert")

        assert rows1 == 30
        assert rows2 == 30

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM market_data_aapl")
            count = cursor.fetchone()[0]
            assert count == 30

    def test_to_sqlite_replace(self, exporter: DataExporter, temp_dir: Path) -> None:
        """Test to_sqlite with replace mode."""
        db_path = temp_dir / "test.db"

        exporter.to_sqlite(db_path, if_exists="replace")
        exporter.to_sqlite(db_path, if_exists="replace")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM market_data_aapl")
            count = cursor.fetchone()[0]
            assert count == 30

    def test_to_sqlite_append(self, exporter: DataExporter, temp_dir: Path) -> None:
        """Test to_sqlite with append mode."""
        db_path = temp_dir / "test.db"

        exporter.to_sqlite(db_path, if_exists="replace")
        exporter.to_sqlite(db_path, if_exists="append")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM market_data_aapl")
            count = cursor.fetchone()[0]
            assert count == 60

    def test_to_sqlite_adds_metadata_columns(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """Test that to_sqlite adds symbol and updated_at columns."""
        db_path = temp_dir / "test.db"
        exporter.to_sqlite(db_path)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(market_data_aapl)")
            columns = [row[1] for row in cursor.fetchall()]
            assert "symbol" in columns
            assert "updated_at" in columns


class TestToAgentJson:
    """Tests for to_agent_json method."""

    def test_to_agent_json_returns_agent_output(self, exporter: DataExporter) -> None:
        """Test that to_agent_json returns AgentOutput."""
        result = exporter.to_agent_json()
        assert isinstance(result, AgentOutput)

    def test_to_agent_json_metadata(self, exporter: DataExporter) -> None:
        """Test that AgentOutput contains metadata."""
        result = exporter.to_agent_json()

        assert result.metadata.version == "1.0"
        assert result.metadata.symbols == ["AAPL"]
        assert "2024-01-01" in result.metadata.period

    def test_to_agent_json_summary(self, exporter: DataExporter) -> None:
        """Test that AgentOutput contains summary."""
        result = exporter.to_agent_json()

        assert "AAPL" in result.summary
        assert "30 data points" in result.summary

    def test_to_agent_json_data_structure(self, exporter: DataExporter) -> None:
        """Test that AgentOutput contains structured data."""
        result = exporter.to_agent_json()

        assert "symbol" in result.data
        assert "row_count" in result.data
        assert "latest" in result.data
        assert "price_stats" in result.data

    def test_to_agent_json_recommendations(self, exporter: DataExporter) -> None:
        """Test that AgentOutput contains recommendations."""
        result = exporter.to_agent_json(include_recommendations=True)
        assert isinstance(result.recommendations, list)

    def test_to_agent_json_no_recommendations(self, exporter: DataExporter) -> None:
        """Test that recommendations can be disabled."""
        result = exporter.to_agent_json(include_recommendations=False)
        assert result.recommendations == []

    def test_to_agent_json_writes_file(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """Test that to_agent_json writes to file."""
        output_path = temp_dir / "agent_output.json"
        _result = exporter.to_agent_json(output_path=output_path)

        assert output_path.exists()
        file_content = json.loads(output_path.read_text(encoding="utf-8"))
        assert file_content["metadata"]["symbols"] == ["AAPL"]
        assert _result is not None

    def test_to_agent_json_to_dict(self, exporter: DataExporter) -> None:
        """Test AgentOutput.to_dict method."""
        result = exporter.to_agent_json()
        dict_output = result.to_dict()

        assert isinstance(dict_output, dict)
        assert "metadata" in dict_output
        assert "summary" in dict_output
        assert "data" in dict_output

    def test_to_agent_json_analysis_result(
        self, analysis_exporter: DataExporter
    ) -> None:
        """Test to_agent_json with AnalysisResult."""
        result = analysis_exporter.to_agent_json()

        assert "statistics" in result.data
        assert "indicators" in result.data


class TestErrorHandling:
    """Tests for error handling."""

    def test_to_json_invalid_path_raises_error(self, exporter: DataExporter) -> None:
        """Test that invalid path raises ExportError."""
        with pytest.raises(ExportError) as exc_info:
            exporter.to_json(output_path="/nonexistent/path/file.json")

        assert exc_info.value.format == "json"
        assert "EXPORT_ERROR" in str(exc_info.value.code)

    def test_to_csv_invalid_path_raises_error(self, exporter: DataExporter) -> None:
        """Test that invalid path raises ExportError."""
        with pytest.raises(ExportError) as exc_info:
            exporter.to_csv(output_path="/nonexistent/path/file.csv")

        assert exc_info.value.format == "csv"

    def test_to_sqlite_invalid_path_raises_error(self, exporter: DataExporter) -> None:
        """Test that invalid path raises ExportError."""
        with pytest.raises(ExportError) as exc_info:
            exporter.to_sqlite("/nonexistent/path/file.db")

        assert exc_info.value.format == "sqlite"


class TestEmptyData:
    """Tests with empty data."""

    @pytest.fixture
    def empty_result(self) -> MarketDataResult:
        """Create a MarketDataResult with empty data."""
        empty_df = pd.DataFrame()
        empty_df["open"] = pd.Series(dtype=float)
        empty_df["high"] = pd.Series(dtype=float)
        empty_df["low"] = pd.Series(dtype=float)
        empty_df["close"] = pd.Series(dtype=float)
        empty_df["volume"] = pd.Series(dtype=int)
        return MarketDataResult(
            symbol="EMPTY",
            data=empty_df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
        )

    def test_to_json_empty_data(self, empty_result: MarketDataResult) -> None:
        """Test to_json with empty data."""
        exporter = DataExporter(empty_result)
        result = exporter.to_json()
        parsed = json.loads(result)

        assert parsed["data"] == []
        assert parsed["row_count"] == 0

    def test_to_csv_empty_data(self, empty_result: MarketDataResult) -> None:
        """Test to_csv with empty data."""
        exporter = DataExporter(empty_result)
        result = exporter.to_csv()

        lines = result.strip().split("\n")
        assert len(lines) == 1

    def test_to_agent_json_empty_data(self, empty_result: MarketDataResult) -> None:
        """Test to_agent_json with empty data."""
        exporter = DataExporter(empty_result)
        result = exporter.to_agent_json()

        assert "No data available" in result.recommendations[0]


class TestSpecialCharacterSymbols:
    """Tests with special character symbols like ^GSPC."""

    @pytest.fixture
    def index_result(self, sample_ohlcv_data: pd.DataFrame) -> MarketDataResult:
        """Create a MarketDataResult for an index symbol."""
        return MarketDataResult(
            symbol="^GSPC",
            data=sample_ohlcv_data,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
        )

    def test_to_sqlite_special_symbol(
        self, index_result: MarketDataResult, temp_dir: Path
    ) -> None:
        """Test to_sqlite with special character symbol."""
        exporter = DataExporter(index_result)
        db_path = temp_dir / "test.db"
        rows = exporter.to_sqlite(db_path)

        assert rows == 30

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "market_data__gspc" in tables

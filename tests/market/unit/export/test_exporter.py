"""Unit tests for DataExporter class in market package.

This module tests the DataExporter class which exports market data
to various formats including JSON, CSV, SQLite, and AI agent-optimized JSON.

Note: These tests are designed to fail initially (Red phase of TDD)
as the market package implementation does not exist yet.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from market.errors import ExportError
from market.export.exporter import DataExporter
from market.types import (
    AgentOutput,
    AnalysisResult,
    DataSource,
    MarketDataResult,
)


@pytest.fixture
def exporter(market_data_result: MarketDataResult) -> DataExporter:
    """Create a DataExporter for testing.

    Parameters
    ----------
    market_data_result : MarketDataResult
        MarketDataResult fixture.

    Returns
    -------
    DataExporter
        A DataExporter instance with MarketDataResult.
    """
    return DataExporter(market_data_result)


@pytest.fixture
def analysis_exporter(analysis_result: AnalysisResult) -> DataExporter:
    """Create a DataExporter with AnalysisResult for testing.

    Parameters
    ----------
    analysis_result : AnalysisResult
        AnalysisResult fixture.

    Returns
    -------
    DataExporter
        A DataExporter instance with AnalysisResult.
    """
    return DataExporter(analysis_result)


class TestDataExporter初期化:
    """Tests for DataExporter initialization."""

    def test_正常系_MarketDataResultで初期化(
        self, market_data_result: MarketDataResult
    ) -> None:
        """MarketDataResultで初期化できることを確認。"""
        exporter = DataExporter(market_data_result)
        assert exporter.symbol == "AAPL"
        assert exporter.result is market_data_result

    def test_正常系_AnalysisResultで初期化(
        self, analysis_result: AnalysisResult
    ) -> None:
        """AnalysisResultで初期化できることを確認。"""
        exporter = DataExporter(analysis_result)
        assert exporter.symbol == "AAPL"
        assert exporter.result is analysis_result

    def test_正常系_カスタム日付フォーマットで初期化(
        self, market_data_result: MarketDataResult
    ) -> None:
        """カスタム日付フォーマットで初期化できることを確認。"""
        exporter = DataExporter(market_data_result, date_format="%d/%m/%Y")
        assert exporter._date_format == "%d/%m/%Y"

    def test_正常系_dataプロパティがDataFrameを返す(
        self, exporter: DataExporter
    ) -> None:
        """dataプロパティがDataFrameを返すことを確認。"""
        data = exporter.data
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 30


class TestToJson:
    """Tests for to_json method."""

    def test_正常系_JSON文字列を返す(self, exporter: DataExporter) -> None:
        """to_jsonがJSON文字列を返すことを確認。"""
        result = exporter.to_json()
        assert isinstance(result, str)

        parsed = json.loads(result)
        assert "symbol" in parsed
        assert parsed["symbol"] == "AAPL"

    def test_正常系_データ配列を含む(self, exporter: DataExporter) -> None:
        """JSONがデータ配列を含むことを確認。"""
        result = exporter.to_json()
        parsed = json.loads(result)

        assert "data" in parsed
        assert len(parsed["data"]) == 30
        assert "close" in parsed["data"][0]

    def test_正常系_メタデータを含む(self, exporter: DataExporter) -> None:
        """メタデータが含まれることを確認。"""
        result = exporter.to_json(include_metadata=True)
        parsed = json.loads(result)

        assert "row_count" in parsed
        assert "columns" in parsed
        assert "source" in parsed
        assert parsed["source"] == "yfinance"

    def test_正常系_メタデータなしで出力(self, exporter: DataExporter) -> None:
        """メタデータなしで出力できることを確認。"""
        result = exporter.to_json(include_metadata=False)
        parsed = json.loads(result)

        assert "symbol" in parsed
        assert "data" in parsed
        assert "row_count" not in parsed

    def test_正常系_ファイルに書き込み(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """to_jsonがファイルに書き込めることを確認。"""
        output_path = temp_dir / "output.json"
        result = exporter.to_json(output_path=output_path)

        assert output_path.exists()
        file_content = output_path.read_text(encoding="utf-8")
        assert result == file_content

    def test_正常系_親ディレクトリを作成(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """to_jsonが親ディレクトリを作成することを確認。"""
        output_path = temp_dir / "nested" / "dir" / "output.json"
        exporter.to_json(output_path=output_path)

        assert output_path.exists()

    def test_正常系_カスタムインデント(self, exporter: DataExporter) -> None:
        """カスタムインデントが適用されることを確認。"""
        result_indent_2 = exporter.to_json(indent=2)
        result_indent_4 = exporter.to_json(indent=4)

        assert len(result_indent_4) > len(result_indent_2)

    def test_正常系_AnalysisResultでJSON出力(
        self, analysis_exporter: DataExporter
    ) -> None:
        """AnalysisResultでto_jsonが動作することを確認。"""
        result = analysis_exporter.to_json()
        parsed = json.loads(result)

        assert "analyzed_at" in parsed
        assert "statistics" in parsed
        assert "indicator_names" in parsed


class TestToCsv:
    """Tests for to_csv method."""

    def test_正常系_CSV文字列を返す(self, exporter: DataExporter) -> None:
        """to_csvがCSV文字列を返すことを確認。"""
        result = exporter.to_csv()
        assert isinstance(result, str)
        assert "close" in result

    def test_正常系_全行を含む(self, exporter: DataExporter) -> None:
        """CSVが全データ行を含むことを確認。"""
        result = exporter.to_csv()
        lines = result.strip().split("\n")

        assert len(lines) == 31  # Header + 30 data rows

    def test_正常系_日付フォーマット(self, exporter: DataExporter) -> None:
        """CSVが正しい日付フォーマットを使用することを確認。"""
        result = exporter.to_csv(date_format="%Y/%m/%d")
        assert "2024/01/01" in result

    def test_正常系_ファイルに書き込み(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """to_csvがファイルに書き込めることを確認。"""
        output_path = temp_dir / "output.csv"
        result = exporter.to_csv(output_path=output_path)

        assert output_path.exists()
        file_content = output_path.read_text(encoding="utf-8")
        assert result == file_content

    def test_正常系_インデックスを含む(self, exporter: DataExporter) -> None:
        """CSVが日付インデックスを含むことを確認。"""
        result = exporter.to_csv(include_index=True)
        assert "date" in result.lower()
        assert "2024-01-01" in result


class TestToSqlite:
    """Tests for to_sqlite method."""

    def test_正常系_テーブルを作成(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """to_sqliteがテーブルを作成することを確認。"""
        db_path = temp_dir / "test.db"
        rows = exporter.to_sqlite(db_path)

        assert rows == 30
        assert db_path.exists()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "market_data_aapl" in tables

    def test_正常系_カスタムテーブル名(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """カスタムテーブル名でto_sqliteが動作することを確認。"""
        db_path = temp_dir / "test.db"
        exporter.to_sqlite(db_path, table_name="custom_table")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "custom_table" in tables

    def test_正常系_UPSERTモード(self, exporter: DataExporter, temp_dir: Path) -> None:
        """to_sqliteがUPSERTを正しく実行することを確認。"""
        db_path = temp_dir / "test.db"

        rows1 = exporter.to_sqlite(db_path, if_exists="upsert")
        rows2 = exporter.to_sqlite(db_path, if_exists="upsert")

        assert rows1 == 30
        assert rows2 == 30

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM market_data_aapl")
            count = cursor.fetchone()[0]
            assert count == 30

    def test_正常系_REPLACEモード(self, exporter: DataExporter, temp_dir: Path) -> None:
        """REPLACEモードでto_sqliteが動作することを確認。"""
        db_path = temp_dir / "test.db"

        exporter.to_sqlite(db_path, if_exists="replace")
        exporter.to_sqlite(db_path, if_exists="replace")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM market_data_aapl")
            count = cursor.fetchone()[0]
            assert count == 30

    def test_正常系_APPENDモード(self, exporter: DataExporter, temp_dir: Path) -> None:
        """APPENDモードでto_sqliteが動作することを確認。"""
        db_path = temp_dir / "test.db"

        exporter.to_sqlite(db_path, if_exists="replace")
        exporter.to_sqlite(db_path, if_exists="append")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM market_data_aapl")
            count = cursor.fetchone()[0]
            assert count == 60

    def test_正常系_メタデータカラムを追加(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """to_sqliteがsymbolとupdated_atカラムを追加することを確認。"""
        db_path = temp_dir / "test.db"
        exporter.to_sqlite(db_path)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(market_data_aapl)")
            columns = [row[1] for row in cursor.fetchall()]
            assert "symbol" in columns
            assert "updated_at" in columns


class TestToAgentJson:
    """Tests for to_agent_json method."""

    def test_正常系_AgentOutputを返す(self, exporter: DataExporter) -> None:
        """to_agent_jsonがAgentOutputを返すことを確認。"""
        result = exporter.to_agent_json()
        assert isinstance(result, AgentOutput)

    def test_正常系_メタデータを含む(self, exporter: DataExporter) -> None:
        """AgentOutputがメタデータを含むことを確認。"""
        result = exporter.to_agent_json()

        assert result.metadata.version == "1.0"
        assert result.metadata.symbols == ["AAPL"]
        assert "2024-01-01" in result.metadata.period

    def test_正常系_サマリーを含む(self, exporter: DataExporter) -> None:
        """AgentOutputがサマリーを含むことを確認。"""
        result = exporter.to_agent_json()

        assert "AAPL" in result.summary
        assert "30 data points" in result.summary

    def test_正常系_データ構造を含む(self, exporter: DataExporter) -> None:
        """AgentOutputが構造化データを含むことを確認。"""
        result = exporter.to_agent_json()

        assert "symbol" in result.data
        assert "row_count" in result.data
        assert "latest" in result.data
        assert "price_stats" in result.data

    def test_正常系_レコメンデーションを含む(self, exporter: DataExporter) -> None:
        """AgentOutputがレコメンデーションを含むことを確認。"""
        result = exporter.to_agent_json(include_recommendations=True)
        assert isinstance(result.recommendations, list)

    def test_正常系_レコメンデーションなし(self, exporter: DataExporter) -> None:
        """レコメンデーションを無効化できることを確認。"""
        result = exporter.to_agent_json(include_recommendations=False)
        assert result.recommendations == []

    def test_正常系_ファイルに書き込み(
        self, exporter: DataExporter, temp_dir: Path
    ) -> None:
        """to_agent_jsonがファイルに書き込めることを確認。"""
        output_path = temp_dir / "agent_output.json"
        _result = exporter.to_agent_json(output_path=output_path)

        assert output_path.exists()
        file_content = json.loads(output_path.read_text(encoding="utf-8"))
        assert file_content["metadata"]["symbols"] == ["AAPL"]
        assert _result is not None

    def test_正常系_to_dictメソッド(self, exporter: DataExporter) -> None:
        """AgentOutput.to_dictメソッドが動作することを確認。"""
        result = exporter.to_agent_json()
        dict_output = result.to_dict()

        assert isinstance(dict_output, dict)
        assert "metadata" in dict_output
        assert "summary" in dict_output
        assert "data" in dict_output

    def test_正常系_AnalysisResultでAgentJSON出力(
        self, analysis_exporter: DataExporter
    ) -> None:
        """AnalysisResultでto_agent_jsonが動作することを確認。"""
        result = analysis_exporter.to_agent_json()

        assert "statistics" in result.data
        assert "indicators" in result.data


class TestErrorHandling:
    """Tests for error handling."""

    def test_異常系_to_json_無効なパスでExportError(
        self, exporter: DataExporter
    ) -> None:
        """無効なパスでto_jsonがExportErrorを発生させることを確認。"""
        with pytest.raises(ExportError) as exc_info:
            exporter.to_json(output_path="/nonexistent/path/file.json")

        assert exc_info.value.format == "json"
        assert "EXPORT_ERROR" in str(exc_info.value.code)

    def test_異常系_to_csv_無効なパスでExportError(
        self, exporter: DataExporter
    ) -> None:
        """無効なパスでto_csvがExportErrorを発生させることを確認。"""
        with pytest.raises(ExportError) as exc_info:
            exporter.to_csv(output_path="/nonexistent/path/file.csv")

        assert exc_info.value.format == "csv"

    def test_異常系_to_sqlite_無効なパスでExportError(
        self, exporter: DataExporter
    ) -> None:
        """無効なパスでto_sqliteがExportErrorを発生させることを確認。"""
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

    def test_エッジケース_to_json_空データ(
        self, empty_result: MarketDataResult
    ) -> None:
        """空データでto_jsonが動作することを確認。"""
        exporter = DataExporter(empty_result)
        result = exporter.to_json()
        parsed = json.loads(result)

        assert parsed["data"] == []
        assert parsed["row_count"] == 0

    def test_エッジケース_to_csv_空データ(self, empty_result: MarketDataResult) -> None:
        """空データでto_csvが動作することを確認。"""
        exporter = DataExporter(empty_result)
        result = exporter.to_csv()

        lines = result.strip().split("\n")
        assert len(lines) == 1  # Header only

    def test_エッジケース_to_agent_json_空データ(
        self, empty_result: MarketDataResult
    ) -> None:
        """空データでto_agent_jsonが動作することを確認。"""
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

    def test_エッジケース_to_sqlite_特殊文字シンボル(
        self, index_result: MarketDataResult, temp_dir: Path
    ) -> None:
        """特殊文字シンボルでto_sqliteが動作することを確認。"""
        exporter = DataExporter(index_result)
        db_path = temp_dir / "test.db"
        rows = exporter.to_sqlite(db_path)

        assert rows == 30

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert "market_data__gspc" in tables

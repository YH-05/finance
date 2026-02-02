"""Unit tests for BloombergDataProcessor class.

This module tests the BloombergDataProcessor which implements the DataCollector
interface for processing Bloomberg data from Excel files.

Tests cover:
- DataCollector inheritance verification
- fetch() method with symbols parameter
- validate() method for DataFrame validation
- Excel file reading
- SQLite storage functionality
- Proper structlog logging usage
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.base_collector import DataCollector
from market.bloomberg_processor import BloombergDataProcessor


class TestBloombergDataProcessorInheritance:
    """Test DataCollector inheritance."""

    def test_正常系_DataCollectorを継承している(self) -> None:
        processor = BloombergDataProcessor()
        assert isinstance(processor, DataCollector)

    def test_正常系_nameプロパティがクラス名を返す(self) -> None:
        processor = BloombergDataProcessor()
        assert processor.name == "BloombergDataProcessor"


class TestBloombergDataProcessorFetch:
    """Test the fetch method."""

    def test_正常系_fetchメソッドがDataFrameを返す(self) -> None:
        processor = BloombergDataProcessor()
        # With empty symbols, should return empty DataFrame
        result = processor.fetch(symbols=[])
        assert isinstance(result, pd.DataFrame)

    def test_正常系_symbolsパラメータを受け取る(self) -> None:
        processor = BloombergDataProcessor()
        result = processor.fetch(symbols=["AAPL", "GOOGL"])
        assert isinstance(result, pd.DataFrame)

    def test_正常系_excel_pathパラメータを受け取る(self) -> None:
        processor = BloombergDataProcessor()
        # Create a temporary Excel file
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            test_path = f.name
            # Create a simple DataFrame and save to Excel
            df = pd.DataFrame(
                {
                    "symbol": ["AAPL", "GOOGL"],
                    "price": [150.0, 140.0],
                    "date": ["2024-01-01", "2024-01-01"],
                }
            )
            df.to_excel(test_path, index=False)

        try:
            result = processor.fetch(symbols=["AAPL"], excel_path=test_path)
            assert isinstance(result, pd.DataFrame)
        finally:
            Path(test_path).unlink(missing_ok=True)

    def test_異常系_存在しないExcelファイルでFileNotFoundError(self) -> None:
        processor = BloombergDataProcessor()
        with pytest.raises(FileNotFoundError):
            processor.fetch(symbols=["AAPL"], excel_path="/nonexistent/path.xlsx")


class TestBloombergDataProcessorValidate:
    """Test the validate method."""

    def test_正常系_有効なDataFrameでTrue(self) -> None:
        processor = BloombergDataProcessor()
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "date": ["2024-01-01"],
                "price": [150.0],
            }
        )
        assert processor.validate(df) is True

    def test_正常系_空のDataFrameでFalse(self) -> None:
        processor = BloombergDataProcessor()
        df = pd.DataFrame()
        assert processor.validate(df) is False

    def test_正常系_必須カラムがない場合False(self) -> None:
        processor = BloombergDataProcessor()
        df = pd.DataFrame({"other_column": [1, 2, 3]})
        # Should return False if required columns are missing
        assert processor.validate(df) is False


class TestBloombergDataProcessorExcelReading:
    """Test Excel file reading functionality."""

    def test_正常系_Excelファイルを読み込める(self) -> None:
        processor = BloombergDataProcessor()

        # Create a temporary Excel file
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            test_path = f.name
            df = pd.DataFrame(
                {
                    "symbol": ["AAPL", "GOOGL", "MSFT"],
                    "price": [150.0, 140.0, 380.0],
                    "date": ["2024-01-01", "2024-01-01", "2024-01-01"],
                }
            )
            df.to_excel(test_path, index=False)

        try:
            result = processor.read_excel(test_path)
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert "symbol" in result.columns
        finally:
            Path(test_path).unlink(missing_ok=True)

    def test_正常系_シンボルでフィルタリングできる(self) -> None:
        processor = BloombergDataProcessor()

        # Create a temporary Excel file
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            test_path = f.name
            df = pd.DataFrame(
                {
                    "symbol": ["AAPL", "GOOGL", "MSFT"],
                    "price": [150.0, 140.0, 380.0],
                    "date": ["2024-01-01", "2024-01-01", "2024-01-01"],
                }
            )
            df.to_excel(test_path, index=False)

        try:
            result = processor.read_excel(test_path, symbols=["AAPL", "GOOGL"])
            assert len(result) == 2
            assert set(result["symbol"].tolist()) == {"AAPL", "GOOGL"}
        finally:
            Path(test_path).unlink(missing_ok=True)


class TestBloombergDataProcessorSQLiteStorage:
    """Test SQLite storage functionality."""

    def test_正常系_SQLiteに保存できる(self) -> None:
        processor = BloombergDataProcessor()

        df = pd.DataFrame(
            {
                "symbol": ["AAPL", "GOOGL"],
                "price": [150.0, 140.0],
                "date": ["2024-01-01", "2024-01-01"],
            }
        )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            processor.save_to_sqlite(df, db_path, "test_table")

            # Verify data was saved
            with sqlite3.connect(db_path) as conn:
                result = pd.read_sql("SELECT * FROM test_table", conn)
                assert len(result) == 2
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_正常系_既存テーブルに追記できる(self) -> None:
        processor = BloombergDataProcessor()

        df1 = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "price": [150.0],
                "date": ["2024-01-01"],
            }
        )

        df2 = pd.DataFrame(
            {
                "symbol": ["GOOGL"],
                "price": [140.0],
                "date": ["2024-01-02"],
            }
        )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            processor.save_to_sqlite(df1, db_path, "test_table")
            processor.save_to_sqlite(df2, db_path, "test_table", if_exists="append")

            # Verify both records exist
            with sqlite3.connect(db_path) as conn:
                result = pd.read_sql("SELECT * FROM test_table", conn)
                assert len(result) == 2
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestBloombergDataProcessorLogging:
    """Test structlog logging usage."""

    def test_正常系_fetchでログが出力される(self) -> None:
        processor = BloombergDataProcessor()

        with patch("market.bloomberg_processor.logger") as mock_logger:
            processor.fetch(symbols=["AAPL"])
            # Verify logging was called
            assert mock_logger.debug.called or mock_logger.info.called

    def test_正常系_validateでログが出力される(self) -> None:
        processor = BloombergDataProcessor()
        df = pd.DataFrame(
            {"symbol": ["AAPL"], "date": ["2024-01-01"], "price": [150.0]}
        )

        with patch("market.bloomberg_processor.logger") as mock_logger:
            processor.validate(df)
            # Verify logging was called
            assert mock_logger.debug.called or mock_logger.info.called


class TestBloombergDataProcessorCollectMethod:
    """Test the inherited collect() convenience method."""

    def test_正常系_collectがfetchとvalidateを呼び出す(self) -> None:
        processor = BloombergDataProcessor()

        # Create a temporary Excel file with valid data
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            test_path = f.name
            df = pd.DataFrame(
                {
                    "symbol": ["AAPL"],
                    "price": [150.0],
                    "date": ["2024-01-01"],
                }
            )
            df.to_excel(test_path, index=False)

        try:
            result = processor.collect(symbols=["AAPL"], excel_path=test_path)
            assert isinstance(result, pd.DataFrame)
        finally:
            Path(test_path).unlink(missing_ok=True)


class TestBloombergDataProcessorDocstrings:
    """Test that all public methods have NumPy-style docstrings."""

    def test_正常系_クラスにDocstringがある(self) -> None:
        assert BloombergDataProcessor.__doc__ is not None
        assert len(BloombergDataProcessor.__doc__) > 50

    def test_正常系_fetchメソッドにDocstringがある(self) -> None:
        assert BloombergDataProcessor.fetch.__doc__ is not None
        assert "Parameters" in BloombergDataProcessor.fetch.__doc__
        assert "Returns" in BloombergDataProcessor.fetch.__doc__

    def test_正常系_validateメソッドにDocstringがある(self) -> None:
        assert BloombergDataProcessor.validate.__doc__ is not None
        assert "Parameters" in BloombergDataProcessor.validate.__doc__
        assert "Returns" in BloombergDataProcessor.validate.__doc__


class TestBloombergDataProcessorExports:
    """Test module exports."""

    def test_正常系_BloombergDataProcessorがエクスポートされている(self) -> None:
        from market.bloomberg_processor import __all__

        assert "BloombergDataProcessor" in __all__

"""Tests for SQL identifier validation in factset_downloaded_data_utils.

factset_downloaded_data_utils.py の全SQL f-string に
_validate_sql_identifier() が適用されていることを検証する。
CWE-89 (SQL Injection) 対策。
"""

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from market.factset.factset_downloaded_data_utils import (
    delete_table_from_database,
    store_to_database,
)


@pytest.fixture
def temp_db() -> Path:
    """一時的なSQLiteデータベースファイルを作成する。"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return Path(f.name)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """store_to_database テスト用のサンプルDataFrame。"""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "P_SYMBOL": ["AAPL", "AAPL"],
            "variable": ["price", "price"],
            "value": [100.0, 101.0],
        }
    )


class TestStoreToDatabase:
    """store_to_database の SQL識別子バリデーション検証。"""

    def test_正常系_有効なテーブル名でデータが書き込まれる(
        self, temp_db: Path, sample_df: pd.DataFrame
    ) -> None:
        store_to_database(sample_df, temp_db, "valid_table")

        conn = sqlite3.connect(temp_db)
        result = pd.read_sql("SELECT * FROM valid_table", conn)
        conn.close()
        assert len(result) == 2

    def test_異常系_不正なテーブル名でValueError(
        self, temp_db: Path, sample_df: pd.DataFrame
    ) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            store_to_database(sample_df, temp_db, "table; DROP TABLE--")

    def test_異常系_空テーブル名でValueError(
        self, temp_db: Path, sample_df: pd.DataFrame
    ) -> None:
        with pytest.raises(ValueError, match="SQL識別子は空にできません"):
            store_to_database(sample_df, temp_db, "")

    def test_異常系_SQLインジェクションパターンのテーブル名を拒否(
        self, temp_db: Path, sample_df: pd.DataFrame
    ) -> None:
        malicious_names = [
            "table; DROP TABLE users--",
            "table' OR '1'='1",
            'table"; DROP TABLE--',
            "table$(command)",
        ]
        for name in malicious_names:
            with pytest.raises(
                ValueError, match="SQL識別子に不正な文字が含まれています"
            ):
                store_to_database(sample_df, temp_db, name)

    def test_異常系_不正なunique_colsカラム名でValueError(
        self, temp_db: Path, sample_df: pd.DataFrame
    ) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            store_to_database(
                sample_df,
                temp_db,
                "valid_table",
                unique_cols=["date", "col; DROP TABLE--"],
            )


class TestDeleteTableFromDatabase:
    """delete_table_from_database の SQL識別子バリデーション検証。"""

    def test_正常系_有効なテーブル名でテーブル削除(self, temp_db: Path) -> None:
        # テーブルを作成
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE valid_table (id INTEGER)")
        conn.commit()
        conn.close()

        # 削除（例外が発生しないことを確認）
        delete_table_from_database(temp_db, "valid_table")

        # 削除されたことを確認
        conn = sqlite3.connect(temp_db)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='valid_table'"
        )
        assert cursor.fetchone() is None
        conn.close()

    def test_異常系_不正なテーブル名でValueError(self, temp_db: Path) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            delete_table_from_database(temp_db, "table; DROP TABLE--")

    def test_異常系_空テーブル名でValueError(self, temp_db: Path) -> None:
        with pytest.raises(ValueError, match="SQL識別子は空にできません"):
            delete_table_from_database(temp_db, "")

    def test_異常系_SQLインジェクションパターンのテーブル名を拒否(
        self,
        temp_db: Path,
    ) -> None:
        malicious_names = [
            "table; DROP TABLE users--",
            "table' OR '1'='1",
            'table"; DROP TABLE--',
        ]
        for name in malicious_names:
            with pytest.raises(
                ValueError, match="SQL識別子に不正な文字が含まれています"
            ):
                delete_table_from_database(temp_db, name)

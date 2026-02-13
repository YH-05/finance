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
    _validate_sql_identifier,
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

    def test_異常系_ハイフンを含むテーブル名でValueError(
        self, temp_db: Path, sample_df: pd.DataFrame
    ) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            store_to_database(sample_df, temp_db, "table-name")

    def test_異常系_ドットを含むテーブル名でValueError(
        self, temp_db: Path, sample_df: pd.DataFrame
    ) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            store_to_database(sample_df, temp_db, "schema.table")

    def test_異常系_SQLキーワードのテーブル名でValueError(
        self, temp_db: Path, sample_df: pd.DataFrame
    ) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            store_to_database(sample_df, temp_db, "DROP")


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

    def test_異常系_ハイフンを含むテーブル名でValueError(self, temp_db: Path) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            delete_table_from_database(temp_db, "my-table")

    def test_異常系_ドットを含むテーブル名でValueError(self, temp_db: Path) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            delete_table_from_database(temp_db, "schema.table")

    def test_異常系_SQLキーワードのテーブル名でValueError(self, temp_db: Path) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            delete_table_from_database(temp_db, "SELECT")


class TestValidateSqlIdentifier:
    """_validate_sql_identifier の直接テスト。"""

    def test_正常系_有効な識別子がそのまま返される(self) -> None:
        assert _validate_sql_identifier("valid_table") == "valid_table"
        assert _validate_sql_identifier("_private") == "_private"
        assert _validate_sql_identifier("Table123") == "Table123"
        assert _validate_sql_identifier("a") == "a"

    def test_異常系_ハイフンを含む識別子でValueError(self) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            _validate_sql_identifier("my-table")

    def test_異常系_ドットを含む識別子でValueError(self) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            _validate_sql_identifier("schema.table")

    def test_異常系_ダブルハイフンコメント攻撃を拒否(self) -> None:
        with pytest.raises(ValueError, match="SQL識別子に不正な文字が含まれています"):
            _validate_sql_identifier("table--comment")

    def test_異常系_SQLキーワードDROPを拒否(self) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            _validate_sql_identifier("DROP")

    def test_異常系_SQLキーワードSELECTを拒否(self) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            _validate_sql_identifier("SELECT")

    def test_異常系_SQLキーワードINSERTを拒否(self) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            _validate_sql_identifier("INSERT")

    def test_異常系_SQLキーワードDELETEを拒否(self) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            _validate_sql_identifier("DELETE")

    def test_異常系_SQLキーワードUNIONを拒否(self) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            _validate_sql_identifier("UNION")

    def test_異常系_SQLキーワード小文字でも拒否(self) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            _validate_sql_identifier("drop")

    def test_異常系_SQLキーワード大文字小文字混在でも拒否(self) -> None:
        with pytest.raises(ValueError, match="SQLキーワードは識別子に使用できません"):
            _validate_sql_identifier("Select")

    def test_正常系_SQLキーワードを含むが完全一致でない識別子は許可(self) -> None:
        # "drop_table" は "DROP" の完全一致ではないので許可
        assert _validate_sql_identifier("drop_table") == "drop_table"
        assert _validate_sql_identifier("select_all") == "select_all"
        assert _validate_sql_identifier("union_data") == "union_data"

    def test_異常系_空文字列でValueError(self) -> None:
        with pytest.raises(ValueError, match="SQL識別子は空にできません"):
            _validate_sql_identifier("")

    def test_異常系_空白のみでValueError(self) -> None:
        with pytest.raises(ValueError, match="SQL識別子は空にできません"):
            _validate_sql_identifier("   ")

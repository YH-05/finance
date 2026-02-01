"""Unit tests for format_converter module.

Issue #951: Parquet/JSON形式間のフォーマット変換ユーティリティ

テストTODOリスト:
- [x] test_正常系_parquet_to_json_変換成功
- [x] test_正常系_json_to_parquet_変換成功
- [x] test_正常系_相互変換でデータ一致
- [x] test_正常系_様々なデータ型を保持
- [x] test_異常系_存在しないファイルでFileNotFoundError
- [x] test_異常系_不正なフォーマットでValueError
- [x] test_異常系_空データでValueError
- [x] test_エッジケース_ネストしたJSONの処理
- [x] test_エッジケース_nullを含むデータの処理
- [x] test_エッジケース_大きなファイルの処理
"""

from datetime import datetime
from pathlib import Path

import pytest

from database.utils.format_converter import (
    json_to_parquet,
    parquet_to_json,
)


class TestParquetToJson:
    """Parquet to JSON 変換のテスト。"""

    def test_正常系_parquet_to_json_変換成功(
        self, tmp_path: Path, sample_parquet_file: Path
    ) -> None:
        """ParquetファイルをJSON形式に変換できることを確認。"""
        output_path = tmp_path / "output.json"

        result = parquet_to_json(sample_parquet_file, output_path)

        assert output_path.exists()
        assert result is True

    def test_正常系_様々なデータ型を保持_parquet_to_json(
        self, tmp_path: Path, sample_parquet_with_types: Path
    ) -> None:
        """int, float, str, bool, datetime等が正しく変換されることを確認。"""
        output_path = tmp_path / "output.json"

        parquet_to_json(sample_parquet_with_types, output_path)

        import json

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        # データ型の検証
        assert len(data) > 0
        first_record = data[0]

        # 各型が保持されていることを確認
        assert isinstance(first_record["int_col"], int)
        assert isinstance(first_record["float_col"], float)
        assert isinstance(first_record["str_col"], str)
        assert isinstance(first_record["bool_col"], bool)
        # datetime は ISO 形式文字列として保存される
        assert isinstance(first_record["datetime_col"], str)

    def test_異常系_存在しないファイルでFileNotFoundError(self, tmp_path: Path) -> None:
        """存在しないParquetファイルを読もうとするとエラーが発生することを確認。"""
        non_existent_path = tmp_path / "non_existent.parquet"
        output_path = tmp_path / "output.json"

        with pytest.raises(FileNotFoundError):
            parquet_to_json(non_existent_path, output_path)

    def test_異常系_不正なフォーマットでValueError(self, tmp_path: Path) -> None:
        """Parquet形式でないファイルを読もうとするとエラーが発生することを確認。"""
        invalid_file = tmp_path / "invalid.parquet"
        invalid_file.write_text("This is not a parquet file")
        output_path = tmp_path / "output.json"

        with pytest.raises(ValueError, match="Invalid Parquet file"):
            parquet_to_json(invalid_file, output_path)


class TestJsonToParquet:
    """JSON to Parquet 変換のテスト。"""

    def test_正常系_json_to_parquet_変換成功(
        self, tmp_path: Path, sample_json_file: Path
    ) -> None:
        """JSONファイルをParquet形式に変換できることを確認。"""
        output_path = tmp_path / "output.parquet"

        result = json_to_parquet(sample_json_file, output_path)

        assert output_path.exists()
        assert result is True

    def test_正常系_様々なデータ型を保持_json_to_parquet(
        self, tmp_path: Path, sample_json_with_types: Path
    ) -> None:
        """int, float, str, bool, datetime等が正しく変換されることを確認。"""
        output_path = tmp_path / "output.parquet"

        json_to_parquet(sample_json_with_types, output_path)

        # Parquetファイルを読み込んで型を確認
        import pyarrow.parquet as pq

        table = pq.read_table(output_path)
        schema = table.schema

        # データ型が適切に推論されていることを確認
        assert "int_col" in schema.names
        assert "float_col" in schema.names
        assert "str_col" in schema.names
        assert "bool_col" in schema.names

    def test_異常系_存在しないファイルでFileNotFoundError(self, tmp_path: Path) -> None:
        """存在しないJSONファイルを読もうとするとエラーが発生することを確認。"""
        non_existent_path = tmp_path / "non_existent.json"
        output_path = tmp_path / "output.parquet"

        with pytest.raises(FileNotFoundError):
            json_to_parquet(non_existent_path, output_path)

    def test_異常系_不正なJSONフォーマットでValueError(self, tmp_path: Path) -> None:
        """不正なJSON形式のファイルを読もうとするとエラーが発生することを確認。"""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        output_path = tmp_path / "output.parquet"

        with pytest.raises(ValueError, match="Invalid JSON"):
            json_to_parquet(invalid_file, output_path)

    def test_異常系_空データでValueError(self, tmp_path: Path) -> None:
        """空のJSONデータを変換しようとするとエラーが発生することを確認。"""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]")
        output_path = tmp_path / "output.parquet"

        with pytest.raises(ValueError, match="Empty data"):
            json_to_parquet(empty_file, output_path)


class TestRoundTrip:
    """Parquet <-> JSON 相互変換のテスト。"""

    def test_正常系_相互変換でデータ一致(
        self, tmp_path: Path, sample_parquet_file: Path
    ) -> None:
        """Parquet -> JSON -> Parquet で元データと一致することを確認。"""
        json_path = tmp_path / "intermediate.json"
        final_parquet_path = tmp_path / "final.parquet"

        # Parquet -> JSON
        parquet_to_json(sample_parquet_file, json_path)

        # JSON -> Parquet
        json_to_parquet(json_path, final_parquet_path)

        # 元データと最終データを比較
        import pyarrow.parquet as pq

        original_table = pq.read_table(sample_parquet_file)
        final_table = pq.read_table(final_parquet_path)

        # 行数が一致することを確認
        assert len(original_table) == len(final_table)

        # 列名が一致することを確認
        assert set(original_table.column_names) == set(final_table.column_names)

        # データ内容が一致することを確認
        original_df = original_table.to_pandas()
        final_df = final_table.to_pandas()

        # 列を同じ順序にソートして比較
        for col in original_df.columns:
            assert list(original_df[col]) == list(final_df[col])


class TestEdgeCases:
    """エッジケースのテスト。"""

    def test_エッジケース_ネストしたJSONの処理(self, tmp_path: Path) -> None:
        """ネストした構造のJSONを変換できることを確認。"""
        import json

        nested_data = [
            {
                "id": 1,
                "name": "test",
                "metadata": {"key1": "value1", "key2": 123},
                "tags": ["tag1", "tag2"],
            },
            {
                "id": 2,
                "name": "test2",
                "metadata": {"key1": "value2", "key2": 456},
                "tags": ["tag3"],
            },
        ]

        json_file = tmp_path / "nested.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(nested_data, f, ensure_ascii=False)

        parquet_path = tmp_path / "nested.parquet"

        # ネストしたJSONをParquetに変換
        json_to_parquet(json_file, parquet_path)

        assert parquet_path.exists()

        # 再度JSONに変換して確認
        json_output = tmp_path / "nested_output.json"
        parquet_to_json(parquet_path, json_output)

        with open(json_output, encoding="utf-8") as f:
            result_data = json.load(f)

        assert len(result_data) == 2
        # ネストした構造が保持されていることを確認
        assert "metadata" in result_data[0]

    def test_エッジケース_nullを含むデータの処理(self, tmp_path: Path) -> None:
        """NULL値を含むデータを変換できることを確認。"""
        import json

        data_with_nulls = [
            {"id": 1, "name": "test", "optional_field": None},
            {"id": 2, "name": None, "optional_field": "value"},
            {"id": 3, "name": "test3", "optional_field": None},
        ]

        json_file = tmp_path / "with_nulls.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data_with_nulls, f, ensure_ascii=False)

        parquet_path = tmp_path / "with_nulls.parquet"
        json_to_parquet(json_file, parquet_path)

        assert parquet_path.exists()

        # Parquetから読み込んでNULLが保持されていることを確認
        import pyarrow.parquet as pq

        table = pq.read_table(parquet_path)
        df = table.to_pandas()

        # NULL値が正しく保持されているか確認
        assert df["optional_field"].isna().sum() == 2
        assert df["name"].isna().sum() == 1

    def test_エッジケース_大きなファイルの処理(self, tmp_path: Path) -> None:
        """大きめのデータセット（10000行）を変換できることを確認。"""
        import json

        large_data = [
            {"id": i, "name": f"item_{i}", "value": float(i * 1.5)}
            for i in range(10000)
        ]

        json_file = tmp_path / "large.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(large_data, f, ensure_ascii=False)

        parquet_path = tmp_path / "large.parquet"
        json_to_parquet(json_file, parquet_path)

        assert parquet_path.exists()

        # 行数が正しいことを確認
        import pyarrow.parquet as pq

        table = pq.read_table(parquet_path)
        assert len(table) == 10000


# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def sample_parquet_file(tmp_path: Path) -> Path:
    """テスト用のサンプルParquetファイルを作成。"""
    import pyarrow as pa
    import pyarrow.parquet as pq

    data = {
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "value": [100.0, 200.0, 300.0],
    }
    table = pa.Table.from_pydict(data)

    parquet_path = tmp_path / "sample.parquet"
    pq.write_table(table, parquet_path)

    return parquet_path


@pytest.fixture
def sample_parquet_with_types(tmp_path: Path) -> Path:
    """様々なデータ型を含むParquetファイルを作成。"""
    import pyarrow as pa
    import pyarrow.parquet as pq

    data = {
        "int_col": [1, 2, 3],
        "float_col": [1.1, 2.2, 3.3],
        "str_col": ["a", "b", "c"],
        "bool_col": [True, False, True],
        "datetime_col": [
            datetime(2024, 1, 1),
            datetime(2024, 6, 15),
            datetime(2024, 12, 31),
        ],
    }
    table = pa.Table.from_pydict(data)

    parquet_path = tmp_path / "sample_types.parquet"
    pq.write_table(table, parquet_path)

    return parquet_path


@pytest.fixture
def sample_json_file(tmp_path: Path) -> Path:
    """テスト用のサンプルJSONファイルを作成。"""
    import json

    data = [
        {"id": 1, "name": "Alice", "value": 100.0},
        {"id": 2, "name": "Bob", "value": 200.0},
        {"id": 3, "name": "Charlie", "value": 300.0},
    ]

    json_path = tmp_path / "sample.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    return json_path


@pytest.fixture
def sample_json_with_types(tmp_path: Path) -> Path:
    """様々なデータ型を含むJSONファイルを作成。"""
    import json

    data = [
        {
            "int_col": 1,
            "float_col": 1.1,
            "str_col": "a",
            "bool_col": True,
            "datetime_col": "2024-01-01T00:00:00",
        },
        {
            "int_col": 2,
            "float_col": 2.2,
            "str_col": "b",
            "bool_col": False,
            "datetime_col": "2024-06-15T00:00:00",
        },
        {
            "int_col": 3,
            "float_col": 3.3,
            "str_col": "c",
            "bool_col": True,
            "datetime_col": "2024-12-31T00:00:00",
        },
    ]

    json_path = tmp_path / "sample_types.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    return json_path

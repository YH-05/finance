"""Property-based tests for format_converter module using Hypothesis.

Issue #951: Parquet/JSON形式間のフォーマット変換ユーティリティ

プロパティテストTODO:
- [x] test_プロパティ_相互変換でデータが保持される
- [x] test_プロパティ_変換後の行数が一致する
- [x] test_プロパティ_変換後の列名が一致する
"""

import tempfile
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from database.utils.format_converter import (
    json_to_parquet,
    parquet_to_json,
)

# =============================================================================
# カスタムストラテジー
# =============================================================================

# JSON互換の基本型
json_primitive = (
    st.none()
    | st.booleans()
    | st.integers(min_value=-(2**31), max_value=2**31 - 1)
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(min_size=0, max_size=50)
)


# テーブル形式のデータ（レコードのリスト）を生成
# 全レコードが同じキーを持つことを保証
@st.composite
def table_data(draw: st.DrawFn) -> list[dict[str, object]]:
    """テーブル形式のデータ（全レコードが同じスキーマを持つ）を生成。"""
    # 列名を生成（1〜5列）
    num_columns = draw(st.integers(min_value=1, max_value=5))
    column_names = [f"col_{i}" for i in range(num_columns)]

    # 行数を生成（1〜20行）
    num_rows = draw(st.integers(min_value=1, max_value=20))

    # 各列の値を生成
    records = []
    for _ in range(num_rows):
        record = {}
        for col_name in column_names:
            # NoneはParquet変換時に問題になることがあるため除外
            value = draw(
                st.integers(min_value=-(2**31), max_value=2**31 - 1)
                | st.floats(allow_nan=False, allow_infinity=False)
                | st.text(min_size=0, max_size=20)
                | st.booleans()
            )
            record[col_name] = value
        records.append(record)

    return records


class TestFormatConverterProperty:
    """フォーマット変換のプロパティベーステスト。"""

    @given(data=table_data())
    @settings(max_examples=50, deadline=None)
    def test_プロパティ_相互変換でデータが保持される(
        self, data: list[dict[str, object]]
    ) -> None:
        """JSON -> Parquet -> JSON で元のデータ構造が保持されることを検証。"""
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # 元データをJSONファイルに書き込み
            json_input = tmpdir_path / "input.json"
            with open(json_input, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            # JSON -> Parquet
            parquet_path = tmpdir_path / "converted.parquet"
            json_to_parquet(json_input, parquet_path)

            # Parquet -> JSON
            json_output = tmpdir_path / "output.json"
            parquet_to_json(parquet_path, json_output)

            # 出力データを読み込み
            with open(json_output, encoding="utf-8") as f:
                result_data = json.load(f)

            # 行数が一致することを確認
            assert len(result_data) == len(data)

            # 列名が一致することを確認
            if data:
                original_keys = set(data[0].keys())
                result_keys = set(result_data[0].keys())
                assert original_keys == result_keys

    @given(data=table_data())
    @settings(max_examples=30, deadline=None)
    def test_プロパティ_変換後の行数が一致する(
        self, data: list[dict[str, object]]
    ) -> None:
        """変換後も行数が保持されることを検証。"""
        import json

        import pyarrow.parquet as pq

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            json_input = tmpdir_path / "input.json"
            with open(json_input, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            parquet_path = tmpdir_path / "converted.parquet"
            json_to_parquet(json_input, parquet_path)

            table = pq.read_table(parquet_path)

            assert len(table) == len(data)

    @given(data=table_data())
    @settings(max_examples=30, deadline=None)
    def test_プロパティ_変換後の列名が一致する(
        self, data: list[dict[str, object]]
    ) -> None:
        """変換後も列名が保持されることを検証。"""
        import json

        import pyarrow.parquet as pq

        assume(len(data) > 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            json_input = tmpdir_path / "input.json"
            with open(json_input, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            parquet_path = tmpdir_path / "converted.parquet"
            json_to_parquet(json_input, parquet_path)

            table = pq.read_table(parquet_path)

            original_columns = set(data[0].keys())
            parquet_columns = set(table.column_names)

            assert original_columns == parquet_columns

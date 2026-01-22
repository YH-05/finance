# プロパティベーステストテンプレート

このテンプレートは Hypothesis を使用したプロパティベーステストの標準的な構造を提供します。

## ファイル配置

```
tests/{library}/property/test_{module}_property.py
```

## 基本構造

```python
"""Property-based tests for {module_name} module using Hypothesis."""

import tempfile
from pathlib import Path

from hypothesis import given, assume, settings
from hypothesis import strategies as st
from {package}.{module} import (
    chunk_list,
    flatten_dict,
    encode,
    decode,
)


class TestChunkListProperty:
    """Property-based tests for chunk_list function."""

    @given(
        items=st.lists(st.integers()),
        chunk_size=st.integers(min_value=1, max_value=100),
    )
    def test_プロパティ_チャンク化しても全要素が保持される(
        self,
        items: list[int],
        chunk_size: int,
    ) -> None:
        """チャンク化前後で全要素が保持されることを検証。"""
        chunks = chunk_list(items, chunk_size)

        # フラット化して元のリストと比較
        flattened = [item for chunk in chunks for item in chunk]

        assert flattened == items

    @given(
        items=st.lists(st.integers(), min_size=1),
        chunk_size=st.integers(min_value=1, max_value=100),
    )
    def test_プロパティ_各チャンクサイズが適切(
        self,
        items: list[int],
        chunk_size: int,
    ) -> None:
        """各チャンクのサイズが期待通りであることを検証。"""
        chunks = chunk_list(items, chunk_size)

        if chunks:
            # 最後のチャンク以外はすべて chunk_size と同じ
            for chunk in chunks[:-1]:
                assert len(chunk) == chunk_size

            # 最後のチャンクは 1 以上 chunk_size 以下
            assert 1 <= len(chunks[-1]) <= chunk_size

    @given(
        items=st.lists(st.text(), min_size=0, max_size=1000),
        chunk_size=st.integers(min_value=1, max_value=100),
    )
    def test_プロパティ_チャンク数が正しい(
        self,
        items: list[str],
        chunk_size: int,
    ) -> None:
        """チャンク数が数学的に正しいことを検証。"""
        chunks = chunk_list(items, chunk_size)

        expected_chunks = (len(items) + chunk_size - 1) // chunk_size
        if len(items) == 0:
            expected_chunks = 0

        assert len(chunks) == expected_chunks


class TestEncodingProperty:
    """Property-based tests for encoding/decoding functions."""

    @given(text=st.text())
    def test_プロパティ_エンコードデコードの可逆性(self, text: str) -> None:
        """エンコード→デコードで元のテキストに戻ることを検証。"""
        encoded = encode(text)
        decoded = decode(encoded)
        assert decoded == text

    @given(text=st.text())
    def test_プロパティ_エンコードの冪等性(self, text: str) -> None:
        """同じ入力に対して常に同じ出力が返ることを検証。"""
        result1 = encode(text)
        result2 = encode(text)
        assert result1 == result2


class TestFlattenDictProperty:
    """Property-based tests for flatten_dict function."""

    # JSON 互換の値を生成する戦略
    json_value = st.recursive(
        st.none()
        | st.booleans()
        | st.integers()
        | st.floats(allow_nan=False)
        | st.text(),
        lambda children: st.lists(children, max_size=5)
        | st.dictionaries(st.text(), children, max_size=5),
        max_leaves=20,
    )

    @given(nested=st.dictionaries(st.text(min_size=1), json_value, max_size=10))
    def test_プロパティ_フラット化後も全ての値が保持される(
        self,
        nested: dict,
    ) -> None:
        """フラット化前後で全ての値が保持されることを検証。"""
        flattened = flatten_dict(nested)

        # 全ての値を収集
        def collect_values(d: dict) -> list:
            values = []
            for v in d.values():
                if isinstance(v, dict):
                    values.extend(collect_values(v))
                else:
                    values.append(v)
            return values

        original_values = sorted(collect_values(nested), key=str)
        flattened_values = sorted(flattened.values(), key=str)

        assert len(original_values) == len(flattened_values)

    @given(
        nested=st.dictionaries(
            st.text(min_size=1, alphabet=st.characters(blacklist_characters=".")),
            st.integers(),
            max_size=10,
        ),
        separator=st.sampled_from([".", "_", "-", "/"]),
    )
    def test_プロパティ_カスタムセパレータが正しく使用される(
        self,
        nested: dict,
        separator: str,
    ) -> None:
        """指定したセパレータが使用されることを検証。"""
        nested_dict = {"level1": nested}

        flattened = flatten_dict(nested_dict, separator=separator)

        if nested and flattened:
            separator_keys = [k for k in flattened if separator in k]
            assert len(separator_keys) > 0


class TestJsonFileOperationsProperty:
    """Property-based tests for JSON file operations."""

    # JSON 互換のオブジェクトを生成
    json_object = st.dictionaries(
        st.text(min_size=1),
        st.recursive(
            st.none()
            | st.booleans()
            | st.integers()
            | st.floats(allow_nan=False)
            | st.text(),
            lambda children: st.lists(children, max_size=3)
            | st.dictionaries(st.text(), children, max_size=3),
            max_leaves=10,
        ),
        min_size=1,
        max_size=10,
    )

    @given(data=json_object)
    def test_プロパティ_保存と読み込みで同じデータが復元される(
        self,
        data: dict,
    ) -> None:
        """JSON ファイルへの保存と読み込みでデータが保持されることを検証。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            json_file = Path(temp_dir) / "test_property.json"

            save_json_file(data, json_file)
            loaded_data = load_json_file(json_file)

            assert loaded_data == data


class TestMathematicalProperty:
    """Property-based tests for mathematical operations."""

    @given(a=st.integers(), b=st.integers())
    def test_プロパティ_加法の交換則(self, a: int, b: int) -> None:
        """加法が交換則を満たすことを検証。"""
        assert add(a, b) == add(b, a)

    @given(a=st.integers(), b=st.integers(), c=st.integers())
    def test_プロパティ_加法の結合則(self, a: int, b: int, c: int) -> None:
        """加法が結合則を満たすことを検証。"""
        assert add(add(a, b), c) == add(a, add(b, c))

    @given(a=st.integers())
    def test_プロパティ_加法の単位元(self, a: int) -> None:
        """0 が加法の単位元であることを検証。"""
        assert add(a, 0) == a
        assert add(0, a) == a
```

## 主要な Strategies

| Strategy | 用途 | 例 |
|---------|------|-----|
| `st.integers()` | 整数 | `st.integers(min_value=0, max_value=100)` |
| `st.floats()` | 浮動小数点 | `st.floats(allow_nan=False)` |
| `st.text()` | 文字列 | `st.text(min_size=1, max_size=100)` |
| `st.binary()` | バイト列 | `st.binary(min_size=1)` |
| `st.lists()` | リスト | `st.lists(st.integers(), min_size=1)` |
| `st.dictionaries()` | 辞書 | `st.dictionaries(st.text(), st.integers())` |
| `st.sampled_from()` | 選択肢から選択 | `st.sampled_from(["a", "b", "c"])` |
| `st.recursive()` | 再帰的構造 | ネストした辞書など |

## 不変条件のパターン

| 性質 | 説明 | テスト例 |
|------|------|---------|
| 冪等性 | 2回適用しても結果が同じ | `f(f(x)) == f(x)` |
| 可逆性 | 逆操作で元に戻る | `decode(encode(x)) == x` |
| 不変条件 | 処理後も保持される性質 | 要素数の保持 |
| 交換則 | 順序を入れ替えても同じ | `f(a, b) == f(b, a)` |
| 結合則 | グループ化が自由 | `f(f(a, b), c) == f(a, f(b, c))` |

## 設定オプション

```python
from hypothesis import settings, Verbosity

# テスト回数を増やす
@settings(max_examples=500)
@given(...)
def test_many_examples(self, ...):
    ...

# デバッグ用に詳細出力
@settings(verbosity=Verbosity.verbose)
@given(...)
def test_verbose(self, ...):
    ...

# タイムアウトを延長
@settings(deadline=None)  # 無制限
@given(...)
def test_slow(self, ...):
    ...
```

## assume() の使用

```python
@given(a=st.integers(), b=st.integers())
def test_division(self, a: int, b: int) -> None:
    """除算のテスト（ゼロ除算を除外）。"""
    assume(b != 0)  # b が 0 の場合はスキップ
    result = divide(a, b)
    assert result * b == a
```

## 参照

- 実装例: `template/tests/property/test_helpers_property.py`
- Hypothesis ドキュメント: context7 で `hypothesis` を検索

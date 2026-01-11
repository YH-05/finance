---
title: テスト戦略ガイドライン
description: t-wada流TDDとテスト作成のベストプラクティス
---

# テスト戦略ガイドライン

## TDD の基本サイクル

```
🔴 Red → 🟢 Green → 🔵 Refactor
```

1. **Red**: 失敗するテストを書く
2. **Green**: テストを通す最小限の実装（仮実装 OK）
3. **Refactor**: リファクタリング

## TDD 実践手順

### 1. TODO リスト作成

実装したい機能を最小単位に分解:

```
[ ] 基本的な機能の動作確認
[ ] エッジケースの処理
[ ] エラーハンドリング
[ ] パフォーマンス要件（必要な場合）
```

### 2. 失敗するテストを書く

```python
def test_正常系_有効なデータで処理成功():
    """chunk_listが正しくチャンク化できることを確認。"""
    result = chunk_list([1, 2, 3, 4, 5], 2)
    assert result == [[1, 2], [3, 4], [5]]
```

### 3. 最小限の実装

```python
# 仮実装（ハードコード）でもOK
def chunk_list(items, chunk_size):
    return [[1, 2], [3, 4], [5]]  # まずテストを通す
```

### 4. リファクタリング

テストが通った後、実装を一般化:

```python
def chunk_list(items: list[T], chunk_size: int) -> list[list[T]]:
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
```

## 三角測量

複数のテストケースで実装を一般化に導く手法。

```python
# Step 1: 仮実装で通す
def test_add_正の数():
    assert add(2, 3) == 5

def add(a, b):
    return 5  # 仮実装

# Step 2: 2つ目のテストで一般化を促す
def test_add_別の正の数():
    assert add(10, 20) == 30  # 仮実装では通らない

def add(a, b):
    return a + b  # 一般化

# Step 3: エッジケースを追加
def test_add_負の数():
    assert add(-1, -2) == -3

def test_add_ゼロ():
    assert add(0, 5) == 5
```

## テスト種別

### 1. 単体テスト（`tests/unit/`）

関数・クラスの基本動作を検証。

```python
class TestChunkList:
    """chunk_list関数のテスト。"""

    def test_正常系_リストを指定サイズに分割できる(self) -> None:
        """リストを指定サイズのチャンクに分割できることを確認。"""
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunks = chunk_list(items, 3)
        assert chunks == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

    def test_異常系_チャンクサイズが0以下でValueError(self) -> None:
        """チャンクサイズが0以下の場合、ValueErrorが発生。"""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_list([1, 2, 3], 0)

    def test_エッジケース_空のリストで空結果(self) -> None:
        """空のリストを処理できることを確認。"""
        assert chunk_list([], 5) == []
```

### 2. プロパティベーステスト（`tests/property/`）

Hypothesis による自動テストケース生成。

```python
from hypothesis import given
from hypothesis import strategies as st

class TestChunkListProperty:
    """chunk_listのプロパティベーステスト。"""

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
        # 最後以外は全てchunk_size
        for chunk in chunks[:-1]:
            assert len(chunk) == chunk_size
        # 最後は1以上chunk_size以下
        assert 1 <= len(chunks[-1]) <= chunk_size
```

### 3. 統合テスト（`tests/integration/`）

コンポーネント間の連携を検証。

```python
class TestDataProcessingPipeline:
    """データ処理パイプラインの統合テスト。"""

    def test_正常系_ファイル読込から処理まで(self, temp_dir: Path) -> None:
        """ファイル読込→データ処理→出力の一連の流れを確認。"""
        # 1. テストデータ作成
        input_file = temp_dir / "input.json"
        save_json_file({"items": [{"id": 1}, {"id": 2}]}, input_file)

        # 2. データ読込
        data = load_json_file(input_file)

        # 3. 処理実行
        processor = SimpleDataProcessor()
        result = process_data(data["items"], processor)

        # 4. 結果検証
        assert len(result) == 2
        assert all(item.get("processed") for item in result)
```

## テスト命名規則

```
test_[正常系|異常系|エッジケース]_条件で結果()
```

例:

-   `test_正常系_有効なデータで処理成功`
-   `test_異常系_不正なサイズでValueError`
-   `test_エッジケース_空リストで空結果`
-   `test_パラメトライズ_様々なサイズで正しく動作`

## パラメトライズテスト

```python
@pytest.mark.parametrize(
    "input_size,chunk_size,expected_chunks",
    [
        (10, 1, 10),   # 1要素ずつ
        (10, 5, 2),    # 半分ずつ
        (10, 10, 1),   # 全体で1チャンク
        (10, 15, 1),   # チャンクサイズが大きい
        (0, 5, 0),     # 空リスト
    ],
)
def test_パラメトライズ_様々なサイズで正しくチャンク数が計算される(
    self,
    input_size: int,
    chunk_size: int,
    expected_chunks: int,
) -> None:
    """様々なサイズの組み合わせで正しいチャンク数になることを確認。"""
    items = list(range(input_size))
    chunks = chunk_list(items, chunk_size)
    assert len(chunks) == expected_chunks
```

## フィクスチャ

`conftest.py` に共通フィクスチャを定義:

```python
@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """テスト用一時ディレクトリ。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    """テスト用サンプルデータ。"""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]

@pytest.fixture
def example_config() -> ExampleConfig:
    """テスト用設定。"""
    return ExampleConfig(name="test", max_items=10, enable_validation=True)
```

## TDD 実践の注意点

### DO（推奨）

-   1 テストで 1 つの振る舞いをテスト
-   Red → Green でコミット
-   日本語テスト名で意図を明確に
-   不安な部分から着手
-   テストリストを常に更新

### DON'T（非推奨）

-   一度に複数のテストを書く
-   テストなしで実装を進める
-   複雑なテストを最初から書く
-   テストの失敗を無視して進む

## リファクタリングのトリガー

以下の場合にリファクタリングを検討:

-   重複コードが発生
-   可読性が低下
-   SOLID 原則に違反
-   テストが複雑化

## テスト実行コマンド

```bash
# 全テスト
make test

# カバレッジ付き
make test-cov

# 単体テストのみ
make test-unit

# プロパティテストのみ
make test-property

# 統合テストのみ
make test-integration

# 特定テストのみ
uv run pytest tests/unit/test_example.py::TestExampleClass::test_正常系_初期化時は空のリスト -v
```

## 参照

-   単体テスト例: `template/tests/unit/test_example.py`
-   プロパティテスト例: `template/tests/property/test_helpers_property.py`
-   統合テスト例: `template/tests/integration/test_example.py`
-   フィクスチャ例: `template/tests/conftest.py`

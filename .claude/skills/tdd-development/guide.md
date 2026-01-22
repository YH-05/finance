# TDD 開発詳細ガイド

このガイドでは、t-wada 流 TDD の詳細なプロセスと実践手法を説明します。

## TDD サイクルの詳細フロー

### 1. TODO リスト作成

実装したい機能を最小単位に分解します：

```yaml
テスト TODO:
  - [ ] 正常系: 基本的な機能の動作確認
  - [ ] 正常系: 複数パターンの入力
  - [ ] 異常系: 無効な入力でエラー
  - [ ] エッジケース: 空入力、境界値
  - [ ] パフォーマンス: 大量データ処理（必要な場合）
```

**ポイント**:
- 不安な部分から着手する
- 小さく始める
- リストは常に更新する

### 2. Red: 失敗するテストを書く

```python
def test_正常系_有効なデータで処理成功():
    """chunk_list が正しくチャンク化できることを確認。"""
    result = chunk_list([1, 2, 3, 4, 5], 2)
    assert result == [[1, 2], [3, 4], [5]]
```

**ポイント**:
- テストは1つだけ書く
- 失敗を確認してから次へ
- テスト名は意図を明確に

### 3. Green: 最小限の実装

```python
# 仮実装（ハードコード）でも OK
def chunk_list(items, chunk_size):
    return [[1, 2], [3, 4], [5]]  # まずテストを通す
```

**ポイント**:
- 最短でテストを通す
- 仮実装は恥ずかしくない
- 完璧を目指さない

### 4. Refactor: リファクタリング

テストが通った後、実装を一般化：

```python
def chunk_list(items: list[T], chunk_size: int) -> list[list[T]]:
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
```

**ポイント**:
- テストが通る状態を維持
- 小さなステップで進める
- 重複を排除

## 三角測量（Triangulation）

複数のテストケースで実装を一般化に導く手法です。

### 基本パターン

```python
# Step 1: 最初のテスト（仮実装で通す）
def test_add_正の数():
    assert add(2, 3) == 5

def add(a, b):
    return 5  # 仮実装

# Step 2: 2つ目のテスト（一般化を促す）
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

### 三角測量が有効なケース

1. **ロジックが単純に見えるとき**
   - 仮実装で通せる場合は三角測量で一般化を促す

2. **複数のパターンが存在するとき**
   - 入力の組み合わせが多い場合

3. **境界条件が重要なとき**
   - 0, null, 空配列などのエッジケース

## テスト設計プロセス

### ステップ 1: 対象機能の分析

```yaml
分析観点:
  入力:
    - パラメータ名と型
    - 必須/オプション
    - 有効な値の範囲
  出力:
    - 戻り値の型
    - 成功/失敗の条件
  副作用:
    - ファイル I/O
    - データベース操作
    - 外部 API 呼び出し
  エラーケース:
    - 無効な入力
    - リソース不足
    - タイムアウト
  境界条件:
    - 空/null
    - 最小値/最大値
    - 配列の境界
```

### ステップ 2: テスト TODO リストの作成

```yaml
テスト TODO:
  正常系:
    - [ ] 基本的な機能の動作確認
    - [ ] 複数パターンの入力
    - [ ] オプションパラメータのテスト

  異常系:
    - [ ] 無効な入力でエラー
    - [ ] null/None の処理
    - [ ] 型不一致の処理

  エッジケース:
    - [ ] 空入力
    - [ ] 境界値（最小値、最大値）
    - [ ] 大量データ

  プロパティ:
    - [ ] 不変条件の検証
    - [ ] 可逆性の検証

  統合:
    - [ ] コンポーネント間連携
    - [ ] エンドツーエンドフロー
```

### ステップ 3: テストケースの分類と優先度付け

| 分類 | 配置先 | 優先度基準 |
|------|--------|-----------|
| 単体テスト | tests/{lib}/unit/ | P0: 主要正常系・クリティカルエラー |
| プロパティテスト | tests/{lib}/property/ | P1-P2: 不変条件・数学的性質 |
| 統合テスト | tests/{lib}/integration/ | P1: コンポーネント連携 |

## フィクスチャの活用

### 基本フィクスチャ（conftest.py）

```python
import pytest
from pathlib import Path
import tempfile
from collections.abc import Iterator

@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    """テスト用サンプルデータ。"""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]

@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """テスト用一時ディレクトリ。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def example_config() -> ExampleConfig:
    """テスト用設定。"""
    return ExampleConfig(name="test", max_items=10, enable_validation=True)
```

### フィクスチャのスコープ

| スコープ | 用途 |
|---------|------|
| function | 各テスト関数で新しいインスタンス（デフォルト） |
| class | 同じテストクラス内で共有 |
| module | 同じモジュール内で共有 |
| session | テストセッション全体で共有 |

```python
@pytest.fixture(scope="session")
def expensive_resource():
    """セッション全体で共有する重いリソース。"""
    resource = create_expensive_resource()
    yield resource
    resource.cleanup()
```

### パラメトライズテスト

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

## プロパティベーステストの設計

### Hypothesis の基本戦略

```python
from hypothesis import given, strategies as st

# 整数リスト
st.lists(st.integers())

# 正の整数
st.integers(min_value=1)

# テキスト
st.text(min_size=1, max_size=100)

# JSON 互換値
json_value = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(),
    lambda children: st.lists(children, max_size=5) | st.dictionaries(st.text(), children, max_size=5),
    max_leaves=20,
)
```

### 不変条件のパターン

```python
# 要素の保持
@given(items=st.lists(st.integers()))
def test_プロパティ_処理後も全要素が保持される(self, items):
    result = process(items)
    assert set(flatten(result)) == set(items)

# 可逆性
@given(data=st.text())
def test_プロパティ_エンコードデコードが可逆(self, data):
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data

# サイズの制約
@given(items=st.lists(st.integers(), min_size=1), chunk_size=st.integers(min_value=1, max_value=100))
def test_プロパティ_チャンクサイズが適切(self, items, chunk_size):
    chunks = chunk_list(items, chunk_size)
    for chunk in chunks[:-1]:
        assert len(chunk) == chunk_size
    assert 1 <= len(chunks[-1]) <= chunk_size
```

## TDD 実践の注意点

### DO（推奨）

| 推奨事項 | 理由 |
|---------|------|
| 1テストで1つの振る舞いをテスト | テスト失敗時に原因特定が容易 |
| Red → Green でコミット | 小さなステップで進捗を記録 |
| 日本語テスト名で意図を明確に | テスト結果の可読性向上 |
| 不安な部分から着手 | リスクの早期発見 |
| テストリストを常に更新 | 進捗の可視化 |

### DON'T（非推奨）

| 非推奨事項 | 理由 |
|---------|------|
| 一度に複数のテストを書く | フィードバックループが長くなる |
| テストなしで実装を進める | リグレッションリスク |
| 複雑なテストを最初から書く | 失敗時のデバッグが困難 |
| テストの失敗を無視して進む | 品質低下の原因 |

## リファクタリングのトリガー

以下の場合にリファクタリングを検討：

1. **重複コードが発生**
   - DRY 原則に違反している
   - コピペしたコードがある

2. **可読性が低下**
   - 関数が長すぎる（20行以上）
   - ネストが深い（3レベル以上）

3. **SOLID 原則に違反**
   - 単一責任原則（SRP）
   - オープン・クローズド原則（OCP）

4. **テストが複雑化**
   - セットアップが複雑
   - モックが多すぎる

## テストダブルの使い分け

| 種類 | 用途 | 例 |
|------|------|-----|
| Stub | 固定値を返す | API レスポンスのモック |
| Mock | 呼び出しを検証 | メソッド呼び出しの確認 |
| Spy | 実装を保持しつつ検証 | ログ出力の確認 |
| Fake | 簡易実装 | インメモリ DB |

```python
# Mock の例
from unittest.mock import Mock, patch

@patch('mymodule.external_api')
def test_正常系_外部APIが呼ばれる(self, mock_api):
    mock_api.return_value = {"status": "ok"}
    result = process_with_api()
    mock_api.assert_called_once()
    assert result["status"] == "ok"
```

## 参照テンプレート

- 単体テスト: `./templates/unit-test.md`
- プロパティテスト: `./templates/property-test.md`
- 統合テスト: `./templates/integration-test.md`
- テンプレート実装例: `template/tests/`

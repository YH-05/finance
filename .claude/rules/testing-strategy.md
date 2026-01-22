# テスト戦略

## 詳細ナレッジベース

TDD の詳細なガイドラインとテンプレートは以下のスキルを参照:

- **スキル**: `.claude/skills/tdd-development/SKILL.md`
- **詳細ガイド**: `.claude/skills/tdd-development/guide.md`
- **テンプレート**: `.claude/skills/tdd-development/templates/`

## TDD の基本サイクル

```
Red → Green → Refactor
```

1. **Red**: 失敗するテストを書く
2. **Green**: テストを通す最小限の実装（仮実装 OK）
3. **Refactor**: リファクタリング

## テスト種別

| 種別 | ディレクトリ | 説明 |
|------|-------------|------|
| 単体テスト | `tests/unit/` | 関数・クラスの基本動作を検証 |
| プロパティテスト | `tests/property/` | Hypothesis による自動テストケース生成 |
| 統合テスト | `tests/integration/` | コンポーネント間の連携を検証 |

## テスト命名規則

```
test_[正常系|異常系|エッジケース]_条件で結果()
```

例:
- `test_正常系_有効なデータで処理成功`
- `test_異常系_不正なサイズでValueError`
- `test_エッジケース_空リストで空結果`
- `test_パラメトライズ_様々なサイズで正しく動作`

## 単体テスト例

```python
class TestChunkList:
    def test_正常系_リストを指定サイズに分割できる(self) -> None:
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunks = chunk_list(items, 3)
        assert chunks == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

    def test_異常系_チャンクサイズが0以下でValueError(self) -> None:
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_list([1, 2, 3], 0)

    def test_エッジケース_空のリストで空結果(self) -> None:
        assert chunk_list([], 5) == []
```

## プロパティベーステスト例

```python
from hypothesis import given
from hypothesis import strategies as st

class TestChunkListProperty:
    @given(
        items=st.lists(st.integers()),
        chunk_size=st.integers(min_value=1, max_value=100),
    )
    def test_プロパティ_チャンク化しても全要素が保持される(
        self,
        items: list[int],
        chunk_size: int,
    ) -> None:
        chunks = chunk_list(items, chunk_size)
        flattened = [item for chunk in chunks for item in chunk]
        assert flattened == items
```

## テスト実行コマンド

```bash
make test              # 全テスト
make test-cov          # カバレッジ付き
make test-unit         # 単体テストのみ
make test-property     # プロパティテストのみ
make test-integration  # 統合テストのみ

# 特定テストのみ
uv run pytest tests/unit/test_example.py::TestClass::test_method -v
```

## TDD 実践の注意点

### DO（推奨）

- 1テストで1つの振る舞いをテスト
- Red → Green でコミット
- 日本語テスト名で意図を明確に
- 不安な部分から着手
- テストリストを常に更新

### DON'T（非推奨）

- 一度に複数のテストを書く
- テストなしで実装を進める
- 複雑なテストを最初から書く
- テストの失敗を無視して進む

## 参照

- **TDDスキル**: `.claude/skills/tdd-development/SKILL.md`（推奨）
- テンプレート: `template/tests/`
- 詳細ガイド: `docs/testing-strategy.md`

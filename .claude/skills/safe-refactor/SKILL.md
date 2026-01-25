---
name: safe-refactor
description: テストカバレッジを維持しながら安全にリファクタリング。/safe-refactor コマンドで使用。
allowed-tools: Read, Bash, Task, Edit
---

# 安全なリファクタリング

テストカバレッジを維持しながら、コードを安全にリファクタリングするスキルです。template/ディレクトリの実装パターンを参考にして、コードの品質と保守性を向上させます。

## 目的

このスキルは以下を提供します：

- **安全なリファクタリング手法**: テストを維持しながらコードを改善
- **リファクタリングパターン集**: template/ ディレクトリの実装例に基づくパターン
- **品質検証プロセス**: リファクタリング前後の品質保証
- **段階的な改善手順**: 小さなステップでの確実な進行

## いつ使用するか

### プロアクティブ使用（自動で使用を検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討してください：

1. **コード品質の問題**
   - 複雑度が高い関数が検出された
   - 重複コードが見つかった
   - 型安全性が低い箇所がある
   - エラーハンドリングが不十分

2. **リファクタリングの必要性**
   - 「コードを整理したい」
   - 「可読性を改善したい」
   - 「保守性を向上させたい」

3. **テンプレート準拠**
   - template/ ディレクトリの実装パターンへの準拠が必要
   - コーディング規約への適合が必要

### 明示的な使用（ユーザー要求）

- `/safe-refactor` コマンド
- 「リファクタリングして」という直接的な要求

## 基本原則

1. **テストが通ることを確認** - リファクタリング前後でテストが通ることを保証
2. **小さなステップで進める** - 一度に大きな変更を加えない
3. **パターンの参照** - template/ディレクトリの実装例を参考にする
4. **コミットの頻度** - 各リファクタリングステップでコミット

## リファクタリングパターン

### パターン1: 型安全性の向上

**参考**: `template/src/template_package/types.py`

```python
# Before: 辞書をそのまま使用
def process_item(item: dict) -> dict:
    return {"id": item["id"], "processed": True}

# After: TypedDictを使用
from typing import TypedDict

class ItemDict(TypedDict):
    id: int
    name: str
    value: int

class ProcessedItemDict(ItemDict):
    processed: bool

def process_item(item: ItemDict) -> ProcessedItemDict:
    return {**item, "processed": True}
```

### パターン2: エラーハンドリングの改善

**参考**: `template/src/template_package/core/example.py`

```python
# Before: 単純なエラー
if not data:
    raise ValueError("Invalid data")

# After: 具体的で実用的なエラー
if not data:
    raise ValueError(
        f"Data cannot be empty when validation is enabled. "
        f"Either provide valid data or set validate=False."
    )
```

### パターン3: ロギングの追加

**参考**: `template/src/template_package/utils/logging_config.py`

```python
from project_name.utils.logging_config import get_logger

logger = get_logger(__name__)

def process_data(data: list) -> list:
    logger.debug(f"Processing {len(data)} items")

    try:
        result = [transform(item) for item in data]
        logger.info(f"Successfully processed {len(result)} items")
        return result
    except Exception as e:
        logger.error(f"Failed to process data: {e}", exc_info=True)
        raise
```

### パターン4: テストの追加・改善

**参考**: `template/tests/`

- 単体テスト: 正常系・異常系・エッジケース
- プロパティベーステスト: Hypothesisを使用した自動テスト
- 統合テスト: コンポーネント間の連携

### パターン5: パフォーマンスの最適化

**参考**: `template/src/template_package/utils/profiling.py`

```python
from project_name.utils.profiling import profile, timeit

@timeit
def optimized_function(data: list) -> list:
    # リスト内包表記を使用
    return [item * 2 for item in data if item > 0]

@profile
def heavy_computation():
    # プロファイリング対象の処理
    pass
```

## プロセス

### ステップ 1: 現状の確認

リファクタリング前にベースラインを記録します。

```bash
# テストが通ることを確認
make test

# カバレッジを記録
make test-cov
```

**チェックポイント**:
- [ ] 全テストが成功している
- [ ] カバレッジ率を記録している

### ステップ 2: リファクタリング対象の特定

以下の観点で改善対象を特定します：

- 複雑度の高い関数
- 重複コード
- 型安全性が低い箇所
- エラーハンドリングが不十分な箇所

**ツールの使用**:
```bash
# 複雑度チェック
make lint

# 型チェック
make typecheck
```

### ステップ 3: 段階的なリファクタリング

1つの改善点に集中して進めます。

**実施内容**:
1. リファクタリングパターンを選択
2. 小さな変更を実施
3. テストを実行して動作確認
4. コミット（リファクタリング内容を明記）

**コミットメッセージ例**:
```
refactor(core): 型安全性の向上

- ItemDict を導入して型安全性を確保
- TypedDict で辞書の構造を明示化

テストカバレッジ: 85% → 85% (維持)
```

### ステップ 4: 品質チェック

リファクタリング後の品質を検証します。

**quality-checker サブエージェント（--validate-only モード）** を使用:
```yaml
subagent_type: "quality-checker"
description: "Validate refactored code"
prompt: |
  リファクタリング後の品質検証を実行してください。
  ## モード
  --validate-only
```

**追加確認**:
```bash
# カバレッジが維持されているか確認
make test-cov

# パフォーマンスの確認（必要に応じて）
make benchmark
```

**チェックポイント**:
- [ ] テストが全て成功
- [ ] カバレッジが維持または向上
- [ ] リント・型チェックがパス
- [ ] パフォーマンスが劣化していない

## リファクタリングのチェックリスト

リファクタリング実施時の確認項目：

- [ ] 関数は単一責任の原則に従っているか
- [ ] 適切な型ヒントが付けられているか
- [ ] エラーメッセージは具体的で実用的か
- [ ] 適切なロギングが実装されているか
- [ ] テストカバレッジは維持/向上しているか
- [ ] template/の実装パターンに準拠しているか
- [ ] ドキュメント（docstring）は更新されているか

## 使用例

### 例1: 型安全性の向上

**状況**: 辞書を多用している関数があり、型安全性が低い

**処理**:
1. 現状確認: `make test` でベースライン記録
2. TypedDict を導入
3. テスト実行: 動作確認
4. コミット: `refactor: TypedDict導入で型安全性向上`

**期待される出力**:
```
型安全性向上完了
- ItemDict, ProcessedItemDict を追加
- process_item() の型ヒントを改善

テスト: ✓ 全て成功
カバレッジ: 85% → 85%（維持）
型チェック: ✓ エラーなし
```

---

### 例2: エラーハンドリングの改善

**状況**: ValueError が曖昧なメッセージで投げられている

**処理**:
1. エラーメッセージを具体的に改善
2. 解決策をメッセージに含める
3. テスト実行: エラーケースのテストも確認
4. コミット: `refactor: エラーメッセージを具体化`

**期待される出力**:
```
エラーハンドリング改善完了
- ValueError のメッセージを具体化
- 解決策を明記

テスト: ✓ 全て成功
例外テスト: ✓ 適切なメッセージを検証
```

---

### 例3: ロギングの追加

**状況**: 関数にロギングが実装されていない

**処理**:
1. `get_logger(__name__)` を追加
2. debug, info, error レベルのログを実装
3. テスト実行: 動作確認
4. コミット: `refactor: ロギング追加`

**期待される出力**:
```
ロギング追加完了
- logger を導入
- debug: 処理開始
- info: 処理成功
- error: 例外発生時

テスト: ✓ 全て成功
```

---

### 例4: パフォーマンス最適化

**状況**: ループ処理が遅い

**処理**:
1. プロファイリング: `@profile` で計測
2. リスト内包表記に変更
3. ベンチマーク: 改善を確認
4. コミット: `perf: リスト内包表記で30%高速化`

**期待される出力**:
```
パフォーマンス最適化完了
- ループ → リスト内包表記

計測結果:
  変更前: 500ms
  変更後: 350ms
  改善率: 30%

テスト: ✓ 全て成功
```

## 品質基準

このスキルの成果物は以下の品質基準を満たす必要があります：

### 必須（MUST）

- [ ] リファクタリング前後でテストが成功している
- [ ] カバレッジが維持または向上している
- [ ] リント・型チェックがパスしている
- [ ] 各リファクタリングステップでコミットしている
- [ ] コミットメッセージに改善内容を明記している

### 推奨（SHOULD）

- template/ ディレクトリの実装パターンに準拠している
- quality-checker サブエージェントで品質検証を実施している
- パフォーマンスが劣化していない（ベンチマーク確認）
- ドキュメント（docstring）が更新されている

### 禁止（NEVER）

- [ ] テストを削除する
- [ ] 外部動作を変更する（リファクタリングは内部構造の改善のみ）
- [ ] 一度に大きな変更を行う
- [ ] テストなしでリファクタリングを進める

## 注意事項

1. **動作の変更は避ける** - リファクタリングは内部構造の改善であり、外部動作は変えない
2. **テストファースト** - テストがない場合は先にテストを書く
3. **段階的コミット** - 大きな変更は小さなコミットに分割
4. **レビューの準備** - 変更理由を明確に説明できるようにする

## 完了条件

このスキルは以下の条件を満たした場合に完了とする：

- [ ] リファクタリング対象が全て改善されている
- [ ] 全テストが成功している
- [ ] カバレッジが維持または向上している
- [ ] 品質チェック（make check-all）がパスしている
- [ ] 各改善がコミットされている
- [ ] quality-checker サブエージェントでの検証が完了している

## 関連スキル

- **coding-standards**: Python コーディング規約
- **tdd-development**: TDD 開発プロセス
- **error-handling**: エラーハンドリングパターン

## 関連エージェント

- **quality-checker**: コード品質の検証・自動修正
- **code-simplifier**: コードの複雑性削減

## 参考資料

- `template/src/template_package/types.py`: 型定義の実装例
- `template/src/template_package/core/example.py`: 関数設計の実装例
- `template/src/template_package/utils/logging_config.py`: ロギング実装例
- `template/src/template_package/utils/profiling.py`: プロファイリング実装例
- `template/tests/`: テスト実装例

## 出力フォーマット

### リファクタリング完了時

```
================================================================================
                    リファクタリング完了
================================================================================

## 改善内容
- 型安全性向上: TypedDict 導入
- エラーハンドリング改善: 具体的なメッセージ
- ロギング追加: debug/info/error レベル

## 品質メトリクス
| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| テスト成功率 | 100% | 100% |
| カバレッジ | 85% | 87% |
| 複雑度 | 15 | 8 |

## コミット履歴
- refactor(core): TypedDict導入で型安全性向上
- refactor(core): エラーメッセージを具体化
- refactor(core): ロギング追加

================================================================================
```

このスキルを使用することで、コードベースを継続的に改善し、長期的な保守性を確保できます。

---
description: t-wada流TDDによるテスト作成
allowed-tools: Task
---

# /write-tests - t-wada流TDDによるテスト作成

> **役割の明確化**: このコマンドは**TDDによるテスト作成**に特化しています。
>
> - コード品質の自動修正 → `/ensure-quality`
> - 既存コードのバグ調査 → `/troubleshoot`
> - コードの詳細分析 → `/analyze`

**目的**: t-wada流TDDサイクル（Red→Green→Refactor）に基づく高品質なテストの作成

## 詳細ナレッジベース

TDD の詳細なガイドラインとテンプレートは以下のスキルを参照:

- **スキル**: `.claude/skills/tdd-development/SKILL.md`
- **詳細ガイド**: `.claude/skills/tdd-development/guide.md`
- **テンプレート**: `.claude/skills/tdd-development/templates/`

## アーキテクチャ

```
test-orchestrator (オーケストレーター)
    │
    ├── [Phase 1] test-planner (設計)
    │       ↓ テスト設計が完了
    ├── [Phase 2] 並列実行
    │   ├── test-unit-writer ────┐
    │   │                        ├── 並列実行（50%高速化）
    │   └── test-property-writer ┘
    │       ↓ 単体・プロパティテストが完了
    └── [Phase 3] test-integration-writer (依存実行)
```

### パフォーマンス改善

| 項目 | 従来 (順序実行) | 最適化後 (並列) | 改善率 |
|------|----------------|-----------------|--------|
| 単体+プロパティ | 順序実行 | 並列実行 | 50%削減 |
| 全体実行時間 | 100% | 60-70% | 30-40%削減 |

## 実行方法

### 基本的な使用（推奨）

**test-orchestrator サブエージェント** を使用:

```yaml
subagent_type: "test-orchestrator"
description: "Create tests with TDD"
prompt: |
  以下の機能のテストを作成してください。

  ## 対象
  {target_description}

  ## ライブラリ
  {library_name}

  ## 要件
  - TDDサイクル (Red→Green→Refactor)
  - 単体テスト、プロパティテスト、統合テストの作成
```

### 個別エージェントの使用

特定のテスト種類のみ作成する場合:

```yaml
# 単体テストのみ
subagent_type: "test-unit-writer"

# プロパティテストのみ
subagent_type: "test-property-writer"

# 統合テストのみ
subagent_type: "test-integration-writer"

# 従来の統合エージェント（全種類を順序実行）
subagent_type: "test-writer"
```

## TDDの基本サイクル

1. 🔴 **Red**: 失敗するテストを書く
2. 🟢 **Green**: テストを通す最小限の実装
3. 🔵 **Refactor**: リファクタリング

## 実行手順

### Phase 1: テスト設計（test-planner）

```yaml
テストTODO:
  - [ ] 正常系: 基本的な機能の動作確認
  - [ ] 異常系: エラーハンドリング
  - [ ] エッジケース: 境界値、空入力
  - [ ] プロパティ: 不変条件の検証
  - [ ] 統合: コンポーネント連携
```

### Phase 2: テスト作成（並列実行）

**単体テスト** (test-unit-writer)
- 関数・クラスの基本動作
- 正常系・異常系・エッジケース
- パラメトライズテストの活用

**プロパティテスト** (test-property-writer)
- Hypothesisによる自動テストケース生成
- 不変条件の検証
- エッジケースの自動発見

### Phase 3: 統合テスト（test-integration-writer）

- コンポーネント間の連携
- ファイルI/Oやデータ処理パイプライン
- エラーのカスケード処理

## テストファイルの配置

```
tests/{library}/
├── unit/                      # 単体テスト
│   └── test_{module}.py
├── property/                  # プロパティベーステスト
│   └── test_{module}_property.py
├── integration/               # 統合テスト
│   └── test_{module}_integration.py
└── conftest.py               # 共通フィクスチャ
```

## テストの命名規則

日本語で意図を明確に表現:

```python
def test_正常系_有効なデータで処理成功():
    """chunk_listが正しくチャンク化できることを確認。"""

def test_異常系_不正なサイズでValueError():
    """チャンクサイズが0以下の場合、ValueErrorが発生することを確認。"""

def test_エッジケース_空リストで空結果():
    """空のリストをチャンク化すると空の結果が返されることを確認。"""

# プロパティテスト
@given(st.lists(st.integers()))
def test_prop_不変条件_要素数の保存(items: list[int]):
    """処理後も要素の総数が変わらないことを確認。"""
```

## templateディレクトリの参考例

| テスト種類 | テンプレート |
|-----------|-------------|
| 単体テスト | `template/tests/unit/test_example.py` |
| プロパティテスト | `template/tests/property/test_helpers_property.py` |
| 統合テスト | `template/tests/integration/test_example.py` |
| フィクスチャ | `template/tests/conftest.py` |

## 三角測量の実践例

```python
# Step 1: 最初のテスト（仮実装で通す）
def test_add_正の数():
    assert add(2, 3) == 5

def add(a, b):
    return 5  # 仮実装

# Step 2: 2つ目のテスト（一般化を促す）
def test_add_別の正の数():
    assert add(10, 20) == 30  # これで仮実装では通らない

def add(a, b):
    return a + b  # 一般化

# Step 3: エッジケースを追加
def test_add_負の数():
    assert add(-1, -2) == -3
```

## TDD実践時の注意点

1. **テストは1つずつ追加** - 一度に複数のテストを書かない
2. **小さく頻繁にコミット** - Red→Green、Refactor完了でコミット
3. **テストの粒度** - 1つのテストで1つの振る舞いをテスト
4. **リファクタリングの判断** - 重複コード、可読性、設計原則
5. **テストファーストの徹底** - 必ず失敗するテストから書く

## 実行コマンド

```bash
# テストの実行
make test              # 全テスト実行
make test-unit         # 単体テストのみ
make test-property     # プロパティベーステストのみ
make test-cov          # カバレッジ付きテスト

# 特定のテストを実行
uv run pytest tests/unit/test_example.py -v
uv run pytest tests/unit/test_example.py::TestClass::test_method -v
```

## 関連エージェント

| エージェント | 役割 |
|-------------|------|
| test-orchestrator | テスト作成の並列実行制御 |
| test-planner | テスト設計・TODOリスト作成 |
| test-unit-writer | 単体テスト作成 |
| test-property-writer | プロパティテスト作成 |
| test-integration-writer | 統合テスト作成 |
| test-writer | 従来の統合エージェント（順序実行） |

このコマンドを使用することで、堅牢で保守性の高いテストスイートを効率的に構築できます。

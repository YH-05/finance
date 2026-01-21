# フェーズ2「コーディングスキル」詳細実装計画

## エグゼクティブサマリー

フェーズ2では3つのスキルを実装し、実装時の品質を自動的に確保する基盤を構築する。

| スキル | 目的 | プリロード対象エージェント |
|--------|------|--------------------------|
| coding-standards | コーディング規約の即座参照 | feature-implementer, code-simplifier, quality-checker, test-*-writer |
| tdd-development | TDDプロセスとテンプレート | test-orchestrator, test-planner, test-*-writer, feature-implementer |
| error-handling | エラー設計パターン | feature-implementer, code-simplifier |

---

## 設計方針

### 1. スキルの粒度

**決定**: 3つの大スキル + 内部モジュール分割

調査で推奨された7つの小スキル（hint-converter, naming-normalizer等）は、3つの大スキル内の`examples/`や`templates/`として組み込む。

**理由**:
- フェーズ1のスキル構造（SKILL.md + guide.md + scripts/）と統一
- スキルプリロードで1-2個のスキルを参照する設計と整合
- エージェントからの参照しやすさ

### 2. 既存エージェントとの関係

**決定**: エージェントはスキルを参照する形に更新

- エージェントの役割（オーケストレーション、実行）は維持
- スキルはナレッジベースとして機能
- エージェント定義にフロントマターで`skills:`を追加

---

## 2.1 コーディング規約スキル (coding-standards)

### 構造

```
.claude/skills/coding-standards/
├── SKILL.md              # クイックリファレンス（型ヒント、命名、Docstring）
├── guide.md              # 詳細規約（docs/coding-standards.mdから移行・整理）
├── examples/
│   ├── type-hints.md     # PEP 695詳細例
│   ├── docstrings.md     # NumPy形式詳細例
│   ├── error-messages.md # エラーメッセージパターン
│   ├── naming.md         # 命名規則詳細例
│   └── logging.md        # ロギング実装パターン
└── scripts/
    ├── __init__.py
    └── style_checker.py  # スタイルチェックユーティリティ
```

### SKILL.md 概要

```markdown
---
name: coding-standards
description: Pythonコーディング規約。型ヒント(PEP695)、命名規則、Docstring、エラーメッセージ、ロギングの標準。
allowed-tools: Read
---
```

**クイックリファレンス内容**:
- 型ヒント: `list[str]`, `def first[T](...)`, `type Alias = ...`
- 命名規則: snake_case/PascalCase/UPPER_SNAKE、Boolean接頭辞
- Docstring: NumPy形式の必須セクション
- エラーメッセージ: 具体的で解決策を示す
- ロギング: `get_logger(__name__)`

### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.1.1 | SKILL.md の作成 | なし | `.claude/skills/coding-standards/SKILL.md` |
| 2.1.2 | guide.md の作成（docs/coding-standards.mdから移行・整理） | 2.1.1 | `guide.md` |
| 2.1.3 | examples/type-hints.md の作成 | 2.1.1 | `examples/type-hints.md` |
| 2.1.4 | examples/docstrings.md の作成 | 2.1.1 | `examples/docstrings.md` |
| 2.1.5 | examples/error-messages.md の作成 | 2.1.1 | `examples/error-messages.md` |
| 2.1.6 | examples/naming.md の作成 | 2.1.1 | `examples/naming.md` |
| 2.1.7 | examples/logging.md の作成 | 2.1.1 | `examples/logging.md` |
| 2.1.8 | scripts/style_checker.py の実装 | 2.1.2 | `scripts/style_checker.py` |
| 2.1.9 | エージェントへのスキル参照追加 | 2.1.2 | エージェント更新 |
| 2.1.10 | .claude/rules/coding-standards.md の更新 | 2.1.2 | ルール更新 |
| 2.1.11 | docs/coding-standards.md の移行・更新 | 2.1.2 | docsをリンクのみに |
| 2.1.12 | テスト・検証 | 2.1.9 | 動作確認 |

**並列実行可能**: 2.1.3〜2.1.7

### scripts/style_checker.py 仕様

```python
"""
スタイルチェックユーティリティ

機能:
- 型ヒントカバレッジ計算
- 命名規則違反検出
- Docstringカバレッジ計算
- ロギング実装チェック

使用例:
uv run python .claude/skills/coding-standards/scripts/style_checker.py \
    --path src/market_analysis/ \
    --output json

入力: ファイルパスまたはディレクトリパス
出力: JSON形式のチェック結果
{
    "type_hint_coverage": 0.85,
    "docstring_coverage": 0.70,
    "naming_violations": [...],
    "logging_coverage": 0.90
}
"""
```

---

## 2.2 TDD開発スキル (tdd-development)

### 構造

```
.claude/skills/tdd-development/
├── SKILL.md              # TDDサイクル、命名規則、ファイル配置
├── guide.md              # 詳細プロセス（三角測量、優先度付け、context7連携）
├── templates/
│   ├── unit-test.md      # 単体テストテンプレート
│   ├── property-test.md  # プロパティテストテンプレート
│   └── integration-test.md # 統合テストテンプレート
└── scripts/
    ├── __init__.py
    └── test_planner.py   # テスト設計支援スクリプト
```

### SKILL.md 概要

```markdown
---
name: tdd-development
description: t-wada流TDD（Red→Green→Refactor）。テスト設計、単体・プロパティ・統合テストのテンプレート。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- TDDサイクル: 🔴Red → 🟢Green → 🔵Refactor
- テスト命名: `test_正常系_xxx`, `test_異常系_xxx`, `test_エッジケース_xxx`
- ファイル配置: `tests/{library}/unit/`, `property/`, `integration/`
- context7必須ケース: pytest高度機能、Hypothesis、pytest-asyncio

### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.2.1 | SKILL.md の作成 | なし | `.claude/skills/tdd-development/SKILL.md` |
| 2.2.2 | guide.md の作成（test-writer, test-plannerから統合） | 2.2.1 | `guide.md` |
| 2.2.3 | templates/unit-test.md の作成 | 2.2.1 | `templates/unit-test.md` |
| 2.2.4 | templates/property-test.md の作成 | 2.2.1 | `templates/property-test.md` |
| 2.2.5 | templates/integration-test.md の作成 | 2.2.1 | `templates/integration-test.md` |
| 2.2.6 | scripts/test_planner.py の実装 | 2.2.2 | `scripts/test_planner.py` |
| 2.2.7 | テストエージェント群へのスキル参照追加 | 2.2.2 | エージェント更新 |
| 2.2.8 | /write-tests コマンドの更新 | 2.2.2 | コマンド更新 |
| 2.2.9 | .claude/rules/testing-strategy.md の更新 | 2.2.2 | ルール更新 |
| 2.2.10 | docs/testing-strategy.md の移行・更新 | 2.2.2 | docsをリンクのみに |
| 2.2.11 | テスト・検証 | 2.2.7 | 動作確認 |

**並列実行可能**: 2.2.3〜2.2.5

### scripts/test_planner.py 仕様

```python
"""
テスト設計支援スクリプト

機能:
- 対象モジュールのAST分析
- 公開関数/クラスの抽出
- テストTODOリストの自動生成
- 優先度の自動付与（P0-P3）

使用例:
uv run python .claude/skills/tdd-development/scripts/test_planner.py \
    --module src/market_analysis/core/fetcher.py \
    --library market_analysis \
    --output yaml

入力: モジュールパス、ライブラリ名
出力: YAML形式のテスト設計書
test_design:
  target: "src/market_analysis/core/fetcher.py"
  library: "market_analysis"
  unit_tests:
    - name: "test_正常系_基本的なデータ取得"
      priority: "P0"
      target_function: "fetch_data"
  property_tests:
    - name: "test_prop_不変条件_データ整合性"
      priority: "P1"
  integration_tests:
    - name: "test_統合_APIエンドツーエンド"
      priority: "P2"
"""
```

---

## 2.3 エラーハンドリングスキル (error-handling)

### 構造

```
.claude/skills/error-handling/
├── SKILL.md              # パターン選択ガイド、シンプル/リッチ概要
├── guide.md              # 詳細設計原則、例外階層、リトライ戦略
├── examples/
│   ├── simple-pattern.md   # シンプルパターン（RSS方式）
│   ├── rich-pattern.md     # リッチパターン（Market Analysis方式）
│   ├── retry-patterns.md   # リトライ・フォールバック
│   └── logging-integration.md # ロギング統合パターン
└── scripts/
    ├── __init__.py
    └── exception_generator.py # 例外クラス生成スクリプト
```

### SKILL.md 概要

```markdown
---
name: error-handling
description: Pythonエラーハンドリングパターン。シンプル/リッチ例外設計、リトライ、ロギング統合。
allowed-tools: Read, Write
---
```

**パターン選択ガイド**:
| 条件 | 推奨パターン |
|------|------------|
| 内部ライブラリ、シンプルな例外 | シンプルパターン（RSS方式） |
| 外部API連携、詳細情報必要 | リッチパターン（Market Analysis方式） |
| エラーのシリアライズ必要 | リッチパターン |

### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.3.1 | SKILL.md の作成 | なし | `.claude/skills/error-handling/SKILL.md` |
| 2.3.2 | guide.md の作成 | 2.3.1 | `guide.md` |
| 2.3.3 | examples/simple-pattern.md の作成 | 2.3.1 | `examples/simple-pattern.md` |
| 2.3.4 | examples/rich-pattern.md の作成 | 2.3.1 | `examples/rich-pattern.md` |
| 2.3.5 | examples/retry-patterns.md の作成 | 2.3.1 | `examples/retry-patterns.md` |
| 2.3.6 | examples/logging-integration.md の作成 | 2.3.1 | `examples/logging-integration.md` |
| 2.3.7 | scripts/exception_generator.py の実装 | 2.3.2 | `scripts/exception_generator.py` |
| 2.3.8 | エージェントへのスキル参照追加 | 2.3.2 | エージェント更新 |
| 2.3.9 | テスト・検証 | 2.3.8 | 動作確認 |

**並列実行可能**: 2.3.3〜2.3.6

### scripts/exception_generator.py 仕様

```python
"""
例外クラス生成スクリプト

機能:
- シンプルパターンの例外クラス生成（RSS方式）
- リッチパターンの例外クラス生成（Market Analysis方式）
- ErrorCode列挙型の自動生成
- errors.pyまたはexceptions.pyファイルの作成

使用例:
# シンプルパターン
uv run python .claude/skills/error-handling/scripts/exception_generator.py \
    --package rss \
    --pattern simple \
    --errors "FeedNotFoundError,FeedFetchError,FeedParseError"

# リッチパターン
uv run python .claude/skills/error-handling/scripts/exception_generator.py \
    --package market_analysis \
    --pattern rich \
    --errors "DataFetchError:API_ERROR,ValidationError:INVALID_PARAMETER"

入力:
- --package: パッケージ名
- --pattern: simple | rich
- --errors: エラークラス名のカンマ区切り（リッチパターンの場合はデフォルトコード付き）
- --output: 出力ファイルパス（オプション、デフォルト: src/{package}/errors.py）

出力: src/{package}/errors.py または src/{package}/exceptions.py
"""
```

---

## 依存関係グラフ

```
フェーズ0（基盤整備）
    │
    └── フェーズ1（レポジトリ管理）
            │
            └── フェーズ2（コーディング）
                    │
                    ├── 2.1 coding-standards ─┐
                    ├── 2.2 tdd-development  ─┼─ 並列実行可能
                    └── 2.3 error-handling  ─┘
```

---

## 完了基準

### スキル作成
- [ ] `.claude/skills/coding-standards/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/tdd-development/` が存在し、SKILL.md, guide.md, templates/ が揃っている
- [ ] `.claude/skills/error-handling/` が存在し、SKILL.md, guide.md, examples/ が揃っている

### エージェント更新
- [ ] `feature-implementer.md` が `skills: [coding-standards, tdd-development, error-handling]` を参照
- [ ] `code-simplifier.md` が `skills: [coding-standards, error-handling]` を参照
- [ ] `quality-checker.md` が `skills: [coding-standards]` を参照
- [ ] テスト関連エージェント群が `skills: [tdd-development, coding-standards]` を参照

### スクリプト動作確認
- [ ] `style_checker.py` が型ヒントカバレッジを計算できる
- [ ] `test_planner.py` がYAML形式のテスト設計書を出力できる
- [ ] `exception_generator.py` がシンプル/リッチ両パターンで例外クラスを生成できる

### 品質確認
- [ ] `make check-all` が成功
- [ ] 既存のテストが全てパス

---

## 変更対象ファイル

### 新規作成
| ファイル | 説明 |
|----------|------|
| `.claude/skills/coding-standards/` | コーディング規約スキル一式 |
| `.claude/skills/tdd-development/` | TDD開発スキル一式 |
| `.claude/skills/error-handling/` | エラーハンドリングスキル一式 |

### 更新対象
| ファイル | 変更内容 |
|----------|----------|
| `.claude/agents/feature-implementer.md` | skills参照追加 |
| `.claude/agents/code-simplifier.md` | skills参照追加 |
| `.claude/agents/quality-checker.md` | skills参照追加 |
| `.claude/agents/test-orchestrator.md` | skills参照追加 |
| `.claude/agents/test-planner.md` | skills参照追加 |
| `.claude/agents/test-unit-writer.md` | skills参照追加 |
| `.claude/agents/test-property-writer.md` | skills参照追加 |
| `.claude/agents/test-integration-writer.md` | skills参照追加 |
| `.claude/commands/write-tests.md` | スキル参照追加 |
| `.claude/rules/coding-standards.md` | スキルへのリンク追加 |
| `.claude/rules/testing-strategy.md` | スキルへのリンク追加 |

---

## 参照ファイル（実装時に読み込む）

| 用途 | ファイル |
|------|----------|
| コーディング規約元データ | `docs/coding-standards.md` |
| テスト戦略元データ | `docs/testing-strategy.md` |
| シンプルエラーパターン | `src/rss/exceptions.py` |
| リッチエラーパターン | `src/market_analysis/errors.py` |
| スキル構造テンプレート | `.claude/skills/agent-expert/SKILL.md` |
| test-writer実装 | `.claude/agents/test-writer.md` |
| test-planner実装 | `.claude/agents/test-planner.md` |

---

## 検証方法

1. **スキル参照テスト**: feature-implementerエージェントを起動し、coding-standardsスキルが参照されることを確認
2. **TDDワークフローテスト**: /write-testsコマンドを実行し、tdd-developmentスキルのテンプレートが使用されることを確認
3. **エラー設計テスト**: 新規パッケージでerror-handlingスキルを参照し、例外クラスが適切に生成されることを確認

---

## 決定事項

| 項目 | 決定内容 |
|------|----------|
| Pythonスクリプト | 全て実装（style_checker.py, test_planner.py, exception_generator.py） |
| docs/coding-standards.md | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |
| docs/testing-strategy.md | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |

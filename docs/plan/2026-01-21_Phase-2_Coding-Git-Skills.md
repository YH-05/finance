# フェーズ 2: コーディングスキル + Git操作スキル

> 元ドキュメント: `2026-01-21_System-Update-Implementation.md`

## 目標

### Wave 1: コーディングスキル
- Pythonコーディング規約スキル
- TDD開発スキル
- エラーハンドリングスキル

### Wave 2: Git操作スキル
- worktree-management スキル（worktree, worktree-done, plan-worktrees, create-worktrees, delete-worktrees を統合）
- git-workflow スキル（push, commit-and-pr, merge-pr, gemini-search を統合）

---

## 設計方針

### 1. スキルの粒度

**Wave 1 決定**: 3つの大スキル + 内部モジュール分割

調査で推奨された7つの小スキル（hint-converter, naming-normalizer等）は、3つの大スキル内の`examples/`や`templates/`として組み込む。

**理由**:
- フェーズ1のスキル構造（SKILL.md + guide.md + examples/）と統一
- スキルプリロードで1-2個のスキルを参照する設計と整合
- エージェントからの参照しやすさ

**Wave 2 決定**: 2つの大スキルに機能を統合

- **worktree-management**: 並列開発環境の管理に特化
- **git-workflow**: Git操作とPR管理に特化

**理由**:
- 関連する機能を1つのスキルに集約し、参照を容易にする
- スキル完成後、対応するコマンドを削除

### 2. 既存エージェントとの関係

**決定**: エージェントはスキルを参照する形に更新

- エージェントの役割（オーケストレーション、実行）は維持
- スキルはナレッジベースとして機能
- エージェント定義にフロントマターで`skills:`を追加

### 3. コマンドとスキルの関係

**決定**: コマンドはスキルを参照する形式に変更（**スキル完成後、削除**）

- スキル完成後、対応するコマンドを削除
- 実際のロジック・ガイダンスはスキルに集約

---

## 依存関係グラフ

```
フェーズ0（基盤整備）
    │
    └── フェーズ1（レポジトリ管理）
            │
            └── フェーズ2（コーディング + Git操作）
                    │
                    ├── Wave 1: コーディングスキル
                    │   ├── 2.1 coding-standards ─┐
                    │   ├── 2.2 tdd-development  ─┼─ 並列実行可能
                    │   └── 2.3 error-handling  ─┘
                    │
                    └── Wave 2: Git操作スキル
                        ├── 2.4 worktree-management ─┐
                        └── 2.5 git-workflow         ─┴─ 並列実行可能
```

---

## Wave 1: コーディングスキル

### 2.1 コーディング規約スキル (coding-standards)

#### 構造

```
.claude/skills/coding-standards/
├── SKILL.md              # クイックリファレンス（型ヒント、命名、Docstring）
├── guide.md              # 詳細規約（docs/coding-standards.mdから移行・整理）
└── examples/
    ├── type-hints.md     # PEP 695詳細例
    ├── docstrings.md     # NumPy形式詳細例
    ├── error-messages.md # エラーメッセージパターン
    ├── naming.md         # 命名規則詳細例
    └── logging.md        # ロギング実装パターン
```

**活用ツール**: スタイルチェックは `ruff`、`pyright` を Bash 経由で使用

#### SKILL.md 概要

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

**プリロード対象エージェント**:
- `feature-implementer`
- `code-simplifier`
- `quality-checker`
- `test-*-writer`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.1.1 | SKILL.md の作成 | なし | `.claude/skills/coding-standards/SKILL.md` |
| 2.1.2 | guide.md の作成（docs/coding-standards.mdから移行・整理） | 2.1.1 | `guide.md` |
| 2.1.3 | examples/type-hints.md の作成 | 2.1.1 | `examples/type-hints.md` |
| 2.1.4 | examples/docstrings.md の作成 | 2.1.1 | `examples/docstrings.md` |
| 2.1.5 | examples/error-messages.md の作成 | 2.1.1 | `examples/error-messages.md` |
| 2.1.6 | examples/naming.md の作成 | 2.1.1 | `examples/naming.md` |
| 2.1.7 | examples/logging.md の作成 | 2.1.1 | `examples/logging.md` |
| 2.1.8 | エージェントへのスキル参照追加 | 2.1.2 | エージェント更新 |
| 2.1.9 | .claude/rules/coding-standards.md の更新 | 2.1.2 | ルール更新 |
| 2.1.10 | docs/coding-standards.md の移行・更新 | 2.1.2 | docsをリンクのみに |
| 2.1.11 | 検証 | 2.1.8 | 動作確認 |

**並列実行可能**: 2.1.3〜2.1.7

---

### 2.2 TDD開発スキル (tdd-development)

#### 構造

```
.claude/skills/tdd-development/
├── SKILL.md              # TDDサイクル、命名規則、ファイル配置
├── guide.md              # 詳細プロセス（三角測量、優先度付け、context7連携）
└── templates/
    ├── unit-test.md      # 単体テストテンプレート
    ├── property-test.md  # プロパティテストテンプレート
    └── integration-test.md # 統合テストテンプレート
```

**活用ツール**: テスト実行は `pytest` を Bash 経由で使用、テスト設計は Claude の推論能力を活用

#### SKILL.md 概要

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

**プリロード対象エージェント**:
- `test-orchestrator`
- `test-planner`
- `test-*-writer`
- `feature-implementer`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.2.1 | SKILL.md の作成 | なし | `.claude/skills/tdd-development/SKILL.md` |
| 2.2.2 | guide.md の作成（test-writer, test-plannerから統合） | 2.2.1 | `guide.md` |
| 2.2.3 | templates/unit-test.md の作成 | 2.2.1 | `templates/unit-test.md` |
| 2.2.4 | templates/property-test.md の作成 | 2.2.1 | `templates/property-test.md` |
| 2.2.5 | templates/integration-test.md の作成 | 2.2.1 | `templates/integration-test.md` |
| 2.2.6 | テストエージェント群へのスキル参照追加 | 2.2.2 | エージェント更新 |
| 2.2.7 | /write-tests コマンドの更新 | 2.2.2 | コマンド更新 |
| 2.2.8 | .claude/rules/testing-strategy.md の更新 | 2.2.2 | ルール更新 |
| 2.2.9 | docs/testing-strategy.md の移行・更新 | 2.2.2 | docsをリンクのみに |
| 2.2.10 | 検証 | 2.2.6 | 動作確認 |

**並列実行可能**: 2.2.3〜2.2.5

---

### 2.3 エラーハンドリングスキル (error-handling)

#### 構造

```
.claude/skills/error-handling/
├── SKILL.md              # パターン選択ガイド、シンプル/リッチ概要
├── guide.md              # 詳細設計原則、例外階層、リトライ戦略
└── examples/
    ├── simple-pattern.md   # シンプルパターン（RSS方式）
    ├── rich-pattern.md     # リッチパターン（Market Analysis方式）
    ├── retry-patterns.md   # リトライ・フォールバック
    └── logging-integration.md # ロギング統合パターン
```

**活用ツール**: 例外クラス生成は Claude の生成能力 + examples/ のテンプレートを活用

#### SKILL.md 概要

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

**プリロード対象エージェント**:
- `feature-implementer`
- `code-simplifier`

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.3.1 | SKILL.md の作成 | なし | `.claude/skills/error-handling/SKILL.md` |
| 2.3.2 | guide.md の作成 | 2.3.1 | `guide.md` |
| 2.3.3 | examples/simple-pattern.md の作成 | 2.3.1 | `examples/simple-pattern.md` |
| 2.3.4 | examples/rich-pattern.md の作成 | 2.3.1 | `examples/rich-pattern.md` |
| 2.3.5 | examples/retry-patterns.md の作成 | 2.3.1 | `examples/retry-patterns.md` |
| 2.3.6 | examples/logging-integration.md の作成 | 2.3.1 | `examples/logging-integration.md` |
| 2.3.7 | エージェントへのスキル参照追加 | 2.3.2 | エージェント更新 |
| 2.3.8 | 検証 | 2.3.7 | 動作確認 |

**並列実行可能**: 2.3.3〜2.3.6

---

## Wave 2: Git操作スキル

### 2.4 worktree-management スキル

#### 構造

```
.claude/skills/worktree-management/
├── SKILL.md              # クイックリファレンス（概要、基本操作）
├── guide.md              # 詳細ガイド（並列開発戦略、Wave管理）
└── examples/
    ├── create-worktree.md      # worktree作成パターン
    ├── parallel-development.md # 並列開発ワークフロー
    └── cleanup.md              # クリーンアップパターン
```

#### SKILL.md 概要

```markdown
---
name: worktree-management
description: Git worktreeを使用した並列開発環境の管理。作成・計画・クリーンアップのベストプラクティス。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- worktree の作成パターン（ブランチ命名規則）
- 並列開発計画（Wave グルーピング）
- クリーンアップフロー（PRマージ確認→削除）
- .mcp.json コピーの重要性

**統合対象コマンド**:
- `/worktree` - worktree作成
- `/worktree-done` - worktreeクリーンアップ
- `/plan-worktrees` - 並列開発計画
- `/create-worktrees` - 一括worktree作成
- `/delete-worktrees` - 一括worktree削除

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.4.1 | SKILL.md の作成 | なし | `.claude/skills/worktree-management/SKILL.md` |
| 2.4.2 | guide.md の作成 | 2.4.1 | `guide.md` |
| 2.4.3 | examples/create-worktree.md の作成 | 2.4.1 | `examples/create-worktree.md` |
| 2.4.4 | examples/parallel-development.md の作成 | 2.4.1 | `examples/parallel-development.md` |
| 2.4.5 | examples/cleanup.md の作成 | 2.4.1 | `examples/cleanup.md` |
| 2.4.6 | コマンドのスキル参照追加 | 2.4.2 | コマンド更新 |
| 2.4.7 | 検証 | 2.4.6 | 動作確認 |

**並列実行可能**: 2.4.3〜2.4.5

---

### 2.5 git-workflow スキル

#### 構造

```
.claude/skills/git-workflow/
├── SKILL.md              # クイックリファレンス（コミット、PR、マージ）
├── guide.md              # 詳細ガイド（Conventional Commits、CI確認）
└── examples/
    ├── commit-patterns.md    # コミットメッセージパターン
    ├── pr-creation.md        # PR作成ワークフロー
    ├── merge-workflow.md     # マージワークフロー
    └── web-search.md         # Gemini検索パターン
```

#### SKILL.md 概要

```markdown
---
name: git-workflow
description: Git操作とPR管理のベストプラクティス。コミット、プッシュ、PR作成、マージ、Web検索。
allowed-tools: Read, Bash
---
```

**クイックリファレンス内容**:
- Conventional Commits フォーマット
- PR作成フロー（品質チェック→コミット→PR）
- マージフロー（コンフリクトチェック→CI確認→マージ）
- Gemini CLI を使用した Web 検索

**統合対象コマンド**:
- `/push` - コミット＆プッシュ
- `/commit-and-pr` - コミット＆PR作成
- `/merge-pr` - PRマージ
- `/gemini-search` - Web検索

#### タスクテーブル

| # | タスク | 依存 | 成果物 |
|---|--------|------|--------|
| 2.5.1 | SKILL.md の作成 | なし | `.claude/skills/git-workflow/SKILL.md` |
| 2.5.2 | guide.md の作成 | 2.5.1 | `guide.md` |
| 2.5.3 | examples/commit-patterns.md の作成 | 2.5.1 | `examples/commit-patterns.md` |
| 2.5.4 | examples/pr-creation.md の作成 | 2.5.1 | `examples/pr-creation.md` |
| 2.5.5 | examples/merge-workflow.md の作成 | 2.5.1 | `examples/merge-workflow.md` |
| 2.5.6 | examples/web-search.md の作成 | 2.5.1 | `examples/web-search.md` |
| 2.5.7 | コマンドのスキル参照追加 | 2.5.2 | コマンド更新 |
| 2.5.8 | 検証 | 2.5.7 | 動作確認 |

**並列実行可能**: 2.5.3〜2.5.6

---

## タスク分解（GitHub Issue）

### Wave 1: コーディングスキル

（各スキルのタスクテーブル参照）

### Wave 2: Git操作スキル

#### worktree-management スキル

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 2.4 | [スキル移行] worktree-management スキル SKILL.md の作成 | M | なし |
| 2.5 | [スキル移行] worktree-management スキル guide.md の作成 | M | #2.4 |
| 2.6 | [スキル移行] worktree-management スキル examples/ の作成 | M | #2.4 |
| 2.7 | [スキル移行] worktree-management スキル コマンド統合 | S | #2.5 |

#### git-workflow スキル

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 2.8 | [スキル移行] git-workflow スキル SKILL.md の作成 | M | なし |
| 2.9 | [スキル移行] git-workflow スキル guide.md の作成 | M | #2.8 |
| 2.10 | [スキル移行] git-workflow スキル examples/ の作成 | M | #2.8 |
| 2.11 | [スキル移行] git-workflow スキル コマンド統合 | S | #2.9 |

#### 統合テスト

| # | タイトル | 工数 | 依存 |
|---|---------|------|------|
| 2.12 | [スキル移行] フェーズ2 Wave 2 統合テスト | M | #2.7, #2.11 |

---

## 完了基準

### Wave 1: コーディングスキル

#### スキル作成
- [ ] `.claude/skills/coding-standards/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/tdd-development/` が存在し、SKILL.md, guide.md, templates/ が揃っている
- [ ] `.claude/skills/error-handling/` が存在し、SKILL.md, guide.md, examples/ が揃っている

#### エージェント更新
- [ ] `feature-implementer.md` が `skills: [coding-standards, tdd-development, error-handling]` を参照
- [ ] `code-simplifier.md` が `skills: [coding-standards, error-handling]` を参照
- [ ] `quality-checker.md` が `skills: [coding-standards]` を参照
- [ ] テスト関連エージェント群が `skills: [tdd-development, coding-standards]` を参照

#### 品質確認
- [ ] `make check-all` が成功
- [ ] 既存のテストが全てパス

### Wave 2: Git操作スキル

#### スキル作成
- [ ] `.claude/skills/worktree-management/` が存在し、SKILL.md, guide.md, examples/ が揃っている
- [ ] `.claude/skills/git-workflow/` が存在し、SKILL.md, guide.md, examples/ が揃っている

#### コマンド更新
- [ ] `/worktree` がスキルを参照
- [ ] `/worktree-done` がスキルを参照
- [ ] `/plan-worktrees` がスキルを参照
- [ ] `/create-worktrees` がスキルを参照
- [ ] `/delete-worktrees` がスキルを参照
- [ ] `/push` がスキルを参照
- [ ] `/commit-and-pr` がスキルを参照
- [ ] `/merge-pr` がスキルを参照
- [ ] `/gemini-search` がスキルを参照

#### 品質確認
- [ ] 各コマンドが既存と同等の機能を提供
- [ ] スキルの guide.md が参照可能

---

## 検証手順

1. **スキル参照テスト**: feature-implementerエージェントを起動し、coding-standardsスキルが参照されることを確認
2. **TDDワークフローテスト**: /write-testsコマンドを実行し、tdd-developmentスキルのテンプレートが使用されることを確認
3. **エラー設計テスト**: 新規パッケージでerror-handlingスキルを参照し、例外クラスが適切に生成されることを確認

---

## 決定事項

| 項目 | 決定内容 |
|------|----------|
| Pythonスクリプト | **実装しない**（既存ツール ruff/pyright/pytest を活用） |
| docs/coding-standards.md | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |
| docs/testing-strategy.md | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |
| Git操作コマンド | スキルを参照する形式に変更（**スキル完成後、削除**） |
| worktree関連 | worktree-management スキルに統合 |
| Git操作関連 | git-workflow スキルに統合 |
| gemini-search | git-workflow スキルに統合（Web検索機能） |

---

## 重要ファイル一覧

### 参照元

| ファイル | 役割 |
|---------|------|
| `docs/coding-standards.md` | コーディング規約元データ |
| `docs/testing-strategy.md` | テスト戦略元データ |
| `src/rss/exceptions.py` | シンプルエラーパターン |
| `src/market_analysis/errors.py` | リッチエラーパターン |
| `.claude/agents/test-writer.md` | test-writer実装 |
| `.claude/agents/test-planner.md` | test-planner実装 |

### 新規作成

| ファイル | 内容 |
|----------|------|
| `.claude/skills/coding-standards/` | コーディング規約スキル一式 |
| `.claude/skills/tdd-development/` | TDD開発スキル一式 |
| `.claude/skills/error-handling/` | エラーハンドリングスキル一式 |
| `.claude/skills/worktree-management/` | Worktree管理スキル |
| `.claude/skills/git-workflow/` | Git操作スキル |

### 変更対象（Wave 1）

| ファイル | 変更内容 |
|----------|----------|
| `.claude/agents/feature-implementer.md` | スキルプリロード参照を追加、`skills: [coding-standards, tdd-development, error-handling]` |
| `.claude/agents/code-simplifier.md` | `skills: [coding-standards, error-handling]` を参照 |
| `.claude/agents/quality-checker.md` | `skills: [coding-standards]` を参照 |
| `.claude/agents/test-orchestrator.md` | `skills: [tdd-development, coding-standards]` を参照 |
| `.claude/agents/test-planner.md` | `skills: [tdd-development, coding-standards]` を参照 |
| `.claude/agents/test-unit-writer.md` | skills参照追加 |
| `.claude/agents/test-property-writer.md` | skills参照追加 |
| `.claude/agents/test-integration-writer.md` | skills参照追加 |
| `.claude/commands/write-tests.md` | スキル参照追加 |
| `.claude/rules/coding-standards.md` | スキルへのリンク追加 |
| `.claude/rules/testing-strategy.md` | スキルへのリンク追加 |
| `docs/coding-standards.md` | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |
| `docs/testing-strategy.md` | スキルへ移行（docs/はスキルへの参照リンクのみ残す） |

### 変更対象（Wave 2）

| ファイル | 変更内容 |
|----------|----------|
| `.claude/commands/worktree.md` | worktree-management スキルを参照 |
| `.claude/commands/worktree-done.md` | worktree-management スキルを参照 |
| `.claude/commands/plan-worktrees.md` | worktree-management スキルを参照 |
| `.claude/commands/create-worktrees.md` | worktree-management スキルを参照 |
| `.claude/commands/delete-worktrees.md` | worktree-management スキルを参照 |
| `.claude/commands/push.md` | git-workflow スキルを参照 |
| `.claude/commands/commit-and-pr.md` | git-workflow スキルを参照 |
| `.claude/commands/merge-pr.md` | git-workflow スキルを参照 |
| `.claude/commands/gemini-search.md` | git-workflow スキルを参照 |

---

## 関連ドキュメント

- [フェーズ0: 基盤整備](./2026-01-21_Phase-0_Foundation.md)
- [フェーズ1: レポジトリ管理スキル](./2026-01-21_Phase-1_Repository-Management.md)
- [フェーズ3: 金融分析スキル](./2026-01-21_Phase-3_Finance-Skills.md)

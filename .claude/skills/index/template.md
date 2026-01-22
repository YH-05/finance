# Index スキル テンプレート

## ディレクトリ構成テンプレート

### 標準形式

```
{project_name}/                             # Project root
├── .claude/                                # Claude Code configuration
│   ├── agents/                             # ({count} agents)
│   ├── commands/                           # ({count} commands)
│   ├── rules/                              # 共有ルール定義
│   ├── skills/                             # ({count} skills)
│   │   ├── {skill-name}/
│   │   └── ...
│   ├── settings.json
│   └── agents.md
│
├── .github/                                # GitHub configuration
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   └── ...
│
├── data/                                   # Data storage layer
│   ├── config/
│   ├── raw/
│   ├── processed/
│   └── exports/
│
├── docs/                                   # Repository documentation
│   ├── {doc-name}.md
│   └── project/                            # Project documentation
│       └── project-{n}/
│
├── src/                                    # Source code
│   ├── {package_name}/                     # Package
│   │   ├── core/
│   │   ├── utils/
│   │   ├── types.py
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── py.typed
│   └── ...
│
├── tests/                                  # Test suite
│   ├── unit/
│   ├── property/
│   └── integration/
│
├── template/                               # Reference templates (read-only)
│
├── CLAUDE.md                               # Project instructions
├── README.md                               # Project overview
├── Makefile                                # Build automation
├── pyproject.toml                          # Python project config
└── uv.lock                                 # Dependency lock file
```

## コメント記法

### カウント表記

ディレクトリ内のファイル数やサブディレクトリ数を表示:

```
├── agents/                             # ({count} agents)
├── commands/                           # ({count} commands)
├── skills/                             # ({count} skills)
```

### プロジェクト説明

プロジェクトディレクトリの目的を表示:

```
├── project-7/                          # エージェント開発
├── project-11/                         # note金融コンテンツ発信強化
├── project-14/                         # 金融ニュース収集
```

### ファイル説明

特定のファイルの用途を表示:

```
├── sqlite_client.py                    # OLTP database client
├── duckdb_client.py                    # OLAP database client
```

## 省略表記ルール

### 同種ファイルの省略

同じパターンのファイルが複数ある場合:

```
# 悪い例（冗長）
├── test_module1.py
├── test_module2.py
├── test_module3.py
├── test_module4.py
├── test_module5.py

# 良い例（省略）
├── unit/                               # (5 test files)
```

### サブディレクトリの省略

詳細が不要なサブディレクトリ:

```
# 深さ制限を超える場合
├── factors/                            # Factor implementations
│   ├── macro/
│   ├── price/
│   ├── quality/
│   ├── size/
│   └── value/

# 標準的なパッケージ構造
├── {package_name}/
│   ├── core/
│   ├── utils/
│   └── ...                             # 詳細は README.md 参照
```

## テーブルテンプレート

### コマンド一覧テーブル

```markdown
| コマンド | 説明 |
| -------- | ---- |
| `/analyze` | 多次元コード分析（分析レポート出力） |
| `/commit-and-pr` | 変更のコミットと PR 作成 |
| `/ensure-quality` | コード品質の自動改善（make check-all 相当） |
```

### スキル一覧テーブル

```markdown
| スキル | 説明 |
| ------ | ---- |
| `agent-expert` | Create and optimize specialized Claude Code agents |
| `architecture-design` | アーキテクチャ設計書を作成するための詳細ガイドとテンプレート |
| `skill-expert` | Create and optimize Claude Code skills |
```

### エージェント一覧テーブル

```markdown
### 汎用エージェント

| エージェント | 説明 |
| ------------ | ---- |
| `Bash` | コマンド実行。git 操作、ターミナルタスク用 |
| `Explore` | コードベース探索。ファイルパターン検索、キーワード検索 |
| `Plan` | 実装計画の設計。ステップバイステップの計画作成 |
```

## マーカーテンプレート

### COMMANDS マーカー

```markdown
## コマンド一覧

<!-- AUTO-GENERATED: COMMANDS -->

| コマンド | 説明 |
| -------- | ---- |
| `/analyze` | 多次元コード分析（分析レポート出力） |
...

<!-- END: COMMANDS -->
```

### SKILLS マーカー

```markdown
## スキル一覧

<!-- AUTO-GENERATED: SKILLS -->

| スキル | 説明 |
| ------ | ---- |
| `agent-expert` | Create and optimize specialized Claude Code agents |
...

<!-- END: SKILLS -->
```

### AGENTS マーカー

```markdown
## エージェント一覧

<!-- AUTO-GENERATED: AGENTS -->

詳細は `.claude/agents.md` を参照。

### 汎用エージェント

| エージェント | 説明 |
| ------------ | ---- |
| `Bash` | コマンド実行 |
...

<!-- END: AGENTS -->
```

### DIRECTORY マーカー

```markdown
## ディレクトリ構成

<!-- AUTO-GENERATED: DIRECTORY -->

```
finance/                                    # Project root
├── .claude/                                # Claude Code configuration
...
```

<!-- END: DIRECTORY -->
```

## 完全な index.md テンプレート

```markdown
---
description: SuperClaudeコマンドリファレンス
---

# SuperClaude リファレンス

このコマンドは、プロジェクトで利用可能なコマンド、スキル、エージェントの一覧を表示・更新します。

## 実行モード

| モード | コマンド          | 説明                                           |
| ------ | ----------------- | ---------------------------------------------- |
| 表示   | `/index`          | 現在のリファレンスを表示                       |
| 更新   | `/index --update` | コマンド/スキル/エージェント/ディレクトリを自動検出して更新 |

---

## コマンド一覧

<!-- AUTO-GENERATED: COMMANDS -->

| コマンド | 説明 |
| -------- | ---- |
| `/analyze` | 多次元コード分析 |
...

<!-- END: COMMANDS -->

---

## スキル一覧

<!-- AUTO-GENERATED: SKILLS -->

| スキル | 説明 |
| ------ | ---- |
| `skill-expert` | スキル設計・管理 |
...

<!-- END: SKILLS -->

---

## エージェント一覧

<!-- AUTO-GENERATED: AGENTS -->

詳細は `.claude/agents.md` を参照。

### 汎用エージェント

| エージェント | 説明 |
| ------------ | ---- |
| `Bash` | コマンド実行 |
...

<!-- END: AGENTS -->

---

## ディレクトリ構成

<!-- AUTO-GENERATED: DIRECTORY -->

```
finance/                                    # Project root
├── .claude/
...
```

<!-- END: DIRECTORY -->
```

## 出力フォーマットテンプレート

### 更新完了時

```
================================================================================
                    /index --update 完了
================================================================================

## 更新結果

| 対象 | 状態 | 変更内容 |
|------|------|----------|
| コマンド | ✓ | {count} 件 |
| スキル | ✓ | {count} 件 |
| エージェント | ✓ | {count} 件 |
| ディレクトリ | ✓ | 更新済み |

## 更新したファイル
- .claude/commands/index.md
- CLAUDE.md（ディレクトリ構成）
- README.md（プロジェクト構造）

================================================================================
```

### 警告あり完了時

```
================================================================================
                    /index --update 完了（警告あり）
================================================================================

## 警告

⚠ {file_path}: {warning_message}

## 更新結果

| 対象 | 状態 | 変更内容 |
|------|------|----------|
| コマンド | ⚠ | {count} 件（{error_count} 件エラー） |
| スキル | ✓ | {count} 件 |
| エージェント | ✓ | {count} 件 |
| ディレクトリ | ✓ | 更新済み |

## 更新したファイル
- .claude/commands/index.md
- CLAUDE.md（ディレクトリ構成）
- README.md（プロジェクト構造）

## 推奨アクション
1. {recommended_action}

================================================================================
```

### エラー終了時

```
================================================================================
                    /index --update エラー
================================================================================

## エラー内容

✗ {error_type}: {error_message}

## 対処方法

{resolution_steps}

================================================================================
```

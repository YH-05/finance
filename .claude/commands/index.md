---
description: SuperClaudeコマンドリファレンス
---

# SuperClaude リファレンス

このコマンドは、プロジェクトで利用可能なコマンド、スキル、エージェントの一覧を表示・更新します。

## 実行モード

| モード | コマンド | 説明 |
|--------|----------|------|
| 表示 | `/index` | 現在のリファレンスを表示 |
| 更新 | `/index --update` | コマンド/スキル/エージェントを自動検出して更新 |

### 自動検出の仕組み

- **コマンド**: `.claude/commands/*.md` の frontmatter `description` から検出
- **スキル**: `.claude/skills/*/SKILL.md` の frontmatter `name`, `description` から検出
- **エージェント**: `.claude/agents.md` から読み込み

---

## コマンド一覧

<!-- AUTO-GENERATED: COMMANDS -->

| コマンド | 説明 |
|----------|------|
| `/issue` | GitHub Issue とタスクの管理・同期を行う |
| `/analyze` | 多次元コード分析（分析レポート出力） |
| `/commit-and-pr` | 変更のコミットとPR作成 |
| `/ensure-quality` | コード品質の自動改善（make check-all相当） |
| `/gemini-search` | Web search using Gemini CLI |
| `/improve` | エビデンスベースの改善実装 |
| `/new-package` | モノレポ内に新しいPythonパッケージを作成する |
| `/new-project` | プロジェクトファイルから開発を開始。LRD・設計ドキュメント作成とタスク分解を行う |
| `/push` | 変更をコミットしてリモートにプッシュ |
| `/review-docs` | ドキュメントの詳細レビューをサブエージェントで実行 |
| `/safe-refactor` | 安全なリファクタリング |
| `/scan` | セキュリティと品質の包括的検証 |
| `/setup-repository` | テンプレートリポジトリの初期化（初回のみ） |
| `/task` | 複雑なタスクの管理 |
| `/troubleshoot` | 体系的なデバッグ |
| `/worktree` | 新しいworktreeとブランチを作成して開発を開始 |
| `/worktree-done` | worktreeの開発完了後、PRマージ確認を経て安全にクリーンアップ |
| `/write-tests` | t-wada流TDDによるテスト作成 |

<!-- END: COMMANDS -->

---

## スキル一覧

<!-- AUTO-GENERATED: SKILLS -->

| スキル | 説明 |
|--------|------|
| `architecture-design` | アーキテクチャ設計書を作成するための詳細ガイドとテンプレート |
| `development-guidelines` | 開発プロセスとコーディング規約を確立するためのガイドとテンプレート |
| `functional-design` | 機能設計書を作成するための詳細ガイドとテンプレート |
| `glossary-creation` | 用語集を作成するための詳細ガイドとテンプレート |
| `prd-writing` | ライブラリ要求定義書(LRD)を作成するための詳細ガイドとテンプレート |
| `project-file` | プロジェクトファイル（project.md）を作成・編集するためのガイド |
| `repository-structure` | リポジトリ構造定義書を作成するための詳細ガイドとテンプレート |

<!-- END: SKILLS -->

---

## エージェント一覧

<!-- AUTO-GENERATED: AGENTS -->

詳細は `.claude/agents.md` を参照。

### 汎用

| エージェント | 説明 |
|-------------|------|
| `Bash` | コマンド実行。git操作、ターミナルタスク用 |
| `general-purpose` | 複雑な質問の調査、コード検索、マルチステップタスク |
| `Explore` | コードベース探索。ファイルパターン検索、キーワード検索 |
| `Plan` | 実装計画の設計。ステップバイステップの計画作成 |

### 品質・分析

| エージェント | 説明 |
|-------------|------|
| `quality-checker` | コード品質の検証・自動修正 |
| `code-analyzer` | コード品質、アーキテクチャ、パフォーマンスの多次元分析 |
| `security-scanner` | OWASP Top 10 に基づくセキュリティ脆弱性の検証 |
| `implementation-validator` | 実装コードの品質検証、スペックとの整合性確認 |

### 開発

| エージェント | 説明 |
|-------------|------|
| `test-writer` | t-wada流TDDに基づくテスト作成 |
| `feature-implementer` | TDDループを自動実行 |
| `debugger` | 体系的なデバッグ |
| `improvement-implementer` | エビデンスベースの改善実装 |

### ドキュメント

| エージェント | 説明 |
|-------------|------|
| `functional-design-writer` | 機能設計書作成 |
| `architecture-design-writer` | アーキテクチャ設計書作成 |
| `development-guidelines-writer` | 開発ガイドライン作成 |
| `repository-structure-writer` | リポジトリ構造定義書作成 |
| `glossary-writer` | 用語集作成 |
| `doc-reviewer` | ドキュメントレビュー |
| `task-decomposer` | タスク分解・GitHub Issues連携・project.md同期 |

<!-- END: AGENTS -->

---

## コマンド選択ガイド

### 品質関連

| やりたいこと | コマンド |
|--------------|----------|
| エラーを自動修正したい | `/ensure-quality` |
| 品質スコアを確認したい | `/scan` |
| コードを分析したい | `/analyze` |
| 改善を実装したい | `/improve` |

### 開発フロー

| やりたいこと | コマンド |
|--------------|----------|
| 独立した作業環境で開発したい | `/worktree <feature-name>` |
| 開発完了後のクリーンアップ | `/worktree-done` |
| 新しいパッケージを作りたい | `/new-package <name>` |
| 新規開発を始めたい | `/new-project @src/<pkg>/docs/project.md` |
| Issue を管理したい | `/issue @src/<pkg>/docs/project.md` |
| テストを書きたい | `/write-tests` |
| リファクタリングしたい | `/safe-refactor` |
| 問題を解決したい | `/troubleshoot` |
| 変更をプッシュしたい | `/push` |
| PR を作成したい | `/commit-and-pr` |

---

## 効率的なワークフロー

### 新機能開発（独立環境で）

```
/worktree feature/xxx → /new-project → /issue → feature-implementer で実装 → /write-tests → /commit-and-pr → (マージ) → /worktree-done
```

### 新機能開発

```
/new-package → /new-project → /issue → feature-implementer で実装 → /write-tests → /push
```

### バグ修正

```
/worktree fix/xxx → /troubleshoot → 修正 → /ensure-quality → /commit-and-pr → (マージ) → /worktree-done
```

### パフォーマンス最適化

```
/analyze → /improve → /scan → /push
```

---

## 更新手順（--update モード）

1. `.claude/commands/*.md` をスキャンし frontmatter から description を抽出
2. `.claude/skills/*/SKILL.md` をスキャンし frontmatter から name, description を抽出
3. `.claude/agents.md` からエージェント定義を読み込み
4. この index.md を更新
5. 結果を表示

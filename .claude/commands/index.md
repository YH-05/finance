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
- **ディレクトリ構成**: プロジェクトルートから4層までスキャン（除外: `__pycache__`, `.git`, `.venv` 等）

### 更新対象ファイル

| ファイル | 更新内容 |
|----------|----------|
| `.claude/commands/index.md` | コマンド/スキル/エージェント/ディレクトリ一覧 |
| `CLAUDE.md` | ディレクトリ構成セクション |
| `README.md` | プロジェクト構造セクション |

---

## コマンド一覧

<!-- AUTO-GENERATED: COMMANDS -->

| コマンド | 説明 |
|----------|------|
| `/analyze` | 多次元コード分析（分析レポート出力） |
| `/analyze-conflicts` | PRのコンフリクトを詳細分析し、問題点と解決策を提示 |
| `/commit-and-pr` | 変更のコミットとPR作成 |
| `/ensure-quality` | コード品質の自動改善（make check-all相当） |
| `/finance-edit` | 金融記事の編集ワークフロー（初稿→批評→修正） |
| `/finance-research` | 金融記事のリサーチワークフロー（データ収集→分析→検証→可視化） |
| `/finance-suggest-topics` | 金融記事のトピック提案（スコアリング付き） |
| `/gemini-search` | Web search using Gemini CLI |
| `/improve` | エビデンスベースの改善実装 |
| `/issue` | GitHub Issue とタスクの管理・同期を行う |
| `/merge-pr` | PRのコンフリクトチェック・CI確認・マージを実行 |
| `/new-finance-article` | 新規金融記事フォルダ作成（カテゴリ別テンプレート） |
| `/new-package` | モノレポ内に新しいPythonパッケージを作成する |
| `/new-project` | 開発プロジェクトを開始（パッケージ開発または軽量プロジェクト） |
| `/push` | 変更をコミットしてリモートにプッシュ |
| `/review-docs` | ドキュメントの詳細レビューをサブエージェントで実行 |
| `/review-pr` | PRレビュー（コード品質・セキュリティ・テスト） |
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
| `agent-memory` | メモリの保存・呼び出し・整理を行うスキル |
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

### 特殊

| エージェント | 説明 |
|-------------|------|
| `claude-code-guide` | Claude Code CLI、Agent SDK、APIに関する質問対応 |
| `statusline-setup` | ステータスライン設定 |

<!-- END: AGENTS -->

---

## ディレクトリ構成

<!-- AUTO-GENERATED: DIRECTORY -->

```
finance/
├── .claude/                      # Claude Code 設定
│   ├── agents/                   # サブエージェント定義 (42)
│   ├── commands/                 # スラッシュコマンド (25)
│   └── skills/                   # スキル定義 (8)
├── .github/                      # GitHub automation
│   ├── ISSUE_TEMPLATE/           # Issue テンプレート
│   └── workflows/                # CI/CD
├── data/                         # データストレージ
│   ├── config/                   # 設定ファイル
│   ├── sqlite/                   # SQLite DB（OLTP）
│   ├── duckdb/                   # DuckDB（OLAP）
│   ├── raw/                      # 生データ（Parquet）
│   │   ├── yfinance/             # yfinance データ
│   │   └── fred/                 # FRED 経済指標
│   ├── processed/                # 加工済みデータ
│   ├── exports/                  # エクスポート（CSV/JSON）
│   └── schemas/                  # JSON スキーマ
├── docs/                         # 共通ドキュメント
├── snippets/                     # 再利用コンテンツ
├── src/
│   ├── finance/                  # 共通インフラパッケージ
│   │   ├── db/                   # データベースクライアント
│   │   │   └── migrations/       # マイグレーション
│   │   └── utils/                # ユーティリティ
│   └── market_analysis/          # 市場分析パッケージ
│       ├── core/                 # コアロジック
│       ├── analysis/             # 分析ロジック
│       ├── api/                  # パブリックAPI
│       ├── visualization/        # チャート生成
│       ├── export/               # データエクスポート
│       ├── utils/                # ユーティリティ
│       └── docs/                 # パッケージドキュメント
├── template/                     # テンプレート（参照専用）
│   ├── src/template_package/     # パッケージテンプレート
│   ├── tests/                    # テストテンプレート
│   └── {article_id}-theme-name-en/  # 記事テンプレート
└── tests/                        # テストスイート
    ├── finance/                  # finance テスト
    └── market_analysis/          # market_analysis テスト
```

<!-- END: DIRECTORY -->

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
| PR をマージしたい | `/merge-pr <pr-number>` |
| PR をレビューしたい | `/review-pr` |
| PR のコンフリクトを分析したい | `/analyze-conflicts <pr-number>` |

---

## 効率的なワークフロー

### 新機能開発（独立環境で）

```
/worktree feature/xxx → /new-project → /issue → feature-implementer で実装 → /write-tests → /commit-and-pr → /merge-pr <number> → /worktree-done
```

### 新機能開発

```
/new-package → /new-project → /issue → feature-implementer で実装 → /write-tests → /push
```

### バグ修正

```
/worktree fix/xxx → /troubleshoot → 修正 → /ensure-quality → /commit-and-pr → /merge-pr <number> → /worktree-done
```

### パフォーマンス最適化

```
/analyze → /improve → /scan → /push
```

---

## 更新手順（--update モード）

### 並列実行アーキテクチャ

Task ツールで4つの Explore サブエージェントを**並列起動**し、結果を統合します。

```
/index --update
    │
    ├─> Task(Explore): コマンド検出 ─────────┐
    ├─> Task(Explore): スキル検出 ──────────┤ 並列
    ├─> Task(Explore): エージェント読み込み ─┤ 実行
    └─> Task(Explore): ディレクトリスキャン ─┘
                        │
                        v
              結果統合（YAML形式）
                        │
        ┌───────────────┼───────────────┐
        v               v               v
   index.md        CLAUDE.md       README.md
    更新             更新            更新
```

### サブエージェント詳細

#### 1. コマンド検出エージェント

```yaml
subagent_type: "Explore"
対象: .claude/commands/*.md（index.md 除く）
抽出: frontmatter description
出力形式:
  commands:
    - name: "analyze"
      description: "多次元コード分析"
```

#### 2. スキル検出エージェント

```yaml
subagent_type: "Explore"
対象: .claude/skills/*/SKILL.md
抽出: frontmatter name, description
出力形式:
  skills:
    - name: "architecture-design"
      description: "アーキテクチャ設計書を作成"
```

#### 3. エージェント読み込みエージェント

```yaml
subagent_type: "Explore"
対象: .claude/agents.md
抽出: カテゴリ別エージェント定義
出力形式:
  agents:
    - category: "汎用"
      items:
        - name: "Bash"
          description: "コマンド実行"
```

#### 4. ディレクトリスキャンエージェント

```yaml
subagent_type: "Explore"
対象: プロジェクトルート
深さ: 4層
除外: __pycache__, .git, .venv, .pytest_cache, .ruff_cache, node_modules, *.egg-info
出力形式:
  directory_structure:
    tree: |
      finance/
      ├── .claude/
      ...
```

### 結果統合スキーマ

```yaml
metadata:
  generated_at: "ISO8601"
  execution_status:
    commands: "success|failed"
    skills: "success|failed"
    agents: "success|failed"
    directory: "success|failed"
  errors: []

commands: [...]
skills: [...]
agents: [...]
directory_structure:
  tree: "ASCII tree string"
```

### エラーハンドリング

| 状況 | 対応 |
|------|------|
| サブエージェントタイムアウト | 既存内容を維持 + 警告表示 |
| ファイル読み込み失敗 | スキップして他を処理 |
| マーカーペア不正 | エラー終了（手動修正を促す） |
| 検出結果が空 | 警告表示、既存内容維持 |

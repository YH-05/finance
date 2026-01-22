---
description: SuperClaudeコマンドリファレンス
---

# /index - SuperClaude リファレンス

このコマンドは index スキルを呼び出し、プロジェクトで利用可能なコマンド、スキル、エージェントの一覧を表示・更新します。

## 実行モード

| モード | コマンド          | 説明                                           |
| ------ | ----------------- | ---------------------------------------------- |
| 表示   | `/index`          | 現在のリファレンスを表示                       |
| 更新   | `/index --update` | コマンド/スキル/エージェント/ディレクトリを自動検出して更新 |

## 使用方法

### 表示モード（/index）

```bash
/index
```

現在の index.md を読み込んでリファレンス情報を表示します。

### 更新モード（/index --update）

```bash
/index --update
```

以下のファイルを自動更新します:
- `.claude/commands/index.md` - コマンド/スキル/エージェント/ディレクトリ一覧
- `CLAUDE.md` - ディレクトリ構成セクション
- `README.md` - プロジェクト構造セクション

---

## 実行手順

### 引数の確認

1. `$ARGUMENTS` を確認
2. `--update` フラグがあれば更新モード、なければ表示モード

### 表示モード

1. 以下のリファレンスセクションを表示:
   - コマンド一覧
   - スキル一覧
   - エージェント一覧
   - ディレクトリ構成

### 更新モード

index スキルの guide.md に従って以下を実行:

1. **並列検出フェーズ**: Task ツールで 4 つのサブエージェントを並列起動
   - コマンド検出: `.claude/commands/*.md` から description を抽出
   - スキル検出: `.claude/skills/*/SKILL.md` から name, description を抽出
   - エージェント読み込み: `.claude/agents.md` から定義を抽出
   - ディレクトリスキャン: プロジェクトルートから 4 層までスキャン

2. **パッケージ README 更新フェーズ**: Task ツールで 5 つのサブエージェントを並列起動
   - finance README: `src/finance/` の README.md を更新
   - market_analysis README: `src/market_analysis/` の README.md を更新
   - rss README: `src/rss/` の README.md を更新
   - factor README: `src/factor/` の README.md を更新
   - strategy README: `src/strategy/` の README.md を更新

3. **統合・更新フェーズ**: 検出結果を統合し、ファイルを更新

---

## 詳細情報

詳細なガイドは index スキルを参照:

- **スキル定義**: `.claude/skills/index/SKILL.md`
- **詳細ガイド**: `.claude/skills/index/guide.md`
- **テンプレート**: `.claude/skills/index/template.md`

---

## コマンド一覧

<!-- AUTO-GENERATED: COMMANDS -->

| コマンド                   | 説明                                                                                           |
| -------------------------- | ---------------------------------------------------------------------------------------------- |
| `/analyze`                 | 多次元コード分析（分析レポート出力）                                                           |
| `/analyze-conflicts`       | PR のコンフリクトを詳細分析し、問題点と解決策を提示                                            |
| `/collect-finance-news`    | テーマ別に金融ニュースを収集し、GitHub Project 15 に自動投稿                                   |
| `/commit-and-pr`           | 変更のコミットと PR 作成                                                                       |
| `/create-worktrees`        | 複数の worktree を一括作成                                                                     |
| `/deep-research`           | 金融市場・投資テーマ専用のディープリサーチ（複数ソース収集 → クロス検証 → 深掘り → レポート） |
| `/delete-worktrees`        | 複数の worktree とブランチを一括削除                                                           |
| `/ensure-quality`          | コード品質の自動改善（make check-all 相当）                                                    |
| `/finance-edit`            | 金融記事の編集ワークフロー（初稿作成 → 批評 → 修正）                                           |
| `/finance-full`            | 記事作成の全工程を一括実行（フォルダ作成 → リサーチ → 執筆）                                   |
| `/finance-research`        | 金融記事のリサーチワークフロー（データ収集 → 分析 → 検証 → 可視化）                            |
| `/finance-suggest-topics`  | 金融記事のトピック提案（スコアリング付き）                                                     |
| `/gemini-search`           | Web search using Gemini CLI                                                                    |
| `/generate-market-report`  | 週次マーケットレポートを自動生成（データ収集 → ニュース検索 → レポート作成）                   |
| `/improve`                 | エビデンスベースの改善実装                                                                     |
| `/index`                   | SuperClaudeコマンドリファレンス                                                                |
| `/issue`                   | GitHub Issue とタスクの管理・同期を行う                                                        |
| `/issue-implement`         | GitHub Issue 番号から自動実装・PR 作成まで一括実行                                             |
| `/issue-refine`            | GitHub Issue の内容をブラッシュアップして更新する                                              |
| `/merge-pr`                | PR のコンフリクトチェック・CI 確認・マージを実行                                               |
| `/new-finance-article`     | 新規金融記事フォルダを作成し、カテゴリ別テンプレートから初期構造を生成                         |
| `/new-package`             | モノレポ内に新しい Python パッケージを作成する                                                 |
| `/new-project`             | 開発プロジェクトを開始。パッケージ開発または軽量プロジェクトに対応                             |
| `/plan-worktrees`          | GitHub Project を参照し、Todo の Issue を並列開発用にグルーピング表示                          |
| `/project-refine`          | プロジェクト全体の適合性チェックとタスク再構成を行う                                           |
| `/push`                    | 変更をコミットしてリモートにプッシュ                                                           |
| `/review-docs`             | ドキュメントの詳細レビューをサブエージェントで実行                                             |
| `/review-pr`               | PR レビュー（コード品質・セキュリティ・テスト）                                                |
| `/safe-refactor`           | 安全なリファクタリング                                                                         |
| `/scan`                    | セキュリティと品質の包括的検証                                                                 |
| `/setup-repository`        | テンプレートリポジトリの初期化（初回のみ）                                                     |
| `/sync-issue`              | GitHub Issue のコメントから進捗・タスク・仕様変更を同期                                        |
| `/task`                    | 複雑なタスクの管理                                                                             |
| `/troubleshoot`            | 体系的なデバッグ                                                                               |
| `/worktree`                | 新しい worktree とブランチを作成して開発を開始                                                 |
| `/worktree-done`           | worktree の開発完了後、PR マージ確認を経て安全にクリーンアップ                                 |
| `/write-tests`             | t-wada 流 TDD によるテスト作成                                                                 |

<!-- END: COMMANDS -->

---

## スキル一覧

<!-- AUTO-GENERATED: SKILLS -->

| スキル                    | 説明                                                                                                                                                                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agent-expert`            | Create and optimize specialized Claude Code agents. Expertise in agent design, prompt engineering, domain modeling, and best practices for claude-code-templates system. Use PROACTIVELY when designing new agents or improving existing ones.                                               |
| `agent-memory`            | Use this skill when the user asks to save, remember, recall, or organize memories. Triggers on: 'remember this', 'save this', 'note this', 'what did we discuss about...', 'check your notes', 'clean up memories'. Also use proactively when discovering valuable findings worth preserving. |
| `architecture-design`     | アーキテクチャ設計書を作成するための詳細ガイドとテンプレート。アーキテクチャ設計時にのみ使用。                                                                                                                                                                                                |
| `create-worktrees`        | /plan-worktrees の結果から複数の worktree を一括作成するスキル。Issue 番号のリストを受け取り、各 Issue に対して /worktree コマンドを順番に実行する。                                                                                                                                          |
| `deep-research`           | 金融市場・投資テーマ専用のディープリサーチワークフロー。複数ソースからデータ収集→クロス検証→深掘り分析→レポート生成までを自動化。                                                                                                                                                            |
| `development-guidelines`  | チーム全体で統一された開発プロセスとコーディング規約を確立するための包括的なガイドとテンプレート。開発ガイドライン作成時、コード実装時に使用する。                                                                                                                                            |
| `finance-news-collection` | 金融ニュース収集のワークフロー定義をスキルとして作成する。                                                                                                                                                                                                                                    |
| `functional-design`       | 機能設計書を作成するための詳細ガイドとテンプレート。機能設計書作成時にのみ使用。                                                                                                                                                                                                              |
| `glossary-creation`       | 用語集を作成するための詳細ガイドとテンプレート。用語集作成時にのみ使用。                                                                                                                                                                                                                      |
| `index`                   | CLAUDE.md/README.md の自動更新機能を提供するスキル。コマンド、スキル、エージェント、ディレクトリ構成の検出と更新を行う。/index（表示）または /index --update（更新）で使用。                                                                                                                  |
| `prd-writing`             | ライブラリ要求定義書(LRD)を作成するための詳細ガイドとテンプレート。LRD 作成時にのみ使用。                                                                                                                                                                                                     |
| `project-file`            | プロジェクトファイル（project.md）を作成・編集するための詳細ガイドとテンプレート。                                                                                                                                                                                                            |
| `project-status-sync`     | GitHub Projects の Issue 完了状態と docs/project/ のプロジェクトドキュメントを同期する。開発完了後にドキュメントを実態に合わせて更新。                                                                                                                                                        |
| `repository-structure`    | リポジトリ構造定義書を作成するための詳細ガイドとテンプレート。リポジトリ構造定義時にのみ使用。                                                                                                                                                                                                |
| `task-decomposition`      | タスク分解、Issue類似性判定、依存関係管理のためのナレッジベーススキル。要件からのタスク分解、Mermaid形式での可視化、Issue管理との連携時に使用。                                                                                                                                               |

<!-- END: SKILLS -->

---

## エージェント一覧

<!-- AUTO-GENERATED: AGENTS -->

詳細は `.claude/agents.md` を参照。

### 汎用エージェント

| エージェント      | 説明                                                   |
| ----------------- | ------------------------------------------------------ |
| `Bash`            | コマンド実行。git 操作、ターミナルタスク用             |
| `general-purpose` | 複雑な質問の調査、コード検索、マルチステップタスク     |
| `Explore`         | コードベース探索。ファイルパターン検索、キーワード検索 |
| `Plan`            | 実装計画の設計。ステップバイステップの計画作成         |

### 品質・分析エージェント

| エージェント               | 説明                                                   |
| -------------------------- | ------------------------------------------------------ |
| `quality-checker`          | コード品質の検証・自動修正                             |
| `code-analyzer`            | コード品質、アーキテクチャ、パフォーマンスの多次元分析 |
| `security-scanner`         | OWASP Top 10 に基づくセキュリティ脆弱性の検証          |
| `implementation-validator` | 実装コードの品質検証、スペックとの整合性確認           |

### 開発エージェント

| エージェント              | 説明                                                                     |
| ------------------------- | ------------------------------------------------------------------------ |
| `test-writer`             | t-wada 流 TDD に基づくテスト作成。Red→Green→Refactor サイクル           |
| `feature-implementer`     | TDD ループを自動実行。GitHub Issue のチェックボックスを更新しながら実装 |
| `debugger`                | 体系的なデバッグ。問題特定、根本原因分析、解決策実装                     |
| `improvement-implementer` | エビデンスベースの改善実装。メトリクス測定→改善→検証                     |

### ドキュメントエージェント

| エージェント                    | 説明                                                                                |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| `functional-design-writer`      | 機能設計書作成。LRD を元に技術的な機能設計を詳細化                                  |
| `architecture-design-writer`    | アーキテクチャ設計書作成。技術スタックとシステム構造を定義                          |
| `development-guidelines-writer` | 開発ガイドライン作成。コーディング規約と開発プロセスを定義                          |
| `repository-structure-writer`   | リポジトリ構造定義書作成。ディレクトリ構造を定義                                    |
| `glossary-writer`               | 用語集作成。ライブラリ固有の用語と技術用語を定義                                    |
| `doc-reviewer`                  | ドキュメントの品質レビューと改善提案                                                |
| `task-decomposer`               | タスク分解と GitHub Issues 連携。類似性判定、依存関係管理、project.md との双方向同期 |

### Issue 管理エージェント

| エージェント       | 説明                                                                       |
| ------------------ | -------------------------------------------------------------------------- |
| `comment-analyzer` | Issue コメントを解析し、進捗・サブタスク・仕様変更を構造化データとして抽出 |

### リサーチエージェント

| エージェント               | 説明                                        |
| -------------------------- | ------------------------------------------- |
| `research-image-collector` | note 記事用の画像を収集し images.json を生成 |

### 金融エージェント

| エージェント              | 説明                                                  |
| ------------------------- | ----------------------------------------------------- |
| `finance-news-collector`  | RSS フィードから金融ニュースを収集し、GitHub Project に投稿 |

### 特殊エージェント

| エージェント        | 説明                                             |
| ------------------- | ------------------------------------------------ |
| `claude-code-guide` | Claude Code CLI、Agent SDK、API に関する質問対応 |
| `statusline-setup`  | ステータスライン設定                             |

<!-- END: AGENTS -->

---

## ディレクトリ構成

<!-- AUTO-GENERATED: DIRECTORY -->

```
finance/                                    # Project root
├── .claude/                                # Claude Code configuration
│   ├── agents/                             # (67 agents)
│   │   ├── deep-research/
│   │   └── finance_news_collector/         # テーマ別収集エージェント
│   ├── agents_sample/
│   ├── archive/
│   ├── commands/                           # (37 commands)
│   ├── commands_sample/
│   ├── rules/                              # 共有ルール定義
│   ├── skills/                             # (15 skills)
│   │   ├── agent-expert/
│   │   ├── agent-memory/
│   │   ├── architecture-design/
│   │   ├── create-worktrees/
│   │   ├── deep-research/
│   │   ├── development-guidelines/
│   │   ├── finance-news-collection/
│   │   ├── functional-design/
│   │   ├── glossary-creation/
│   │   ├── index/
│   │   ├── prd-writing/
│   │   ├── project-file/
│   │   ├── project-status-sync/
│   │   ├── repository-structure/
│   │   └── task-decomposition/
│   ├── sounds/
│   ├── settings.json
│   ├── settings.local.json
│   └── agents.md
│
├── .github/                                # GitHub configuration
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── PUSH_TEMPLATE.md
│   └── dependabot.yml
│
├── .benchmarks/
├── .gitignore
│
├── data/                                   # Data storage layer
│   ├── config/
│   ├── duckdb/                             # OLAP database
│   ├── sqlite/                             # OLTP database
│   ├── raw/                                # Raw data (Parquet)
│   │   ├── fred/indicators/
│   │   ├── rss/                            # (33 feed subscriptions)
│   │   │   └── feeds.json
│   │   └── yfinance/
│   │       ├── forex/
│   │       ├── indices/
│   │       └── stocks/
│   ├── processed/
│   │   ├── daily/
│   │   └── aggregated/
│   ├── exports/
│   │   ├── csv/
│   │   └── json/
│   ├── schemas/                            # (14 JSON schemas)
│   └── README.md
│
├── docs/                                   # Repository documentation
│   ├── coding-standards.md
│   ├── development-process.md
│   ├── diagram-guidelines.md
│   ├── document-management.md
│   ├── github-projects-automation.md
│   ├── testing-strategy.md
│   ├── type-checker-migration.md
│   ├── code-analysis-report/               # Code analysis reports
│   ├── plan/                               # Project plans
│   ├── pr-review/                          # PR review reports
│   └── project/                            # Project documentation
│       ├── project-7/                      # エージェント開発
│       │   ├── README.md
│       │   ├── image-collector-guide.md
│       │   └── research/
│       ├── project-11/                     # note金融コンテンツ発信強化
│       │   ├── README.md
│       │   ├── market-analysis-guidelines.md
│       │   └── note-magazine-strategy.md
│       ├── project-14/                     # 金融ニュース収集
│       │   ├── README.md
│       │   ├── finance-news-*.md           # (4 guide files)
│       │   └── research/
│       ├── project-16/                     # src_sample Migration
│       │   └── README.md
│       └── project-17/                     # Market Report System
│           └── README.md
│
├── src/                                    # Source code
│   ├── finance/                            # Core infrastructure
│   │   ├── db/                             # Database layer
│   │   │   ├── sqlite_client.py
│   │   │   ├── duckdb_client.py
│   │   │   ├── connection.py
│   │   │   └── migrations/
│   │   ├── utils/
│   │   │   └── logging_config.py
│   │   ├── types.py
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── py.typed
│   │
│   ├── market_analysis/                    # Market analysis library
│   │   ├── core/                           # Data fetchers (yfinance, FRED)
│   │   ├── analysis/                       # Analysis algorithms
│   │   ├── api/                            # Public API
│   │   ├── visualization/                  # Chart generation
│   │   ├── export/                         # Data export
│   │   ├── utils/                          # Utilities (cache, retry)
│   │   ├── docs/                           # (8 documentation files)
│   │   ├── errors.py
│   │   ├── types.py
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── py.typed
│   │
│   ├── rss/                                # RSS feed monitoring
│   │   ├── cli/                            # CLI interface
│   │   ├── core/                           # Parser, HTTP client, diff detector
│   │   ├── mcp/                            # MCP server integration
│   │   ├── services/                       # Service layer
│   │   ├── storage/                        # JSON persistence
│   │   ├── validators/                     # URL validation
│   │   ├── utils/                          # Logging
│   │   ├── docs/                           # (8 documentation files)
│   │   ├── exceptions.py
│   │   ├── types.py
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── py.typed
│   │
│   ├── factor/                             # Factor analysis library
│   │   ├── core/                           # Core algorithms
│   │   ├── factors/                        # Factor implementations
│   │   │   ├── macro/
│   │   │   ├── price/
│   │   │   ├── quality/
│   │   │   ├── size/
│   │   │   └── value/
│   │   ├── providers/                      # Data providers
│   │   ├── validation/                     # Factor validation
│   │   ├── utils/
│   │   ├── docs/
│   │   ├── types.py
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── py.typed
│   │
│   └── strategy/                           # Strategy library
│       ├── core/
│       ├── output/                         # Output formatter
│       ├── rebalance/                      # Rebalancing
│       ├── risk/                           # Risk management
│       ├── providers/                      # Data providers
│       ├── visualization/                  # Chart generation
│       ├── utils/
│       ├── docs/
│       ├── types.py
│       ├── __init__.py
│       ├── README.md
│       └── py.typed
│
├── tests/                                  # Test suite
│   ├── unit/                               # Unit tests
│   │   ├── market_analysis/                # (5 test files)
│   │   ├── validators/                     # (1 test file)
│   │   └── __init__.py
│   │
│   ├── rss/                                # RSS tests
│   │   ├── unit/                           # (16 test files)
│   │   │   ├── core/
│   │   │   ├── mcp/
│   │   │   ├── cli/
│   │   │   ├── services/
│   │   │   ├── storage/
│   │   │   ├── utils/
│   │   │   └── validators/
│   │   ├── integration/                    # (1 integration test)
│   │   ├── property/
│   │   └── storage/unit/
│   │
│   ├── finance/                            # Finance tests
│   │   ├── db/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   └── unit/
│   │
│   ├── market_analysis/
│   │   ├── unit/
│   │   │   ├── core/
│   │   │   ├── analysis/
│   │   │   ├── api/
│   │   │   ├── export/
│   │   │   ├── utils/
│   │   │   └── visualization/
│   │   ├── property/
│   │   └── integration/
│   │
│   ├── factor/
│   │   ├── unit/
│   │   ├── property/
│   │   └── integration/
│   │
│   ├── strategy/
│   │   ├── unit/
│   │   ├── property/
│   │   └── integration/
│   │
│   ├── finance_news_collector/             # News collector tests
│   │
│   ├── quant/                              # Quantitative analysis
│   │   ├── unit/
│   │   ├── property/
│   │   └── integration/
│   │
│   ├── property/                           # Property tests
│   └── integration/                        # Integration tests
│
├── template/                               # Reference templates (read-only)
│   ├── src/template_package/
│   │   ├── core/
│   │   └── utils/
│   ├── tests/
│   │   ├── unit/
│   │   ├── property/
│   │   └── integration/
│   ├── {article_id}-theme-name-en/
│   │   ├── 01_research/visualize/
│   │   ├── 02_edit/
│   │   └── 03_published/
│   ├── market_report/
│   │   ├── 01_research/market_data/
│   │   ├── 02_edit/
│   │   ├── 03_published/
│   │   └── sample/
│   ├── stock_analysis/
│   │   ├── 01_research/market_data/
│   │   ├── 02_edit/
│   │   └── 03_published/
│   ├── economic_indicators/
│   │   ├── 01_research/market_data/
│   │   ├── 02_edit/
│   │   └── 03_published/
│   ├── investment_education/
│   │   ├── 01_research/
│   │   ├── 02_edit/
│   │   └── 03_published/
│   └── quant_analysis/
│       ├── 01_research/market_data/
│       ├── 02_edit/
│       └── 03_published/
│
├── articles/                               # Finance article workspace
│   └── {category}_{id}_{slug}/
│       ├── article-meta.json
│       ├── 01_research/
│       ├── 02_edit/
│       └── 03_published/
│
├── notebook/                               # Jupyter notebooks
├── notebook_sample/
│   └── archived/
│
├── examples/
├── scripts/                                # Utility scripts
│   ├── setup.sh
│   ├── update_project_name.py
│   └── collect_finance_news*.py            # ニュース収集スクリプト
│
├── snippets/                               # Reusable content
│   ├── disclaimer.md
│   ├── not-advice.md
│   ├── data-source.md
│   ├── investment-risk.md
│   ├── warning.md
│   ├── cta-premium.md
│   └── sns-announcement.md
│
├── src_sample/                             # Sample/legacy code
│   ├── src-memo/
│   ├── test_roic_analysis/
│   └── archived/
│
├── trash/                                  # Garbage folder (pending deletion)
│
├── CLAUDE.md                               # Project instructions
├── README.md                               # Project overview
├── Makefile                                # Build automation
├── pyproject.toml                          # Python project config
├── uv.lock                                 # Dependency lock file
├── .python-version                         # Python version spec
├── .pre-commit-config.yaml                 # Pre-commit hooks
└── .mcp.json                               # MCP server config
```

<!-- END: DIRECTORY -->

---

## コマンド選択ガイド

### 品質関連

| やりたいこと           | コマンド          |
| ---------------------- | ----------------- |
| エラーを自動修正したい | `/ensure-quality` |
| 品質スコアを確認したい | `/scan`           |
| コードを分析したい     | `/analyze`        |
| 改善を実装したい       | `/improve`        |

### 開発フロー

| やりたいこと                  | コマンド                                  |
| ----------------------------- | ----------------------------------------- |
| 並列開発の計画を立てたい      | `/plan-worktrees <project-number>`        |
| 独立した作業環境で開発したい  | `/worktree <feature-name>`                |
| 開発完了後のクリーンアップ    | `/worktree-done`                          |
| 新しいパッケージを作りたい    | `/new-package <name>`                     |
| 新規開発を始めたい            | `/new-project @src/<pkg>/docs/project.md` |
| Issue を管理したい            | `/issue @src/<pkg>/docs/project.md`       |
| テストを書きたい              | `/write-tests`                            |
| リファクタリングしたい        | `/safe-refactor`                          |
| 問題を解決したい              | `/troubleshoot`                           |
| 変更をプッシュしたい          | `/push`                                   |
| PR を作成したい               | `/commit-and-pr`                          |
| PR をマージしたい             | `/merge-pr <pr-number>`                   |
| PR をレビューしたい           | `/review-pr`                              |
| PR のコンフリクトを分析したい | `/analyze-conflicts <pr-number>`          |

---

## 効率的なワークフロー

### チーム並列開発

```
/plan-worktrees <project> → 各メンバーが Wave 1 の Issue を担当 → /worktree feature/issue-N → 実装 → /commit-and-pr → Wave 2 に進む
```

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

## 関連スキル

- **index**: `.claude/skills/index/SKILL.md`

## 参考資料

- `CLAUDE.md`: プロジェクト全体のガイドライン
- `.claude/agents.md`: エージェント定義

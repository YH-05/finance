---
description: SuperClaudeコマンドリファレンス
---

# SuperClaude リファレンス

このコマンドは、プロジェクトで利用可能なコマンド、スキル、エージェントの一覧を表示・更新します。

## 実行モード

| モード | コマンド          | 説明                                           |
| ------ | ----------------- | ---------------------------------------------- |
| 表示   | `/index`          | 現在のリファレンスを表示                       |
| 更新   | `/index --update` | コマンド/スキル/エージェントを自動検出して更新 |

### 自動検出の仕組み

-   **コマンド**: `.claude/commands/*.md` の frontmatter `description` から検出
-   **スキル**: `.claude/skills/*/SKILL.md` の frontmatter `name`, `description` から検出
-   **エージェント**: `.claude/agents.md` から読み込み
-   **ディレクトリ構成**: プロジェクトルートから 4 層までスキャン（除外: `__pycache__`, `.git`, `.venv` 等）

### 更新対象ファイル

| ファイル                    | 更新内容                                      |
| --------------------------- | --------------------------------------------- |
| `.claude/commands/index.md` | コマンド/スキル/エージェント/ディレクトリ一覧 |
| `CLAUDE.md`                 | ディレクトリ構成セクション                    |
| `README.md`                 | プロジェクト構造セクション                    |

---

## コマンド一覧

<!-- AUTO-GENERATED: COMMANDS -->

| コマンド                  | 説明                                                                                                               |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `/analyze`                | 多次元コード分析（分析レポート出力）                                                                               |
| `/analyze-conflicts`      | PR のコンフリクトを詳細分析し、問題点と解決策を提示                                                                |
| `/commit-and-pr`          | 変更のコミットと PR 作成                                                                                           |
| `/create-worktrees`       | 複数 Worktree 一括作成                                                                                             |
| `/ensure-quality`         | コード品質の自動改善（make check-all 相当）                                                                        |
| `/finance-edit`           | 金融記事の編集ワークフロー（初稿作成 → 批評 → 修正）                                                               |
| `/finance-research`       | 金融記事のリサーチワークフロー（データ収集 → 分析 → 検証 → 可視化）                                                |
| `/finance-suggest-topics` | 金融記事のトピック提案（スコアリング付き）                                                                         |
| `/gemini-search`          | Web search using Gemini CLI                                                                                        |
| `/improve`                | エビデンスベースの改善実装                                                                                         |
| `/issue`                  | GitHub Issue とタスクの管理・同期を行う                                                                            |
| `/issue-refine`           | GitHub Issue の内容をブラッシュアップして更新する                                                                  |
| `/merge-pr`               | PR のコンフリクトチェック・CI 確認・マージを実行                                                                   |
| `/new-finance-article`    | 新規金融記事フォルダを作成し、カテゴリ別テンプレートから初期構造を生成                                             |
| `/new-package`            | モノレポ内に新しい Python パッケージを作成する                                                                     |
| `/new-project`            | 開発プロジェクトを開始。パッケージ開発または軽量プロジェクトに対応                                                 |
| `/plan-worktrees`         | GitHub Project を参照し、Todo の Issue を並列開発用にグルーピング表示                                              |
| `/project-refine`         | プロジェクト全体の適合性チェックとタスク再構成を行う                                                               |
| `/push`                   | 変更をコミットしてリモートにプッシュ                                                                               |
| `/review-docs`            | ドキュメントの詳細レビューをサブエージェントで実行                                                                 |
| `/review-pr`              | PR レビュー（コード品質・セキュリティ・テスト）                                                                    |
| `/safe-refactor`          | 安全なリファクタリング                                                                                             |
| `/scan`                   | セキュリティと品質の包括的検証                                                                                     |
| `/setup-repository`       | テンプレートリポジトリの初期化（初回のみ）                                                                         |
| `/sync-issue`             | GitHub Issue のコメントから進捗・タスク・仕様変更を同期                                                            |
| `/task`                   | 複雑なタスクの管理                                                                                                 |
| `/troubleshoot`           | 体系的なデバッグ                                                                                                   |
| `/worktree`               | 新しい worktree とブランチを作成して開発を開始                                                                     |
| `/worktree-done`          | worktree の開発完了後、PR マージ確認を経て安全にクリーンアップ                                                     |
| `/write-tests`            | t-wada 流 TDD によるテスト作成                                                                                     |

<!-- END: COMMANDS -->

---

## スキル一覧

<!-- AUTO-GENERATED: SKILLS -->

| スキル                   | 説明                                                                                                                                                                                                                                                                                          |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agent-expert`           | Create and optimize specialized Claude Code agents. Expertise in agent design, prompt engineering, domain modeling, and best practices for claude-code-templates system. Use PROACTIVELY when designing new agents or improving existing ones.                                               |
| `agent-memory`           | Use this skill when the user asks to save, remember, recall, or organize memories. Triggers on: 'remember this', 'save this', 'note this', 'what did we discuss about...', 'check your notes', 'clean up memories'. Also use proactively when discovering valuable findings worth preserving. |
| `architecture-design`    | アーキテクチャ設計書を作成するための詳細ガイドとテンプレート。アーキテクチャ設計時にのみ使用。                                                                                                                                                                                                |
| `create-worktrees`       | /plan-worktrees の結果から複数の worktree を一括作成するスキル。Issue 番号のリストを受け取り、各 Issue に対して /worktree コマンドを順番に実行する。                                                                                                                                          |
| `development-guidelines` | チーム全体で統一された開発プロセスとコーディング規約を確立するための包括的なガイドとテンプレート。開発ガイドライン作成時、コード実装時に使用する。                                                                                                                                            |
| `functional-design`      | 機能設計書を作成するための詳細ガイドとテンプレート。機能設計書作成時にのみ使用。                                                                                                                                                                                                              |
| `glossary-creation`      | 用語集を作成するための詳細ガイドとテンプレート。用語集作成時にのみ使用。                                                                                                                                                                                                                      |
| `prd-writing`            | ライブラリ要求定義書(LRD)を作成するための詳細ガイドとテンプレート。LRD 作成時にのみ使用。                                                                                                                                                                                                     |
| `project-file`           | プロジェクトファイル（project.md）を作成・編集するための詳細ガイドとテンプレート。                                                                                                                                                                                                            |
| `repository-structure`   | リポジトリ構造定義書を作成するための詳細ガイドとテンプレート。リポジトリ構造定義時にのみ使用。                                                                                                                                                                                                |

<!-- END: SKILLS -->

---

## エージェント一覧

<!-- AUTO-GENERATED: AGENTS -->

詳細は `.claude/agents.md` を参照。

### 汎用

| エージェント      | 説明                                                   |
| ----------------- | ------------------------------------------------------ |
| `Bash`            | コマンド実行。git 操作、ターミナルタスク用             |
| `general-purpose` | 複雑な質問の調査、コード検索、マルチステップタスク     |
| `Explore`         | コードベース探索。ファイルパターン検索、キーワード検索 |
| `Plan`            | 実装計画の設計。ステップバイステップの計画作成         |

### 品質・分析

| エージェント               | 説明                                                   |
| -------------------------- | ------------------------------------------------------ |
| `quality-checker`          | コード品質の検証・自動修正                             |
| `code-analyzer`            | コード品質、アーキテクチャ、パフォーマンスの多次元分析 |
| `security-scanner`         | OWASP Top 10 に基づくセキュリティ脆弱性の検証          |
| `implementation-validator` | 実装コードの品質検証、スペックとの整合性確認           |

### 開発

| エージェント              | 説明                             |
| ------------------------- | -------------------------------- |
| `test-writer`             | t-wada 流 TDD に基づくテスト作成 |
| `feature-implementer`     | TDD ループを自動実行             |
| `debugger`                | 体系的なデバッグ                 |
| `improvement-implementer` | エビデンスベースの改善実装       |

### ドキュメント

| エージェント                    | 説明                                            |
| ------------------------------- | ----------------------------------------------- |
| `functional-design-writer`      | 機能設計書作成                                  |
| `architecture-design-writer`    | アーキテクチャ設計書作成                        |
| `development-guidelines-writer` | 開発ガイドライン作成                            |
| `repository-structure-writer`   | リポジトリ構造定義書作成                        |
| `glossary-writer`               | 用語集作成                                      |
| `doc-reviewer`                  | ドキュメントレビュー                            |
| `task-decomposer`               | タスク分解・GitHub Issues 連携・project.md 同期 |

### Issue管理

| エージェント        | 説明                                                                       |
| ------------------- | -------------------------------------------------------------------------- |
| `comment-analyzer`  | Issue コメントを解析し、進捗・サブタスク・仕様変更を構造化データとして抽出 |

### リサーチ

| エージェント               | 説明                                           |
| -------------------------- | ---------------------------------------------- |
| `research-image-collector` | note記事用の画像を収集し images.json を生成    |

### 特殊

| エージェント        | 説明                                             |
| ------------------- | ------------------------------------------------ |
| `claude-code-guide` | Claude Code CLI、Agent SDK、API に関する質問対応 |
| `statusline-setup`  | ステータスライン設定                             |

### 専門領域

| エージェント   | 説明                                                                               |
| -------------- | ---------------------------------------------------------------------------------- |
| `agent-expert` | エージェント設計・最適化の専門家。新規エージェント作成や既存エージェント改善を支援 |

<!-- END: AGENTS -->

---

## ディレクトリ構成

<!-- AUTO-GENERATED: DIRECTORY -->

```
finance/                                     # Project root
├── .claude/                                 # Claude Code configuration (48 agents + 30 commands + 10 skills)
│   ├── agents/                              # (46) Specialized agents
│   ├── agents_sample/                       # (22) Sample agent definitions
│   ├── archive/                             # (2) Archived agents
│   ├── commands/                            # (30) Slash commands
│   ├── commands_sample/                     # (12) Sample command definitions
│   ├── skills/                              # (10) Skill modules
│   │   ├── agent-expert/                    # Agent design skill
│   │   ├── agent-memory/                    # Knowledge graph memory system
│   │   ├── architecture-design/             # Architecture design skill
│   │   ├── create-worktrees/                # Multi-worktree creation
│   │   ├── development-guidelines/          # Guidelines skill
│   │   ├── functional-design/               # Functional design skill
│   │   ├── glossary-creation/               # Glossary skill
│   │   ├── prd-writing/                     # PRD skill
│   │   ├── project-file/                    # Project file skill
│   │   └── repository-structure/            # Repo structure skill
│   ├── settings.json
│   ├── settings.local.json
│   └── agents.md
│
├── .github/                                 # GitHub configuration
│   ├── ISSUE_TEMPLATE/                      # (4) Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── PUSH_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows/                           # (3) GitHub Actions workflows
│
├── data/                                    # Data storage layer
│   ├── config/                              # Configuration files
│   ├── duckdb/                              # DuckDB OLAP database
│   ├── sqlite/                              # SQLite OLTP database
│   ├── raw/                                 # Raw data (Parquet format)
│   │   ├── fred/indicators/
│   │   └── yfinance/                        # stocks, forex, indices
│   ├── processed/                           # Processed data
│   │   ├── daily/
│   │   └── aggregated/
│   ├── exports/                             # Exported data
│   │   ├── csv/
│   │   └── json/
│   ├── schemas/                             # (12) JSON schemas
│   └── README.md
│
├── docs/                                    # Repository documentation
│   ├── coding-standards.md
│   ├── development-process.md
│   ├── diagram-guidelines.md
│   ├── document-management.md
│   ├── image-collector-guide.md
│   ├── testing-strategy.md
│   ├── type-checker-migration.md
│   ├── pr-review/                           # (14) PR review reports (YAML)
│   └── project/                             # Project research docs
│
├── src/                                     # Source code
│   ├── finance/                             # Core infrastructure package
│   │   ├── db/                              # Database layer
│   │   │   ├── sqlite_client.py             # SQLite client (OLTP)
│   │   │   ├── duckdb_client.py             # DuckDB client (OLAP)
│   │   │   ├── connection.py
│   │   │   └── migrations/                  # Database schema migrations
│   │   ├── utils/
│   │   │   └── logging_config.py
│   │   ├── types.py
│   │   └── py.typed                         # PEP 561 marker
│   │
│   ├── market_analysis/                     # Market analysis library
│   │   ├── core/                            # Data fetchers (yfinance, FRED)
│   │   ├── analysis/                        # Analysis algorithms (indicators, correlation)
│   │   ├── api/                             # Public API (analysis, chart, market_data)
│   │   ├── visualization/                   # Chart generation
│   │   ├── export/                          # Data export
│   │   ├── utils/                           # Utilities (cache, retry, validators)
│   │   ├── errors.py
│   │   ├── types.py
│   │   ├── docs/                            # (8) Library documentation
│   │   └── py.typed
│   │
│   └── rss/                                 # RSS feed monitoring package
│       ├── cli/                             # CLI interface
│       ├── core/                            # Parser, HTTP client, diff detector
│       ├── mcp/                             # MCP server integration
│       ├── services/                        # Service layer
│       ├── storage/                         # JSON persistence
│       ├── validators/                      # URL validation
│       ├── utils/                           # Logging
│       ├── exceptions.py
│       ├── types.py
│       ├── docs/                            # (8) Library documentation
│       └── py.typed
│
├── tests/                                   # Test suite
│   ├── finance/                             # Finance package tests
│   │   └── db/unit/                         # (3) DB client tests
│   ├── market_analysis/                     # Market analysis tests
│   │   └── unit/                            # (24) Tests
│   └── rss/                                 # RSS package tests
│       ├── unit/                            # (13) Unit tests
│       └── integration/                     # (1) Integration test
│
├── template/                                # Reference templates (read-only)
│   ├── src/template_package/                # Package structure template
│   ├── tests/                               # Test structure template
│   ├── {article_id}-theme-name-en/          # Article template
│   │   ├── 01_research/
│   │   ├── 02_edit/
│   │   └── 03_published/
│   ├── market_report/                       # Market report template
│   ├── stock_analysis/                      # Stock analysis template
│   ├── economic_indicators/                 # Economic indicators template
│   ├── investment_education/                # Investment education template
│   └── quant_analysis/                      # Quantitative analysis template
│
├── snippets/                                # Reusable content
│   ├── disclaimer.md
│   ├── not-advice.md
│   ├── data-source.md
│   ├── investment-risk.md
│   ├── warning.md
│   ├── cta-premium.md
│   └── sns-announcement.md
│
├── scripts/                                 # Utility scripts
│   ├── setup.sh
│   └── update_project_name.py
│
├── CLAUDE.md                                # Project instructions
├── README.md                                # Project overview
├── Makefile                                 # Build automation
├── pyproject.toml                           # Python project config
├── uv.lock                                  # Dependency lock file
├── .python-version                          # Python version spec
├── .pre-commit-config.yaml
├── .mcp.json                                # MCP server config
└── .gitignore
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

## 更新手順（--update モード）

### 並列実行アーキテクチャ

Task ツールで 7 つのサブエージェントを**並列起動**し、結果を統合します。

```
/index --update
    │
    ├─> Task(Explore): コマンド検出 ─────────────┐
    ├─> Task(Explore): スキル検出 ────────────────┤
    ├─> Task(Explore): エージェント読み込み ──────┤ 並列実行
    ├─> Task(Explore): ディレクトリスキャン ──────┤ (7エージェント)
    ├─> Task(package-readme-updater): finance README ──┤
    ├─> Task(package-readme-updater): market_analysis README ─┤
    └─> Task(package-readme-updater): rss README ──────┘
                        │
                        v
          結果統合（YAML形式 + README更新確認）
                        │
        ┌───────────────┼──────────────────┬──────────────────┐
        v               v                  v                  v
   index.md        CLAUDE.md          README.md       src/*/README.md
    更新             更新               更新              更新（3つ）
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

#### 5. finance README 更新エージェント

```yaml
subagent_type: "package-readme-updater"
対象: src/finance/
パッケージ名: "finance"
モード: "minimal" # 最小限の構成
出力: src/finance/README.md
```

#### 6. market_analysis README 更新エージェント

```yaml
subagent_type: "package-readme-updater"
対象: src/market_analysis/
パッケージ名: "market_analysis"
モード: "detailed" # 詳細構成（既存維持）
出力: src/market_analysis/README.md
```

#### 7. rss README 更新エージェント

```yaml
subagent_type: "package-readme-updater"
対象: src/rss/
パッケージ名: "rss"
モード: "standard" # 標準構成（テンプレート→実装）
出力: src/rss/README.md
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
        package_readme_finance: "success|failed"
        package_readme_market_analysis: "success|failed"
        package_readme_rss: "success|failed"
    errors: []

commands: [...]
skills: [...]
agents: [...]
directory_structure:
    tree: "ASCII tree string"
package_readmes:
    finance: "updated|skipped|failed"
    market_analysis: "updated|skipped|failed"
    rss: "updated|skipped|failed"
```

### エラーハンドリング

| 状況                         | 対応                                        |
| ---------------------------- | ------------------------------------------- |
| サブエージェントタイムアウト | 既存内容を維持 + 警告表示                   |
| ファイル読み込み失敗         | スキップして他を処理                        |
| マーカーペア不正             | エラー終了（手動修正を促す）                |
| 検出結果が空                 | 警告表示、既存内容維持                      |
| **README.md 不在**           | **警告を出し、テンプレートから新規作成**    |
| ****init**.py パース失敗**   | **警告を出し、API セクションを "N/A" 表示** |
| **テストディレクトリ不在**   | **警告せず、テスト統計を "0" 表示**         |
| **カバレッジ計測失敗**       | **警告せず、カバレッジを "N/A" 表示**       |

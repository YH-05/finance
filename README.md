# finance - 金融市場分析・コンテンツ発信支援ライブラリ

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-latest-green.svg)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/YH-05/finance/actions/workflows/ci.yml/badge.svg)](https://github.com/YH-05/finance/actions/workflows/ci.yml)

金融市場の分析と note.com での金融・投資コンテンツ発信を効率化する Python ライブラリです。

## 主要機能

- **市場データ取得・分析**: Yahoo Finance (yfinance) を使用した株価・為替・指標データの取得と分析
- **チャート・グラフ生成**: 分析結果の可視化と図表作成
- **記事生成支援**: 分析結果を元に記事下書きを生成
- **データベースインフラ**: SQLite (OLTP) + DuckDB (OLAP) のデュアルデータベース構成

## パッケージ構成

| パッケージ | 説明 |
|-----------|------|
| `finance` | 共通データベースインフラ、ユーティリティ |
| `market_analysis` | 市場データ取得・分析機能 |


## ⚠️ よくある問題とトラブルシューティング

### Python バージョンの問題

このプロジェクトは**Python 3.12以上**をサポートしています。3.12未満のバージョンを使用すると、型チェックや CI/CD で問題が発生する場合があります。

**問題の症状：**

-   pyright が「Template string literals (t-strings) require Python 3.14 or newer」などのエラーを報告
-   GitHub CI の lint ジョブが失敗
-   ローカルでは問題ないのに CI で失敗する

**原因：**

-   システムに複数の Python バージョンがインストールされている場合、意図しないバージョン（例: Python 3.14）が使用される可能性があります
-   pyright がプロジェクトのターゲットバージョンと異なる標準ライブラリをチェックしようとしてエラーが発生

**解決方法：**

1. **Python バージョンを明示的に指定：**

    ```bash
    uv python pin 3.12  # または 3.13 など
    ```

    これにより`.python-version`ファイルが作成され、uv が指定したバージョンを使用するようになります。

2. **仮想環境を再構築：**

    ```bash
    uv sync --all-extras
    ```

3. **pre-commit フックを確認：**
    ```bash
    uv run pre-commit run --all-files
    ```

**予防策：**

-   プロジェクトのセットアップ時に`uv python pin 3.12`（または `3.13` 等）を実行
-   `.python-version`ファイルを gitignore から除外することを検討（チームで統一するため）
-   CI/CD ワークフローでは Python 3.12 と 3.13 の両方でテストを実行（すでに`.github/workflows/ci.yml`で設定済み）

### その他のトラブルシューティング

**依存関係のエラー：**

```bash
# 依存関係をクリーンインストール
uv sync --reinstall
```

**pre-commit フックのエラー：**

```bash
# pre-commitキャッシュをクリア
uv run pre-commit clean
uv run pre-commit install --install-hooks
```

**型チェックエラー：**

```bash
# pyright設定の確認
uv run pyright --version
# pyproject.tomlのpyright設定を確認
```

## 📁 プロジェクト構造

<!-- AUTO-GENERATED: DIRECTORY -->

```
finance/                                     # Project root
├── .claude/                                 # Claude Code configuration (67 agents + 36 commands + 13 skills)
│   ├── agents/                              # (67) Specialized agents
│   │   ├── deep-research/
│   │   └── finance_news_collector/          # テーマ別収集エージェント
│   ├── commands/                            # (36) Slash commands
│   ├── rules/                               # Shared rule definitions
│   ├── skills/                              # (13) Skill modules
│   └── agents.md
├── .github/                                 # GitHub configuration
│   ├── ISSUE_TEMPLATE/                      # Issue templates
│   └── workflows/                           # GitHub Actions workflows
├── data/                                    # Data storage layer
│   ├── config/                              # Configuration files
│   ├── duckdb/                              # DuckDB OLAP database
│   ├── sqlite/                              # SQLite OLTP database
│   ├── raw/                                 # Raw data (Parquet format)
│   │   ├── fred/indicators/
│   │   ├── rss/                             # (33) RSS feed subscriptions
│   │   └── yfinance/                        # stocks, forex, indices
│   ├── processed/                           # Processed data (daily/aggregated)
│   ├── exports/                             # Exported data (csv/json)
│   └── schemas/                             # (14) JSON schemas
├── docs/                                    # Repository documentation
│   ├── code-analysis-report/                # Code analysis reports
│   ├── plan/                                # Project plans
│   ├── pr-review/                           # PR review reports
│   └── project/                             # Project documentation
│       ├── project-7/                       # エージェント開発
│       ├── project-11/                      # note金融コンテンツ発信強化
│       ├── project-14/                      # 金融ニュース収集
│       └── project-16/                      # src_sample Migration
├── src/                                     # Source code (172 Python files)
│   ├── finance/                             # Core infrastructure (11 files)
│   │   ├── db/                              # Database layer (SQLite + DuckDB)
│   │   │   └── migrations/                  # Database schema migrations
│   │   ├── utils/                           # Utilities (logging)
│   │   ├── types.py
│   │   └── py.typed
│   ├── market_analysis/                     # Market analysis library (41 files)
│   │   ├── core/                            # Data fetchers (yfinance, FRED)
│   │   ├── analysis/                        # Analysis algorithms
│   │   ├── api/                             # Public API
│   │   ├── visualization/                   # Chart generation
│   │   ├── export/                          # Data export
│   │   ├── utils/                           # Utilities (cache, retry, validators)
│   │   ├── errors.py
│   │   ├── types.py
│   │   ├── docs/                            # (8) Library documentation
│   │   └── py.typed
│   ├── rss/                                 # RSS feed monitoring package (32 files)
│   │   ├── cli/                             # CLI interface
│   │   ├── core/                            # Parser, HTTP client, diff detector
│   │   ├── mcp/                             # MCP server integration
│   │   ├── services/                        # Service layer
│   │   ├── storage/                         # JSON persistence
│   │   ├── validators/                      # URL validation
│   │   ├── utils/                           # Logging
│   │   ├── exceptions.py
│   │   ├── types.py
│   │   ├── docs/                            # (8) Library documentation
│   │   └── py.typed
│   ├── factor/                              # Factor analysis library (50 files)
│   │   ├── core/                            # Core algorithms
│   │   ├── factors/                         # Factor implementations (macro, price, quality, size, value)
│   │   ├── providers/                       # Data providers
│   │   ├── validation/                      # Factor validation
│   │   ├── utils/
│   │   └── py.typed
│   └── strategy/                            # Strategy library (29 files)
│       ├── core/
│       ├── output/                          # Output formatter
│       ├── rebalance/                       # Rebalancing
│       ├── risk/                            # Risk management
│       ├── providers/                       # Data providers
│       ├── utils/
│       └── py.typed
├── tests/                                   # Test suite (65+ test files)
│   ├── finance/                             # Finance package tests
│   │   └── db/unit/                         # (3) DB client tests
│   ├── market_analysis/                     # Market analysis tests
│   │   └── unit/                            # (19) Tests
│   ├── rss/                                 # RSS package tests
│   │   ├── unit/                            # (16) Unit tests
│   │   └── integration/                     # (2) Integration tests
│   ├── factor/                              # Factor analysis tests (33 files)
│   ├── strategy/                            # Strategy tests (13 files)
│   └── finance_news_collector/              # News collector tests
├── template/                                # Reference templates (read-only)
│   ├── src/template_package/                # Package structure template
│   ├── tests/                               # Test structure template
│   └── {article_id}-theme-name-en/          # Article template
├── snippets/                                # Reusable content (disclaimers, etc.)
├── scripts/                                 # Utility scripts
├── CLAUDE.md                                # Project instructions
├── README.md                                # Project overview
├── Makefile                                 # Build automation
├── pyproject.toml                           # Python project config
└── uv.lock                                  # Dependency lock file
```

<!-- END: DIRECTORY -->

## 📚 ドキュメント階層

### 🎯 主要ドキュメント

-   **[CLAUDE.md](CLAUDE.md)** - プロジェクト全体の包括的なガイド
    -   プロジェクト概要とコーディング規約
    -   よく使うコマンドと GitHub 操作
    -   型ヒント、テスト戦略、セキュリティ

## 🤖 Claude Code 開発フロー

このプロジェクトでは、スラッシュコマンド、スキル、サブエージェントを組み合わせて開発を進めます。

### コマンド・スキル・エージェントの違い

| 種類               | 説明                                                       | 定義場所           |
| ------------------ | ---------------------------------------------------------- | ------------------ |
| スラッシュコマンド | `/xxx` で直接呼び出す開発タスク                            | `.claude/commands/` |
| スキル             | コマンドから自動的に呼び出されるドキュメント生成・管理機能 | `.claude/skills/`   |
| サブエージェント   | 品質検証・レビューを行う自律エージェント                   | `.claude/agents/`   |

### 開発フェーズと使用するコマンド

#### フェーズ 1: 初期化

| コマンド              | 用途                                   |
| --------------------- | -------------------------------------- |
| `/setup-repository` | テンプレートリポジトリの初期化（初回のみ） |

#### フェーズ 2: 企画・設計

| コマンド       | 用途                                   | 関連スキル/エージェント                              |
| -------------- | -------------------------------------- | ---------------------------------------------------- |
| `/new-package <package_name>` | 新規Pythonパッケージ作成（project.md含む） | -                                                    |
| `/new-project @src/<package_name>/docs/project.md` | プロジェクトファイルからLRD・設計ドキュメントを作成 | prd-writing, functional-design, architecture-design 等 |
| `/review-docs` | ドキュメントの品質レビュー             | doc-reviewer エージェント                            |

#### フェーズ 3: 実装

| コマンド                          | 用途                               | 関連スキル/エージェント                |
| --------------------------------- | ---------------------------------- | -------------------------------------- |
| `/issue @src/<package_name>/docs/project.md` | Issue管理・タスク分解・GitHub同期 | task-decomposer, feature-implementer |
| `/write-tests`                    | TDDによるテスト作成                | -                                      |

#### フェーズ 4: 品質管理

| コマンド          | 用途                                   |
| ----------------- | -------------------------------------- |
| `/ensure-quality` | format→lint→typecheck→testの自動修正   |
| `/safe-refactor`  | テストカバレッジを維持したリファクタリング |
| `/analyze`        | コード分析レポート出力（改善は行わない） |
| `/improve`        | エビデンスベースの改善実装             |
| `/scan`           | セキュリティ・品質の包括的検証         |

#### フェーズ 5: デバッグ・完了

| コマンド          | 用途                   |
| ----------------- | ---------------------- |
| `/troubleshoot`   | 体系的なデバッグ       |
| `/task`           | 複雑なタスクの分解・管理 |
| `/commit-and-pr`  | コミットとPR作成       |

### 典型的なワークフロー例

#### 新機能開発

1. `/new-package <package_name>` - 新規パッケージを作成
2. `/new-project @src/<package_name>/docs/project.md` - project.md作成 → LRD・設計ドキュメントを作成
3. `/review-docs` - 設計ドキュメントをレビュー
4. `/issue @src/<package_name>/docs/project.md` - Issueを作成・管理し、feature-implementerで実装
5. `/ensure-quality` - 品質チェック・自動修正
6. `/commit-and-pr` - PRを作成

#### バグ修正

1. `/troubleshoot --fix` - 原因特定と修正
2. `/ensure-quality` - 品質チェック
3. `/commit-and-pr` - PRを作成

#### パフォーマンス改善

1. `/analyze --perf` - パフォーマンス分析
2. `/improve --perf` - 改善を実装
3. `/scan --validate` - 品質検証

### 詳細情報

すべてのコマンドの詳細は `/index` コマンドで確認できます。

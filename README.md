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

## 🚀 クイックスタート

```bash
# リポジトリをクローン
git clone https://github.com/YH-05/finance.git
cd finance

# Python バージョンを設定（3.12以上）
uv python pin 3.12

# セットアップ
make setup
```

## 使用例

```python
from finance.db import SQLiteClient, DuckDBClient

# SQLite（トランザクション処理）
with SQLiteClient() as client:
    client.execute("INSERT INTO assets (symbol, name) VALUES (?, ?)", ("AAPL", "Apple Inc."))

# DuckDB（分析クエリ）
with DuckDBClient() as client:
    result = client.query("SELECT * FROM prices_daily WHERE symbol = 'AAPL'")
```

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
finance/
├── .claude/                      # Claude Code 設定
│   ├── agents/                   # サブエージェント定義 (45)
│   ├── commands/                 # スラッシュコマンド (27)
│   └── skills/                   # スキル定義 (10)
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
│   ├── market_analysis/          # 市場分析パッケージ
│   │   ├── core/                 # データフェッチャー
│   │   ├── analysis/             # 分析ロジック
│   │   ├── api/                  # パブリックAPI
│   │   ├── visualization/        # チャート生成
│   │   ├── export/               # データエクスポート
│   │   ├── utils/                # ユーティリティ
│   │   └── docs/                 # パッケージドキュメント
│   └── rss/                      # RSS配信パッケージ
│       ├── cli/                  # CLIインターフェース
│       ├── core/                 # フィード生成
│       ├── mcp/                  # MCPサーバー
│       ├── services/             # サービス層
│       ├── storage/              # JSON永続化
│       ├── validators/           # バリデーション
│       ├── utils/                # ユーティリティ
│       └── docs/                 # ライブラリドキュメント
├── template/                     # テンプレート（参照専用）
│   ├── src/template_package/     # パッケージテンプレート
│   ├── tests/                    # テストテンプレート
│   └── {article_id}-theme-name-en/  # 記事テンプレート
├── tests/                        # テストスイート
│   ├── finance/                  # finance テスト
│   ├── market_analysis/          # market_analysis テスト
│   └── rss/                      # rss テスト
├── pyproject.toml                # 依存関係
├── CLAUDE.md                     # Claude Code ガイド
└── README.md                     # このファイル
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

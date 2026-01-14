---
title: CLAUDE.md
created_at: 2025-12-30
updated_at: 2026-01-14
# このプロパティは、Claude Codeが関連するドキュメントの更新を検知するために必要です。消去しないでください。
---

# finance - 金融市場分析・コンテンツ発信支援ライブラリ

**Python 3.12+** | uv | Ruff | pyright | pytest + Hypothesis | pre-commit | GitHub Actions

## プロジェクト概要

金融市場の分析とnote.comでの金融・投資コンテンツ発信を効率化するPythonライブラリ。

### 主要機能

- **市場データ取得・分析**: Yahoo Finance (yfinance) を使用した株価・為替・指標データの取得と分析
- **チャート・グラフ生成**: 分析結果の可視化と図表作成
- **記事生成支援**: 分析結果を元に記事下書きを生成

## クイックリファレンス

### 必須コマンド

```bash
# 品質チェック
make check-all          # 全チェック（format, lint, typecheck, test）
make format             # コードフォーマット
make lint               # リント
make typecheck          # 型チェック
make test               # テスト実行
make test-cov           # カバレッジ付きテスト

# 依存関係
uv add package_name     # 通常パッケージ追加
uv add --dev pkg        # 開発用パッケージ追加
uv sync --all-extras    # 全依存関係を同期

# GitHub操作
/commit-and-pr コマンド  # PR作成（gh pr create使用）
/merge-pr <number>       # PRマージ（コンフリクト・CI確認→マージ）
make issue TITLE="x" BODY="y"           # Issue作成
```

### Git 規則

-   **ブランチ**: `feature/` | `fix/` | `refactor/` | `docs/` | `test/` | `release/`
-   **ラベル**: `enhancement` | `bug` | `refactor` | `documentation` | `test`
-   **pre-push hook**: プロジェクト整合性チェック（循環依存・ステータス不整合を検出）
    - Critical エラー → push をブロック
    - Warning → 警告表示（`--strict` でブロック）
    - スキップ: `git push --no-verify`

### PR / Issue 規則

-   **言語**: タイトル・本文は**日本語**で記述
-   **PRテンプレート**:
    ```markdown
    ## 概要
    - <変更点1>
    - <変更点2>

    ## テストプラン
    - [ ] make check-all が成功することを確認
    ```
-   **Issueテンプレート**:
    ```markdown
    ## 概要
    [機能・問題の概要]

    ## 詳細
    [詳細な説明]

    ## 受け入れ条件
    - [ ] [条件1]
    ```

## 実装規約

### 実装フロー

1. format → lint → typecheck → test
2. 新機能は TDD 必須
3. 全コードにログ必須
4. 重い処理はプロファイル実施

### コーディングスタイル

| 項目         | 規約                            |
| ------------ | ------------------------------- |
| 型ヒント     | Python 3.12+ スタイル（PEP 695） |
| Docstring    | NumPy 形式                      |
| クラス名     | PascalCase                      |
| 関数/変数名  | snake_case                      |
| 定数         | UPPER_SNAKE                     |
| プライベート | \_prefix                        |

### Docstring（NumPy 形式）

```python
def process_items(
    items: list[dict[str, Any]],
    max_count: int = 100,
    validate: bool = True,
) -> list[dict[str, Any]]:
    """Process a list of items with optional validation.

    Parameters
    ----------
    items : list[dict[str, Any]]
        List of items to process
    max_count : int, default=100
        Maximum number of items to process
    validate : bool, default=True
        Whether to validate items before processing

    Returns
    -------
    list[dict[str, Any]]
        Processed items

    Raises
    ------
    ValueError
        If items is empty when validation is enabled
    TypeError
        If items contains non-dict elements

    Examples
    --------
    >>> items = [{"id": 1, "name": "test"}]
    >>> result = process_items(items)
    >>> len(result)
    1
    """
```

### エラーメッセージ

```python
# ❌ Bad
raise ValueError("Invalid input")

# ✅ Good
raise ValueError(f"Expected positive integer, got {count}")
raise ValueError(f"Failed to process {source_file}: {e}")
raise FileNotFoundError(f"Config not found. Create by: python -m {__package__}.init")
```

### ロギング（必須）

```python
from finance.utils.logging_config import get_logger

logger = get_logger(__name__)

def process_data(data: list) -> list:
    logger.debug("Processing started", item_count=len(data))
    try:
        result = transform(data)
        logger.info("Processing completed", output_count=len(result))
        return result
    except Exception as e:
        logger.error("Processing failed", error=str(e), exc_info=True)
        raise
```

### 環境変数

| 変数名      | 説明                              | デフォルト  |
| ----------- | --------------------------------- | ----------- |
| LOG_LEVEL   | ログレベル                        | INFO        |
| LOG_FORMAT  | フォーマット (json/text)          | text        |
| PROJECT_ENV | 環境 (development/production)     | development |

### アンカーコメント

```python
# AIDEV-NOTE: 実装の意図や背景の説明
# AIDEV-TODO: 未完了タスク
# AIDEV-QUESTION: 確認が必要な疑問点
```

## template/ 参照パターン

実装前に必ず参照すること。template/ は変更・削除禁止。

| 実装対象         | 参照先                                                   |
| ---------------- | -------------------------------------------------------- |
| モジュール概要   | `template/src/template_package/README.md`               |
| クラス/関数      | `template/src/template_package/core/example.py`         |
| 型定義           | `template/src/template_package/types.py`                |
| ユーティリティ   | `template/src/template_package/utils/helpers.py`        |
| ロギング設定     | `template/src/template_package/utils/logging_config.py` |
| プロファイリング | `template/src/template_package/utils/profiling.py`      |
| 単体テスト       | `template/tests/unit/`                                  |
| プロパティテスト | `template/tests/property/`                              |
| 統合テスト       | `template/tests/integration/`                           |
| フィクスチャ     | `template/tests/conftest.py`                            |

### プロファイリング使用例

```python
from finance.utils.profiling import profile, timeit, profile_context

@profile  # 詳細プロファイリング
def heavy_function():
    ...

@timeit  # 実行時間計測
def timed_function():
    ...

with profile_context("処理名"):  # コンテキスト計測
    ...
```

## タスク別ガイド参照

| タスク             | 参照先                                                     |
| ------------------ | ---------------------------------------------------------- |
| 並行開発計画       | `/plan-worktrees <project_number>` コマンド（依存関係解析→Wave グルーピング）|
| 並行開発環境作成   | `/worktree <branch_name>` コマンド（worktree + ブランチ） |
| 開発完了クリーンアップ | `/worktree-done <branch_name>` コマンド（PRマージ確認 → 削除） |
| パッケージ作成     | `/new-package <package_name>` コマンド                      |
| 開発開始（パッケージ）| `/new-project @src/<library_name>/docs/project.md`（LRD → 設計 → タスク）|
| 開発開始（軽量）   | `/new-project "プロジェクト名"`（インタビュー → GitHub Project → Issue）|
| Issue管理          | `/issue @src/<library_name>/docs/project.md` コマンド       |
| Issueブラッシュアップ | `/issue-refine 番号` コマンド（内容改善・明確化・テンプレート準拠）|
| プロジェクト健全性 | `/project-refine` コマンド（適合性チェック・タスク再構成）|
| Issueコメント同期  | `/sync-issue #番号` コマンド（コメント→進捗・タスク・仕様同期）|
| テスト作成         | `/write-tests` コマンド または `docs/testing-strategy.md` |
| ドキュメント作成   | `docs/document-management.md`                             |
| 図表作成           | `docs/diagram-guidelines.md`                              |
| コーディング規約   | `docs/coding-standards.md`                                |
| 開発プロセス       | `docs/development-process.md`                             |
| コード品質改善     | `/ensure-quality` コマンド（自動修正）                     |
| リファクタリング   | `/safe-refactor` コマンド                                  |
| コード分析         | `/analyze` コマンド（分析レポート出力）                    |
| 改善実装           | `/improve` コマンド（エビデンスベース改善）                |
| セキュリティ検証   | `/scan` コマンド（検証・スコアリング）                     |
| デバッグ           | `/troubleshoot` コマンド（体系的デバッグ）                 |
| タスク管理         | `/task` コマンド（複雑タスク分解・管理）                   |
| Git操作            | `/commit-and-pr` コマンド                                  |
| PRマージ           | `/merge-pr` コマンド（コンフリクトチェック・CI確認・マージ） |
| コンフリクト分析   | `/analyze-conflicts` コマンド（詳細分析・問題点・解決策） |
| PRレビュー         | `/review-pr` コマンド（コード品質・セキュリティ・テスト） |
| ドキュメントレビュー | `/review-docs` コマンド                                  |
| 初期化（初回のみ） | `/setup-repository` コマンド                             |
| コマンド一覧       | `/index` コマンド                                          |
| **金融記事作成**   |                                                            |
| トピック提案       | `/finance-suggest-topics` コマンド（スコアリング付き提案） |
| 記事初期化         | `/new-finance-article` コマンド（カテゴリ別テンプレート）  |
| リサーチ実行       | `/finance-research` コマンド（データ収集→分析→決定）       |
| 編集・批評         | `/finance-edit` コマンド（初稿→批評→修正）                 |

## エビデンスベース開発

### 禁止語と推奨語

| 禁止           | 推奨                       |
| -------------- | -------------------------- |
| best, optimal  | measured X, documented Y   |
| faster, slower | reduces X%, increases Y ms |
| always, never  | typically, in most cases   |
| perfect, ideal | meets requirement X        |

### 証拠要件

-   **性能**: "measured Xms" | "reduces X%"
-   **品質**: "coverage X%" | "complexity Y"
-   **セキュリティ**: "scan detected X"

## 効率化テクニック

### コミュニケーション記法

```
→  処理フロー      analyze → fix → test
|  選択/区切り     option1 | option2
&  並列/結合       task1 & task2
»  シーケンス      step1 » step2
@  参照/場所       @file:line
```

### 実行パターン

-   **並列**: 依存なし & 競合なし → 複数ファイル読込、独立テスト
-   **バッチ**: 同種操作 → 一括フォーマット、インポート修正
-   **逐次**: 依存あり | 状態変更 → DB マイグレ、段階的リファクタ

### エラーリカバリー

-   **リトライ**: max 3 回、指数バックオフ
-   **フォールバック**: 高速手法 → 確実な手法
-   **状態復元**: チェックポイント » ロールバック

## ディレクトリ構成

<!-- AUTO-GENERATED: DIRECTORY -->

```
.claude/                      # Claude Code設定
├── agents/                   # サブエージェント定義 (48)
├── commands/                 # スラッシュコマンド (30)
└── skills/                   # スキル定義 (10)

data/                         # データストレージ
├── config/                   # 設定ファイル（FRED series等）
├── sqlite/                   # SQLite DB（OLTP: トランザクション処理）
├── duckdb/                   # DuckDB（OLAP: 分析クエリ）
├── raw/                      # 生データ（Parquet形式）
│   ├── yfinance/             # yfinance取得データ（stocks/forex/indices）
│   └── fred/                 # FRED経済指標
├── processed/                # 加工済みデータ（daily/aggregated）
├── exports/                  # エクスポート（csv/json）
└── schemas/                  # JSONスキーマ (12)

src/
├── finance/                  # 共通インフラパッケージ
│   ├── db/                   # データベースクライアント
│   │   ├── sqlite_client.py  # SQLiteClient（トランザクション操作）
│   │   ├── duckdb_client.py  # DuckDBClient（分析クエリ+Parquet）
│   │   ├── connection.py     # 接続管理
│   │   └── migrations/       # マイグレーションシステム
│   ├── utils/                # ユーティリティ
│   │   └── logging_config.py # ロギング設定
│   ├── types.py              # 型定義
│   └── py.typed              # PEP 561マーカー
├── market_analysis/          # 市場分析パッケージ
│   ├── core/                 # データフェッチャー（yfinance, FRED）
│   ├── analysis/             # 分析ロジック（indicators, correlation）
│   ├── api/                  # パブリックAPI（analysis, chart, market_data）
│   ├── visualization/        # チャート生成
│   ├── export/               # データエクスポート
│   ├── utils/                # ユーティリティ（cache, retry, validators）
│   └── docs/                 # ライブラリドキュメント (8)
└── rss/                      # RSS配信パッケージ
    ├── cli/                  # CLIインターフェース
    ├── core/                 # コア機能（parser, diff_detector）
    ├── mcp/                  # MCPサーバー統合
    ├── services/             # サービス層
    ├── storage/              # JSON永続化
    ├── validators/           # バリデーション
    ├── utils/                # ユーティリティ
    └── docs/                 # ライブラリドキュメント (8)

tests/
├── finance/                  # financeパッケージテスト
│   └── db/unit/              # DBユニットテスト (3)
├── market_analysis/          # market_analysisテスト
│   └── unit/                 # ユニットテスト (24)
└── rss/                      # rssテスト
    ├── unit/                 # ユニットテスト (13)
    └── integration/          # 統合テスト (1)

template/                     # テンプレート（参照専用）
├── src/template_package/     # パッケージテンプレート
├── tests/                    # テストテンプレート
├── {article_id}-theme-name-en/  # 記事テンプレート
├── market_report/            # 市場レポートテンプレート
├── stock_analysis/           # 個別銘柄分析テンプレート
├── economic_indicators/      # 経済指標解説テンプレート
├── investment_education/     # 投資教育テンプレート
└── quant_analysis/           # クオンツ分析テンプレート

articles/                     # 金融記事ワークスペース
└── {category}_{id}_{slug}/   # 記事フォルダ
    ├── article-meta.json     # 記事メタデータ・ワークフロー状態
    ├── 01_research/          # リサーチ成果物
    ├── 02_edit/              # 編集成果物
    └── 03_published/         # 公開版

docs/                         # リポジトリ共通ドキュメント（規約等）
snippets/                     # 再利用コンテンツ（免責事項等）
```

<!-- END: DIRECTORY -->

## 更新トリガー

-   仕様/依存関係/構造/規約の変更時
-   同一質問 2 回以上 → FAQ 追加
-   エラーパターン 2 回以上 → トラブルシューティング追加

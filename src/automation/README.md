# automation

Claude Agent SDK を使った自動化スクリプト集。金融ニュース収集などのワークフローを自動実行します。

## 概要

このパッケージは、Claude Code のスキルやワークフローをプログラマティックに実行するためのスクリプトを提供します。

**主な特徴:**

- Claude Agent SDK による自動化
- 定期実行（cron / launchd）対応
- MCP サーバー設定の自動読み込み（`.mcp.json`）
- 構造化ロギング

<!-- AUTO-GENERATED: QUICKSTART -->

## クイックスタート

### インストール

```bash
# automation 依存関係をインストール
uv sync --extra automation
```

### 基本的な使い方

```python
from automation.news_collector import run_news_collection

# 1. デフォルト設定で実行（過去7日分のニュース収集）
await run_news_collection()

# 2. カスタム設定で実行
await run_news_collection(
    days=3,                        # 過去3日分
    themes=["index", "macro"],     # 特定テーマのみ
    dry_run=True                   # 投稿せず確認のみ
)
```

### CLIから実行

```bash
# 基本実行
uv run python -m automation

# オプション付き実行
uv run python -m automation --days 3 --themes index,macro --dry-run

# スクリプトエントリポイントから実行
uv run collect-finance-news --days 7
```

### よくある使い方

#### パターン1: 定期的なニュース収集（デフォルト設定）

```python
from automation.news_collector import run_news_collection

# 毎日実行する場合（cronやlaunchdから呼び出し）
success = await run_news_collection()
if not success:
    # エラーハンドリング
    logger.error("News collection failed")
```

#### パターン2: 特定テーマのみ収集

```python
from automation.news_collector import run_news_collection

# 株価指数とマクロ経済のみ
await run_news_collection(
    days=3,
    themes=["index", "macro"]
)
```

#### パターン3: テスト実行（ドライラン）

```python
from automation.news_collector import run_news_collection

# GitHub投稿せずに動作確認
await run_news_collection(
    days=1,
    dry_run=True
)
```

<!-- END: QUICKSTART -->

<!-- AUTO-GENERATED: STRUCTURE -->

## ディレクトリ構成

```
automation/
├── __init__.py          # パッケージ定義
├── __main__.py          # モジュールエントリポイント
├── dev.py               # 開発用テストスクリプト
├── news_collector.py    # ニュース収集ワークフロー実行
└── README.md            # このファイル
```

<!-- END: STRUCTURE -->

<!-- AUTO-GENERATED: IMPLEMENTATION -->

## 実装状況

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|-----------|------|
| `__init__.py` | ✅ 実装済み | 1 | 7 |
| `__main__.py` | ✅ 実装済み | 1 | 13 |
| `news_collector.py` | ✅ 実装済み | 1 | 362 |
| `dev.py` | 🚧 開発中 | 1 | 19 |

<!-- END: IMPLEMENTATION -->

<!-- AUTO-GENERATED: API -->

## 公開API

### 主要クラス

#### `NewsCollectorConfig`

**説明**: ニュース収集の設定を管理するdataclass

**基本的な使い方**:

```python
from automation.news_collector import NewsCollectorConfig

# 設定を作成
config = NewsCollectorConfig(
    days=3,
    themes=["index", "macro"],
    dry_run=True
)

# コマンド引数文字列を生成
args = config.to_command_args()
# → "--days 3 --themes "index,macro" --dry-run"
```

**主な属性**:

| 属性 | 型 | デフォルト | 説明 |
|------|------|-----------|------|
| `days` | `int` | `7` | 過去何日分のニュースを対象とするか |
| `project` | `int` | `15` | GitHub Project 番号 |
| `themes` | `list[str]` | `[]` | 対象テーマのリスト（空の場合は全テーマ） |
| `dry_run` | `bool` | `False` | True の場合、GitHub 投稿せずに結果確認のみ |

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `to_command_args()` | コマンド引数文字列を生成 | `str` |

---

#### `NewsCollector`

**説明**: 金融ニュース収集の実行を管理するクラス。Claude Agent SDKを使用してfinance-news-workflowスキルを実行します。

**基本的な使い方**:

```python
from automation.news_collector import NewsCollector, NewsCollectorConfig

# 設定を作成
config = NewsCollectorConfig(days=3, dry_run=True)

# コレクターを初期化
collector = NewsCollector(config)

# 実行
success = await collector.run()
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `run()` | ニュース収集ワークフローを実行 | `bool` |
| `_find_project_root()` | プロジェクトルートディレクトリを検索 | `Path` |
| `_load_mcp_config()` | MCP設定ファイルを読み込み | `dict[str, Any]` |

---

### 関数

#### `run_news_collection(*, days=7, project=15, themes=None, dry_run=False)`

**説明**: ニュース収集を実行するメインエントリポイント

**使用例**:

```python
from automation.news_collector import run_news_collection

# デフォルト設定で実行
await run_news_collection()

# オプション指定
await run_news_collection(
    days=3,
    themes=["index", "macro"],
    dry_run=True
)
```

**パラメータ**:

| パラメータ | 型 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `days` | `int` | `7` | 過去何日分のニュースを対象とするか |
| `project` | `int` | `15` | GitHub Project 番号 |
| `themes` | `Sequence[str] \| None` | `None` | 対象テーマのリスト（None の場合は全テーマ） |
| `dry_run` | `bool` | `False` | True の場合、GitHub 投稿せずに結果確認のみ |

**戻り値**: `bool` - 成功した場合 True

---

#### `parse_args(argv=None)`

**説明**: コマンドライン引数をパースする

**使用例**:

```python
from automation.news_collector import parse_args

# sys.argvから引数を取得
config = parse_args()

# カスタム引数リストをパース
config = parse_args(["--days", "3", "--dry-run"])
```

---

#### `main()`

**説明**: CLI エントリポイント

**使用例**:

```bash
# Pythonモジュールとして実行
uv run python -m automation.news_collector

# スクリプトとして実行
uv run collect-finance-news --days 3
```

**戻り値**: `int` - 終了コード（0: 成功, 1: 失敗, 130: キーボード割り込み）

<!-- END: API -->

<!-- AUTO-GENERATED: STATS -->

## モジュール統計

| 項目 | 値 |
|------|-----|
| Python ファイル数 | 4 |
| 総行数（実装コード） | 401 |
| テストファイル数 | 0 |
| テストカバレッジ | N/A |

<!-- END: STATS -->

## シェルスクリプトから実行

```bash
# プロジェクトルートから
./scripts/collect-news.sh

# オプション付き
./scripts/collect-news.sh --days 3 --dry-run
```

## 定期実行の設定

### Cron（Linux/macOS）

```crontab
# 毎日朝7時に実行
0 7 * * * /path/to/finance/scripts/collect-news.sh >> /var/log/finance-news.log 2>&1
```

### Launchd（macOS）

```bash
# plist ファイルをコピー（パスを環境に合わせて編集）
cp scripts/com.finance.news-collector.plist ~/Library/LaunchAgents/

# 有効化
launchctl load ~/Library/LaunchAgents/com.finance.news-collector.plist

# 無効化
launchctl unload ~/Library/LaunchAgents/com.finance.news-collector.plist

# 手動実行テスト
launchctl start com.finance.news-collector
```

## 依存関係

- `claude-agent-sdk>=0.1.22`: Claude Agent SDK
- `anyio>=4.0.0`: 非同期ランタイム
- `database`: ロギングユーティリティ（フォールバックあり）

## MCP サーバー設定

プロジェクトルートの `.mcp.json` を自動的に読み込みます。
RSS MCP サーバーなどが設定されている場合、そのまま利用可能です。

## 関連リソース

| リソース | パス |
|---------|------|
| finance-news-workflow スキル | `.claude/skills/finance-news-workflow/SKILL.md` |
| テーマ設定 | `data/config/finance-news-themes.json` |
| 定期実行スクリプト | `scripts/collect-news.sh` |
| launchd plist | `scripts/com.finance.news-collector.plist` |
| GitHub Project | https://github.com/users/YH-05/projects/15 |

## 更新履歴

このREADME.mdは、モジュール構造や公開APIに変更があった場合に更新してください。

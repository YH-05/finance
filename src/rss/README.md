# rss

RSS/Atomフィード管理パッケージ

## 概要

このパッケージは、RSS/Atomフィードの取得、パース、差分検出、永続化、スケジューリング機能を提供します。

**主な機能:**
- フィード登録・管理（URL、カテゴリ、取得間隔）
- フィード取得・パース（RSS 2.0/Atom対応、非同期処理）
- 差分検出（新規エントリーのみ抽出）
- 記事コンテンツ抽出（trafilatura統合、ペイウォール検出）
- JSON永続化（フィード情報・エントリー）
- 日次バッチスケジューリング（APScheduler統合）
- MCP統合（Model Context Protocol対応）
- キーワード検索（フィードエントリーの全文検索）

**現在のバージョン:** 0.1.0

<!-- AUTO-GENERATED: QUICKSTART -->

## クイックスタート

### インストール

```bash
# このリポジトリのパッケージとして利用
uv sync --all-extras
```

### 基本的な使い方

```python
import asyncio
from pathlib import Path
from rss import FeedManager, FeedFetcher

# 1. フィードマネージャーを作成
data_dir = Path("data/raw/rss")
manager = FeedManager(data_dir)

# 2. フィードを登録
feed_id = manager.add_feed(
    url="https://example.com/feed.xml",
    title="Example Feed",
    category="finance",
)

# 3. フィードを取得（非同期）
async def fetch_feeds():
    fetcher = FeedFetcher(data_dir)
    results = await fetcher.fetch_all()

    for result in results:
        if result.success:
            print(f"{result.feed_id}: {result.new_items} new items")

# 実行
asyncio.run(fetch_feeds())
```

### よくある使い方

#### ユースケース1: フィード一覧と検索

```python
from pathlib import Path
from rss import FeedManager, FeedReader

manager = FeedManager(Path("data/raw/rss"))
reader = FeedReader(Path("data/raw/rss"))

# 登録済みフィード一覧
feeds = manager.list_feeds()
for feed in feeds:
    print(f"{feed.title}: {feed.url}")

# 全エントリー取得（ページング）
items = reader.get_items(limit=10, offset=0)
for item in items:
    print(f"{item.title}: {item.link}")

# キーワード検索
results = reader.search_items("金融政策", limit=5)
for item in results:
    print(f"{item.title}")
```

#### ユースケース2: 記事コンテンツ抽出

```python
import asyncio
from pathlib import Path
from rss import ArticleExtractor

# 記事本文を抽出
async def extract_article():
    extractor = ArticleExtractor()
    result = await extractor.extract("https://example.com/article")

    if result.status == "success":
        print(f"Title: {result.title}")
        print(f"Content length: {len(result.content or '')}")
    elif result.status == "paywall":
        print("Paywall detected")

asyncio.run(extract_article())
```

#### ユースケース3: 日次バッチスケジューリング

```python
from pathlib import Path
from rss import BatchScheduler, FeedFetcher

# フェッチャーを作成
fetcher = FeedFetcher(Path("data/raw/rss"))

# 毎日午前6時にフィード取得を実行
scheduler = BatchScheduler(fetcher, hour=6, minute=0)

# 手動実行
stats = scheduler.run_batch()
print(f"Success: {stats.success_count}/{stats.total_feeds}")
print(f"New items: {stats.new_items}")

# 自動実行（バックグラウンド）
scheduler.start(blocking=False)
# 停止する場合
# scheduler.stop()
```

**注意**: スケジューリング機能を使用するには `apscheduler` が必要です。

```bash
uv sync --extra scheduler
```

<!-- END: QUICKSTART -->

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->

```
rss/
├── __init__.py              # 公開API定義
├── py.typed                 # PEP 561型マーカー
├── types.py                 # 型定義（Feed, FeedItem, FetchResult等）
├── exceptions.py            # カスタム例外（7種類）
├── cli/                     # CLIインターフェース
│   ├── __init__.py
│   └── main.py              # 7コマンド（add/list/fetch/remove/search/show/update）
├── core/                    # コア機能
│   ├── __init__.py
│   ├── diff_detector.py     # 差分検出
│   ├── http_client.py       # HTTP通信（httpx）
│   └── parser.py            # RSS/Atomパーサー（feedparser）
├── mcp/                     # MCP統合
│   ├── __init__.py
│   └── server.py            # MCPサーバー（9ツール提供）
├── services/                # サービス層
│   ├── __init__.py
│   ├── article_content_checker.py    # 記事コンテンツ検証
│   ├── article_extractor.py          # 記事本文抽出
│   ├── article_extractor_cli.py      # 抽出CLI
│   ├── batch_scheduler.py            # バッチスケジューリング
│   ├── feed_fetcher.py               # フィード取得
│   ├── feed_manager.py               # フィード管理
│   ├── feed_reader.py                # フィード読込・検索
│   └── news_categorizer.py           # ニュース分類
├── storage/                 # 永続化層
│   ├── __init__.py
│   ├── json_storage.py      # JSONストレージ
│   └── lock_manager.py      # ファイルロック
├── utils/                   # ユーティリティ
│   ├── __init__.py
│   └── url_normalizer.py    # URL正規化
└── validators/              # バリデーション層
    ├── __init__.py
    └── url_validator.py     # URL/タイトル/カテゴリ検証
```

<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール        | 状態        | ファイル数 | 行数  | 説明                                             |
| ----------------- | ----------- | ---------- | ----- | ------------------------------------------------ |
| `types.py`        | ✅ 実装済み | 1          | 409   | 型定義（Feed, FeedItem, BatchStats, ExtractedArticle等） |
| `exceptions.py`   | ✅ 実装済み | 1          | 161   | カスタム例外（7種類）                            |
| `cli/`            | ✅ 実装済み | 2          | 727   | CLIインターフェース（7コマンド）                 |
| `core/`           | ✅ 実装済み | 4          | 829   | コア機能（HTTP/パース/差分検出）                 |
| `mcp/`            | ✅ 実装済み | 2          | 654   | MCPサーバー統合（9ツール提供）                   |
| `services/`       | ✅ 実装済み | 8          | 3,535 | サービス層（Manager/Fetcher/Reader/Scheduler/ArticleExtractor/ContentChecker/Categorizer） |
| `storage/`        | ✅ 実装済み | 3          | 669   | 永続化層（JSONストレージ・ロック管理）           |
| `utils/`          | ✅ 実装済み | 3          | 345   | ユーティリティ（URL正規化）                      |
| `validators/`     | ✅ 実装済み | 2          | 235   | バリデーション（URL/タイトル/カテゴリ）          |

**テストカバレッジ**: 全モジュールにテストが存在（unit: 15ファイル, integration: 3ファイル, property: 2ファイル）

<!-- END: IMPLEMENTATION -->

## 公開API

<!-- AUTO-GENERATED: API -->

### クイックスタート

パッケージの基本的な使い方:

```python
import asyncio
from pathlib import Path
from rss import FeedManager, FeedFetcher

# フィード管理
manager = FeedManager(Path("data/raw/rss"))
feed_id = manager.add_feed("https://example.com/feed.xml", "Example", "finance")

# フィード取得（非同期）
async def fetch_all():
    fetcher = FeedFetcher(Path("data/raw/rss"))
    results = await fetcher.fetch_all()
    return results

asyncio.run(fetch_all())
```

### 主要クラス

#### `FeedManager`

**説明**: フィード登録・管理を行うサービスクラス。URL検証、重複チェック、JSON永続化を統合。

**基本的な使い方**:

```python
from pathlib import Path
from rss import FeedManager

# 初期化
manager = FeedManager(Path("data/raw/rss"))

# フィード登録
feed_id = manager.add_feed(
    url="https://example.com/feed.xml",
    title="Example Feed",
    category="finance",
)

# フィード一覧
feeds = manager.list_feeds()

# フィード削除
manager.remove_feed(feed_id)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `add_feed(url, title, category)` | フィード登録（URL検証・重複チェック） | `str` (feed_id) |
| `list_feeds()` | 全フィード取得 | `list[Feed]` |
| `get_feed(feed_id)` | フィード取得 | `Feed` |
| `remove_feed(feed_id)` | フィード削除 | `None` |
| `update_feed_status(feed_id, status)` | ステータス更新 | `None` |

---

#### `FeedFetcher`

**説明**: フィード取得・パース・差分検出・永続化を統合したサービスクラス。非同期処理に対応。

**基本的な使い方**:

```python
import asyncio
from pathlib import Path
from rss import FeedFetcher

# 初期化
fetcher = FeedFetcher(Path("data/raw/rss"))

# 全フィード取得（非同期）
async def fetch_all_feeds():
    results = await fetcher.fetch_all()
    for result in results:
        if result.success:
            print(f"{result.new_items} new items")

asyncio.run(fetch_all_feeds())

# 個別フィード取得（非同期）
async def fetch_single_feed(feed_id):
    result = await fetcher.fetch_feed(feed_id)
    return result

asyncio.run(fetch_single_feed("feed-id-123"))
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `fetch_feed(feed_id)` | 個別フィード取得（非同期） | `FetchResult` |
| `fetch_all(max_concurrent=5)` | 全フィード取得（並列実行、非同期） | `list[FetchResult]` |

---

#### `FeedReader`

**説明**: 永続化されたフィードエントリーの読み込み・検索を行うサービスクラス。

**基本的な使い方**:

```python
from pathlib import Path
from rss import FeedReader

# 初期化
reader = FeedReader(Path("data/raw/rss"))

# 全エントリー取得（ページング）
items = reader.get_items(limit=10, offset=0)

# キーワード検索
results = reader.search_items("金融政策", limit=5)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `get_items(feed_id, limit, offset)` | 全エントリー取得（ページング対応） | `list[FeedItem]` |
| `search_items(keyword, limit, offset)` | キーワード検索 | `list[FeedItem]` |

---

#### `BatchScheduler`

**説明**: 日次バッチスケジューリングを提供するサービスクラス。APScheduler統合。

**基本的な使い方**:

```python
from pathlib import Path
from rss import BatchScheduler, FeedFetcher

# フェッチャーを作成
fetcher = FeedFetcher(Path("data/raw/rss"))

# スケジューラーを作成
scheduler = BatchScheduler(fetcher, hour=6, minute=0)

# 手動実行
stats = scheduler.run_batch()
print(f"Success: {stats.success_count}/{stats.total_feeds}")

# 自動実行（バックグラウンド）
scheduler.start(blocking=False)
scheduler.stop()
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `run_batch()` | バッチ手動実行 | `BatchStats` |
| `start(blocking=True)` | スケジューラー起動 | `None` |
| `stop()` | スケジューラー停止 | `None` |

---

#### `ArticleExtractor`

**説明**: Webページから記事コンテンツを抽出するサービスクラス。trafilaturaをメインエンジンとして使用。

**基本的な使い方**:

```python
import asyncio
from rss import ArticleExtractor

# 初期化
extractor = ArticleExtractor()

# 単一記事の抽出
async def extract_single():
    result = await extractor.extract("https://example.com/article")
    if result.status == "success":
        print(f"Title: {result.title}")
        print(f"Content: {result.content[:200]}...")
    elif result.status == "paywall":
        print("Paywall detected")

asyncio.run(extract_single())

# 複数記事の一括抽出
async def extract_batch():
    urls = [
        "https://example.com/article1",
        "https://example.com/article2",
    ]
    results = await extractor.extract_batch(urls, max_concurrent=3)
    for result in results:
        print(f"{result.url}: {result.status}")

asyncio.run(extract_batch())
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `extract(url)` | 単一記事の抽出 | `ExtractedArticle` |
| `extract_batch(urls, max_concurrent)` | 複数記事の一括抽出 | `list[ExtractedArticle]` |

---

### 関数

#### `get_logger(name, module=None)`

**説明**: 構造化ロギング用のロガーを取得する関数。

**使用例**:

```python
from rss import get_logger

logger = get_logger(__name__, module="my_module")
logger.info("Processing started", count=10)
logger.error("Processing failed", error="Connection timeout")
```

---

### 型定義

データ構造の定義。型ヒントやバリデーションに使用:

```python
from rss import (
    # データモデル
    Feed,                # フィード情報（id, url, title, category 等）
    FeedItem,            # フィードエントリー（title, link, published 等）
    FetchResult,         # 取得結果（success, new_items, error 等）
    BatchStats,          # バッチ統計（total_feeds, success_count 等）
    ExtractedArticle,    # 記事抽出結果（title, content, status 等）

    # Enum
    FetchInterval,       # 取得間隔（DAILY/WEEKLY/MANUAL）
    FetchStatus,         # 取得ステータス（SUCCESS/FAILURE/PENDING）
    ExtractionStatus,    # 抽出ステータス（SUCCESS/FAILED/PAYWALL/TIMEOUT）
)
```

---

### 例外クラス

エラーハンドリングに使用:

```python
from rss import (
    RSSError,                  # 基底例外
    FeedNotFoundError,         # フィード未発見
    FeedAlreadyExistsError,    # フィード重複
    FeedFetchError,            # 取得失敗
    FeedParseError,            # パース失敗
    InvalidURLError,           # URL不正
    FileLockError,             # ファイルロック失敗
)
```

**使用例**:

```python
from pathlib import Path
from rss import FeedManager, FeedNotFoundError

manager = FeedManager(Path("data/raw/rss"))
try:
    feed = manager.get_feed("invalid_id")
except FeedNotFoundError as e:
    print(f"Feed not found: {e}")
```

<!-- END: API -->

## 統計

<!-- AUTO-GENERATED: STATS -->

| 項目                     | 値     |
| ------------------------ | ------ |
| Pythonファイル数         | 27     |
| 総行数（実装コード）     | 7,672  |
| モジュール数             | 9      |
| テストファイル数         | 35     |
| 実装カバレッジ           | 100% (全モジュールにテストあり) |

**主要コンポーネント**:
- サービスクラス: 8 (Manager/Fetcher/Reader/Scheduler/ArticleExtractor/ArticleContentChecker/Categorizer/ArticleExtractorCLI)
- コアモジュール: 3 (HTTP/Parser/DiffDetector)
- データモデル: 8 (Feed/FeedItem/FetchResult/BatchStats/ExtractedArticle/FetchInterval/FetchStatus/ExtractionStatus)
- 例外クラス: 7 (基底 + 6種類の専用例外)
- ユーティリティ: 2 (URL正規化/バリデーション)
- MCP統合: 9ツール (フィード管理・取得・検索)
- CLI統合: 7コマンド (add/list/fetch/remove/search/show/update)

<!-- END: STATS -->

## 依存関係

### 必須依存関係

| パッケージ | 用途 | 最小バージョン |
|-----------|------|---------------|
| `httpx` | HTTP通信（非同期対応） | 0.28.1+ |
| `feedparser` | RSS/Atomフィードパース | 6.0.12+ |
| `trafilatura` | Webページコンテンツ抽出 | 2.1.0+ |
| `lxml` | HTML/XMLパーサー | 5.3.0+ |
| `filelock` | ファイルロック管理 | 3.20.3+ |

### オプション依存関係

| パッケージ | 用途 | インストール方法 |
|-----------|------|-----------------|
| `apscheduler` | バッチスケジューリング | `uv add apscheduler` or `uv sync --extra scheduler` |
| `fastmcp` | MCP統合 | `uv sync --extra mcp` |
| `click` | CLI機能 | `uv sync --extra cli` |

### インストール例

```bash
# 基本機能のみ
uv sync

# スケジューリング機能を含む
uv sync --extra scheduler

# 全機能を有効化
uv sync --all-extras
```

## 開発ガイド

### 拡張方法

1. **新しいサービス追加**: `services/` にクラスを作成し、`services/__init__.py` でエクスポート
2. **新しいバリデーター追加**: `validators/` にクラスを作成
3. **型定義追加**: `types.py` に追加し、`__init__.py` の `__all__` に登録

### テスト実行

```bash
# 全テスト実行
make test

# カバレッジ付きテスト
make test-cov

# 特定のテストのみ実行
pytest tests/rss/unit/services/test_feed_manager.py
```

### 品質チェック

```bash
# 全チェック実行
make check-all

# フォーマット
make format

# リント
make lint

# 型チェック
make typecheck
```

## 関連ドキュメント

-   `src/rss/docs/project.md` - プロジェクトファイル（要件・タスク）
-   `src/rss/docs/functional-design.md` - 機能設計書
-   `src/rss/docs/architecture.md` - アーキテクチャ設計書
-   `template/src/template_package/README.md` - テンプレート実装の詳細
-   `docs/development-guidelines.md` - 開発ガイドライン

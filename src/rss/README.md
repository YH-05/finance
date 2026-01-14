# rss

RSS/Atomフィード管理パッケージ

## 概要

このパッケージは、RSS/Atomフィードの取得、パース、差分検出、永続化、スケジューリング機能を提供します。

**主な機能:**
- フィード登録・管理（URL、カテゴリ、取得間隔）
- フィード取得・パース（RSS 2.0/Atom対応）
- 差分検出（新規エントリーのみ抽出）
- JSON永続化（フィード情報・エントリー）
- 日次バッチスケジューリング（APScheduler統合）
- MCP統合（Model Context Protocol対応）

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

# 3. フィードを取得
fetcher = FeedFetcher(data_dir)
results = fetcher.fetch_all()

# 4. 結果を確認
for result in results:
    if result.success:
        print(f"{result.feed_id}: {result.new_items} new items")
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
items = reader.get_all_items(limit=10, offset=0)
for item in items:
    print(f"{item.title}: {item.link}")

# キーワード検索
results = reader.search_items("金融政策", limit=5)
for item in results:
    print(f"{item.title}")
```

#### ユースケース2: 日次バッチスケジューリング

```python
from pathlib import Path
from rss import BatchScheduler

# 毎日午前6時にフィード取得を実行
scheduler = BatchScheduler.create_from_data_dir(
    Path("data/raw/rss"),
    hour=6,
    minute=0,
)

# 手動実行
stats = scheduler.run_batch()
print(f"Success: {stats.success_count}/{stats.total_feeds}")
print(f"New items: {stats.new_items}")

# 自動実行（バックグラウンド）
scheduler.start(blocking=False)
```

**注意**: スケジューリング機能を使用するには `apscheduler` が必要です。

```bash
uv add 'finance[scheduler]'
```

<!-- END: QUICKSTART -->

## ディレクトリ構成

<!-- AUTO-GENERATED: STRUCTURE -->
```
rss/
├── __init__.py
├── py.typed
├── types.py
├── exceptions.py
├── cli/
│   ├── __init__.py
│   └── main.py
├── core/
│   ├── __init__.py
│   ├── diff_detector.py
│   ├── http_client.py
│   └── parser.py
├── docs/
│   ├── architecture.md
│   ├── development-guidelines.md
│   ├── functional-design.md
│   ├── glossary.md
│   ├── library-requirements.md
│   ├── project.md
│   ├── repository-structure.md
│   └── tasks.md
├── mcp/
│   ├── __init__.py
│   └── server.py
├── services/
│   ├── __init__.py
│   ├── batch_scheduler.py
│   ├── feed_fetcher.py
│   ├── feed_manager.py
│   └── feed_reader.py
├── storage/
│   ├── __init__.py
│   ├── json_storage.py
│   └── lock_manager.py
├── utils/
│   ├── __init__.py
│   └── logging_config.py
└── validators/
    ├── __init__.py
    └── url_validator.py
```
<!-- END: STRUCTURE -->

## 実装状況

<!-- AUTO-GENERATED: IMPLEMENTATION -->

| モジュール | 状態 | ファイル数 | 行数 |
|-----------|------|-----------|-----|
| `types.py` | ✅ 実装済み | 1 | 237 |
| `exceptions.py` | ✅ 実装済み | 1 | 120 |
| `cli/` | ✅ 実装済み | 2 | 520 |
| `core/` | ✅ 実装済み | 4 | 578 |
| `mcp/` | ✅ 実装済み | 2 | 540 |
| `services/` | ✅ 実装済み | 5 | 1,341 |
| `storage/` | ✅ 実装済み | 3 | 546 |
| `utils/` | ✅ 実装済み | 2 | 275 |
| `validators/` | ✅ 実装済み | 2 | 189 |

<!-- END: IMPLEMENTATION -->

## 公開API

<!-- AUTO-GENERATED: API -->

### クイックスタート

パッケージの基本的な使い方:

```python
from pathlib import Path
from rss import FeedManager, FeedFetcher

# フィード管理
manager = FeedManager(Path("data/raw/rss"))
feed_id = manager.add_feed("https://example.com/feed.xml", "Example", "finance")

# フィード取得
fetcher = FeedFetcher(Path("data/raw/rss"))
results = fetcher.fetch_all()
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

**説明**: フィード取得・パース・差分検出・永続化を統合したサービスクラス。

**基本的な使い方**:

```python
from pathlib import Path
from rss import FeedFetcher

# 初期化
fetcher = FeedFetcher(Path("data/raw/rss"))

# 全フィード取得
results = fetcher.fetch_all()
for result in results:
    if result.success:
        print(f"{result.new_items} new items")

# 個別フィード取得
result = fetcher.fetch_feed(feed_id)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `fetch_feed(feed_id)` | 個別フィード取得 | `FetchResult` |
| `fetch_all()` | 全フィード取得（並列実行） | `list[FetchResult]` |

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
items = reader.get_all_items(limit=10, offset=0)

# キーワード検索
results = reader.search_items("金融政策", limit=5)
```

**主なメソッド**:

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `get_all_items(limit, offset)` | 全エントリー取得 | `list[FeedItem]` |
| `search_items(keyword, limit, offset)` | キーワード検索 | `list[FeedItem]` |

---

#### `BatchScheduler`

**説明**: 日次バッチスケジューリングを提供するサービスクラス。APScheduler統合。

**基本的な使い方**:

```python
from pathlib import Path
from rss import BatchScheduler

# ファクトリメソッドで作成
scheduler = BatchScheduler.create_from_data_dir(
    Path("data/raw/rss"),
    hour=6,
    minute=0,
)

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

### 関数

このパッケージは主にクラスベースのAPIを提供しています。

---

### 型定義

データ構造の定義。型ヒントやバリデーションに使用:

```python
from rss import (
    # データモデル
    Feed,           # フィード情報
    FeedItem,       # フィードエントリー
    FetchResult,    # 取得結果
    BatchStats,     # バッチ統計

    # Enum
    FetchInterval,  # 取得間隔（DAILY/WEEKLY/MANUAL）
    FetchStatus,    # 取得ステータス（SUCCESS/FAILURE/PENDING）
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
from rss import FeedManager, FeedNotFoundError

manager = FeedManager(Path("data/raw/rss"))
try:
    feed = manager.get_feed("invalid_id")
except FeedNotFoundError as e:
    print(f"Feed not found: {e}")
```

---

### ユーティリティ

ロギング設定:

```python
from rss import get_logger

logger = get_logger(__name__, module="my_module")
logger.info("Processing started")
```

<!-- END: API -->

## 統計

<!-- AUTO-GENERATED: STATS -->

| 項目 | 値 |
|-----|---|
| Pythonファイル数 | 23 |
| 総行数（実装コード） | 4,427 |
| モジュール数 | 7 |
| テストファイル数 | 14 |
| テストカバレッジ | N/A |

<!-- END: STATS -->

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

# rss

RSS/Atomフィード管理パッケージ

## 概要

このパッケージは、RSS/Atomフィードの取得、パース、管理機能を提供します。

**主な機能:**
- フィード取得・パース
- エントリー管理
- 更新監視

**現在のバージョン:** 0.1.0

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

### サービスクラス

```python
from rss import (
    BatchScheduler,
    FeedFetcher,
    FeedManager,
    FeedReader,
)
```

### データモデル

```python
from rss import (
    BatchStats,
    Feed,
    FeedItem,
    FetchInterval,
    FetchResult,
    FetchStatus,
)
```

### 例外クラス

```python
from rss import (
    FeedAlreadyExistsError,
    FeedFetchError,
    FeedNotFoundError,
    FeedParseError,
    FileLockError,
    InvalidURLError,
    RSSError,
)
```

### ユーティリティ

```python
from rss import (
    get_logger,
)
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

## 使用例

### フィード管理

```python
from pathlib import Path
from rss.services import FeedManager

manager = FeedManager(Path("data/raw/rss"))

# フィード登録
feed_id = manager.add_feed(
    url="https://example.com/feed.xml",
    title="Example Feed",
    category="finance",
)

# フィード一覧取得
feeds = manager.list_feeds()

# フィード削除
manager.remove_feed(feed_id)
```

### フィード取得

```python
from pathlib import Path
from rss.services import FeedFetcher

fetcher = FeedFetcher(Path("data/raw/rss"))

# 全フィード取得
results = fetcher.fetch_all()
for result in results:
    if result.success:
        print(f"{result.feed_id}: {result.new_items} new items")
```

### 日次バッチ実行

APSchedulerを使用した日次バッチ実行機能を提供します。

```python
from pathlib import Path
from rss.services import BatchScheduler, FeedFetcher

# 方法1: FeedFetcherから作成
fetcher = FeedFetcher(Path("data/raw/rss"))
scheduler = BatchScheduler(fetcher, hour=6, minute=0)  # 毎日午前6時

# 方法2: ファクトリメソッドを使用
scheduler = BatchScheduler.create_from_data_dir(
    Path("data/raw/rss"),
    hour=7,
    minute=30,  # 毎日午前7時30分
)

# 手動でバッチ実行
stats = scheduler.run_batch()
print(f"Success: {stats.success_count}/{stats.total_feeds}")
print(f"New items: {stats.new_items}")

# スケジューラーを起動（ブロッキングモード）
scheduler.start(blocking=True)

# バックグラウンドモードで起動
scheduler.start(blocking=False)
# ... 他の処理 ...
scheduler.stop()
```

**注意**: 日次バッチ実行機能を使用するには、APSchedulerをインストールする必要があります:

```bash
uv add 'finance[scheduler]'
# または
uv add apscheduler
```

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

-   `template/src/template_package/README.md` - テンプレート実装の詳細
-   `docs/development-guidelines.md` - 開発ガイドライン

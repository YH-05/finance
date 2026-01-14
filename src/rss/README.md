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
├── core/
│   ├── __init__.py
│   └── diff_detector.py
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
| `types.py` | ✅ 実装済み | 1 | 280 |
| `exceptions.py` | ✅ 実装済み | 1 | 161 |
| `core/` | ✅ 実装済み | 2 | 97 |
| `storage/` | ✅ 実装済み | 3 | 667 |
| `utils/` | ✅ 実装済み | 2 | 367 |
| `validators/` | 🚧 開発中 | 2 | 235 |

<!-- END: IMPLEMENTATION -->

## 公開API

<!-- AUTO-GENERATED: API -->

### 関数

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
| Pythonファイル数 | 12 |
| 総行数（実装コード） | 1,807 |
| モジュール数 | 4 |
| テストファイル数 | 3 |
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

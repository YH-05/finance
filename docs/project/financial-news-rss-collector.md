# RSS MCP API 調査結果 - 金融ニュース収集

**調査日**: 2026-01-15
**Issue**: [#148](https://github.com/YH-05/finance/issues/148)
**ステータス**: 完了

## 概要

RSS MCP サーバーが提供する API を調査し、金融ニュース収集に最適な API と使用方法を決定しました。

## RSS MCP サーバーが提供する7つのツール

### 1. フィード管理

#### 1.1 `rss_list_feeds` - フィード一覧取得

```python
# パラメータ
category: str | None = None          # カテゴリでフィルタリング
enabled_only: bool = False           # 有効なフィードのみ

# レスポンス
{
    "feeds": [
        {
            "feed_id": str,
            "url": str,
            "title": str,
            "category": str,
            "fetch_interval": str,      # "daily" | "weekly" | "manual"
            "created_at": str,
            "updated_at": str,
            "last_fetched": str | None,
            "last_status": str,
            "enabled": bool
        }
    ],
    "total": int
}
```

#### 1.2 `rss_add_feed` - 新規フィード追加

```python
# パラメータ
url: str                             # フィードURL（HTTP/HTTPS）
title: str                           # フィードタイトル（1-200文字）
category: str                        # カテゴリ（1-50文字）
fetch_interval: str = "daily"        # "daily" | "weekly" | "manual"
validate_url: bool = False           # URL到達性確認
enabled: bool = True                 # 有効化フラグ

# レスポンス
{
    "feed": { ... },                 # フィードオブジェクト
    "success": bool
}
```

#### 1.3 `rss_update_feed` - フィード更新

```python
# パラメータ
feed_id: str                         # 更新対象のフィードID
title: str | None = None             # 新しいタイトル
category: str | None = None          # 新しいカテゴリ
fetch_interval: str | None = None    # 新しい取得間隔
enabled: bool | None = None          # 新しい有効化状態

# レスポンス
{
    "feed": { ... },
    "success": bool
}
```

#### 1.4 `rss_remove_feed` - フィード削除

```python
# パラメータ
feed_id: str                         # 削除対象のフィードID

# レスポンス
{
    "feed_id": str,
    "success": bool
}
```

### 2. 記事取得

#### 2.1 `rss_get_items` - 記事一覧取得 ⭐️推奨

```python
# パラメータ
feed_id: str | None = None           # フィードID（Noneで全フィード）
limit: int = 10                      # 最大取得数
offset: int = 0                      # ページネーション用オフセット

# レスポンス
{
    "items": [
        {
            "item_id": str,
            "title": str,
            "link": str,
            "published": str,
            "summary": str,
            "content": str,
            "author": str,
            "fetched_at": str
        }
    ],
    "total": int
}
```

#### 2.2 `rss_fetch_feed` - 最新記事取得（非同期）⭐️推奨

```python
# パラメータ
feed_id: str                         # 取得対象のフィードID

# レスポンス
{
    "feed_id": str,
    "success": bool,
    "items_count": int,              # 取得後の総アイテム数
    "new_items": int,                # 新規アイテム数
    "error_message": str | None      # エラー時のみ
}
```

### 3. 記事検索

#### 3.1 `rss_search_items` - キーワード検索 ⭐️推奨

```python
# パラメータ
query: str                           # 検索クエリ
category: str | None = None          # カテゴリフィルタ
fields: list[str] | None = None      # 検索対象フィールド
                                     # デフォルト: ["title", "summary", "content"]
limit: int = 50                      # 最大結果数

# レスポンス
{
    "items": [ ... ],
    "total": int,
    "query": str
}
```

## 金融ニュース収集に最適な API

### 推奨ワークフロー

#### ステップ1: 初期セットアップ（フィード登録）

```python
# 日経新聞、Bloomberg、ロイターなどの金融ニュースフィードを登録
rss_add_feed(
    url="https://example.com/finance/rss",
    title="日経新聞 - 経済",
    category="finance",
    fetch_interval="daily",
    enabled=True
)
```

#### ステップ2: 最新記事の取得

**方法A: 全フィードから記事を取得**

```python
# すべての金融フィードから最新10件を取得
result = rss_get_items(feed_id=None, limit=10, offset=0)

# ページネーションで次の10件を取得
result = rss_get_items(feed_id=None, limit=10, offset=10)
```

**方法B: 特定フィードの最新記事を即座に取得**

```python
# 特定のフィードから最新記事を取得（新規記事のみ検出）
result = await rss_fetch_feed(feed_id="feed_123")
print(f"新規記事: {result['new_items']}件")
```

#### ステップ3: 特定トピックの記事を検索

```python
# "日銀"に関する記事を検索
result = rss_search_items(
    query="日銀",
    category="finance",
    fields=["title", "summary", "content"],
    limit=50
)

# "金利政策"に関する記事を検索
result = rss_search_items(
    query="金利政策",
    category="finance",
    limit=50
)
```

## サンプルコード: Python APIの直接利用

### 例1: フィード管理と記事取得

```python
from pathlib import Path
from rss.services.feed_manager import FeedManager
from rss.services.feed_reader import FeedReader
from rss.services.feed_fetcher import FeedFetcher
from rss.types import FetchInterval

# データディレクトリ
data_dir = Path("data/raw/rss")

# 1. フィード追加
manager = FeedManager(data_dir)
feed = manager.add_feed(
    url="https://example.com/finance/rss",
    title="日経新聞 - 経済",
    category="finance",
    fetch_interval=FetchInterval.DAILY,
    enabled=True
)
print(f"フィード追加: {feed.feed_id}")

# 2. フィード一覧取得
feeds = manager.list_feeds(category="finance", enabled_only=True)
print(f"金融フィード数: {len(feeds)}")

# 3. 記事取得
reader = FeedReader(data_dir)
items = reader.get_items(feed_id=feed.feed_id, limit=10)
print(f"記事数: {len(items)}")

for item in items:
    print(f"- {item.title}")
    print(f"  公開日: {item.published}")
    print(f"  URL: {item.link}")

# 4. 最新記事を取得
import asyncio

async def fetch_latest():
    fetcher = FeedFetcher(data_dir)
    result = await fetcher.fetch_feed(feed.feed_id)
    print(f"新規記事: {result.new_items}件")
    print(f"総記事数: {result.items_count}件")

asyncio.run(fetch_latest())
```

### 例2: キーワード検索

```python
from pathlib import Path
from rss.services.feed_reader import FeedReader

data_dir = Path("data/raw/rss")
reader = FeedReader(data_dir)

# "日銀"に関する記事を検索
items = reader.search_items(
    query="日銀",
    category="finance",
    fields=["title", "summary", "content"],
    limit=50
)

print(f"検索結果: {len(items)}件")
for item in items:
    print(f"- {item.title}")
    print(f"  要約: {item.summary[:100]}...")
```

### 例3: カテゴリ別記事取得

```python
from pathlib import Path
from rss.services.feed_manager import FeedManager
from rss.services.feed_reader import FeedReader

data_dir = Path("data/raw/rss")

# 金融カテゴリのフィード一覧
manager = FeedManager(data_dir)
finance_feeds = manager.list_feeds(category="finance", enabled_only=True)

# 各フィードから最新記事を取得
reader = FeedReader(data_dir)
all_items = []

for feed in finance_feeds:
    items = reader.get_items(feed_id=feed.feed_id, limit=5)
    all_items.extend(items)
    print(f"{feed.title}: {len(items)}件")

print(f"合計: {len(all_items)}件の記事")
```

## エラーハンドリング

全てのツールは以下の例外を返す可能性があります：

```python
# エラーレスポンス
{
    "error": str,               # エラーメッセージ
    "error_type": str,          # エラータイプ
    "success": False            # 成功フラグ（ツールによる）
}

# エラータイプ
- FeedAlreadyExistsError    # フィードが既に存在
- FeedNotFoundError         # フィードが見つからない
- InvalidURLError           # 無効なURL
- FeedFetchError            # 取得エラー
- FeedParseError            # パースエラー
- RSSError                  # その他のRSSエラー
```

## 金融ニュース収集のベストプラクティス

### 1. フィード登録時の推奨設定

```python
# 主要な金融ニュースソース
financial_feeds = [
    {
        "url": "https://www.nikkei.com/rss/...",
        "title": "日経新聞 - 経済",
        "category": "finance",
        "fetch_interval": "daily"
    },
    {
        "url": "https://jp.reuters.com/rss/...",
        "title": "ロイター - マーケット",
        "category": "finance",
        "fetch_interval": "daily"
    }
]
```

### 2. 定期的な記事更新

```python
# 全フィードから最新記事を取得
async def update_all_feeds():
    manager = FeedManager(data_dir)
    fetcher = FeedFetcher(data_dir)

    feeds = manager.list_feeds(enabled_only=True)

    for feed in feeds:
        result = await fetcher.fetch_feed(feed.feed_id)
        print(f"{feed.title}: 新規{result.new_items}件")
```

### 3. トピック別記事収集

```python
# 特定のトピックに関する記事を収集
topics = ["日銀", "金利", "為替", "株価", "GDP"]

reader = FeedReader(data_dir)
topic_articles = {}

for topic in topics:
    items = reader.search_items(
        query=topic,
        category="finance",
        limit=20
    )
    topic_articles[topic] = items
    print(f"{topic}: {len(items)}件")
```

## 結論

### 金融ニュース収集に最適な3つのAPI

1. **`rss_get_items`**:
   - 金融記事の一覧表示・閲覧
   - ページネーション機能で大量の記事を効率的に取得

2. **`rss_fetch_feed`**:
   - 最新記事の定期取得
   - 新規記事の差分検出で重複を回避

3. **`rss_search_items`**:
   - 特定トピックの記事検索
   - カテゴリとキーワードで柔軟な絞り込み

### 次のステップ

1. 主要な金融ニュースソースのフィード URL を収集
2. `rss_add_feed` でフィードを登録
3. 定期的に `rss_fetch_feed` で最新記事を取得
4. `rss_search_items` で関心のあるトピックを検索
5. 取得した記事を `market_analysis` パッケージで分析

## 参考資料

- RSS MCP サーバー実装: `src/rss/mcp/server.py`
- フィード管理: `src/rss/services/feed_manager.py`
- フィード取得: `src/rss/services/feed_fetcher.py`
- フィード読み込み: `src/rss/services/feed_reader.py`
- 型定義: `src/rss/types.py`

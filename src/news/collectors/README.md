# news.collectors

ニュースソースからの記事収集モジュール。

## 概要

RSS フィード、yfinance API、Web スクレイピングなどのソースから記事メタデータを収集する Collector クラスを提供します。抽象基底クラス `BaseCollector` と具象実装 `RSSCollector` で構成。

**収集フロー:**

```
RSSフィード → HTTP取得 → FeedParser解析 → CollectedArticle変換 → フィルタリング
```

**主な特徴:**

- **非同期対応**: `asyncio` / `httpx.AsyncClient` による非ブロッキング I/O
- **年齢フィルタ**: `max_age_hours` パラメータで古い記事を除外
- **ドメインフィルタ**: ブロックドメインからの記事を自動除外
- **User-Agent ローテーション**: ボットブロッキング対策
- **エラー追跡**: フィード別のエラー記録（`FeedError`）

## クイックスタート

### RSS 記事の収集

```python
from news.collectors import RSSCollector
from news.config import load_config

config = load_config("data/config/news-collection-config.yaml")
collector = RSSCollector(config=config)

# 直近24時間の記事を収集
articles = await collector.collect(max_age_hours=24)
print(f"収集数: {len(articles)}")

# フィードエラーを確認
for error in collector.feed_errors:
    print(f"エラー: {error.feed_name} - {error.error}")
```

### カスタム Collector の作成

```python
from news.collectors.base import BaseCollector
from news.models import CollectedArticle, SourceType

class MyCollector(BaseCollector):
    @property
    def source_type(self) -> SourceType:
        return SourceType.SCRAPE

    async def collect(
        self, max_age_hours: int = 168
    ) -> list[CollectedArticle]:
        # カスタム収集ロジック
        return []
```

## API リファレンス

### BaseCollector（ABC）

すべての Collector の抽象基底クラス。

| メソッド/プロパティ | 型 | 説明 |
|-------------------|-----|------|
| `source_type` | `SourceType`（抽象） | ソース種別を返す |
| `collect(max_age_hours)` | `list[CollectedArticle]`（抽象） | 記事を収集する（async） |

### RSSCollector

RSS フィードからの記事収集。`BaseCollector` を継承。

**コンストラクタ:**

```python
RSSCollector(config: NewsWorkflowConfig)
```

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `collect(max_age_hours=168)` | RSS フィードから記事を収集（async） | `list[CollectedArticle]` |

**プロパティ:**

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `source_type` | `SourceType` | 常に `SourceType.RSS` |
| `feed_errors` | `list[FeedError]` | 直近の収集時のフィードエラー |

**内部処理:**

1. プリセット設定ファイルから有効なフィードを読み込み
2. `httpx.AsyncClient` で各フィードを非同期取得
3. `FeedParser` で RSS/Atom を解析
4. `CollectedArticle` に変換し年齢フィルタを適用
5. ブロックドメインの記事を除外
6. 個別フィードのエラーは記録して続行（graceful degradation）

## モジュール構成

```
news/collectors/
├── __init__.py   # パッケージエクスポート（BaseCollector, RSSCollector）
├── base.py       # BaseCollector 抽象基底クラス
├── rss.py        # RSSCollector 実装
└── README.md     # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| httpx | 非同期 HTTP クライアント |
| rss.core.parser | RSS/Atom フィード解析 |

## 関連モジュール

- [news.core](../core/README.md) - 基本プロトコル・データモデル
- [news.models](../README.md) - パイプラインデータモデル（CollectedArticle）
- [news.extractors](../extractors/README.md) - 次段階: 記事本文抽出
- [news.config](../config/README.md) - ワークフロー設定

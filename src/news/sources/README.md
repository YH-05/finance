# news.sources

ニュースデータソース実装モジュール。

## 概要

`SourceProtocol` を実装した各種ニュースデータソースを提供します。yfinance API を使用した Ticker / Search ベースのニュース取得に対応。

**データソース一覧:**

| ソース | 説明 | API |
|--------|------|-----|
| `IndexNewsSource` | 株価指数ニュース（^GSPC, ^DJI 等） | yfinance Ticker |
| `StockNewsSource` | 個別株ニュース（MAG7、セクター代表銘柄） | yfinance Ticker |
| `SectorNewsSource` | セクター ETF ニュース（XLF, XLK 等） | yfinance Ticker |
| `CommodityNewsSource` | コモディティニュース（GC=F, CL=F 等） | yfinance Ticker |
| `MacroNewsSource` | マクロ経済ニュース（キーワード検索） | yfinance Search |
| `SearchNewsSource` | テーマ別ニュース（汎用キーワード検索） | yfinance Search |

## クイックスタート

### 株価指数ニュースの取得

```python
from news.sources.yfinance import IndexNewsSource

source = IndexNewsSource()
result = source.fetch("^GSPC", count=10)

if result.success:
    for article in result.articles:
        print(f"[{article.published}] {article.title}")
```

### 複数銘柄の一括取得

```python
from news.sources.yfinance import StockNewsSource

source = StockNewsSource()
results = source.fetch_all(
    identifiers=["AAPL", "GOOGL", "MSFT", "NVDA"],
    count=5,
)

for result in results:
    print(f"{result.ticker}: {len(result.articles)}件")
```

### テーマ別検索

```python
from news.sources.yfinance import SearchNewsSource

source = SearchNewsSource()
result = source.fetch("Federal Reserve interest rate", count=10)
print(f"検索結果: {len(result.articles)}件")
```

## API リファレンス

### 共通インターフェース

すべてのソースは以下のインターフェースを持ちます:

| メソッド/プロパティ | 説明 |
|-------------------|------|
| `source_name` | ソース名（例: `"yfinance_ticker"`） |
| `source_type` | ソース種別（`ArticleSource` enum） |
| `fetch(identifier, count)` | 単一識別子でニュース取得 |
| `fetch_all(identifiers, count)` | 複数識別子で一括取得 |

### ユーティリティ関数

| 関数 | 説明 |
|------|------|
| `fetch_with_retry(func, *args)` | リトライ付きフェッチ |
| `ticker_news_to_article(news_item)` | Ticker ニュースを Article に変換 |
| `search_news_to_article(news_item)` | Search ニュースを Article に変換 |
| `validate_ticker(ticker)` | ティッカーシンボルのバリデーション |
| `validate_query(query)` | 検索クエリのバリデーション |

## yfinance サブパッケージ構成

```
news/sources/
├── __init__.py           # パッケージ docstring
├── yfinance/
│   ├── __init__.py       # エクスポート（6ソース + 5ユーティリティ）
│   ├── base.py           # 共通ユーティリティ、変換関数、リトライロジック
│   ├── index.py          # IndexNewsSource（株価指数）
│   ├── stock.py          # StockNewsSource（個別株）
│   ├── sector.py         # SectorNewsSource（セクター ETF）
│   ├── commodity.py      # CommodityNewsSource（コモディティ）
│   ├── macro.py          # MacroNewsSource（マクロ経済）
│   └── search.py         # SearchNewsSource（テーマ検索）
└── README.md             # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| yfinance | Yahoo Finance API 連携 |

## 関連モジュール

- [news.core](../core/README.md) - SourceProtocol, ArticleSource, FetchResult 定義
- [news.processors](../processors/README.md) - パイプライン連携
- [news.sinks](../sinks/README.md) - 取得データの出力先

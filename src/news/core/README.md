# news.core

ニュースパッケージのコアモジュール。プロトコル定義、データモデル、共通型を提供。

## 概要

news パッケージ全体で使用する基本的なプロトコル（インターフェース）、データモデル、列挙型、エラークラスを定義します。Protocol ベースの設計により、各コンポーネント（Source、Processor、Sink）を疎結合に保ちます。

**主な機能:**

- **プロトコル定義**: `SourceProtocol`, `ProcessorProtocol`, `SinkProtocol`（`runtime_checkable`）
- **データモデル**: `Article`, `FetchResult`（Pydantic BaseModel）
- **列挙型**: `ArticleSource`, `ContentType`, `SinkType`, `ProcessorType`
- **重複チェック**: `DuplicateChecker`
- **履歴管理**: `CollectionHistory`, `CollectionRun`, `SourceStats`
- **エラークラス**: `NewsError`, `SourceError`, `RateLimitError`, `ValidationError`

## クイックスタート

### SourceProtocol の実装

```python
from news.core import SourceProtocol, ArticleSource, FetchResult

class MySource:
    @property
    def source_name(self) -> str:
        return "my_source"

    @property
    def source_type(self) -> ArticleSource:
        return ArticleSource.SCRAPER

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        # ニュース取得ロジック
        ...

    def fetch_all(
        self, identifiers: list[str], count: int = 10
    ) -> list[FetchResult]:
        return [self.fetch(ident, count) for ident in identifiers]

# runtime_checkable なので isinstance チェック可能
assert isinstance(MySource(), SourceProtocol)
```

### SinkProtocol の実装

```python
from news.core import SinkProtocol, SinkType, Article, FetchResult

class MySink:
    @property
    def sink_name(self) -> str:
        return "my_sink"

    @property
    def sink_type(self) -> SinkType:
        return SinkType.FILE

    def write(
        self, articles: list[Article], metadata: dict | None = None
    ) -> bool:
        # 書き出しロジック
        return True

    def write_batch(self, results: list[FetchResult]) -> bool:
        return all(self.write(r.articles) for r in results)
```

### ProcessorProtocol の実装

```python
from news.core import ProcessorProtocol, ProcessorType, Article

class MyProcessor:
    @property
    def processor_name(self) -> str:
        return "my_processor"

    @property
    def processor_type(self) -> ProcessorType:
        return ProcessorType.SUMMARIZER

    def process(self, article: Article) -> Article:
        return article.model_copy(update={"summary_ja": "要約..."})

    def process_batch(self, articles: list[Article]) -> list[Article]:
        return [self.process(a) for a in articles]
```

## API リファレンス

### プロトコル

| プロトコル | 説明 | メソッド |
|-----------|------|---------|
| `SourceProtocol` | データソースインターフェース | `fetch()`, `fetch_all()` |
| `ProcessorProtocol` | AI 処理インターフェース | `process()`, `process_batch()` |
| `SinkProtocol` | 出力先インターフェース | `write()`, `write_batch()` |

### データモデル

| モデル | 説明 |
|--------|------|
| `Article` | 統一ニュース記事モデル（Pydantic BaseModel） |
| `FetchResult` | ニュース取得結果（success, articles, error） |
| `RetryConfig` | リトライ設定 |

### 列挙型

| 列挙型 | 値 | 説明 |
|--------|-----|------|
| `ArticleSource` | `YFINANCE_TICKER`, `YFINANCE_SEARCH`, `SCRAPER`, `RSS` | 記事ソース種別 |
| `ContentType` | `ARTICLE`, `VIDEO`, `PRESS_RELEASE`, `UNKNOWN` | コンテンツ種別 |
| `SinkType` | `FILE`, `GITHUB`, `REPORT` | 出力先種別 |
| `ProcessorType` | `SUMMARIZER`, `CLASSIFIER`, `TAGGER` | AI 処理種別 |

### ユーティリティクラス

| クラス | 説明 |
|--------|------|
| `DuplicateChecker` | 記事の重複チェック |
| `CollectionHistory` | 収集履歴管理 |
| `CollectionRun` | 単一収集実行の記録 |
| `SourceStats` | ソース別統計 |
| `SinkResult` | Sink 出力結果 |

### 例外クラス

| 例外 | 説明 |
|------|------|
| `NewsError` | news パッケージの基底例外 |
| `SourceError` | データソースエラー |
| `RateLimitError` | レート制限エラー |
| `ValidationError` | バリデーションエラー |

## モジュール構成

```
news/core/
├── __init__.py    # パッケージエクスポート（21項目）
├── article.py     # Article, ArticleSource, ContentType, Provider, Thumbnail
├── dedup.py       # DuplicateChecker
├── errors.py      # NewsError, SourceError, RateLimitError, ValidationError
├── history.py     # CollectionHistory, CollectionRun, SinkResult, SourceStats
├── processor.py   # ProcessorProtocol, ProcessorType
├── result.py      # FetchResult, RetryConfig
├── sink.py        # SinkProtocol, SinkType
├── source.py      # SourceProtocol
└── README.md      # このファイル
```

## 関連モジュール

- [news.collectors](../collectors/README.md) - コレクター実装（BaseCollector 継承）
- [news.extractors](../extractors/README.md) - 記事本文抽出（BaseExtractor 継承）
- [news.processors](../processors/README.md) - AI 処理（ProcessorProtocol 実装）
- [news.sinks](../sinks/README.md) - 出力先（SinkProtocol 実装）
- [news.sources](../sources/README.md) - データソース（SourceProtocol 実装）

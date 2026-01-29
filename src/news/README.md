# news

金融ニュースの自動収集・処理・公開パイプラインを提供するパッケージです。

## 概要

このパッケージは、複数のデータソース（RSS、yfinance）からニュース記事を収集し、
本文抽出・AI要約・GitHub Issue作成までの一連のワークフローを自動化します。

**現在のバージョン:** 0.1.0

## 主要機能

- **ニュース収集**: RSSフィード、yfinance APIからの記事取得
- **本文抽出**: Trafilaturaを使用したWebページからの本文抽出
- **AI要約**: Claude APIを使用した構造化日本語要約生成
- **Issue作成**: GitHub Issue作成とProject追加の自動化
- **重複検出**: URL/タイトルベースの重複記事検出

## ディレクトリ構成

```
news/
├── __init__.py              # 公開API定義
├── py.typed                 # PEP 561マーカー
├── models.py                # ワークフロー用モデル定義
├── types.py                 # 型定義
│
├── core/                    # コアコンポーネント
│   ├── article.py           # Article/ArticleSource/ContentType
│   ├── result.py            # FetchResult/RetryConfig
│   ├── sink.py              # SinkProtocol/SinkType
│   ├── source.py            # SourceProtocol
│   ├── processor.py         # ProcessorProtocol
│   ├── dedup.py             # 重複検出ロジック
│   ├── history.py           # 履歴管理
│   └── errors.py            # 例外クラス
│
├── collectors/              # データ収集
│   ├── base.py              # BaseCollector
│   └── rss.py               # RSSCollector
│
├── sources/                 # yfinanceデータソース
│   └── yfinance/
│       ├── base.py          # YFinanceSourceBase
│       ├── index.py         # IndexSource
│       ├── stock.py         # StockSource
│       ├── sector.py        # SectorSource
│       ├── macro.py         # MacroSource
│       ├── commodity.py     # CommoditySource
│       └── search.py        # SearchSource
│
├── extractors/              # 本文抽出
│   ├── base.py              # ExtractorProtocol
│   └── trafilatura.py       # TrafilaturaExtractor
│
├── processors/              # 記事処理
│   ├── classifier.py        # カテゴリ分類
│   ├── summarizer.py        # 要約処理
│   ├── pipeline.py          # パイプライン統合
│   └── agent_base.py        # エージェントベース処理
│
├── sinks/                   # 出力先
│   ├── file.py              # FileSink（JSON出力）
│   └── github.py            # GitHubSink（Issue作成）
│
├── config/                  # 設定管理
│   ├── models.py            # 設定モデル
│   ├── loader.py            # YAMLローダー
│   ├── workflow.py          # ワークフロー設定
│   └── errors.py            # 設定エラー
│
├── collector.py             # Collector（ソース→シンク統合）
├── orchestrator.py          # NewsWorkflowOrchestrator
├── summarizer.py            # Summarizer（Claude API）
├── publisher.py             # Publisher（GitHub Issue）
│
├── scripts/                 # CLIスクリプト
│   ├── __main__.py          # エントリーポイント
│   ├── collect.py           # 収集コマンド
│   └── finance_news_workflow.py  # ワークフローCLI
│
└── utils/                   # ユーティリティ
    └── logging_config.py    # 構造化ロギング
```

## 実装状況

| モジュール | 状態 | 説明 |
|-----------|------|------|
| `core/article.py` | ✅ 実装済み | 統一記事モデル（Pydantic） |
| `core/result.py` | ✅ 実装済み | FetchResult/RetryConfig |
| `core/sink.py` | ✅ 実装済み | SinkProtocol定義 |
| `core/source.py` | ✅ 実装済み | SourceProtocol定義 |
| `core/dedup.py` | ✅ 実装済み | URL/タイトルベース重複検出 |
| `collectors/rss.py` | ✅ 実装済み | RSSフィード収集 |
| `sources/yfinance/` | ✅ 実装済み | yfinance統合（6ソース） |
| `extractors/trafilatura.py` | ✅ 実装済み | Trafilatura本文抽出 |
| `sinks/file.py` | ✅ 実装済み | JSON/CSV出力 |
| `sinks/github.py` | ✅ 実装済み | GitHub Issue作成 |
| `config/workflow.py` | ✅ 実装済み | YAMLワークフロー設定 |
| `collector.py` | ✅ 実装済み | 収集オーケストレーション |
| `orchestrator.py` | ✅ 実装済み | 完全ワークフロー統合 |
| `summarizer.py` | ✅ 実装済み | Claude AI要約 |
| `publisher.py` | ✅ 実装済み | GitHub Issue/Project |

## 公開API

```python
from news import (
    # コアモデル
    Article,
    ArticleSource,
    ContentType,
    Provider,
    Thumbnail,

    # 結果・設定
    FetchResult,
    RetryConfig,

    # シンク
    FileSink,
    WriteMode,
    SinkProtocol,
    SinkType,

    # 要約
    Summarizer,

    # ロギング
    get_logger,
)
```

## 使用例

### 基本的な収集フロー

```python
from news.collector import Collector, CollectorConfig
from news.sources.yfinance.index import IndexSource
from news.sinks.file import FileSink, WriteMode

# 設定
config = CollectorConfig(max_articles_per_source=10)
collector = Collector(config=config)

# ソース・シンク登録
collector.register_source(IndexSource(symbols=["^GSPC", "^DJI"]))
collector.register_sink(FileSink(path="output.json", mode=WriteMode.APPEND))

# 収集実行
result = collector.collect()
print(f"Collected {result.total_articles} articles")
```

### 完全ワークフロー

```python
from news.orchestrator import NewsWorkflowOrchestrator
from news.config.workflow import load_config

# 設定ロード
config = load_config("data/config/news-collection-config.yaml")

# オーケストレーター作成
orchestrator = NewsWorkflowOrchestrator(config=config)

# ワークフロー実行（collect -> extract -> summarize -> publish）
result = await orchestrator.run(
    statuses=["index"],      # フィルタリング
    max_articles=10,         # 最大記事数
    dry_run=False,           # 実行モード
)

print(f"Published: {result.total_published}/{result.total_collected}")
```

### CLI実行

```bash
# ワークフロー実行
uv run python -m news.scripts.finance_news_workflow \
    --config data/config/news-collection-config.yaml \
    --statuses index \
    --max-articles 10

# 収集のみ
uv run python -m news collect --source yfinance --symbols ^GSPC ^DJI
```

## ワークフローパイプライン

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Collector   │ -> │  Extractor   │ -> │  Summarizer  │ -> │  Publisher   │
│  (RSS収集)   │    │  (本文抽出)  │    │  (AI要約)    │    │  (Issue作成) │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
     |                    |                    |                    |
     v                    v                    v                    v
 CollectedArticle   ExtractedArticle   SummarizedArticle   PublishedArticle
```

## 設定ファイル

`data/config/news-collection-config.yaml`:

```yaml
feeds:
  - name: "CNBC Markets"
    url: "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    category: "index"

filtering:
  max_age_hours: 72

extraction:
  min_body_length: 100
  max_retries: 3
  timeout_seconds: 30
  concurrency: 5

summarization:
  concurrency: 3
  prompt_template: |
    以下のニュース記事を日本語で要約してください。
    ...

github:
  repo: "YH-05/finance"
  project_id: "PVT_xxx"
  project_number: 15
```

## 依存関係

### パッケージ依存

- `rss` パッケージ: RSSフィード処理
- `database` パッケージ: ロギング設定

### 外部ライブラリ

- `pydantic`: データバリデーション
- `trafilatura`: 本文抽出
- `anthropic`: Claude API
- `httpx`: HTTP クライアント

## 関連ドキュメント

- `data/config/news-collection-config.yaml` - 設定例
- `docs/project/project-29/` - 実装仕様
- `.claude/skills/finance-news-workflow/` - ワークフロースキル

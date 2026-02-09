# news.processors

AI 処理およびパイプライン実行モジュール。

## 概要

ニュース記事の AI 処理（要約、分類、タグ付け）と Source → Processor → Sink のパイプライン実行を提供します。Claude Agent SDK を使用した AI 処理と、柔軟なパイプライン構成に対応。

**主な機能:**

- **AgentProcessor**: Claude Agent SDK ベースの AI 処理基盤
- **SummarizerProcessor**: 記事の AI 要約（日本語）
- **ClassifierProcessor**: 記事のカテゴリ分類
- **Pipeline**: Source → Processor → Sink チェーン実行

## クイックスタート

### パイプラインの構築と実行

```python
from pathlib import Path
from news.processors import Pipeline, SummarizerProcessor
from news.sources.yfinance import IndexNewsSource
from news.sinks import FileSink

pipeline = (
    Pipeline()
    .add_source(IndexNewsSource())
    .add_processor(SummarizerProcessor())
    .add_sink(FileSink(output_dir=Path("data/news")))
)

result = pipeline.run(identifiers=["^GSPC", "^DJI"])
print(f"取得: {result.articles_fetched}, 処理: {result.articles_processed}")
```

### AI 要約プロセッサー

```python
from news.processors import SummarizerProcessor

processor = SummarizerProcessor()
processed_article = processor.process(article)
print(processed_article.summary_ja)
```

## API リファレンス

### AgentProcessor

Claude Agent SDK ベースの AI 処理基盤クラス。

| メソッド | 説明 |
|---------|------|
| `process(article)` | 単一記事を AI 処理 |
| `process_batch(articles)` | 複数記事をバッチ処理 |

### SummarizerProcessor

記事の日本語要約を生成する AI プロセッサー。

### ClassifierProcessor

記事のカテゴリ分類を行う AI プロセッサー。

### Pipeline

Source → Processor → Sink チェーンの実行。

**コンストラクタ:**

```python
Pipeline(config: PipelineConfig | None = None)
```

**メソッド（ビルダーパターン）:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `add_source(source)` | データソースを追加 | `Pipeline`（self） |
| `add_processor(processor)` | AI プロセッサーを追加 | `Pipeline`（self） |
| `add_sink(sink)` | 出力先を追加 | `Pipeline`（self） |
| `run(identifiers, count)` | パイプラインを実行 | `PipelineResult` |

### PipelineConfig

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `continue_on_error` | `bool` | エラー時に処理を続行するか |

### PipelineResult

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `success` | `bool` | パイプライン全体の成否 |
| `articles_fetched` | `int` | 取得記事数 |
| `articles_processed` | `int` | 処理済み記事数 |
| `articles` | `list[Article]` | 処理済み記事リスト |
| `errors` | `list[StageError]` | ステージ別エラー |

### 例外クラス

| 例外 | 説明 |
|------|------|
| `PipelineError` | パイプライン実行エラー（stage, cause 情報付き） |
| `StageError` | ステージエラー情報 |
| `AgentProcessorError` | AI 処理エラー |
| `SDKNotInstalledError` | Claude Agent SDK 未インストール |

## モジュール構成

```
news/processors/
├── __init__.py       # パッケージエクスポート
├── agent_base.py     # AgentProcessor 基盤クラス
├── classifier.py     # ClassifierProcessor
├── pipeline.py       # Pipeline, PipelineConfig, PipelineResult
├── summarizer.py     # SummarizerProcessor
└── README.md         # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| claude-agent-sdk | Claude API 呼び出し（オプション） |
| pydantic | データバリデーション |

## 関連モジュール

- [news.core](../core/README.md) - ProcessorProtocol 定義
- [news.sources](../sources/README.md) - パイプラインのデータソース
- [news.sinks](../sinks/README.md) - パイプラインの出力先

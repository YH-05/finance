"""Unit tests for Pipeline in the news package.

Tests for the Pipeline class that manages Source -> Processor -> Sink chain execution
with batch processing, parallel execution, and error handling.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from news.core.article import Article, ArticleSource
from news.core.processor import ProcessorProtocol, ProcessorType
from news.core.result import FetchResult
from news.core.sink import SinkProtocol, SinkType
from news.core.source import SourceProtocol
from news.processors.pipeline import (
    Pipeline,
    PipelineConfig,
    PipelineError,
    PipelineResult,
    StageError,
)
from pydantic import HttpUrl

# === Test Helpers ===


def _make_article(
    url: str = "https://example.com/news/1",
    title: str = "Test Article",
) -> Article:
    """Create a test article with minimal required fields."""
    return Article(
        url=HttpUrl(url),
        title=title,
        published_at=datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc),
        source=ArticleSource.YFINANCE_TICKER,
    )


class StubSource:
    """Stub source that returns configured FetchResults."""

    def __init__(
        self,
        articles: list[Article] | None = None,
        *,
        fail: bool = False,
    ) -> None:
        self._articles = articles or []
        self._fail = fail
        self.fetch_called: list[tuple[str, int]] = []
        self.fetch_all_called: list[tuple[list[str], int]] = []

    @property
    def source_name(self) -> str:
        return "stub_source"

    @property
    def source_type(self) -> ArticleSource:
        return ArticleSource.YFINANCE_TICKER

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        self.fetch_called.append((identifier, count))
        if self._fail:
            return FetchResult(
                articles=[],
                success=False,
                ticker=identifier,
            )
        return FetchResult(
            articles=self._articles,
            success=True,
            ticker=identifier,
        )

    def fetch_all(
        self,
        identifiers: list[str],
        count: int = 10,
    ) -> list[FetchResult]:
        self.fetch_all_called.append((identifiers, count))
        return [self.fetch(ident, count) for ident in identifiers]


class StubProcessor:
    """Stub processor that adds a suffix to article titles."""

    def __init__(
        self,
        suffix: str = " [processed]",
        *,
        fail: bool = False,
    ) -> None:
        self._suffix = suffix
        self._fail = fail
        self.processed_count = 0

    @property
    def processor_name(self) -> str:
        return "stub_processor"

    @property
    def processor_type(self) -> ProcessorType:
        return ProcessorType.SUMMARIZER

    def process(self, article: Article) -> Article:
        if self._fail:
            msg = "Stub processor failure"
            raise RuntimeError(msg)
        self.processed_count += 1
        return article.model_copy(
            update={"summary_ja": (article.summary_ja or "") + self._suffix},
        )

    def process_batch(self, articles: list[Article]) -> list[Article]:
        return [self.process(a) for a in articles]


class StubSink:
    """Stub sink that records written articles."""

    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail
        self.written_articles: list[Article] = []
        self.written_results: list[FetchResult] = []
        self.write_count = 0

    @property
    def sink_name(self) -> str:
        return "stub_sink"

    @property
    def sink_type(self) -> SinkType:
        return SinkType.FILE

    def write(
        self,
        articles: list[Article],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        self.write_count += 1
        if self._fail:
            return False
        self.written_articles.extend(articles)
        return True

    def write_batch(self, results: list[FetchResult]) -> bool:
        self.written_results.extend(results)
        for result in results:
            if result.success:
                self.written_articles.extend(result.articles)
        return True


class FailingProcessor:
    """Processor that raises an exception on every call."""

    @property
    def processor_name(self) -> str:
        return "failing_processor"

    @property
    def processor_type(self) -> ProcessorType:
        return ProcessorType.SUMMARIZER

    def process(self, article: Article) -> Article:
        msg = "Processor always fails"
        raise RuntimeError(msg)

    def process_batch(self, articles: list[Article]) -> list[Article]:
        msg = "Processor always fails"
        raise RuntimeError(msg)


# === Tests for PipelineConfig ===


class TestPipelineConfig:
    """Test PipelineConfig model."""

    def test_正常系_デフォルト値で作成できる(self) -> None:
        """PipelineConfigがデフォルト値で作成できることを確認。"""
        config = PipelineConfig()
        assert config.continue_on_error is True
        assert config.batch_size == 50
        assert config.max_workers == 4

    def test_正常系_カスタム値で作成できる(self) -> None:
        """PipelineConfigがカスタム値で作成できることを確認。"""
        config = PipelineConfig(
            continue_on_error=False,
            batch_size=100,
            max_workers=8,
        )
        assert config.continue_on_error is False
        assert config.batch_size == 100
        assert config.max_workers == 8

    def test_異常系_batch_sizeが0以下でエラー(self) -> None:
        """batch_sizeが0以下の場合にValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="greater than"):
            PipelineConfig(batch_size=0)

    def test_異常系_max_workersが0以下でエラー(self) -> None:
        """max_workersが0以下の場合にValueErrorが発生することを確認。"""
        with pytest.raises(ValueError, match="greater than"):
            PipelineConfig(max_workers=0)


# === Tests for PipelineResult ===


class TestPipelineResult:
    """Test PipelineResult model."""

    def test_正常系_成功結果を作成できる(self) -> None:
        """成功したPipelineResultを作成できることを確認。"""
        articles = [_make_article()]
        result = PipelineResult(
            success=True,
            articles_fetched=5,
            articles_processed=5,
            articles_output=5,
            output_articles=articles,
        )
        assert result.success is True
        assert result.articles_fetched == 5
        assert result.articles_processed == 5
        assert result.articles_output == 5
        assert len(result.output_articles) == 1
        assert len(result.errors) == 0

    def test_正常系_エラー付き結果を作成できる(self) -> None:
        """エラーを含むPipelineResultを作成できることを確認。"""
        error = StageError(
            stage="source",
            source_name="test_source",
            error_message="Connection failed",
        )
        result = PipelineResult(
            success=False,
            articles_fetched=0,
            articles_processed=0,
            articles_output=0,
            output_articles=[],
            errors=[error],
        )
        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].stage == "source"


class TestStageError:
    """Test StageError model."""

    def test_正常系_StageErrorを作成できる(self) -> None:
        """StageErrorを正常に作成できることを確認。"""
        error = StageError(
            stage="processor",
            source_name="summarizer",
            error_message="Rate limit exceeded",
        )
        assert error.stage == "processor"
        assert error.source_name == "summarizer"
        assert error.error_message == "Rate limit exceeded"

    def test_正常系_article_urlはオプショナル(self) -> None:
        """article_urlがNoneでもStageErrorを作成できることを確認。"""
        error = StageError(
            stage="sink",
            source_name="file_sink",
            error_message="Permission denied",
            article_url=None,
        )
        assert error.article_url is None


# === Tests for Pipeline ===


class TestPipelineInit:
    """Test Pipeline initialization."""

    def test_正常系_デフォルト設定で作成できる(self) -> None:
        """Pipelineをデフォルト設定で作成できることを確認。"""
        pipeline = Pipeline()
        assert pipeline.config is not None
        assert len(pipeline.sources) == 0
        assert len(pipeline.processors) == 0
        assert len(pipeline.sinks) == 0

    def test_正常系_カスタムConfigで作成できる(self) -> None:
        """カスタムPipelineConfigでPipelineを作成できることを確認。"""
        config = PipelineConfig(batch_size=100)
        pipeline = Pipeline(config=config)
        assert pipeline.config.batch_size == 100


class TestPipelineAddSource:
    """Test Pipeline.add_source method."""

    def test_正常系_SourceProtocol準拠オブジェクトを追加できる(self) -> None:
        """SourceProtocol準拠オブジェクトを追加できることを確認。"""
        pipeline = Pipeline()
        source = StubSource()
        result = pipeline.add_source(source)
        assert result is pipeline  # Fluent API
        assert len(pipeline.sources) == 1

    def test_正常系_複数のソースを追加できる(self) -> None:
        """複数のソースを追加できることを確認。"""
        pipeline = Pipeline()
        pipeline.add_source(StubSource()).add_source(StubSource())
        assert len(pipeline.sources) == 2


class TestPipelineAddProcessor:
    """Test Pipeline.add_processor method."""

    def test_正常系_ProcessorProtocol準拠オブジェクトを追加できる(self) -> None:
        """ProcessorProtocol準拠オブジェクトを追加できることを確認。"""
        pipeline = Pipeline()
        processor = StubProcessor()
        result = pipeline.add_processor(processor)
        assert result is pipeline  # Fluent API
        assert len(pipeline.processors) == 1

    def test_正常系_複数のプロセッサを追加できる(self) -> None:
        """複数のプロセッサを追加できることを確認。"""
        pipeline = Pipeline()
        pipeline.add_processor(StubProcessor(suffix=" [a]")).add_processor(
            StubProcessor(suffix=" [b]")
        )
        assert len(pipeline.processors) == 2


class TestPipelineAddSink:
    """Test Pipeline.add_sink method."""

    def test_正常系_SinkProtocol準拠オブジェクトを追加できる(self) -> None:
        """SinkProtocol準拠オブジェクトを追加できることを確認。"""
        pipeline = Pipeline()
        sink = StubSink()
        result = pipeline.add_sink(sink)
        assert result is pipeline  # Fluent API
        assert len(pipeline.sinks) == 1

    def test_正常系_複数のシンクを追加できる(self) -> None:
        """複数のシンクを追加できることを確認。"""
        pipeline = Pipeline()
        pipeline.add_sink(StubSink()).add_sink(StubSink())
        assert len(pipeline.sinks) == 2


class TestPipelineRun:
    """Test Pipeline.run method - main execution flow."""

    def test_正常系_ソースのみで実行できる(self) -> None:
        """ソースのみが登録されている場合でもrunが成功することを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        pipeline = Pipeline()
        pipeline.add_source(source)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_fetched == 1

    def test_正常系_Source_Processor_Sinkの完全チェーンを実行できる(
        self,
    ) -> None:
        """Source -> Processor -> Sink の完全チェーンが実行できることを確認。"""
        articles = [_make_article(), _make_article(url="https://example.com/news/2")]
        source = StubSource(articles=articles)
        processor = StubProcessor()
        sink = StubSink()

        pipeline = Pipeline()
        pipeline.add_source(source).add_processor(processor).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_fetched == 2
        assert result.articles_processed == 2
        assert result.articles_output == 2
        assert len(sink.written_articles) == 2
        # Check that processing was applied
        for article in sink.written_articles:
            assert article.summary_ja is not None
            assert "[processed]" in article.summary_ja

    def test_正常系_複数プロセッサが順番に適用される(self) -> None:
        """複数のプロセッサが順番に適用されることを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        proc_a = StubProcessor(suffix=" [a]")
        proc_b = StubProcessor(suffix=" [b]")
        sink = StubSink()

        pipeline = Pipeline()
        pipeline.add_source(source).add_processor(proc_a).add_processor(
            proc_b
        ).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert len(sink.written_articles) == 1
        # Both processors applied in order
        summary_ja = sink.written_articles[0].summary_ja
        assert summary_ja is not None
        assert " [a] [b]" in summary_ja

    def test_正常系_複数ソースからの記事が統合される(self) -> None:
        """複数ソースからフェッチした記事が統合されることを確認。"""
        source1 = StubSource(articles=[_make_article()])
        source2 = StubSource(articles=[_make_article(url="https://example.com/news/2")])
        sink = StubSink()

        pipeline = Pipeline()
        pipeline.add_source(source1).add_source(source2).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_fetched == 2
        assert len(sink.written_articles) == 2

    def test_正常系_複数シンクに出力される(self) -> None:
        """複数のシンクに対して出力されることを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        sink1 = StubSink()
        sink2 = StubSink()

        pipeline = Pipeline()
        pipeline.add_source(source).add_sink(sink1).add_sink(sink2)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert len(sink1.written_articles) == 1
        assert len(sink2.written_articles) == 1

    def test_正常系_identifiersなしでも実行できる(self) -> None:
        """identifiersがNoneの場合でもrunが成功することを確認。"""
        pipeline = Pipeline()
        result = pipeline.run()
        assert result.success is True
        assert result.articles_fetched == 0

    def test_正常系_ソースが空の場合は空の結果を返す(self) -> None:
        """ソースが登録されていない場合、空の結果を返すことを確認。"""
        pipeline = Pipeline()
        sink = StubSink()
        pipeline.add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_fetched == 0
        assert len(sink.written_articles) == 0


class TestPipelineErrorHandling:
    """Test Pipeline error handling."""

    def test_正常系_ソースエラーでcontinue_on_errorが有効時は継続(
        self,
    ) -> None:
        """ソースエラー時にcontinue_on_error=Trueなら他のソースを継続処理することを確認。"""
        failing_source = StubSource(fail=True)
        working_source = StubSource(
            articles=[_make_article(url="https://example.com/news/working")]
        )
        sink = StubSink()

        config = PipelineConfig(continue_on_error=True)
        pipeline = Pipeline(config=config)
        pipeline.add_source(failing_source).add_source(working_source).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        # Pipeline continues despite one source failing
        assert result.articles_fetched >= 1
        assert len(sink.written_articles) >= 1

    def test_正常系_プロセッサエラーでcontinue_on_errorが有効時は継続(
        self,
    ) -> None:
        """プロセッサエラー時にcontinue_on_error=Trueなら他の記事を継続処理することを確認。"""
        articles = [
            _make_article(),
            _make_article(url="https://example.com/news/2"),
        ]
        source = StubSource(articles=articles)
        failing_proc = FailingProcessor()
        sink = StubSink()

        config = PipelineConfig(continue_on_error=True)
        pipeline = Pipeline(config=config)
        pipeline.add_source(source).add_processor(failing_proc).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        # Pipeline should still complete, but with errors
        assert len(result.errors) > 0
        assert result.errors[0].stage == "processor"

    def test_異常系_シンクエラーでcontinue_on_errorが有効時は継続(
        self,
    ) -> None:
        """シンクエラー時にcontinue_on_error=Trueなら他のシンクを継続処理することを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        failing_sink = StubSink(fail=True)
        working_sink = StubSink()

        config = PipelineConfig(continue_on_error=True)
        pipeline = Pipeline(config=config)
        pipeline.add_source(source).add_sink(failing_sink).add_sink(working_sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert len(result.errors) > 0
        # Working sink still receives articles
        assert len(working_sink.written_articles) == 1

    def test_異常系_continue_on_error無効時はプロセッサエラーで停止(
        self,
    ) -> None:
        """continue_on_error=Falseの場合、プロセッサエラーで例外が発生することを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        failing_proc = FailingProcessor()

        config = PipelineConfig(continue_on_error=False)
        pipeline = Pipeline(config=config)
        pipeline.add_source(source).add_processor(failing_proc)

        with pytest.raises(PipelineError):
            pipeline.run(identifiers=["AAPL"])


class TestPipelineBatchProcessing:
    """Test Pipeline batch processing."""

    def test_正常系_バッチサイズに分割して処理される(self) -> None:
        """記事がバッチサイズに分割して処理されることを確認。"""
        # Create multiple articles
        articles = [
            _make_article(url=f"https://example.com/news/{i}") for i in range(10)
        ]
        source = StubSource(articles=articles)
        processor = StubProcessor()
        sink = StubSink()

        config = PipelineConfig(batch_size=3)
        pipeline = Pipeline(config=config)
        pipeline.add_source(source).add_processor(processor).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_fetched == 10
        assert result.articles_processed == 10
        assert len(sink.written_articles) == 10
        # Processor should have processed all articles
        assert processor.processed_count == 10

    def test_正常系_バッチサイズが記事数より大きい場合も正常動作(self) -> None:
        """バッチサイズが記事数より大きい場合も正常に動作することを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        processor = StubProcessor()
        sink = StubSink()

        config = PipelineConfig(batch_size=100)
        pipeline = Pipeline(config=config)
        pipeline.add_source(source).add_processor(processor).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_processed == 1


class TestPipelineEdgeCases:
    """Test Pipeline edge cases."""

    def test_エッジケース_プロセッサなしで実行できる(self) -> None:
        """プロセッサが登録されていない場合でもrunが成功することを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        sink = StubSink()

        pipeline = Pipeline()
        pipeline.add_source(source).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_fetched == 1
        assert result.articles_output == 1
        assert len(sink.written_articles) == 1

    def test_エッジケース_シンクなしで実行できる(self) -> None:
        """シンクが登録されていない場合でもrunが成功することを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        processor = StubProcessor()

        pipeline = Pipeline()
        pipeline.add_source(source).add_processor(processor)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_fetched == 1
        assert result.articles_processed == 1

    def test_エッジケース_空のidentifiersリストで実行(self) -> None:
        """空のidentifiersリストでrunを呼んだ場合の動作を確認。"""
        pipeline = Pipeline()
        source = StubSource()
        pipeline.add_source(source)

        result = pipeline.run(identifiers=[])
        assert result.success is True
        assert result.articles_fetched == 0

    def test_エッジケース_すべてのソースが空の場合(self) -> None:
        """すべてのソースが空のFetchResultを返す場合の動作を確認。"""
        source = StubSource(articles=[])
        processor = StubProcessor()
        sink = StubSink()

        pipeline = Pipeline()
        pipeline.add_source(source).add_processor(processor).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert result.success is True
        assert result.articles_fetched == 0
        assert result.articles_processed == 0
        assert result.articles_output == 0

    def test_エッジケース_ソースが失敗しても0記事を返す(self) -> None:
        """すべてのソースが失敗する場合、0記事で成功結果を返すことを確認。"""
        source = StubSource(fail=True)
        sink = StubSink()

        config = PipelineConfig(continue_on_error=True)
        pipeline = Pipeline(config=config)
        pipeline.add_source(source).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        # No articles fetched, but pipeline itself succeeds
        assert result.articles_fetched == 0

    def test_正常系_output_articlesに最終結果が含まれる(self) -> None:
        """PipelineResultのoutput_articlesに最終的な処理済み記事が含まれることを確認。"""
        articles = [_make_article()]
        source = StubSource(articles=articles)
        processor = StubProcessor()
        sink = StubSink()

        pipeline = Pipeline()
        pipeline.add_source(source).add_processor(processor).add_sink(sink)

        result = pipeline.run(identifiers=["AAPL"])
        assert len(result.output_articles) == 1
        assert result.output_articles[0].summary_ja is not None


class TestPipelineFluentAPI:
    """Test Pipeline fluent (builder) API."""

    def test_正常系_メソッドチェーンでパイプラインを構築できる(self) -> None:
        """add_source, add_processor, add_sinkをチェーンして構築できることを確認。"""
        pipeline = (
            Pipeline()
            .add_source(StubSource())
            .add_processor(StubProcessor())
            .add_sink(StubSink())
        )
        assert len(pipeline.sources) == 1
        assert len(pipeline.processors) == 1
        assert len(pipeline.sinks) == 1

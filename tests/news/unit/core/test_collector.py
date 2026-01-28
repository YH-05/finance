"""Unit tests for the Collector class.

This module tests the main orchestration class that manages news sources and sinks.
"""

from datetime import datetime, timezone

import pytest

from news.core.article import Article, ArticleSource
from news.core.result import FetchResult
from news.core.sink import SinkProtocol, SinkType
from news.core.source import SourceProtocol


class MockSource:
    """Mock implementation of SourceProtocol for testing."""

    def __init__(
        self,
        name: str = "mock_source",
        articles: list[Article] | None = None,
        should_fail: bool = False,
    ) -> None:
        self._name = name
        self._articles = articles or []
        self._should_fail = should_fail
        self._fetch_calls: list[tuple[str, int]] = []

    @property
    def source_name(self) -> str:
        return self._name

    @property
    def source_type(self) -> ArticleSource:
        return ArticleSource.YFINANCE_TICKER

    def fetch(self, identifier: str, count: int = 10) -> FetchResult:
        self._fetch_calls.append((identifier, count))
        if self._should_fail:
            from news.core.errors import SourceError

            return FetchResult(
                articles=[],
                success=False,
                ticker=identifier,
                error=SourceError(
                    message="Mock fetch failed",
                    source=self._name,
                    ticker=identifier,
                ),
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
        return [self.fetch(ident, count) for ident in identifiers]


class MockSink:
    """Mock implementation of SinkProtocol for testing."""

    def __init__(
        self,
        name: str = "mock_sink",
        should_fail: bool = False,
    ) -> None:
        self._name = name
        self._should_fail = should_fail
        self.written_articles: list[Article] = []
        self.write_calls: int = 0

    @property
    def sink_name(self) -> str:
        return self._name

    @property
    def sink_type(self) -> SinkType:
        return SinkType.FILE

    def write(
        self,
        articles: list[Article],
        metadata: dict | None = None,
    ) -> bool:
        self.write_calls += 1
        if self._should_fail:
            return False
        self.written_articles.extend(articles)
        return True

    def write_batch(self, results: list[FetchResult]) -> bool:
        return all(self.write(result.articles) for result in results)


def create_test_article(
    url: str = "https://example.com/news/1",
    title: str = "Test Article",
) -> Article:
    """Create a test article with default values."""
    return Article(
        url=url,
        title=title,
        published_at=datetime.now(timezone.utc),
        source=ArticleSource.YFINANCE_TICKER,
    )


# =============================================================================
# Tests
# =============================================================================


class TestCollectorInstantiation:
    """Tests for Collector instantiation."""

    def test_正常系_デフォルト設定でインスタンス化できる(self) -> None:
        """Collector can be instantiated with default settings."""
        from news.collector import Collector

        collector = Collector()
        assert collector is not None

    def test_正常系_設定を指定してインスタンス化できる(self) -> None:
        """Collector can be instantiated with custom config."""
        from news.collector import Collector, CollectorConfig

        config = CollectorConfig()
        collector = Collector(config=config)
        assert collector is not None


class TestSourceRegistration:
    """Tests for source registration."""

    def test_正常系_ソースを登録できる(self) -> None:
        """Source can be registered to the Collector."""
        from news.collector import Collector

        collector = Collector()
        source = MockSource(name="test_source")

        collector.register_source(source)

        assert source.source_name in collector.sources

    def test_正常系_複数のソースを登録できる(self) -> None:
        """Multiple sources can be registered."""
        from news.collector import Collector

        collector = Collector()
        source1 = MockSource(name="source_1")
        source2 = MockSource(name="source_2")

        collector.register_source(source1)
        collector.register_source(source2)

        assert len(collector.sources) == 2
        assert "source_1" in collector.sources
        assert "source_2" in collector.sources

    def test_異常系_同名のソースを登録するとValueError(self) -> None:
        """Registering a source with the same name raises ValueError."""
        from news.collector import Collector

        collector = Collector()
        source1 = MockSource(name="duplicate_source")
        source2 = MockSource(name="duplicate_source")

        collector.register_source(source1)

        with pytest.raises(ValueError, match="already registered"):
            collector.register_source(source2)


class TestSinkRegistration:
    """Tests for sink registration."""

    def test_正常系_シンクを登録できる(self) -> None:
        """Sink can be registered to the Collector."""
        from news.collector import Collector

        collector = Collector()
        sink = MockSink(name="test_sink")

        collector.register_sink(sink)

        assert sink.sink_name in collector.sinks

    def test_正常系_複数のシンクを登録できる(self) -> None:
        """Multiple sinks can be registered."""
        from news.collector import Collector

        collector = Collector()
        sink1 = MockSink(name="sink_1")
        sink2 = MockSink(name="sink_2")

        collector.register_sink(sink1)
        collector.register_sink(sink2)

        assert len(collector.sinks) == 2
        assert "sink_1" in collector.sinks
        assert "sink_2" in collector.sinks

    def test_異常系_同名のシンクを登録するとValueError(self) -> None:
        """Registering a sink with the same name raises ValueError."""
        from news.collector import Collector

        collector = Collector()
        sink1 = MockSink(name="duplicate_sink")
        sink2 = MockSink(name="duplicate_sink")

        collector.register_sink(sink1)

        with pytest.raises(ValueError, match="already registered"):
            collector.register_sink(sink2)


class TestCollect:
    """Tests for the collect() method."""

    def test_正常系_1ソース1シンクで収集できる(self) -> None:
        """Articles from one source are written to one sink."""
        from news.collector import Collector

        collector = Collector()
        article = create_test_article()
        source = MockSource(name="source", articles=[article])
        sink = MockSink(name="sink")

        collector.register_source(source)
        collector.register_sink(sink)

        result = collector.collect()

        assert result.success
        assert result.total_articles == 1
        assert sink.written_articles == [article]

    def test_正常系_複数ソースから収集できる(self) -> None:
        """Articles from multiple sources are collected."""
        from news.collector import Collector

        collector = Collector()
        article1 = create_test_article(url="https://example.com/1", title="Article 1")
        article2 = create_test_article(url="https://example.com/2", title="Article 2")
        source1 = MockSource(name="source_1", articles=[article1])
        source2 = MockSource(name="source_2", articles=[article2])
        sink = MockSink(name="sink")

        collector.register_source(source1)
        collector.register_source(source2)
        collector.register_sink(sink)

        result = collector.collect()

        assert result.success
        assert result.total_articles == 2
        assert len(sink.written_articles) == 2

    def test_正常系_複数シンクに出力できる(self) -> None:
        """Articles are written to multiple sinks."""
        from news.collector import Collector

        collector = Collector()
        article = create_test_article()
        source = MockSource(name="source", articles=[article])
        sink1 = MockSink(name="sink_1")
        sink2 = MockSink(name="sink_2")

        collector.register_source(source)
        collector.register_sink(sink1)
        collector.register_sink(sink2)

        result = collector.collect()

        assert result.success
        assert sink1.written_articles == [article]
        assert sink2.written_articles == [article]

    def test_異常系_1ソースの失敗で全体が止まらない(self) -> None:
        """One source failure doesn't stop the entire collection."""
        from news.collector import Collector

        collector = Collector()
        article = create_test_article()
        failing_source = MockSource(name="failing", should_fail=True)
        working_source = MockSource(name="working", articles=[article])
        sink = MockSink(name="sink")

        collector.register_source(failing_source)
        collector.register_source(working_source)
        collector.register_sink(sink)

        result = collector.collect()

        assert result.success  # Overall success if at least some articles collected
        assert result.total_articles == 1
        assert len(result.source_errors) == 1
        assert "failing" in result.source_errors

    def test_異常系_1シンクの失敗で全体が止まらない(self) -> None:
        """One sink failure doesn't stop writing to other sinks."""
        from news.collector import Collector

        collector = Collector()
        article = create_test_article()
        source = MockSource(name="source", articles=[article])
        failing_sink = MockSink(name="failing_sink", should_fail=True)
        working_sink = MockSink(name="working_sink")

        collector.register_source(source)
        collector.register_sink(failing_sink)
        collector.register_sink(working_sink)

        result = collector.collect()

        assert result.success  # Overall success if at least one sink succeeded
        assert working_sink.written_articles == [article]
        assert len(result.sink_errors) == 1
        assert "failing_sink" in result.sink_errors

    def test_エッジケース_ソースなしで収集すると空の結果(self) -> None:
        """Collecting without sources returns empty result."""
        from news.collector import Collector

        collector = Collector()
        sink = MockSink(name="sink")
        collector.register_sink(sink)

        result = collector.collect()

        assert result.success
        assert result.total_articles == 0
        assert sink.written_articles == []

    def test_エッジケース_シンクなしで収集すると警告(self) -> None:
        """Collecting without sinks still collects but warns."""
        from news.collector import Collector

        collector = Collector()
        article = create_test_article()
        source = MockSource(name="source", articles=[article])
        collector.register_source(source)

        result = collector.collect()

        # Collection succeeds but no output
        assert result.success
        assert result.total_articles == 1
        assert result.no_sinks_warning is True

    def test_異常系_全ソース失敗で失敗(self) -> None:
        """Collection fails if all sources fail."""
        from news.collector import Collector

        collector = Collector()
        failing_source = MockSource(name="failing", should_fail=True)
        sink = MockSink(name="sink")

        collector.register_source(failing_source)
        collector.register_sink(sink)

        result = collector.collect()

        assert not result.success
        assert result.total_articles == 0
        assert len(result.source_errors) == 1


class TestCollectFromSource:
    """Tests for the collect_from_source() method."""

    def test_正常系_特定ソースから収集できる(self) -> None:
        """Can collect from a specific source by name."""
        from news.collector import Collector

        collector = Collector()
        article1 = create_test_article(url="https://example.com/1")
        article2 = create_test_article(url="https://example.com/2")
        source1 = MockSource(name="source_1", articles=[article1])
        source2 = MockSource(name="source_2", articles=[article2])

        collector.register_source(source1)
        collector.register_source(source2)

        result = collector.collect_from_source("source_1")

        assert result.success
        assert result.article_count == 1

    def test_異常系_存在しないソース名でKeyError(self) -> None:
        """Requesting non-existent source raises KeyError."""
        from news.collector import Collector

        collector = Collector()

        with pytest.raises(KeyError, match="not found"):
            collector.collect_from_source("nonexistent")


class TestCollectionResult:
    """Tests for CollectionResult data class."""

    def test_正常系_結果にメタデータが含まれる(self) -> None:
        """CollectionResult contains collection metadata."""
        from news.collector import Collector

        collector = Collector()
        article = create_test_article()
        source = MockSource(name="source", articles=[article])
        sink = MockSink(name="sink")

        collector.register_source(source)
        collector.register_sink(sink)

        result = collector.collect()

        assert result.total_articles == 1
        assert result.sources_processed == 1
        assert result.sinks_written == 1
        assert result.collected_at is not None

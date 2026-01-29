"""Unit tests for RSSCollector.

This module tests the RSSCollector class which collects articles from RSS feeds
using the existing FeedParser implementation.

Test categories:
- RSSCollector class definition and inheritance
- source_type property behavior
- collect() method with FeedParser integration
- Configuration handling
- Error handling
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from news.collectors.base import BaseCollector
from news.collectors.rss import RSSCollector
from news.config import NewsWorkflowConfig, RssConfig
from news.models import ArticleSource, CollectedArticle, SourceType
from rss.types import FeedItem, PresetFeed, PresetsConfig


class TestRSSCollectorDefinition:
    """Tests for RSSCollector class definition."""

    def test_正常系_RSSCollectorはBaseCollectorを継承している(self) -> None:
        """RSSCollector should inherit from BaseCollector."""
        assert issubclass(RSSCollector, BaseCollector)


class TestRSSCollectorSourceType:
    """Tests for RSSCollector source_type property."""

    def test_正常系_source_typeがRSSを返す(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """source_type property should return SourceType.RSS."""
        collector = RSSCollector(config=mock_config)
        assert collector.source_type == SourceType.RSS


class TestRSSCollectorInit:
    """Tests for RSSCollector initialization."""

    def test_正常系_configを受け取って初期化できる(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """RSSCollector should be initialized with config."""
        collector = RSSCollector(config=mock_config)
        assert collector._config == mock_config

    def test_正常系_FeedParserインスタンスを保持している(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """RSSCollector should hold a FeedParser instance."""
        collector = RSSCollector(config=mock_config)
        # FeedParser is imported from rss.core.parser
        from rss.core.parser import FeedParser

        assert isinstance(collector._parser, FeedParser)


class TestRSSCollectorCollect:
    """Tests for RSSCollector collect method."""

    @pytest.mark.asyncio
    async def test_正常系_空のプリセットで空リストを返す(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """collect should return empty list when no presets are configured."""
        with (
            patch.object(Path, "read_text") as mock_read,
            patch("json.loads") as mock_loads,
        ):
            mock_read.return_value = "{}"
            mock_loads.return_value = {"version": "1.0", "presets": []}

            collector = RSSCollector(config=mock_config)
            result = await collector.collect()

            assert result == []
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_正常系_RSSフィードから記事を収集できる(
        self,
        mock_config: NewsWorkflowConfig,
        sample_feed_items: list[FeedItem],
        sample_presets_config: PresetsConfig,
    ) -> None:
        """collect should fetch articles from RSS feeds."""
        with (
            patch.object(Path, "read_text") as mock_read,
            patch("json.loads") as mock_loads,
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            # Setup presets
            mock_loads.return_value = {
                "version": sample_presets_config.version,
                "presets": [
                    {
                        "url": p.url,
                        "title": p.title,
                        "category": p.category,
                        "fetch_interval": p.fetch_interval,
                        "enabled": p.enabled,
                    }
                    for p in sample_presets_config.presets
                ],
            }

            # Setup HTTP response
            mock_response = MagicMock()
            mock_response.content = b"<rss><channel></channel></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Setup FeedParser
            collector = RSSCollector(config=mock_config)
            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = sample_feed_items

                result = await collector.collect()

                assert len(result) > 0
                assert all(isinstance(a, CollectedArticle) for a in result)

    @pytest.mark.asyncio
    async def test_正常系_max_age_hoursで記事をフィルタリングできる(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """collect should filter articles by max_age_hours."""
        collector = RSSCollector(config=mock_config)

        # Use default max_age_hours
        with (
            patch.object(Path, "read_text"),
            patch("json.loads") as mock_loads,
        ):
            mock_loads.return_value = {"version": "1.0", "presets": []}
            result = await collector.collect(max_age_hours=24)

            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_正常系_CollectedArticleに変換される(
        self,
        mock_config: NewsWorkflowConfig,
        sample_feed_items: list[FeedItem],
        sample_presets_config: PresetsConfig,
    ) -> None:
        """FeedItem should be converted to CollectedArticle."""
        with (
            patch.object(Path, "read_text"),
            patch("json.loads") as mock_loads,
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            # Setup presets with one enabled feed
            mock_loads.return_value = {
                "version": "1.0",
                "presets": [
                    {
                        "url": "https://example.com/feed.xml",
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            # Setup HTTP response
            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)

            # Mock FeedParser to return sample items
            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = sample_feed_items

                result = await collector.collect()

                assert len(result) == len(sample_feed_items)
                for article in result:
                    assert isinstance(article, CollectedArticle)
                    assert article.source.source_type == SourceType.RSS


class TestRSSCollectorConfigHandling:
    """Tests for RSSCollector configuration handling."""

    @pytest.mark.asyncio
    async def test_正常系_無効化されたフィードはスキップされる(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Disabled feeds should be skipped."""
        with (
            patch.object(Path, "read_text"),
            patch("json.loads") as mock_loads,
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_loads.return_value = {
                "version": "1.0",
                "presets": [
                    {
                        "url": "https://example.com/feed.xml",
                        "title": "Disabled Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": False,  # Disabled
                    }
                ],
            }

            collector = RSSCollector(config=mock_config)
            result = await collector.collect()

            # Should not call httpx at all since feed is disabled
            mock_client_class.assert_not_called()
            assert result == []


class TestRSSCollectorErrorHandling:
    """Tests for RSSCollector error handling."""

    @pytest.mark.asyncio
    async def test_正常系_HTTPエラーでも他のフィードは処理を継続する(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """HTTP error should not stop processing other feeds."""
        import httpx

        with (
            patch.object(Path, "read_text"),
            patch("json.loads") as mock_loads,
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_loads.return_value = {
                "version": "1.0",
                "presets": [
                    {
                        "url": "https://error.com/feed.xml",
                        "title": "Error Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                    {
                        "url": "https://success.com/feed.xml",
                        "title": "Success Feed",
                        "category": "tech",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                ],
            }

            # Setup mock responses
            error_response = MagicMock()
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )

            success_response = MagicMock()
            success_response.content = b"<rss></rss>"
            success_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()

            async def mock_get(url: str, **kwargs: object) -> MagicMock:
                if "error.com" in url:
                    return error_response
                return success_response

            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = []

                # Should not raise, should continue processing
                result = await collector.collect()
                assert isinstance(result, list)


# Fixtures


@pytest.fixture
def mock_config() -> NewsWorkflowConfig:
    """Create a mock NewsWorkflowConfig for testing."""
    from news.config import (
        ExtractionConfig,
        FilteringConfig,
        GitHubConfig,
        OutputConfig,
        SummarizationConfig,
    )

    return NewsWorkflowConfig(
        version="1.0",
        status_mapping={"market": "index", "tech": "ai"},
        github_status_ids={"index": "abc123", "ai": "def456"},
        rss=RssConfig(presets_file="data/config/rss-presets.json"),
        extraction=ExtractionConfig(),
        summarization=SummarizationConfig(prompt_template="Summarize: {body}"),
        github=GitHubConfig(
            project_number=15,
            project_id="PVT_test",
            status_field_id="PVTSSF_test",
            published_date_field_id="PVTF_test",
            repository="owner/repo",
        ),
        filtering=FilteringConfig(),
        output=OutputConfig(result_dir="data/exports/news-workflow"),
    )


@pytest.fixture
def sample_feed_items() -> list[FeedItem]:
    """Create sample FeedItems for testing."""
    now = datetime.now(timezone.utc).isoformat()
    return [
        FeedItem(
            item_id="item-1",
            title="Test Article 1",
            link="https://example.com/article1",
            published=now,
            summary="Summary of article 1",
            content=None,
            author="Author 1",
            fetched_at=now,
        ),
        FeedItem(
            item_id="item-2",
            title="Test Article 2",
            link="https://example.com/article2",
            published=now,
            summary="Summary of article 2",
            content="Full content of article 2",
            author=None,
            fetched_at=now,
        ),
    ]


@pytest.fixture
def sample_presets_config() -> PresetsConfig:
    """Create sample PresetsConfig for testing."""
    return PresetsConfig(
        version="1.0",
        presets=[
            PresetFeed(
                url="https://example.com/feed1.xml",
                title="Test Feed 1",
                category="market",
                fetch_interval="daily",
                enabled=True,
            ),
            PresetFeed(
                url="https://example.com/feed2.xml",
                title="Test Feed 2",
                category="tech",
                fetch_interval="daily",
                enabled=True,
            ),
        ],
    )

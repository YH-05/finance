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

from datetime import datetime, timedelta, timezone
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

    @pytest.mark.asyncio
    async def test_正常系_category未指定時にotherがデフォルト値として設定される(
        self,
        mock_config: NewsWorkflowConfig,
        sample_feed_items: list[FeedItem],
    ) -> None:
        """category should default to 'other' when not specified in preset."""
        with (
            patch.object(Path, "read_text"),
            patch("json.loads") as mock_loads,
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            # Setup presets WITHOUT category field
            mock_loads.return_value = {
                "version": "1.0",
                "presets": [
                    {
                        "url": "https://example.com/feed.xml",
                        "title": "No Category Feed",
                        # "category" is intentionally omitted
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

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = sample_feed_items

                result = await collector.collect()

                # Verify that category defaults to "other"
                assert len(result) == len(sample_feed_items)
                for article in result:
                    assert article.source.category == "other"

    @pytest.mark.asyncio
    async def test_正常系_category指定時にその値が設定される(
        self,
        mock_config: NewsWorkflowConfig,
        sample_feed_items: list[FeedItem],
    ) -> None:
        """category should be set to the specified value when present in preset."""
        with (
            patch.object(Path, "read_text"),
            patch("json.loads") as mock_loads,
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            # Setup presets WITH category field
            mock_loads.return_value = {
                "version": "1.0",
                "presets": [
                    {
                        "url": "https://example.com/feed.xml",
                        "title": "Market Feed",
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

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = sample_feed_items

                result = await collector.collect()

                # Verify that category is set to the specified value
                assert len(result) == len(sample_feed_items)
                for article in result:
                    assert article.source.category == "market"


class TestRSSCollectorDateFiltering:
    """Tests for RSSCollector date filtering functionality."""

    @pytest.mark.asyncio
    async def test_正常系_cutoff_time以前の古い記事はフィルタリングされる(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Articles older than cutoff_time should be filtered out."""
        # Create old article (10 days ago)
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        old_feed_items = [
            FeedItem(
                item_id="old-item",
                title="Old Article",
                link="https://example.com/old",
                published=old_time.isoformat(),
                summary="Old article summary",
                content=None,
                author=None,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            ),
        ]

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
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = old_feed_items

                # max_age_hours=168 (7 days) should filter out 10-day old article
                result = await collector.collect(max_age_hours=168)

                assert len(result) == 0

    @pytest.mark.asyncio
    async def test_正常系_cutoff_time以後の新しい記事は含まれる(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Articles within cutoff_time should be included."""
        # Create recent article (1 day ago)
        recent_time = datetime.now(timezone.utc) - timedelta(days=1)
        recent_feed_items = [
            FeedItem(
                item_id="recent-item",
                title="Recent Article",
                link="https://example.com/recent",
                published=recent_time.isoformat(),
                summary="Recent article summary",
                content=None,
                author=None,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            ),
        ]

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
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = recent_feed_items

                # max_age_hours=168 (7 days) should include 1-day old article
                result = await collector.collect(max_age_hours=168)

                assert len(result) == 1
                assert result[0].title == "Recent Article"

    @pytest.mark.asyncio
    async def test_正常系_publishedがNoneの記事は含まれる(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Articles with published=None should be included (not filtered out)."""
        # Create article with no published date
        null_published_feed_items = [
            FeedItem(
                item_id="null-published-item",
                title="No Published Date Article",
                link="https://example.com/no-date",
                published=None,
                summary="Article without published date",
                content=None,
                author=None,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            ),
        ]

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
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = null_published_feed_items

                # Articles with None published should be included
                result = await collector.collect(max_age_hours=168)

                assert len(result) == 1
                assert result[0].published is None

    @pytest.mark.asyncio
    async def test_正常系_UTCで時刻比較が行われる(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Time comparison should be done in UTC timezone."""
        # Create article with explicit UTC timezone (5 days ago)
        utc_time = datetime.now(timezone.utc) - timedelta(days=5)
        utc_feed_items = [
            FeedItem(
                item_id="utc-item",
                title="UTC Timezone Article",
                link="https://example.com/utc",
                published=utc_time.isoformat(),
                summary="Article with UTC timezone",
                content=None,
                author=None,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            ),
        ]

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
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = utc_feed_items

                # 5-day old article should be included with 7-day max_age
                result = await collector.collect(max_age_hours=168)

                assert len(result) == 1
                assert result[0].published is not None
                assert result[0].published.tzinfo is not None

    @pytest.mark.asyncio
    async def test_正常系_新旧混在の記事から古い記事のみフィルタリング(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Only old articles should be filtered, recent ones should remain."""
        now = datetime.now(timezone.utc)
        mixed_feed_items = [
            FeedItem(
                item_id="old-item",
                title="Old Article",
                link="https://example.com/old",
                published=(now - timedelta(days=10)).isoformat(),
                summary="Old article",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
            FeedItem(
                item_id="recent-item",
                title="Recent Article",
                link="https://example.com/recent",
                published=(now - timedelta(days=2)).isoformat(),
                summary="Recent article",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
            FeedItem(
                item_id="null-item",
                title="No Date Article",
                link="https://example.com/no-date",
                published=None,
                summary="No date article",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
        ]

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
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = mixed_feed_items

                # max_age_hours=168 (7 days) should filter old, keep recent and null
                result = await collector.collect(max_age_hours=168)

                assert len(result) == 2
                titles = {a.title for a in result}
                assert "Recent Article" in titles
                assert "No Date Article" in titles
                assert "Old Article" not in titles


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


class TestRSSCollectorDomainFiltering:
    """Tests for RSSCollector domain filtering functionality."""

    @pytest.mark.asyncio
    async def test_正常系_ブロックドメインの記事が収集結果から除外される(
        self,
        mock_config_with_domain_filter: NewsWorkflowConfig,
        sample_feed_items: list[FeedItem],
    ) -> None:
        """Articles from blocked domains should be excluded from collection results."""
        # Create articles with blocked and non-blocked domains
        now = datetime.now(timezone.utc)
        mixed_domain_items = [
            FeedItem(
                item_id="blocked-item",
                title="Blocked Article",
                link="https://seekingalpha.com/article/123",
                published=now.isoformat(),
                summary="Article from blocked domain",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
            FeedItem(
                item_id="allowed-item",
                title="Allowed Article",
                link="https://cnbc.com/article/456",
                published=now.isoformat(),
                summary="Article from allowed domain",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
        ]

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
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config_with_domain_filter)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = mixed_domain_items

                result = await collector.collect()

                assert len(result) == 1
                assert "cnbc.com" in str(result[0].url)
                assert "seekingalpha.com" not in str(result[0].url)

    @pytest.mark.asyncio
    async def test_正常系_フィルタリング無効時は全て収集される(
        self,
        mock_config_with_domain_filter_disabled: NewsWorkflowConfig,
    ) -> None:
        """All articles should be collected when domain filtering is disabled."""
        now = datetime.now(timezone.utc)
        blocked_domain_items = [
            FeedItem(
                item_id="blocked-item",
                title="Article from Blocked Domain",
                link="https://seekingalpha.com/article/123",
                published=now.isoformat(),
                summary="Article from blocked domain",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
        ]

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
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config_with_domain_filter_disabled)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = blocked_domain_items

                result = await collector.collect()

                # All articles should pass through when filtering is disabled
                assert len(result) == 1
                assert "seekingalpha.com" in str(result[0].url)

    @pytest.mark.asyncio
    async def test_正常系_サブドメインもブロックされる(
        self,
        mock_config_with_domain_filter: NewsWorkflowConfig,
    ) -> None:
        """Subdomains of blocked domains should also be blocked."""
        now = datetime.now(timezone.utc)
        subdomain_items = [
            FeedItem(
                item_id="subdomain-item",
                title="Subdomain Article",
                link="https://www.seekingalpha.com/article/123",
                published=now.isoformat(),
                summary="Article from subdomain of blocked domain",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
        ]

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
                        "title": "Test Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    }
                ],
            }

            mock_response = MagicMock()
            mock_response.content = b"<rss></rss>"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config_with_domain_filter)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = subdomain_items

                result = await collector.collect()

                # Subdomain should also be blocked
                assert len(result) == 0

    def test_正常系_filter_blocked_domainsで除外数が正しく返される(
        self,
        mock_config_with_domain_filter: NewsWorkflowConfig,
    ) -> None:
        """_filter_blocked_domains should correctly count blocked articles."""
        from news.models import CollectedArticle

        now = datetime.now(timezone.utc)
        articles = [
            CollectedArticle(
                url="https://seekingalpha.com/article/1",  # type: ignore[arg-type]
                title="Blocked 1",
                published=now,
                raw_summary="Summary 1",
                source=ArticleSource(
                    source_type=SourceType.RSS,
                    source_name="Test",
                    category="market",
                ),
                collected_at=now,
            ),
            CollectedArticle(
                url="https://investorplace.com/article/2",  # type: ignore[arg-type]
                title="Blocked 2",
                published=now,
                raw_summary="Summary 2",
                source=ArticleSource(
                    source_type=SourceType.RSS,
                    source_name="Test",
                    category="market",
                ),
                collected_at=now,
            ),
            CollectedArticle(
                url="https://cnbc.com/article/3",  # type: ignore[arg-type]
                title="Allowed",
                published=now,
                raw_summary="Summary 3",
                source=ArticleSource(
                    source_type=SourceType.RSS,
                    source_name="Test",
                    category="market",
                ),
                collected_at=now,
            ),
        ]

        collector = RSSCollector(config=mock_config_with_domain_filter)
        filtered = collector._filter_blocked_domains(articles)

        assert len(filtered) == 1
        assert filtered[0].title == "Allowed"


@pytest.fixture
def mock_config_with_domain_filter() -> NewsWorkflowConfig:
    """Create a mock NewsWorkflowConfig with domain filtering enabled."""
    from news.config import (
        DomainFilteringConfig,
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
        domain_filtering=DomainFilteringConfig(
            enabled=True,
            log_blocked=True,
            blocked_domains=["seekingalpha.com", "investorplace.com"],
        ),
    )


@pytest.fixture
def mock_config_with_domain_filter_disabled() -> NewsWorkflowConfig:
    """Create a mock NewsWorkflowConfig with domain filtering disabled."""
    from news.config import (
        DomainFilteringConfig,
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
        domain_filtering=DomainFilteringConfig(
            enabled=False,
            log_blocked=False,
            blocked_domains=["seekingalpha.com"],
        ),
    )


class TestInvalidFeedSkip:
    """Tests for invalid feed skip and error logging functionality."""

    @pytest.mark.asyncio
    async def test_正常系_無効フィードがスキップされ他のフィード処理が継続される(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Invalid feed should be skipped and processing continues with other feeds."""
        import httpx

        now = datetime.now(timezone.utc)
        valid_feed_items = [
            FeedItem(
                item_id="valid-item",
                title="Valid Article",
                link="https://example.com/valid",
                published=now.isoformat(),
                summary="Valid article summary",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
        ]

        with (
            patch.object(Path, "read_text"),
            patch("json.loads") as mock_loads,
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            mock_loads.return_value = {
                "version": "1.0",
                "presets": [
                    {
                        "url": "https://invalid.com/feed.xml",
                        "title": "Invalid Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                    {
                        "url": "https://valid.com/feed.xml",
                        "title": "Valid Feed",
                        "category": "tech",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                ],
            }

            # Setup error response for invalid feed
            error_response = MagicMock()
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )

            # Setup success response for valid feed
            success_response = MagicMock()
            success_response.content = b"<rss></rss>"
            success_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()

            async def mock_get(url: str, **kwargs: object) -> MagicMock:
                if "invalid.com" in url:
                    return error_response
                return success_response

            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = valid_feed_items

                articles = await collector.collect()

                # One article from valid feed
                assert len(articles) == 1
                # One error from invalid feed
                assert len(collector.feed_errors) == 1
                assert (
                    collector.feed_errors[0].feed_url == "https://invalid.com/feed.xml"
                )
                assert collector.feed_errors[0].error_type == "fetch"

    @pytest.mark.asyncio
    async def test_正常系_エラー情報がfeed_errorsに記録される(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Error information should be recorded in feed_errors."""
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
                ],
            }

            # Setup error response
            error_response = MagicMock()
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "500 Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)
            await collector.collect()

            assert len(collector.feed_errors) == 1
            feed_error = collector.feed_errors[0]
            assert feed_error.feed_url == "https://error.com/feed.xml"
            assert feed_error.feed_name == "Error Feed"
            assert "500" in feed_error.error
            assert feed_error.error_type == "fetch"
            assert feed_error.timestamp is not None

    @pytest.mark.asyncio
    async def test_正常系_全フィード失敗時は空リストを返す(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """When all feeds fail, should return empty list."""
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
                        "url": "https://error1.com/feed.xml",
                        "title": "Error Feed 1",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                    {
                        "url": "https://error2.com/feed.xml",
                        "title": "Error Feed 2",
                        "category": "tech",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                ],
            }

            # All feeds fail
            error_response = MagicMock()
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Network error",
                request=MagicMock(),
                response=MagicMock(status_code=503),
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)
            articles = await collector.collect()

            assert len(articles) == 0
            assert len(collector.feed_errors) == 2

    @pytest.mark.asyncio
    async def test_正常系_feed_errorsプロパティがコピーを返す(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """feed_errors property should return a copy of the list."""
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
                ],
            }

            error_response = MagicMock()
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)
            await collector.collect()

            errors1 = collector.feed_errors
            errors2 = collector.feed_errors

            # Should be equal content but different objects
            assert errors1 == errors2
            assert errors1 is not errors2

    @pytest.mark.asyncio
    async def test_正常系_collect呼び出しごとにfeed_errorsがクリアされる(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """feed_errors should be cleared on each collect() call."""
        import httpx

        now = datetime.now(timezone.utc)
        valid_items = [
            FeedItem(
                item_id="item",
                title="Article",
                link="https://example.com/article",
                published=now.isoformat(),
                summary="Summary",
                content=None,
                author=None,
                fetched_at=now.isoformat(),
            ),
        ]

        with (
            patch.object(Path, "read_text"),
            patch("json.loads") as mock_loads,
            patch("httpx.AsyncClient") as mock_client_class,
        ):
            # First call: one error
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
                ],
            }

            error_response = MagicMock()
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)
            await collector.collect()
            assert len(collector.feed_errors) == 1

            # Second call: no errors
            mock_loads.return_value = {
                "version": "1.0",
                "presets": [
                    {
                        "url": "https://valid.com/feed.xml",
                        "title": "Valid Feed",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                ],
            }

            success_response = MagicMock()
            success_response.content = b"<rss></rss>"
            success_response.raise_for_status = MagicMock()

            mock_client.get = AsyncMock(return_value=success_response)

            with patch.object(collector._parser, "parse") as mock_parse:
                mock_parse.return_value = valid_items
                await collector.collect()

            # feed_errors should be cleared
            assert len(collector.feed_errors) == 0


class TestFeedErrorClassification:
    """Tests for error classification in RSSCollector."""

    def test_正常系_HTTPエラーがfetchに分類される(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """HTTP errors should be classified as 'fetch'."""
        import httpx

        collector = RSSCollector(config=mock_config)

        # Test HTTP status error
        http_error = httpx.HTTPStatusError(
            "500 Error",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )
        assert collector._classify_error(http_error) == "fetch"

        # Test timeout error
        timeout_error = httpx.TimeoutException("Connection timeout")
        assert collector._classify_error(timeout_error) == "fetch"

    def test_正常系_パース関連エラーがparseに分類される(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Parse-related errors should be classified as 'parse'."""
        import json

        collector = RSSCollector(config=mock_config)

        # Test JSON decode error
        json_error = json.JSONDecodeError("Invalid JSON", "", 0)
        assert collector._classify_error(json_error) == "parse"

        # Test ValueError with parse-related message
        parse_error = ValueError("Failed to parse XML content")
        assert collector._classify_error(parse_error) == "parse"

    def test_正常系_ファイル未検出エラーがvalidationに分類される(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """FileNotFoundError should be classified as 'validation'."""
        collector = RSSCollector(config=mock_config)

        file_error = FileNotFoundError("Config file not found")
        assert collector._classify_error(file_error) == "validation"

    def test_正常系_不明なエラーがfetchに分類される(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Unknown errors should default to 'fetch'."""
        collector = RSSCollector(config=mock_config)

        unknown_error = RuntimeError("Some unknown error")
        assert collector._classify_error(unknown_error) == "fetch"


class TestFeedErrorCounting:
    """Tests for error counting in RSSCollector."""

    @pytest.mark.asyncio
    async def test_正常系_エラータイプ別件数が正しく集計される(
        self,
        mock_config: NewsWorkflowConfig,
    ) -> None:
        """Error counts by type should be correctly aggregated."""
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
                        "url": "https://error1.com/feed.xml",
                        "title": "Error Feed 1",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                    {
                        "url": "https://error2.com/feed.xml",
                        "title": "Error Feed 2",
                        "category": "tech",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                    {
                        "url": "https://error3.com/feed.xml",
                        "title": "Error Feed 3",
                        "category": "market",
                        "fetch_interval": "daily",
                        "enabled": True,
                    },
                ],
            }

            # All feeds fail with HTTP errors
            error_response = MagicMock()
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=error_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            collector = RSSCollector(config=mock_config)
            await collector.collect()

            error_counts = collector._count_error_types()
            assert error_counts == {"fetch": 3}

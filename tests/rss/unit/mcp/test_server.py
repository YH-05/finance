"""Tests for rss.mcp.server module.

This module tests the MCP server tools for RSS feed management.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from rss.mcp.server import (
    _feed_to_dict,
    _get_data_dir,
    _item_to_dict,
    rss_add_feed,
    rss_fetch_feed,
    rss_get_items,
    rss_list_feeds,
    rss_remove_feed,
    rss_search_items,
    rss_update_feed,
)
from rss.types import Feed, FeedItem, FetchInterval, FetchResult, FetchStatus


class TestGetDataDir:
    """Tests for _get_data_dir function."""

    def test_returns_default_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should return default data directory when RSS_DATA_DIR is not set."""
        monkeypatch.delenv("RSS_DATA_DIR", raising=False)
        with patch("rss.mcp.server.DEFAULT_DATA_DIR", temp_dir / "default"):
            result = _get_data_dir()
            assert result == temp_dir / "default"
            assert result.exists()

    def test_returns_custom_dir_from_env(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should return custom directory from RSS_DATA_DIR environment variable."""
        custom_dir = temp_dir / "custom_rss"
        monkeypatch.setenv("RSS_DATA_DIR", str(custom_dir))
        result = _get_data_dir()
        assert result == custom_dir
        assert result.exists()


class TestFeedToDict:
    """Tests for _feed_to_dict function."""

    def test_converts_feed_to_dict(self) -> None:
        """Should convert Feed dataclass to dictionary."""
        feed = Feed(
            feed_id="test-feed-123",
            url="https://example.com/feed.xml",
            title="Test Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )

        result = _feed_to_dict(feed)

        assert result["feed_id"] == "test-feed-123"
        assert result["url"] == "https://example.com/feed.xml"
        assert result["title"] == "Test Feed"
        assert result["category"] == "finance"
        assert result["fetch_interval"] == "daily"
        assert result["last_status"] == "pending"
        assert result["enabled"] is True


class TestItemToDict:
    """Tests for _item_to_dict function."""

    def test_converts_item_to_dict(self) -> None:
        """Should convert FeedItem dataclass to dictionary."""
        item = FeedItem(
            item_id="item-123",
            title="Test Article",
            link="https://example.com/article",
            published="2026-01-01T10:00:00Z",
            summary="Article summary",
            content="Full content",
            author="Test Author",
            fetched_at="2026-01-01T12:00:00Z",
        )

        result = _item_to_dict(item)

        assert result["item_id"] == "item-123"
        assert result["title"] == "Test Article"
        assert result["link"] == "https://example.com/article"
        assert result["published"] == "2026-01-01T10:00:00Z"
        assert result["summary"] == "Article summary"
        assert result["content"] == "Full content"
        assert result["author"] == "Test Author"


class TestRssListFeeds:
    """Tests for rss_list_feeds tool."""

    def test_returns_feeds_list(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should return list of feeds."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        mock_feed = Feed(
            feed_id="feed-1",
            url="https://example.com/feed.xml",
            title="Test Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            mock_manager.return_value.list_feeds.return_value = [mock_feed]

            result = rss_list_feeds()

            assert result["total"] == 1
            assert len(result["feeds"]) == 1
            assert result["feeds"][0]["feed_id"] == "feed-1"

    def test_handles_rss_error(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should handle RSS errors gracefully."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            from rss.exceptions import RSSError

            mock_manager.return_value.list_feeds.side_effect = RSSError("Test error")

            result = rss_list_feeds()

            assert "error" in result
            assert result["error_type"] == "RSSError"


class TestRssGetItems:
    """Tests for rss_get_items tool."""

    def test_returns_items_list(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should return list of items."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        mock_item = FeedItem(
            item_id="item-1",
            title="Test Article",
            link="https://example.com/article",
            published="2026-01-01T10:00:00Z",
            summary="Summary",
            content=None,
            author=None,
            fetched_at="2026-01-01T12:00:00Z",
        )

        with patch("rss.mcp.server.FeedReader") as mock_reader:
            mock_reader.return_value.get_items.return_value = [mock_item]

            result = rss_get_items(feed_id="feed-1", limit=10)

            assert result["total"] == 1
            assert len(result["items"]) == 1
            assert result["items"][0]["item_id"] == "item-1"


class TestRssSearchItems:
    """Tests for rss_search_items tool."""

    def test_returns_search_results(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should return search results."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        mock_item = FeedItem(
            item_id="item-1",
            title="Bitcoin Article",
            link="https://example.com/bitcoin",
            published="2026-01-01T10:00:00Z",
            summary="Bitcoin news",
            content=None,
            author=None,
            fetched_at="2026-01-01T12:00:00Z",
        )

        with patch("rss.mcp.server.FeedReader") as mock_reader:
            mock_reader.return_value.search_items.return_value = [mock_item]

            result = rss_search_items(query="Bitcoin")

            assert result["total"] == 1
            assert result["query"] == "Bitcoin"
            assert len(result["items"]) == 1


class TestRssAddFeed:
    """Tests for rss_add_feed tool."""

    def test_adds_new_feed(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should add a new feed successfully."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        mock_feed = Feed(
            feed_id="new-feed-123",
            url="https://example.com/feed.xml",
            title="New Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            mock_manager.return_value.add_feed.return_value = mock_feed

            result = rss_add_feed(
                url="https://example.com/feed.xml",
                title="New Feed",
                category="finance",
            )

            assert result["success"] is True
            assert result["feed"]["feed_id"] == "new-feed-123"

    def test_handles_duplicate_feed(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should handle duplicate feed error."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            from rss.exceptions import FeedAlreadyExistsError

            mock_manager.return_value.add_feed.side_effect = FeedAlreadyExistsError(
                "Feed already exists"
            )

            result = rss_add_feed(
                url="https://example.com/feed.xml",
                title="Duplicate Feed",
                category="finance",
            )

            assert result["success"] is False
            assert result["error_type"] == "FeedAlreadyExistsError"

    def test_handles_invalid_url(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should handle invalid URL error."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            from rss.exceptions import InvalidURLError

            mock_manager.return_value.add_feed.side_effect = InvalidURLError(
                "Invalid URL"
            )

            result = rss_add_feed(
                url="ftp://invalid.com/feed.xml",
                title="Invalid Feed",
                category="finance",
            )

            assert result["success"] is False
            assert result["error_type"] == "InvalidURLError"


class TestRssUpdateFeed:
    """Tests for rss_update_feed tool."""

    def test_updates_feed(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should update feed successfully."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        mock_feed = Feed(
            feed_id="feed-123",
            url="https://example.com/feed.xml",
            title="Updated Title",
            category="economics",
            fetch_interval=FetchInterval.WEEKLY,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            mock_manager.return_value.update_feed.return_value = mock_feed

            result = rss_update_feed(
                feed_id="feed-123",
                title="Updated Title",
                category="economics",
            )

            assert result["success"] is True
            assert result["feed"]["title"] == "Updated Title"

    def test_handles_feed_not_found(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should handle feed not found error."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            from rss.exceptions import FeedNotFoundError

            mock_manager.return_value.update_feed.side_effect = FeedNotFoundError(
                "Feed not found"
            )

            result = rss_update_feed(feed_id="nonexistent", title="New Title")

            assert result["success"] is False
            assert result["error_type"] == "FeedNotFoundError"


class TestRssRemoveFeed:
    """Tests for rss_remove_feed tool."""

    def test_removes_feed(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should remove feed successfully."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            mock_manager.return_value.remove_feed.return_value = None

            result = rss_remove_feed(feed_id="feed-123")

            assert result["success"] is True
            assert result["feed_id"] == "feed-123"

    def test_handles_feed_not_found(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should handle feed not found error."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        with patch("rss.mcp.server.FeedManager") as mock_manager:
            from rss.exceptions import FeedNotFoundError

            mock_manager.return_value.remove_feed.side_effect = FeedNotFoundError(
                "Feed not found"
            )

            result = rss_remove_feed(feed_id="nonexistent")

            assert result["success"] is False
            assert result["error_type"] == "FeedNotFoundError"


class TestRssFetchFeed:
    """Tests for rss_fetch_feed tool."""

    @pytest.mark.asyncio
    async def test_fetches_feed(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should fetch feed successfully."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        mock_result = FetchResult(
            feed_id="feed-123",
            success=True,
            items_count=10,
            new_items=3,
            error_message=None,
        )

        with patch("rss.mcp.server.FeedFetcher") as mock_fetcher:
            mock_fetcher.return_value.fetch_feed = AsyncMock(return_value=mock_result)

            result = await rss_fetch_feed(feed_id="feed-123")

            assert result["success"] is True
            assert result["feed_id"] == "feed-123"
            assert result["items_count"] == 10
            assert result["new_items"] == 3

    @pytest.mark.asyncio
    async def test_handles_fetch_failure(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should handle fetch failure."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        mock_result = FetchResult(
            feed_id="feed-123",
            success=False,
            items_count=0,
            new_items=0,
            error_message="Connection timeout",
        )

        with patch("rss.mcp.server.FeedFetcher") as mock_fetcher:
            mock_fetcher.return_value.fetch_feed = AsyncMock(return_value=mock_result)

            result = await rss_fetch_feed(feed_id="feed-123")

            assert result["success"] is False
            assert result["error_message"] == "Connection timeout"

    @pytest.mark.asyncio
    async def test_handles_feed_not_found_exception(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ) -> None:
        """Should handle FeedNotFoundError exception."""
        monkeypatch.setenv("RSS_DATA_DIR", str(temp_dir))

        with patch("rss.mcp.server.FeedFetcher") as mock_fetcher:
            from rss.exceptions import FeedNotFoundError

            mock_fetcher.return_value.fetch_feed = AsyncMock(
                side_effect=FeedNotFoundError("Feed not found")
            )

            result = await rss_fetch_feed(feed_id="nonexistent")

            assert result["success"] is False
            assert result["error_type"] == "FeedNotFoundError"

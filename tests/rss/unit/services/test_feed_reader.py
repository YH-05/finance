"""Unit tests for FeedReader class."""

from pathlib import Path

import pytest

from rss.services.feed_reader import FeedReader
from rss.storage.json_storage import JSONStorage
from rss.types import (
    Feed,
    FeedItem,
    FeedItemsData,
    FeedsData,
    FetchInterval,
    FetchStatus,
)


def _create_test_feed(
    feed_id: str = "feed-001",
    url: str = "https://example.com/feed.xml",
    title: str = "Test Feed",
    category: str = "finance",
) -> Feed:
    """Create a test feed."""
    return Feed(
        feed_id=feed_id,
        url=url,
        title=title,
        category=category,
        fetch_interval=FetchInterval.DAILY,
        created_at="2026-01-14T10:00:00Z",
        updated_at="2026-01-14T10:00:00Z",
        last_fetched="2026-01-14T10:00:00Z",
        last_status=FetchStatus.SUCCESS,
        enabled=True,
    )


def _create_test_item(
    item_id: str = "item-001",
    title: str = "Test Article",
    link: str = "https://example.com/article",
    published: str | None = "2026-01-14T10:00:00Z",
    summary: str | None = "Test summary",
    content: str | None = "Test content",
    author: str | None = "Test Author",
) -> FeedItem:
    """Create a test feed item."""
    return FeedItem(
        item_id=item_id,
        title=title,
        link=link,
        published=published,
        summary=summary,
        content=content,
        author=author,
        fetched_at="2026-01-14T10:00:00Z",
    )


class TestFeedReaderInit:
    """Test FeedReader initialization."""

    def test_init_success(self, tmp_path: Path) -> None:
        """Test successful initialization."""
        reader = FeedReader(tmp_path)
        assert reader.data_dir == tmp_path
        assert reader.storage is not None

    def test_init_invalid_data_dir_type(self) -> None:
        """Test initialization with invalid data_dir type."""
        with pytest.raises(ValueError, match="data_dir must be a Path object"):
            FeedReader("invalid")  # type: ignore[arg-type]


class TestGetItems:
    """Test get_items method."""

    def test_get_items_empty_storage(self, tmp_path: Path) -> None:
        """Test get_items returns empty list when no items exist."""
        reader = FeedReader(tmp_path)
        result = reader.get_items(feed_id="non-existent")
        assert result == []

    def test_get_items_single_feed(self, tmp_path: Path) -> None:
        """Test get_items returns items from a single feed."""
        # Setup storage with items
        storage = JSONStorage(tmp_path)
        feed_id = "feed-001"
        items = [
            _create_test_item(item_id="item-001", title="Article 1"),
            _create_test_item(item_id="item-002", title="Article 2"),
        ]
        storage.save_items(
            feed_id, FeedItemsData(version="1.0", feed_id=feed_id, items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.get_items(feed_id=feed_id)

        assert len(result) == 2
        assert result[0].title == "Article 1"
        assert result[1].title == "Article 2"

    def test_get_items_sorted_by_published_desc(self, tmp_path: Path) -> None:
        """Test get_items returns items sorted by published date descending."""
        storage = JSONStorage(tmp_path)
        feed_id = "feed-001"
        items = [
            _create_test_item(item_id="item-001", published="2026-01-10T10:00:00Z"),
            _create_test_item(item_id="item-002", published="2026-01-14T10:00:00Z"),
            _create_test_item(item_id="item-003", published="2026-01-12T10:00:00Z"),
        ]
        storage.save_items(
            feed_id, FeedItemsData(version="1.0", feed_id=feed_id, items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.get_items(feed_id=feed_id)

        assert len(result) == 3
        assert result[0].published == "2026-01-14T10:00:00Z"
        assert result[1].published == "2026-01-12T10:00:00Z"
        assert result[2].published == "2026-01-10T10:00:00Z"

    def test_get_items_with_limit(self, tmp_path: Path) -> None:
        """Test get_items respects limit parameter."""
        storage = JSONStorage(tmp_path)
        feed_id = "feed-001"
        items = [
            _create_test_item(
                item_id=f"item-{i:03d}", published=f"2026-01-{10+i:02d}T10:00:00Z"
            )
            for i in range(5)
        ]
        storage.save_items(
            feed_id, FeedItemsData(version="1.0", feed_id=feed_id, items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.get_items(feed_id=feed_id, limit=2)

        assert len(result) == 2

    def test_get_items_with_offset(self, tmp_path: Path) -> None:
        """Test get_items respects offset parameter."""
        storage = JSONStorage(tmp_path)
        feed_id = "feed-001"
        items = [
            _create_test_item(item_id="item-001", published="2026-01-14T10:00:00Z"),
            _create_test_item(item_id="item-002", published="2026-01-13T10:00:00Z"),
            _create_test_item(item_id="item-003", published="2026-01-12T10:00:00Z"),
        ]
        storage.save_items(
            feed_id, FeedItemsData(version="1.0", feed_id=feed_id, items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.get_items(feed_id=feed_id, offset=1)

        assert len(result) == 2
        assert result[0].published == "2026-01-13T10:00:00Z"

    def test_get_items_with_limit_and_offset(self, tmp_path: Path) -> None:
        """Test get_items respects both limit and offset parameters."""
        storage = JSONStorage(tmp_path)
        feed_id = "feed-001"
        items = [
            _create_test_item(
                item_id=f"item-{i:03d}", published=f"2026-01-{14-i:02d}T10:00:00Z"
            )
            for i in range(5)
        ]
        storage.save_items(
            feed_id, FeedItemsData(version="1.0", feed_id=feed_id, items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.get_items(feed_id=feed_id, limit=2, offset=1)

        assert len(result) == 2
        # After sorting desc and offset=1, should get 2nd and 3rd items
        assert result[0].published == "2026-01-13T10:00:00Z"
        assert result[1].published == "2026-01-12T10:00:00Z"

    def test_get_items_all_feeds(self, tmp_path: Path) -> None:
        """Test get_items with feed_id=None returns items from all feeds."""
        storage = JSONStorage(tmp_path)

        # Setup feeds registry
        feed1 = _create_test_feed(feed_id="feed-001", category="finance")
        feed2 = _create_test_feed(feed_id="feed-002", category="economics")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed1, feed2]))

        # Setup items for each feed
        items1 = [_create_test_item(item_id="item-001", title="Finance Article")]
        items2 = [_create_test_item(item_id="item-002", title="Economics Article")]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items1)
        )
        storage.save_items(
            "feed-002", FeedItemsData(version="1.0", feed_id="feed-002", items=items2)
        )

        reader = FeedReader(tmp_path)
        result = reader.get_items(feed_id=None)

        assert len(result) == 2
        titles = {item.title for item in result}
        assert "Finance Article" in titles
        assert "Economics Article" in titles

    def test_get_items_handles_none_published(self, tmp_path: Path) -> None:
        """Test get_items handles items with None published date."""
        storage = JSONStorage(tmp_path)
        feed_id = "feed-001"
        items = [
            _create_test_item(item_id="item-001", published="2026-01-14T10:00:00Z"),
            _create_test_item(item_id="item-002", published=None),
            _create_test_item(item_id="item-003", published="2026-01-12T10:00:00Z"),
        ]
        storage.save_items(
            feed_id, FeedItemsData(version="1.0", feed_id=feed_id, items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.get_items(feed_id=feed_id)

        # None published should be sorted to the end
        assert len(result) == 3
        assert result[0].published == "2026-01-14T10:00:00Z"
        assert result[1].published == "2026-01-12T10:00:00Z"
        assert result[2].published is None


class TestSearchItems:
    """Test search_items method."""

    def test_search_items_empty_storage(self, tmp_path: Path) -> None:
        """Test search_items returns empty list when no items exist."""
        reader = FeedReader(tmp_path)
        result = reader.search_items(query="test")
        assert result == []

    def test_search_items_title_match(self, tmp_path: Path) -> None:
        """Test search_items matches in title field."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [
            _create_test_item(item_id="item-001", title="Bitcoin reaches new high"),
            _create_test_item(item_id="item-002", title="Stock market update"),
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="Bitcoin")

        assert len(result) == 1
        assert result[0].title == "Bitcoin reaches new high"

    def test_search_items_summary_match(self, tmp_path: Path) -> None:
        """Test search_items matches in summary field."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [
            _create_test_item(
                item_id="item-001", title="Article 1", summary="Bitcoin price analysis"
            ),
            _create_test_item(
                item_id="item-002", title="Article 2", summary="Weather forecast"
            ),
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="Bitcoin")

        assert len(result) == 1
        assert result[0].item_id == "item-001"

    def test_search_items_content_match(self, tmp_path: Path) -> None:
        """Test search_items matches in content field."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [
            _create_test_item(
                item_id="item-001", content="Full article about cryptocurrency trading"
            ),
            _create_test_item(
                item_id="item-002", content="Weather report for tomorrow"
            ),
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="cryptocurrency")

        assert len(result) == 1
        assert result[0].item_id == "item-001"

    def test_search_items_case_insensitive(self, tmp_path: Path) -> None:
        """Test search_items is case insensitive."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [_create_test_item(item_id="item-001", title="BITCOIN news")]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="bitcoin")

        assert len(result) == 1

    def test_search_items_with_fields(self, tmp_path: Path) -> None:
        """Test search_items respects fields parameter."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [
            _create_test_item(
                item_id="item-001",
                title="Regular article",
                summary="Bitcoin mentioned in summary",
            ),
            _create_test_item(
                item_id="item-002",
                title="Bitcoin in title",
                summary="No match here",
            ),
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        # Only search in title field
        result = reader.search_items(query="Bitcoin", fields=["title"])

        assert len(result) == 1
        assert result[0].item_id == "item-002"

    def test_search_items_with_category_filter(self, tmp_path: Path) -> None:
        """Test search_items respects category filter."""
        storage = JSONStorage(tmp_path)
        feed1 = _create_test_feed(feed_id="feed-001", category="finance")
        feed2 = _create_test_feed(feed_id="feed-002", category="economics")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed1, feed2]))

        items1 = [
            _create_test_item(item_id="item-001", title="Bitcoin finance article")
        ]
        items2 = [
            _create_test_item(item_id="item-002", title="Bitcoin economics article")
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items1)
        )
        storage.save_items(
            "feed-002", FeedItemsData(version="1.0", feed_id="feed-002", items=items2)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="Bitcoin", category="finance")

        assert len(result) == 1
        assert result[0].item_id == "item-001"

    def test_search_items_with_limit(self, tmp_path: Path) -> None:
        """Test search_items respects limit parameter."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [
            _create_test_item(item_id=f"item-{i:03d}", title=f"Bitcoin article {i}")
            for i in range(5)
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="Bitcoin", limit=2)

        assert len(result) == 2

    def test_search_items_sorted_by_published_desc(self, tmp_path: Path) -> None:
        """Test search_items returns results sorted by published date descending."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [
            _create_test_item(
                item_id="item-001",
                title="Bitcoin old",
                published="2026-01-10T10:00:00Z",
            ),
            _create_test_item(
                item_id="item-002",
                title="Bitcoin new",
                published="2026-01-14T10:00:00Z",
            ),
            _create_test_item(
                item_id="item-003",
                title="Bitcoin mid",
                published="2026-01-12T10:00:00Z",
            ),
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="Bitcoin")

        assert len(result) == 3
        assert result[0].published == "2026-01-14T10:00:00Z"
        assert result[1].published == "2026-01-12T10:00:00Z"
        assert result[2].published == "2026-01-10T10:00:00Z"

    def test_search_items_partial_match(self, tmp_path: Path) -> None:
        """Test search_items supports partial matching."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [
            _create_test_item(item_id="item-001", title="Cryptocurrency trading guide")
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="crypto")

        assert len(result) == 1

    def test_search_items_handles_none_fields(self, tmp_path: Path) -> None:
        """Test search_items handles items with None summary/content."""
        storage = JSONStorage(tmp_path)
        feed = _create_test_feed(feed_id="feed-001")
        storage.save_feeds(FeedsData(version="1.0", feeds=[feed]))

        items = [
            _create_test_item(
                item_id="item-001", title="Bitcoin article", summary=None, content=None
            ),
        ]
        storage.save_items(
            "feed-001", FeedItemsData(version="1.0", feed_id="feed-001", items=items)
        )

        reader = FeedReader(tmp_path)
        result = reader.search_items(query="Bitcoin")

        assert len(result) == 1

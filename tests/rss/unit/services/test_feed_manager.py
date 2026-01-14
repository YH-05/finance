"""Unit tests for FeedManager class."""

import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from rss.exceptions import FeedAlreadyExistsError, FeedFetchError, FeedNotFoundError
from rss.services.feed_manager import FeedManager
from rss.types import (
    FetchInterval,
    FetchStatus,
)


class TestFeedManagerInit:
    """Test FeedManager initialization."""

    def test_init_success(self, tmp_path: Path) -> None:
        """Test successful initialization."""
        manager = FeedManager(tmp_path)
        assert manager.data_dir == tmp_path
        assert manager.storage is not None
        assert manager.validator is not None

    def test_init_invalid_data_dir_type(self) -> None:
        """Test initialization with invalid data_dir type."""
        with pytest.raises(ValueError, match="data_dir must be a Path object"):
            FeedManager("invalid")  # type: ignore[arg-type]


class TestAddFeed:
    """Test add_feed method."""

    def test_add_feed_success(self, tmp_path: Path) -> None:
        """Test adding a feed successfully."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        assert feed.url == "https://example.com/feed.xml"
        assert feed.title == "Example Feed"
        assert feed.category == "finance"
        assert feed.fetch_interval == FetchInterval.DAILY
        assert feed.enabled is True
        assert feed.last_status == FetchStatus.PENDING
        assert feed.last_fetched is None

    def test_add_feed_generates_uuid(self, tmp_path: Path) -> None:
        """Test that feed_id is a valid UUID v4."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        # Verify UUID v4 format
        parsed_uuid = uuid.UUID(feed.feed_id)
        assert parsed_uuid.version == 4

    def test_add_feed_saves_to_storage(self, tmp_path: Path) -> None:
        """Test that feed is saved to feeds.json."""
        manager = FeedManager(tmp_path)

        manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        # Verify file exists
        feeds_file = tmp_path / "feeds.json"
        assert feeds_file.exists()

        # Verify can be loaded
        feeds_data = manager.storage.load_feeds()
        assert len(feeds_data.feeds) == 1
        assert feeds_data.feeds[0].url == "https://example.com/feed.xml"

    def test_add_feed_validates_url(self, tmp_path: Path) -> None:
        """Test that URL validation is performed."""
        manager = FeedManager(tmp_path)

        from rss.exceptions import InvalidURLError

        # Invalid scheme
        with pytest.raises(InvalidURLError):
            manager.add_feed(
                url="ftp://example.com/feed.xml",
                title="Example Feed",
                category="finance",
            )

        # Empty URL
        with pytest.raises(InvalidURLError):
            manager.add_feed(
                url="",
                title="Example Feed",
                category="finance",
            )

    def test_add_feed_duplicate_url_raises_error(self, tmp_path: Path) -> None:
        """Test that duplicate URL raises FeedAlreadyExistsError."""
        manager = FeedManager(tmp_path)

        # Add first feed
        manager.add_feed(
            url="https://example.com/feed.xml",
            title="First Feed",
            category="finance",
        )

        # Try to add duplicate
        with pytest.raises(FeedAlreadyExistsError, match="already exists"):
            manager.add_feed(
                url="https://example.com/feed.xml",
                title="Second Feed",
                category="finance",
            )

    def test_add_feed_with_validate_url_success(self, tmp_path: Path) -> None:
        """Test adding feed with URL reachability check."""
        manager = FeedManager(tmp_path)

        # Mock httpx.Client
        with patch("rss.services.feed_manager.httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.head.return_value = (
                mock_response
            )

            feed = manager.add_feed(
                url="https://example.com/feed.xml",
                title="Example Feed",
                category="finance",
                validate_url=True,
            )

            assert feed.url == "https://example.com/feed.xml"
            mock_client.return_value.__enter__.return_value.head.assert_called_once()

    def test_add_feed_with_validate_url_unreachable(self, tmp_path: Path) -> None:
        """Test that unreachable URL raises FeedFetchError."""
        manager = FeedManager(tmp_path)

        # Mock httpx.Client to raise timeout
        with patch("rss.services.feed_manager.httpx.Client") as mock_client:
            import httpx

            mock_client.return_value.__enter__.return_value.head.side_effect = (
                httpx.TimeoutException("Connection timeout")
            )

            with pytest.raises(FeedFetchError, match="timeout"):
                manager.add_feed(
                    url="https://example.com/feed.xml",
                    title="Example Feed",
                    category="finance",
                    validate_url=True,
                )

    def test_add_feed_validates_title(self, tmp_path: Path) -> None:
        """Test that title validation is performed."""
        manager = FeedManager(tmp_path)

        # Empty title
        with pytest.raises(ValueError, match="Title must be"):
            manager.add_feed(
                url="https://example.com/feed.xml",
                title="",
                category="finance",
            )

        # Too long title (> 200 chars)
        with pytest.raises(ValueError, match="Title must be"):
            manager.add_feed(
                url="https://example.com/feed.xml",
                title="x" * 201,
                category="finance",
            )

    def test_add_feed_validates_category(self, tmp_path: Path) -> None:
        """Test that category validation is performed."""
        manager = FeedManager(tmp_path)

        # Empty category
        with pytest.raises(ValueError, match="Category must be"):
            manager.add_feed(
                url="https://example.com/feed.xml",
                title="Example Feed",
                category="",
            )

        # Too long category (> 50 chars)
        with pytest.raises(ValueError, match="Category must be"):
            manager.add_feed(
                url="https://example.com/feed.xml",
                title="Example Feed",
                category="x" * 51,
            )

    def test_add_feed_with_custom_options(self, tmp_path: Path) -> None:
        """Test adding feed with custom options."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
            fetch_interval=FetchInterval.WEEKLY,
            enabled=False,
        )

        assert feed.fetch_interval == FetchInterval.WEEKLY
        assert feed.enabled is False


class TestListFeeds:
    """Test list_feeds method."""

    def test_list_feeds_empty(self, tmp_path: Path) -> None:
        """Test listing feeds when no feeds exist."""
        manager = FeedManager(tmp_path)

        feeds = manager.list_feeds()

        assert feeds == []

    def test_list_feeds_returns_all(self, tmp_path: Path) -> None:
        """Test listing all feeds."""
        manager = FeedManager(tmp_path)

        # Add multiple feeds
        manager.add_feed(
            url="https://example.com/feed1.xml",
            title="Feed 1",
            category="finance",
        )
        manager.add_feed(
            url="https://example.com/feed2.xml",
            title="Feed 2",
            category="tech",
        )

        feeds = manager.list_feeds()

        assert len(feeds) == 2

    def test_list_feeds_filter_by_category(self, tmp_path: Path) -> None:
        """Test filtering feeds by category."""
        manager = FeedManager(tmp_path)

        # Add feeds in different categories
        manager.add_feed(
            url="https://example.com/feed1.xml",
            title="Feed 1",
            category="finance",
        )
        manager.add_feed(
            url="https://example.com/feed2.xml",
            title="Feed 2",
            category="tech",
        )
        manager.add_feed(
            url="https://example.com/feed3.xml",
            title="Feed 3",
            category="finance",
        )

        finance_feeds = manager.list_feeds(category="finance")
        tech_feeds = manager.list_feeds(category="tech")

        assert len(finance_feeds) == 2
        assert len(tech_feeds) == 1
        assert all(f.category == "finance" for f in finance_feeds)
        assert all(f.category == "tech" for f in tech_feeds)

    def test_list_feeds_enabled_only(self, tmp_path: Path) -> None:
        """Test filtering enabled feeds only."""
        manager = FeedManager(tmp_path)

        # Add enabled and disabled feeds
        manager.add_feed(
            url="https://example.com/feed1.xml",
            title="Feed 1",
            category="finance",
            enabled=True,
        )
        manager.add_feed(
            url="https://example.com/feed2.xml",
            title="Feed 2",
            category="finance",
            enabled=False,
        )
        manager.add_feed(
            url="https://example.com/feed3.xml",
            title="Feed 3",
            category="finance",
            enabled=True,
        )

        all_feeds = manager.list_feeds()
        enabled_feeds = manager.list_feeds(enabled_only=True)

        assert len(all_feeds) == 3
        assert len(enabled_feeds) == 2
        assert all(f.enabled for f in enabled_feeds)

    def test_list_feeds_combined_filters(self, tmp_path: Path) -> None:
        """Test combining category and enabled filters."""
        manager = FeedManager(tmp_path)

        # Add various feeds
        manager.add_feed(
            url="https://example.com/feed1.xml",
            title="Feed 1",
            category="finance",
            enabled=True,
        )
        manager.add_feed(
            url="https://example.com/feed2.xml",
            title="Feed 2",
            category="finance",
            enabled=False,
        )
        manager.add_feed(
            url="https://example.com/feed3.xml",
            title="Feed 3",
            category="tech",
            enabled=True,
        )

        filtered = manager.list_feeds(category="finance", enabled_only=True)

        assert len(filtered) == 1
        assert filtered[0].title == "Feed 1"


class TestGetFeed:
    """Test get_feed method."""

    def test_get_feed_success(self, tmp_path: Path) -> None:
        """Test getting a feed by ID."""
        manager = FeedManager(tmp_path)

        added_feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        retrieved = manager.get_feed(added_feed.feed_id)

        assert retrieved.feed_id == added_feed.feed_id
        assert retrieved.url == added_feed.url
        assert retrieved.title == added_feed.title

    def test_get_feed_not_found(self, tmp_path: Path) -> None:
        """Test that non-existent feed_id raises FeedNotFoundError."""
        manager = FeedManager(tmp_path)

        with pytest.raises(FeedNotFoundError, match="not found"):
            manager.get_feed("non-existent-id")


class TestUpdateFeed:
    """Test update_feed method."""

    def test_update_feed_title(self, tmp_path: Path) -> None:
        """Test updating feed title."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Original Title",
            category="finance",
        )

        updated = manager.update_feed(feed.feed_id, title="New Title")

        assert updated.title == "New Title"

        # Verify persisted
        retrieved = manager.get_feed(feed.feed_id)
        assert retrieved.title == "New Title"

    def test_update_feed_category(self, tmp_path: Path) -> None:
        """Test updating feed category."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        updated = manager.update_feed(feed.feed_id, category="tech")

        assert updated.category == "tech"

    def test_update_feed_fetch_interval(self, tmp_path: Path) -> None:
        """Test updating feed fetch interval."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
        )

        updated = manager.update_feed(feed.feed_id, fetch_interval=FetchInterval.WEEKLY)

        assert updated.fetch_interval == FetchInterval.WEEKLY

    def test_update_feed_enabled(self, tmp_path: Path) -> None:
        """Test updating feed enabled status."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
            enabled=True,
        )

        updated = manager.update_feed(feed.feed_id, enabled=False)

        assert updated.enabled is False

    def test_update_feed_updates_timestamp(self, tmp_path: Path) -> None:
        """Test that updated_at is updated on changes."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )
        original_updated_at = feed.updated_at

        # Wait a tiny bit to ensure time difference
        import time

        time.sleep(0.01)

        updated = manager.update_feed(feed.feed_id, title="New Title")

        assert updated.updated_at != original_updated_at
        # Verify new timestamp is later
        original_dt = datetime.fromisoformat(original_updated_at.replace("Z", "+00:00"))
        updated_dt = datetime.fromisoformat(updated.updated_at.replace("Z", "+00:00"))
        assert updated_dt > original_dt

    def test_update_feed_not_found(self, tmp_path: Path) -> None:
        """Test that updating non-existent feed raises FeedNotFoundError."""
        manager = FeedManager(tmp_path)

        with pytest.raises(FeedNotFoundError, match="not found"):
            manager.update_feed("non-existent-id", title="New Title")

    def test_update_feed_validates_title(self, tmp_path: Path) -> None:
        """Test that title validation is performed on update."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        with pytest.raises(ValueError, match="Title must be"):
            manager.update_feed(feed.feed_id, title="")

    def test_update_feed_validates_category(self, tmp_path: Path) -> None:
        """Test that category validation is performed on update."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        with pytest.raises(ValueError, match="Category must be"):
            manager.update_feed(feed.feed_id, category="")

    def test_update_feed_multiple_fields(self, tmp_path: Path) -> None:
        """Test updating multiple fields at once."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Original Title",
            category="finance",
            enabled=True,
        )

        updated = manager.update_feed(
            feed.feed_id,
            title="New Title",
            category="tech",
            enabled=False,
        )

        assert updated.title == "New Title"
        assert updated.category == "tech"
        assert updated.enabled is False


class TestRemoveFeed:
    """Test remove_feed method."""

    def test_remove_feed_success(self, tmp_path: Path) -> None:
        """Test removing a feed."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        manager.remove_feed(feed.feed_id)

        # Verify removed
        with pytest.raises(FeedNotFoundError):
            manager.get_feed(feed.feed_id)

        # Verify list is empty
        assert manager.list_feeds() == []

    def test_remove_feed_deletes_items_directory(self, tmp_path: Path) -> None:
        """Test that items directory is deleted when feed is removed."""
        manager = FeedManager(tmp_path)

        feed = manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        # Create items directory with some data
        items_dir = tmp_path / feed.feed_id
        items_dir.mkdir(parents=True, exist_ok=True)
        items_file = items_dir / "items.json"
        items_file.write_text('{"version": "1.0", "items": []}', encoding="utf-8")

        assert items_dir.exists()

        manager.remove_feed(feed.feed_id)

        # Verify items directory is deleted
        assert not items_dir.exists()

    def test_remove_feed_not_found(self, tmp_path: Path) -> None:
        """Test that removing non-existent feed raises FeedNotFoundError."""
        manager = FeedManager(tmp_path)

        with pytest.raises(FeedNotFoundError, match="not found"):
            manager.remove_feed("non-existent-id")

    def test_remove_feed_preserves_other_feeds(self, tmp_path: Path) -> None:
        """Test that removing a feed doesn't affect other feeds."""
        manager = FeedManager(tmp_path)

        feed1 = manager.add_feed(
            url="https://example.com/feed1.xml",
            title="Feed 1",
            category="finance",
        )
        feed2 = manager.add_feed(
            url="https://example.com/feed2.xml",
            title="Feed 2",
            category="finance",
        )

        manager.remove_feed(feed1.feed_id)

        # Feed 2 should still exist
        remaining = manager.list_feeds()
        assert len(remaining) == 1
        assert remaining[0].feed_id == feed2.feed_id


class TestLogging:
    """Test structured logging behavior."""

    def test_add_feed_logs_info(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that adding feed logs at INFO level."""
        manager = FeedManager(tmp_path)
        manager.add_feed(
            url="https://example.com/feed.xml",
            title="Example Feed",
            category="finance",
        )

        # Check for info-level log about successful registration in captured output
        captured = capsys.readouterr()
        # Structured logging outputs to stdout
        assert "registered" in captured.out.lower() or "info" in captured.out.lower()

    def test_duplicate_feed_logs_warning(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that duplicate feed detection logs at WARNING level."""
        manager = FeedManager(tmp_path)
        manager.add_feed(
            url="https://example.com/feed.xml",
            title="First Feed",
            category="finance",
        )

        # Try to add duplicate
        with pytest.raises(FeedAlreadyExistsError):
            manager.add_feed(
                url="https://example.com/feed.xml",
                title="Second Feed",
                category="finance",
            )

        # Check for warning-level log about duplicate in captured output
        captured = capsys.readouterr()
        assert "duplicate" in captured.out.lower() or "warning" in captured.out.lower()

    def test_feed_not_found_logs_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that feed not found logs at ERROR level."""
        manager = FeedManager(tmp_path)

        with pytest.raises(FeedNotFoundError):
            manager.get_feed("non-existent-id")

        # Check for error-level log in captured output
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "error" in captured.out.lower()

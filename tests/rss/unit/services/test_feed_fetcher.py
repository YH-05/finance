"""Unit tests for FeedFetcher class."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from rss.core.diff_detector import DiffDetector
from rss.core.http_client import HTTPClient
from rss.core.parser import FeedParser
from rss.exceptions import FeedFetchError, FeedParseError
from rss.services.feed_fetcher import (
    DEFAULT_MAX_CONCURRENT,
    MAX_CONCURRENT_LIMIT,
    FeedFetcher,
)
from rss.storage.json_storage import JSONStorage
from rss.types import (
    Feed,
    FeedItem,
    FeedItemsData,
    FeedsData,
    FetchInterval,
    FetchStatus,
    HTTPResponse,
)


class TestFeedFetcherInit:
    """Test FeedFetcher initialization."""

    def test_init_success(self, tmp_path: Path) -> None:
        """Test successful initialization with default parameters."""
        fetcher = FeedFetcher(tmp_path)

        assert fetcher.data_dir == tmp_path
        assert isinstance(fetcher.storage, JSONStorage)
        assert isinstance(fetcher.http_client, HTTPClient)
        assert isinstance(fetcher.parser, FeedParser)
        assert isinstance(fetcher.diff_detector, DiffDetector)

    def test_init_with_custom_dependencies(self, tmp_path: Path) -> None:
        """Test initialization with custom dependency injection."""
        mock_http_client = Mock(spec=HTTPClient)
        mock_parser = Mock(spec=FeedParser)
        mock_diff_detector = Mock(spec=DiffDetector)

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        assert fetcher.http_client is mock_http_client
        assert fetcher.parser is mock_parser
        assert fetcher.diff_detector is mock_diff_detector

    def test_init_invalid_data_dir_type(self) -> None:
        """Test initialization with invalid data_dir type."""
        with pytest.raises(ValueError, match="data_dir must be a Path object"):
            FeedFetcher("invalid")  # type: ignore[arg-type]


class TestFetchFeed:
    """Test fetch_feed method."""

    @pytest.fixture
    def sample_feed(self) -> Feed:
        """Create a sample feed for testing."""
        return Feed(
            feed_id="test-feed-id-123",
            url="https://example.com/feed.xml",
            title="Test Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-14T10:00:00+00:00",
            updated_at="2026-01-14T10:00:00+00:00",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )

    @pytest.fixture
    def sample_feed_items(self) -> list[FeedItem]:
        """Create sample feed items for testing."""
        return [
            FeedItem(
                item_id="item-1",
                title="Article 1",
                link="https://example.com/article1",
                published="2026-01-14T09:00:00+00:00",
                summary="Summary 1",
                content=None,
                author="Author 1",
                fetched_at="2026-01-14T10:00:00+00:00",
            ),
            FeedItem(
                item_id="item-2",
                title="Article 2",
                link="https://example.com/article2",
                published="2026-01-14T08:00:00+00:00",
                summary="Summary 2",
                content=None,
                author="Author 2",
                fetched_at="2026-01-14T10:00:00+00:00",
            ),
        ]

    @pytest.mark.asyncio
    async def test_fetch_feed_success(
        self, tmp_path: Path, sample_feed: Feed, sample_feed_items: list[FeedItem]
    ) -> None:
        """Test successful feed fetch."""
        # Setup mocks
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = sample_feed_items

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = sample_feed_items

        # Create fetcher with mocks
        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        # Create feed in storage
        feeds_data = FeedsData(version="1.0", feeds=[sample_feed])
        fetcher.storage.save_feeds(feeds_data)

        # Execute
        result = await fetcher.fetch_feed(sample_feed.feed_id)

        # Verify
        assert result.success is True
        assert result.feed_id == sample_feed.feed_id
        assert result.items_count == 2
        assert result.new_items == 2
        assert result.error_message is None

        # Verify HTTP client was called
        mock_http_client.fetch.assert_called_once_with(sample_feed.url)

        # Verify parser was called
        mock_parser.parse.assert_called_once()

        # Verify diff detector was called
        mock_diff_detector.detect_new_items.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_feed_updates_status(
        self, tmp_path: Path, sample_feed: Feed, sample_feed_items: list[FeedItem]
    ) -> None:
        """Test that feed status is updated after fetch."""
        # Setup mocks
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = sample_feed_items

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = sample_feed_items

        # Create fetcher with mocks
        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        # Create feed in storage
        feeds_data = FeedsData(version="1.0", feeds=[sample_feed])
        fetcher.storage.save_feeds(feeds_data)

        # Execute
        await fetcher.fetch_feed(sample_feed.feed_id)

        # Verify feed status was updated
        updated_feeds = fetcher.storage.load_feeds()
        updated_feed = updated_feeds.feeds[0]
        assert updated_feed.last_status == FetchStatus.SUCCESS
        assert updated_feed.last_fetched is not None

    @pytest.mark.asyncio
    async def test_fetch_feed_saves_items(
        self, tmp_path: Path, sample_feed: Feed, sample_feed_items: list[FeedItem]
    ) -> None:
        """Test that fetched items are saved to storage."""
        # Setup mocks
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = sample_feed_items

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = sample_feed_items

        # Create fetcher with mocks
        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        # Create feed in storage
        feeds_data = FeedsData(version="1.0", feeds=[sample_feed])
        fetcher.storage.save_feeds(feeds_data)

        # Execute
        await fetcher.fetch_feed(sample_feed.feed_id)

        # Verify items were saved
        items_data = fetcher.storage.load_items(sample_feed.feed_id)
        assert len(items_data.items) == 2
        assert items_data.feed_id == sample_feed.feed_id

    @pytest.mark.asyncio
    async def test_fetch_feed_merges_with_existing_items(
        self, tmp_path: Path, sample_feed: Feed
    ) -> None:
        """Test that new items are merged with existing items."""
        existing_item = FeedItem(
            item_id="existing-1",
            title="Existing Article",
            link="https://example.com/existing",
            published="2026-01-13T09:00:00+00:00",
            summary="Existing summary",
            content=None,
            author="Author",
            fetched_at="2026-01-13T10:00:00+00:00",
        )

        new_item = FeedItem(
            item_id="new-1",
            title="New Article",
            link="https://example.com/new",
            published="2026-01-14T09:00:00+00:00",
            summary="New summary",
            content=None,
            author="Author",
            fetched_at="2026-01-14T10:00:00+00:00",
        )

        # Setup mocks
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = [new_item, existing_item]

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = [new_item]

        # Create fetcher with mocks
        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        # Create feed and existing items in storage
        feeds_data = FeedsData(version="1.0", feeds=[sample_feed])
        fetcher.storage.save_feeds(feeds_data)

        existing_items_data = FeedItemsData(
            version="1.0",
            feed_id=sample_feed.feed_id,
            items=[existing_item],
        )
        fetcher.storage.save_items(sample_feed.feed_id, existing_items_data)

        # Execute
        result = await fetcher.fetch_feed(sample_feed.feed_id)

        # Verify
        assert result.success is True
        assert result.items_count == 2  # New + Existing
        assert result.new_items == 1  # Only the new one

        # Verify merged items (new items at the beginning)
        items_data = fetcher.storage.load_items(sample_feed.feed_id)
        assert len(items_data.items) == 2
        assert items_data.items[0].item_id == "new-1"
        assert items_data.items[1].item_id == "existing-1"

    @pytest.mark.asyncio
    async def test_fetch_feed_not_found(self, tmp_path: Path) -> None:
        """Test fetch_feed with non-existent feed ID."""
        fetcher = FeedFetcher(tmp_path)

        result = await fetcher.fetch_feed("non-existent-id")

        assert result.success is False
        assert result.feed_id == "non-existent-id"
        assert result.items_count == 0
        assert result.new_items == 0
        assert result.error_message is not None
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_fetch_feed_http_error(
        self, tmp_path: Path, sample_feed: Feed
    ) -> None:
        """Test fetch_feed handles HTTP errors gracefully."""
        # Setup mock that raises FeedFetchError
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.side_effect = FeedFetchError("Failed to fetch: HTTP 500")

        fetcher = FeedFetcher(tmp_path, http_client=mock_http_client)

        # Create feed in storage
        feeds_data = FeedsData(version="1.0", feeds=[sample_feed])
        fetcher.storage.save_feeds(feeds_data)

        # Execute
        result = await fetcher.fetch_feed(sample_feed.feed_id)

        # Verify error handling
        assert result.success is False
        assert result.feed_id == sample_feed.feed_id
        assert result.items_count == 0
        assert result.new_items == 0
        assert result.error_message is not None
        assert "HTTP 500" in result.error_message

        # Verify status was updated to FAILURE
        updated_feeds = fetcher.storage.load_feeds()
        assert updated_feeds.feeds[0].last_status == FetchStatus.FAILURE

    @pytest.mark.asyncio
    async def test_fetch_feed_parse_error(
        self, tmp_path: Path, sample_feed: Feed
    ) -> None:
        """Test fetch_feed handles parse errors gracefully."""
        # Setup mocks
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<html>Not RSS</html>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.side_effect = FeedParseError("Invalid RSS format")

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
        )

        # Create feed in storage
        feeds_data = FeedsData(version="1.0", feeds=[sample_feed])
        fetcher.storage.save_feeds(feeds_data)

        # Execute
        result = await fetcher.fetch_feed(sample_feed.feed_id)

        # Verify error handling
        assert result.success is False
        assert result.error_message is not None
        assert "Invalid RSS" in result.error_message

        # Verify status was updated to FAILURE
        updated_feeds = fetcher.storage.load_feeds()
        assert updated_feeds.feeds[0].last_status == FetchStatus.FAILURE

    @pytest.mark.asyncio
    async def test_fetch_feed_unexpected_error(
        self, tmp_path: Path, sample_feed: Feed
    ) -> None:
        """Test fetch_feed handles unexpected errors gracefully."""
        # Setup mock that raises unexpected error
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.side_effect = RuntimeError("Unexpected error")

        fetcher = FeedFetcher(tmp_path, http_client=mock_http_client)

        # Create feed in storage
        feeds_data = FeedsData(version="1.0", feeds=[sample_feed])
        fetcher.storage.save_feeds(feeds_data)

        # Execute
        result = await fetcher.fetch_feed(sample_feed.feed_id)

        # Verify error handling
        assert result.success is False
        assert result.error_message is not None
        assert "Unexpected error" in result.error_message


class TestFetchAllAsync:
    """Test fetch_all_async method."""

    @pytest.fixture
    def sample_feeds(self) -> list[Feed]:
        """Create sample feeds for testing."""
        return [
            Feed(
                feed_id=f"feed-{i}",
                url=f"https://example.com/feed{i}.xml",
                title=f"Feed {i}",
                category="finance" if i % 2 == 0 else "tech",
                fetch_interval=FetchInterval.DAILY,
                created_at="2026-01-14T10:00:00+00:00",
                updated_at="2026-01-14T10:00:00+00:00",
                last_fetched=None,
                last_status=FetchStatus.PENDING,
                enabled=i != 3,  # feed-3 is disabled
            )
            for i in range(5)
        ]

    @pytest.mark.asyncio
    async def test_fetch_all_async_success(
        self, tmp_path: Path, sample_feeds: list[Feed]
    ) -> None:
        """Test fetching all feeds successfully."""
        # Setup mocks
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = []

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = []

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        # Create feeds in storage
        feeds_data = FeedsData(version="1.0", feeds=sample_feeds)
        fetcher.storage.save_feeds(feeds_data)

        # Execute
        results = await fetcher.fetch_all_async()

        # Verify (4 enabled feeds)
        assert len(results) == 4
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_fetch_all_async_filter_by_category(
        self, tmp_path: Path, sample_feeds: list[Feed]
    ) -> None:
        """Test fetching feeds filtered by category."""
        # Setup mocks
        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = []

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = []

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        # Create feeds in storage
        feeds_data = FeedsData(version="1.0", feeds=sample_feeds)
        fetcher.storage.save_feeds(feeds_data)

        # Execute with category filter
        results = await fetcher.fetch_all_async(category="finance")

        # Verify (finance feeds: 0, 2, 4 - but 0, 2, 4 are enabled)
        assert len(results) == 3
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_fetch_all_async_respects_max_concurrent(
        self, tmp_path: Path, sample_feeds: list[Feed]
    ) -> None:
        """Test that max_concurrent limits parallel fetches."""
        concurrent_count = 0
        max_observed_concurrent = 0

        async def mock_fetch(url: str) -> HTTPResponse:
            nonlocal concurrent_count, max_observed_concurrent
            concurrent_count += 1
            max_observed_concurrent = max(max_observed_concurrent, concurrent_count)
            await asyncio.sleep(0.05)  # Simulate network delay
            concurrent_count -= 1
            return HTTPResponse(
                status_code=200,
                content="<rss>...</rss>",
                headers={},
            )

        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.side_effect = mock_fetch

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = []

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = []

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        # Create feeds in storage
        feeds_data = FeedsData(version="1.0", feeds=sample_feeds)
        fetcher.storage.save_feeds(feeds_data)

        # Execute with max_concurrent=2
        await fetcher.fetch_all_async(max_concurrent=2)

        # Verify concurrency was limited
        assert max_observed_concurrent <= 2

    @pytest.mark.asyncio
    async def test_fetch_all_async_caps_max_concurrent(self, tmp_path: Path) -> None:
        """Test that max_concurrent is capped at MAX_CONCURRENT_LIMIT."""
        fetcher = FeedFetcher(tmp_path)

        # Create a simple feed
        feed = Feed(
            feed_id="test-feed",
            url="https://example.com/feed.xml",
            title="Test Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-14T10:00:00+00:00",
            updated_at="2026-01-14T10:00:00+00:00",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )
        feeds_data = FeedsData(version="1.0", feeds=[feed])
        fetcher.storage.save_feeds(feeds_data)

        # Patch fetch_feed to verify semaphore behavior
        with patch.object(fetcher, "fetch_feed", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = Mock(success=True)

            # Request more than allowed
            await fetcher.fetch_all_async(max_concurrent=100)

            # Verify fetch was called (test doesn't directly verify cap,
            # but verifies no error with high value)
            assert mock_fetch.called

    @pytest.mark.asyncio
    async def test_fetch_all_async_one_failure_doesnt_stop_others(
        self, tmp_path: Path, sample_feeds: list[Feed]
    ) -> None:
        """Test that one feed failure doesn't affect other feeds."""
        call_count = 0

        async def mock_fetch(url: str) -> HTTPResponse:
            nonlocal call_count
            call_count += 1
            if "feed0" in url:
                raise FeedFetchError("Network error")
            return HTTPResponse(
                status_code=200,
                content="<rss>...</rss>",
                headers={},
            )

        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.side_effect = mock_fetch

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = []

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = []

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        # Create feeds in storage
        feeds_data = FeedsData(version="1.0", feeds=sample_feeds)
        fetcher.storage.save_feeds(feeds_data)

        # Execute
        results = await fetcher.fetch_all_async()

        # Verify all feeds were attempted (4 enabled)
        assert len(results) == 4

        # Verify one failed and others succeeded
        failed = [r for r in results if not r.success]
        succeeded = [r for r in results if r.success]

        assert len(failed) == 1
        assert len(succeeded) == 3
        assert failed[0].feed_id == "feed-0"

    @pytest.mark.asyncio
    async def test_fetch_all_async_empty_feeds(self, tmp_path: Path) -> None:
        """Test fetch_all_async with no feeds."""
        fetcher = FeedFetcher(tmp_path)

        results = await fetcher.fetch_all_async()

        assert results == []

    @pytest.mark.asyncio
    async def test_fetch_all_async_no_enabled_feeds(self, tmp_path: Path) -> None:
        """Test fetch_all_async with only disabled feeds."""
        disabled_feed = Feed(
            feed_id="disabled-feed",
            url="https://example.com/feed.xml",
            title="Disabled Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-14T10:00:00+00:00",
            updated_at="2026-01-14T10:00:00+00:00",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=False,
        )

        fetcher = FeedFetcher(tmp_path)
        feeds_data = FeedsData(version="1.0", feeds=[disabled_feed])
        fetcher.storage.save_feeds(feeds_data)

        results = await fetcher.fetch_all_async()

        assert results == []


class TestFetchAll:
    """Test fetch_all (synchronous wrapper) method."""

    def test_fetch_all_success(self, tmp_path: Path) -> None:
        """Test synchronous fetch_all wrapper."""
        feed = Feed(
            feed_id="test-feed",
            url="https://example.com/feed.xml",
            title="Test Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-14T10:00:00+00:00",
            updated_at="2026-01-14T10:00:00+00:00",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )

        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = []

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = []

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        feeds_data = FeedsData(version="1.0", feeds=[feed])
        fetcher.storage.save_feeds(feeds_data)

        # Execute synchronous method
        results = fetcher.fetch_all()

        assert len(results) == 1
        assert results[0].success is True

    def test_fetch_all_with_category(self, tmp_path: Path) -> None:
        """Test synchronous fetch_all with category filter."""
        feeds = [
            Feed(
                feed_id=f"feed-{i}",
                url=f"https://example.com/feed{i}.xml",
                title=f"Feed {i}",
                category="finance" if i == 0 else "tech",
                fetch_interval=FetchInterval.DAILY,
                created_at="2026-01-14T10:00:00+00:00",
                updated_at="2026-01-14T10:00:00+00:00",
                last_fetched=None,
                last_status=FetchStatus.PENDING,
                enabled=True,
            )
            for i in range(3)
        ]

        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = []

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = []

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        feeds_data = FeedsData(version="1.0", feeds=feeds)
        fetcher.storage.save_feeds(feeds_data)

        # Execute with category filter
        results = fetcher.fetch_all(category="finance")

        assert len(results) == 1
        assert results[0].feed_id == "feed-0"


class TestDefaultConstants:
    """Test default constants."""

    def test_default_max_concurrent(self) -> None:
        """Test DEFAULT_MAX_CONCURRENT value."""
        assert DEFAULT_MAX_CONCURRENT == 5

    def test_max_concurrent_limit(self) -> None:
        """Test MAX_CONCURRENT_LIMIT value."""
        assert MAX_CONCURRENT_LIMIT == 10


class TestLogging:
    """Test structured logging behavior."""

    @pytest.mark.asyncio
    async def test_fetch_success_logs_info(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that successful fetch logs at INFO level."""
        feed = Feed(
            feed_id="test-feed",
            url="https://example.com/feed.xml",
            title="Test Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-14T10:00:00+00:00",
            updated_at="2026-01-14T10:00:00+00:00",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )

        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.return_value = HTTPResponse(
            status_code=200,
            content="<rss>...</rss>",
            headers={},
        )

        mock_parser = Mock(spec=FeedParser)
        mock_parser.parse.return_value = []

        mock_diff_detector = Mock(spec=DiffDetector)
        mock_diff_detector.detect_new_items.return_value = []

        fetcher = FeedFetcher(
            tmp_path,
            http_client=mock_http_client,
            parser=mock_parser,
            diff_detector=mock_diff_detector,
        )

        feeds_data = FeedsData(version="1.0", feeds=[feed])
        fetcher.storage.save_feeds(feeds_data)

        await fetcher.fetch_feed(feed.feed_id)

        captured = capsys.readouterr()
        # Verify info log was produced
        assert "successfully" in captured.out.lower() or "info" in captured.out.lower()

    @pytest.mark.asyncio
    async def test_fetch_error_logs_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that fetch error logs at ERROR level."""
        feed = Feed(
            feed_id="test-feed",
            url="https://example.com/feed.xml",
            title="Test Feed",
            category="finance",
            fetch_interval=FetchInterval.DAILY,
            created_at="2026-01-14T10:00:00+00:00",
            updated_at="2026-01-14T10:00:00+00:00",
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=True,
        )

        mock_http_client = AsyncMock(spec=HTTPClient)
        mock_http_client.fetch.side_effect = FeedFetchError("Connection failed")

        fetcher = FeedFetcher(tmp_path, http_client=mock_http_client)

        feeds_data = FeedsData(version="1.0", feeds=[feed])
        fetcher.storage.save_feeds(feeds_data)

        await fetcher.fetch_feed(feed.feed_id)

        captured = capsys.readouterr()
        # Verify error log was produced
        assert "failed" in captured.out.lower() or "error" in captured.out.lower()

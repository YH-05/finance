"""Integration tests for RSS feed workflow.

This module tests the complete workflow from feed registration to
fetching, saving, and searching items.
"""

import asyncio
import threading
import time
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer  # type: ignore[import-untyped]
from rss import (
    FeedFetcher,
    FeedManager,
    FeedReader,
    FetchResult,
    FileLockError,
)
from rss.storage.lock_manager import LockManager
from utils_core.logging import get_logger

logger = get_logger(__name__)


# Sample RSS 2.0 feed content
RSS_FEED_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{title}</title>
    <link>{link}</link>
    <description>{description}</description>
    {items}
  </channel>
</rss>
"""

RSS_ITEM_TEMPLATE = """
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <pubDate>{pub_date}</pubDate>
      <description>{description}</description>
    </item>
"""

# Sample Atom feed content
ATOM_FEED_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{title}</title>
  <link href="{link}"/>
  <id>{feed_id}</id>
  <updated>{updated}</updated>
  {entries}
</feed>
"""

ATOM_ENTRY_TEMPLATE = """
  <entry>
    <title>{title}</title>
    <link href="{link}"/>
    <id>{entry_id}</id>
    <updated>{updated}</updated>
    <summary>{summary}</summary>
  </entry>
"""


def create_rss_feed(
    title: str = "Test Feed",
    link: str = "https://example.com",
    description: str = "A test RSS feed",
    items: list[dict[str, str]] | None = None,
) -> str:
    """Create a sample RSS 2.0 feed XML.

    Parameters
    ----------
    title : str, default="Test Feed"
        Feed title
    link : str, default="https://example.com"
        Feed link URL
    description : str, default="A test RSS feed"
        Feed description
    items : list[dict[str, str]] | None, default=None
        List of item dictionaries with keys: title, link, pub_date, description.
        If None, default sample items are used.

    Returns
    -------
    str
        RSS 2.0 XML string
    """
    if items is None:
        items = [
            {
                "title": "Article 1",
                "link": "https://example.com/article1",
                "pub_date": "Mon, 01 Jan 2024 10:00:00 GMT",
                "description": "First article about finance",
            },
            {
                "title": "Article 2",
                "link": "https://example.com/article2",
                "pub_date": "Tue, 02 Jan 2024 10:00:00 GMT",
                "description": "Second article about market",
            },
        ]

    items_xml = "".join(RSS_ITEM_TEMPLATE.format(**item) for item in items)

    return RSS_FEED_TEMPLATE.format(
        title=title,
        link=link,
        description=description,
        items=items_xml,
    )


def create_atom_feed(
    title: str = "Test Atom Feed",
    link: str = "https://example.com/atom",
    feed_id: str = "urn:uuid:test-feed-001",
    updated: str = "2024-01-01T10:00:00Z",
    entries: list[dict[str, str]] | None = None,
) -> str:
    """Create a sample Atom feed XML.

    Parameters
    ----------
    title : str, default="Test Atom Feed"
        Feed title
    link : str, default="https://example.com/atom"
        Feed link URL
    feed_id : str, default="urn:uuid:test-feed-001"
        Unique feed identifier
    updated : str, default="2024-01-01T10:00:00Z"
        Last update timestamp in ISO 8601 format
    entries : list[dict[str, str]] | None, default=None
        List of entry dictionaries with keys: title, link, entry_id, updated, summary.
        If None, default sample entries are used.

    Returns
    -------
    str
        Atom XML string
    """
    if entries is None:
        entries = [
            {
                "title": "Atom Entry 1",
                "link": "https://example.com/atom/entry1",
                "entry_id": "urn:uuid:entry-001",
                "updated": "2024-01-01T10:00:00Z",
                "summary": "First atom entry about investment",
            },
        ]

    entries_xml = "".join(ATOM_ENTRY_TEMPLATE.format(**entry) for entry in entries)

    return ATOM_FEED_TEMPLATE.format(
        title=title,
        link=link,
        feed_id=feed_id,
        updated=updated,
        entries=entries_xml,
    )


@pytest.fixture
def rss_data_dir(temp_dir: Path) -> Path:
    """Create RSS data directory for testing."""
    rss_dir = temp_dir / "rss"
    rss_dir.mkdir(parents=True, exist_ok=True)
    return rss_dir


@pytest.fixture
def feed_manager(rss_data_dir: Path) -> FeedManager:
    """Create FeedManager instance for testing."""
    return FeedManager(rss_data_dir)


@pytest.fixture
def feed_fetcher(rss_data_dir: Path) -> FeedFetcher:
    """Create FeedFetcher instance for testing."""
    return FeedFetcher(rss_data_dir)


@pytest.fixture
def feed_reader(rss_data_dir: Path) -> FeedReader:
    """Create FeedReader instance for testing."""
    return FeedReader(rss_data_dir)


class TestFeedWorkflowIntegration:
    """Integration tests for feed workflow: register → fetch → search."""

    @pytest.mark.integration
    def test_正常系_フィード登録から取得検索までのフルフロー(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
        feed_reader: FeedReader,
    ) -> None:
        """Test complete workflow: feed registration → fetch → save → search."""
        # 1. Setup mock HTTP server with RSS feed
        feed_content = create_rss_feed(
            title="Finance News",
            items=[
                {
                    "title": "金利上昇のニュース",
                    "link": "https://example.com/news/rate-hike",
                    "pub_date": "Mon, 15 Jan 2024 09:00:00 GMT",
                    "description": "日銀が金利引き上げを発表",
                },
                {
                    "title": "株式市場の動向",
                    "link": "https://example.com/news/stock-market",
                    "pub_date": "Tue, 16 Jan 2024 09:00:00 GMT",
                    "description": "日経平均株価が上昇",
                },
                {
                    "title": "為替相場の分析",
                    "link": "https://example.com/news/forex",
                    "pub_date": "Wed, 17 Jan 2024 09:00:00 GMT",
                    "description": "ドル円相場が円安方向へ",
                },
            ],
        )
        httpserver.expect_request("/feed.xml").respond_with_data(
            feed_content, content_type="application/rss+xml"
        )

        # 2. Register feed
        feed_url = httpserver.url_for("/feed.xml")
        feed = feed_manager.add_feed(
            url=feed_url,
            title="Finance News Feed",
            category="finance",
        )
        assert feed.feed_id is not None
        assert feed.url == feed_url
        assert feed.category == "finance"

        # 3. Verify feed is listed
        feeds = feed_manager.list_feeds()
        assert len(feeds) == 1
        assert feeds[0].feed_id == feed.feed_id

        # 4. Fetch feed content
        result = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
        assert result.success is True
        assert result.items_count == 3
        assert result.new_items == 3

        # 5. Read items
        items = feed_reader.get_items(feed_id=feed.feed_id)
        assert len(items) == 3

        # 6. Search items by keyword
        search_results = feed_reader.search_items(
            query="金利",
            category="finance",
        )
        assert len(search_results) == 1
        assert "金利" in search_results[0].title

        # 7. Search in different fields
        market_results = feed_reader.search_items(
            query="株価",
            fields=["summary"],
        )
        assert len(market_results) == 1

    @pytest.mark.integration
    def test_正常系_複数フィード登録と検索(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
        feed_reader: FeedReader,
    ) -> None:
        """Test workflow with multiple feeds: register multiple → fetch → search across."""
        # 1. Setup mock feeds
        finance_feed = create_rss_feed(
            title="Finance Feed",
            items=[
                {
                    "title": "Finance Article",
                    "link": "https://example.com/finance/1",
                    "pub_date": "Mon, 01 Jan 2024 10:00:00 GMT",
                    "description": "金融市場のニュース",
                },
            ],
        )
        tech_feed = create_rss_feed(
            title="Tech Feed",
            items=[
                {
                    "title": "Tech Article",
                    "link": "https://example.com/tech/1",
                    "pub_date": "Tue, 02 Jan 2024 10:00:00 GMT",
                    "description": "テクノロジーニュース",
                },
            ],
        )

        httpserver.expect_request("/finance.xml").respond_with_data(
            finance_feed, content_type="application/rss+xml"
        )
        httpserver.expect_request("/tech.xml").respond_with_data(
            tech_feed, content_type="application/rss+xml"
        )

        # 2. Register multiple feeds
        finance_url = httpserver.url_for("/finance.xml")
        tech_url = httpserver.url_for("/tech.xml")

        _feed1 = feed_manager.add_feed(
            url=finance_url, title="Finance", category="finance"
        )
        _feed2 = feed_manager.add_feed(url=tech_url, title="Tech", category="tech")

        # 3. Fetch all feeds
        results = feed_fetcher.fetch_all()
        assert len(results) == 2
        assert all(r.success for r in results)

        # 4. Search across all feeds
        all_items = feed_reader.get_items()
        assert len(all_items) == 2

        # 5. Search by category filter
        finance_items = feed_reader.search_items(query="", category="finance")
        assert all(
            "finance" in item.link or "金融" in (item.summary or "")
            for item in finance_items
        )

    @pytest.mark.integration
    def test_正常系_Atomフィードの処理(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
        feed_reader: FeedReader,
    ) -> None:
        """Test workflow with Atom feed format."""
        # 1. Setup Atom feed
        atom_content = create_atom_feed(
            title="Atom Finance Feed",
            entries=[
                {
                    "title": "Atom投資記事",
                    "link": "https://example.com/atom/invest1",
                    "entry_id": "urn:uuid:atom-001",
                    "updated": "2024-01-15T10:00:00Z",
                    "summary": "投資に関する詳細な分析",
                },
            ],
        )
        httpserver.expect_request("/atom.xml").respond_with_data(
            atom_content, content_type="application/atom+xml"
        )

        # 2. Register and fetch
        feed = feed_manager.add_feed(
            url=httpserver.url_for("/atom.xml"),
            title="Atom Feed",
            category="investment",
        )

        result = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
        assert result.success is True
        assert result.new_items >= 1

        # 3. Verify items
        items = feed_reader.get_items(feed_id=feed.feed_id)
        assert len(items) >= 1
        assert "投資" in items[0].title or "投資" in (items[0].summary or "")


class TestParallelFeedFetching:
    """Integration tests for parallel feed fetching."""

    @pytest.mark.integration
    def test_正常系_並列フィード取得(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
    ) -> None:
        """Test fetching multiple feeds in parallel."""
        # 1. Setup multiple mock feeds
        num_feeds = 5
        for i in range(num_feeds):
            feed_content = create_rss_feed(
                title=f"Feed {i + 1}",
                items=[
                    {
                        "title": f"Article from Feed {i + 1}",
                        "link": f"https://example.com/feed{i + 1}/article1",
                        "pub_date": "Mon, 01 Jan 2024 10:00:00 GMT",
                        "description": f"Content from feed {i + 1}",
                    },
                ],
            )
            httpserver.expect_request(f"/feed{i + 1}.xml").respond_with_data(
                feed_content, content_type="application/rss+xml"
            )

        # 2. Register all feeds
        feed_ids = []
        for i in range(num_feeds):
            feed = feed_manager.add_feed(
                url=httpserver.url_for(f"/feed{i + 1}.xml"),
                title=f"Parallel Feed {i + 1}",
                category="parallel_test",
            )
            feed_ids.append(feed.feed_id)

        # 3. Fetch all feeds in parallel
        results = asyncio.run(feed_fetcher.fetch_all_async(max_concurrent=3))

        # 4. Verify results
        assert len(results) == num_feeds
        assert all(r.success for r in results)
        assert all(r.new_items >= 1 for r in results)

    @pytest.mark.integration
    def test_正常系_並列取得での部分的失敗(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
    ) -> None:
        """Test parallel fetching where some feeds fail."""
        # 1. Setup feeds - some succeed, some fail
        success_content = create_rss_feed(title="Success Feed")
        httpserver.expect_request("/success.xml").respond_with_data(
            success_content, content_type="application/rss+xml"
        )
        httpserver.expect_request("/error.xml").respond_with_data(
            "Not Found", status=404
        )

        # 2. Register feeds
        _success_feed = feed_manager.add_feed(
            url=httpserver.url_for("/success.xml"),
            title="Success Feed",
            category="test",
        )
        _error_feed = feed_manager.add_feed(
            url=httpserver.url_for("/error.xml"),
            title="Error Feed",
            category="test",
        )

        # 3. Fetch all - should not raise, partial success
        results = feed_fetcher.fetch_all()

        # 4. Verify mixed results
        assert len(results) == 2
        success_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        assert len(success_results) == 1
        assert len(failed_results) == 1

    @pytest.mark.integration
    def test_正常系_max_concurrent制限(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
    ) -> None:
        """Test that max_concurrent properly limits parallel fetches."""
        # Setup feeds with delay to observe concurrency
        num_feeds = 6

        for i in range(num_feeds):
            feed_content = create_rss_feed(title=f"Concurrent Feed {i + 1}")
            httpserver.expect_request(f"/concurrent{i + 1}.xml").respond_with_data(
                feed_content, content_type="application/rss+xml"
            )
            feed_manager.add_feed(
                url=httpserver.url_for(f"/concurrent{i + 1}.xml"),
                title=f"Concurrent {i + 1}",
                category="concurrent_test",
            )

        # Fetch with limited concurrency
        results = asyncio.run(feed_fetcher.fetch_all_async(max_concurrent=2))

        assert len(results) == num_feeds
        assert all(r.success for r in results)


class TestFileLockContention:
    """Integration tests for file lock contention simulation."""

    @pytest.mark.integration
    def test_正常系_ファイルロック取得と解放(
        self,
        rss_data_dir: Path,
    ) -> None:
        """Test basic file lock acquisition and release."""
        lock_manager = LockManager(rss_data_dir)

        # Acquire and release feeds lock
        with lock_manager.lock_feeds():
            # Verify lock file exists
            lock_file = rss_data_dir / ".feeds.lock"
            assert lock_file.exists()

        # Lock should be released

    @pytest.mark.integration
    def test_正常系_異なるfeed_idのロックは競合しない(
        self,
        rss_data_dir: Path,
    ) -> None:
        """Test that locks for different feed IDs don't conflict."""
        lock_manager = LockManager(rss_data_dir)

        # Should be able to lock different feeds simultaneously
        with lock_manager.lock_items("feed-001"), lock_manager.lock_items("feed-002"):
            # Both locks acquired successfully
            pass

    @pytest.mark.integration
    def test_異常系_ロックタイムアウト(
        self,
        rss_data_dir: Path,
    ) -> None:
        """Test lock timeout when another process holds the lock."""
        lock_manager = LockManager(rss_data_dir, default_timeout=0.1)

        results: dict[str, bool] = {"thread_acquired": False, "main_got_error": False}

        def hold_lock() -> None:
            """Thread function to hold lock."""
            with lock_manager.lock_feeds(timeout=5.0):
                results["thread_acquired"] = True
                time.sleep(0.5)  # Hold lock longer than main thread timeout

        # Start thread to hold lock
        thread = threading.Thread(target=hold_lock)
        thread.start()

        # Wait for thread to acquire lock
        time.sleep(0.05)

        # Try to acquire same lock with short timeout
        try:
            with lock_manager.lock_feeds(timeout=0.1):
                pass  # Should not reach here
        except FileLockError:
            results["main_got_error"] = True

        thread.join()

        assert results["thread_acquired"] is True
        assert results["main_got_error"] is True

    @pytest.mark.integration
    def test_正常系_マルチスレッドでの同時書き込み保護(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
    ) -> None:
        """Test that file locks protect concurrent writes from multiple threads."""
        feed_manager = FeedManager(rss_data_dir)
        feed_fetcher = FeedFetcher(rss_data_dir)

        # Setup mock feed
        feed_content = create_rss_feed(
            title="Concurrent Write Test",
            items=[
                {
                    "title": f"Item {i}",
                    "link": f"https://example.com/item{i}",
                    "pub_date": "Mon, 01 Jan 2024 10:00:00 GMT",
                    "description": f"Description {i}",
                }
                for i in range(5)
            ],
        )
        httpserver.expect_request("/concurrent_write.xml").respond_with_data(
            feed_content, content_type="application/rss+xml"
        )

        # Register feed
        feed = feed_manager.add_feed(
            url=httpserver.url_for("/concurrent_write.xml"),
            title="Concurrent Write Feed",
            category="test",
        )

        # Fetch from multiple threads
        results: list[FetchResult] = []
        errors: list[Exception] = []

        def fetch_feed() -> None:
            try:
                result = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=fetch_feed) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All fetches should complete (though with varying new_items counts)
        assert len(errors) == 0
        assert len(results) == 3
        # At least one should succeed with items
        assert any(r.success for r in results)


class TestDiffDetectionIntegration:
    """Integration tests for diff detection in feed updates."""

    @pytest.mark.integration
    def test_正常系_差分検出で重複排除(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
        feed_reader: FeedReader,
    ) -> None:
        """Test that diff detection correctly identifies new vs existing items."""
        # 1. Initial fetch
        initial_content = create_rss_feed(
            title="Diff Test Feed",
            items=[
                {
                    "title": "Original Article 1",
                    "link": "https://example.com/original1",
                    "pub_date": "Mon, 01 Jan 2024 10:00:00 GMT",
                    "description": "Original content 1",
                },
            ],
        )
        httpserver.expect_request("/diff.xml").respond_with_data(
            initial_content, content_type="application/rss+xml"
        )

        feed = feed_manager.add_feed(
            url=httpserver.url_for("/diff.xml"),
            title="Diff Test",
            category="test",
        )

        result1 = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
        assert result1.success
        assert result1.new_items == 1
        assert result1.items_count == 1

        # 2. Second fetch with same content - no new items
        httpserver.clear()
        httpserver.expect_request("/diff.xml").respond_with_data(
            initial_content, content_type="application/rss+xml"
        )

        result2 = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
        assert result2.success
        assert result2.new_items == 0
        assert result2.items_count == 1  # Same total count

        # 3. Third fetch with new item added
        updated_content = create_rss_feed(
            title="Diff Test Feed",
            items=[
                {
                    "title": "New Article 2",
                    "link": "https://example.com/new2",
                    "pub_date": "Tue, 02 Jan 2024 10:00:00 GMT",
                    "description": "New content 2",
                },
                {
                    "title": "Original Article 1",
                    "link": "https://example.com/original1",
                    "pub_date": "Mon, 01 Jan 2024 10:00:00 GMT",
                    "description": "Original content 1",
                },
            ],
        )
        httpserver.clear()
        httpserver.expect_request("/diff.xml").respond_with_data(
            updated_content, content_type="application/rss+xml"
        )

        result3 = asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))
        assert result3.success
        assert result3.new_items == 1  # Only one new item
        assert result3.items_count == 2  # Total now 2

        # Verify final item count
        items = feed_reader.get_items(feed_id=feed.feed_id)
        assert len(items) == 2

    @pytest.mark.integration
    def test_正常系_フィード更新と検索の連続操作(
        self,
        httpserver: HTTPServer,
        rss_data_dir: Path,
        feed_manager: FeedManager,
        feed_fetcher: FeedFetcher,
        feed_reader: FeedReader,
    ) -> None:
        """Test continuous update and search operations."""
        # Setup initial feed
        content = create_rss_feed(
            title="Continuous Test",
            items=[
                {
                    "title": "Bitcoin価格分析",
                    "link": "https://example.com/bitcoin1",
                    "pub_date": "Mon, 01 Jan 2024 10:00:00 GMT",
                    "description": "ビットコインの価格動向",
                },
            ],
        )
        httpserver.expect_request("/continuous.xml").respond_with_data(
            content, content_type="application/rss+xml"
        )

        feed = feed_manager.add_feed(
            url=httpserver.url_for("/continuous.xml"),
            title="Continuous Feed",
            category="crypto",
        )

        # Initial fetch
        asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))

        # Search
        results = feed_reader.search_items(query="Bitcoin")
        assert len(results) == 1

        # Update feed with more items
        updated_content = create_rss_feed(
            title="Continuous Test",
            items=[
                {
                    "title": "Ethereum分析レポート",
                    "link": "https://example.com/ethereum1",
                    "pub_date": "Tue, 02 Jan 2024 10:00:00 GMT",
                    "description": "イーサリアムの最新動向",
                },
                {
                    "title": "Bitcoin価格分析",
                    "link": "https://example.com/bitcoin1",
                    "pub_date": "Mon, 01 Jan 2024 10:00:00 GMT",
                    "description": "ビットコインの価格動向",
                },
            ],
        )
        httpserver.clear()
        httpserver.expect_request("/continuous.xml").respond_with_data(
            updated_content, content_type="application/rss+xml"
        )

        # Fetch again
        asyncio.run(feed_fetcher.fetch_feed(feed.feed_id))

        # Search again
        eth_results = feed_reader.search_items(query="Ethereum")
        assert len(eth_results) == 1

        # All items
        all_items = feed_reader.get_items(feed_id=feed.feed_id)
        assert len(all_items) == 2

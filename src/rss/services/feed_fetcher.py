"""Feed fetching service for RSS feeds.

This module provides the FeedFetcher class that integrates feed fetching,
parsing, diff detection, and storage operations.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..core.diff_detector import DiffDetector
from ..core.http_client import HTTPClient
from ..core.parser import FeedParser
from ..exceptions import FeedFetchError, FeedParseError
from ..storage.json_storage import JSONStorage
from ..types import Feed, FeedItemsData, FetchResult, FetchStatus


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="feed_fetcher")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()

DEFAULT_MAX_CONCURRENT = 5
MAX_CONCURRENT_LIMIT = 10


class FeedFetcher:
    """Service for fetching, parsing, and storing RSS feeds.

    This class integrates HTTPClient, FeedParser, DiffDetector, and JSONStorage
    to provide a complete feed fetching workflow.

    Parameters
    ----------
    data_dir : Path
        Root directory for RSS feed data (e.g., data/raw/rss/)
    http_client : HTTPClient | None, default=None
        HTTP client instance (creates new one if None)
    parser : FeedParser | None, default=None
        Feed parser instance (creates new one if None)
    diff_detector : DiffDetector | None, default=None
        Diff detector instance (creates new one if None)

    Attributes
    ----------
    data_dir : Path
        Root directory for RSS feed data
    storage : JSONStorage
        JSON storage for persistence
    http_client : HTTPClient
        HTTP client for fetching feeds
    parser : FeedParser
        Feed parser for parsing content
    diff_detector : DiffDetector
        Diff detector for finding new items

    Examples
    --------
    >>> from pathlib import Path
    >>> fetcher = FeedFetcher(Path("data/raw/rss"))
    >>> result = await fetcher.fetch_feed("feed-id-123")
    >>> print(result.success)
    True
    """

    def __init__(
        self,
        data_dir: Path,
        http_client: HTTPClient | None = None,
        parser: FeedParser | None = None,
        diff_detector: DiffDetector | None = None,
    ) -> None:
        """Initialize FeedFetcher.

        Parameters
        ----------
        data_dir : Path
            Root directory for RSS feed data
        http_client : HTTPClient | None, default=None
            HTTP client instance (creates new one if None)
        parser : FeedParser | None, default=None
            Feed parser instance (creates new one if None)
        diff_detector : DiffDetector | None, default=None
            Diff detector instance (creates new one if None)

        Raises
        ------
        ValueError
            If data_dir is not a Path object
        """
        if not isinstance(data_dir, Path):
            logger.error(
                "Invalid data_dir type",
                data_dir=str(data_dir),
                expected_type="Path",
                actual_type=type(data_dir).__name__,
            )
            raise ValueError(f"data_dir must be a Path object, got {type(data_dir)}")

        self.data_dir = data_dir
        self.storage = JSONStorage(data_dir)
        self.http_client = http_client or HTTPClient()
        self.parser = parser or FeedParser()
        self.diff_detector = diff_detector or DiffDetector()

        logger.debug("FeedFetcher initialized", data_dir=str(data_dir))

    async def fetch_feed(self, feed_id: str) -> FetchResult:
        """Fetch a single feed by its ID.

        This method performs the complete fetch workflow:
        1. Get feed information from storage
        2. Fetch content via HTTPClient
        3. Parse content via FeedParser
        4. Detect new items via DiffDetector
        5. Merge and save items
        6. Update feed status (last_fetched, last_status)

        Parameters
        ----------
        feed_id : str
            Feed identifier (UUID format)

        Returns
        -------
        FetchResult
            Result containing success status, item counts, and error message

        Examples
        --------
        >>> fetcher = FeedFetcher(Path("data/raw/rss"))
        >>> result = await fetcher.fetch_feed("550e8400-e29b-41d4-a716-446655440000")
        >>> if result.success:
        ...     print(f"Fetched {result.items_count} items, {result.new_items} new")
        """
        logger.debug("Fetching feed", feed_id=feed_id)

        try:
            # 1. Get feed information
            feed = self._get_feed(feed_id)
            if feed is None:
                logger.error("Feed not found", feed_id=feed_id)
                return FetchResult(
                    feed_id=feed_id,
                    success=False,
                    items_count=0,
                    new_items=0,
                    error_message=f"Feed with ID '{feed_id}' not found",
                )

            logger.debug(
                "Feed found",
                feed_id=feed_id,
                url=feed.url,
                title=feed.title,
            )

            # 2. Fetch content
            response = await self.http_client.fetch(feed.url)
            logger.debug(
                "Content fetched",
                feed_id=feed_id,
                status_code=response.status_code,
                content_length=len(response.content),
            )

            # 3. Parse content
            fetched_items = self.parser.parse(response.content.encode("utf-8"))
            logger.debug(
                "Content parsed",
                feed_id=feed_id,
                fetched_count=len(fetched_items),
            )

            # 4. Load existing items and detect new ones
            existing_data = self.storage.load_items(feed_id)
            new_items = self.diff_detector.detect_new_items(
                existing_data.items, fetched_items
            )
            logger.debug(
                "Diff detected",
                feed_id=feed_id,
                existing_count=len(existing_data.items),
                new_count=len(new_items),
            )

            # 5. Merge and save items (new items at the beginning)
            merged_items = new_items + existing_data.items
            items_data = FeedItemsData(
                version="1.0",
                feed_id=feed_id,
                items=merged_items,
            )
            self.storage.save_items(feed_id, items_data)

            # 6. Update feed status
            self._update_feed_status(feed_id, FetchStatus.SUCCESS)

            logger.info(
                "Feed fetched successfully",
                feed_id=feed_id,
                title=feed.title,
                items_count=len(merged_items),
                new_items=len(new_items),
            )

            return FetchResult(
                feed_id=feed_id,
                success=True,
                items_count=len(merged_items),
                new_items=len(new_items),
                error_message=None,
            )

        except FeedFetchError as e:
            return self._handle_fetch_error(
                feed_id=feed_id,
                error=e,
                log_message="Feed fetch failed",
                include_traceback=False,
            )

        except FeedParseError as e:
            return self._handle_fetch_error(
                feed_id=feed_id,
                error=e,
                log_message="Feed parse failed",
                include_traceback=False,
            )

        except Exception as e:
            return self._handle_fetch_error(
                feed_id=feed_id,
                error=e,
                log_message="Unexpected error during feed fetch",
                include_traceback=True,
            )

    async def fetch_all_async(
        self,
        *,
        category: str | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
    ) -> list[FetchResult]:
        """Fetch all feeds asynchronously with concurrency control.

        This method fetches multiple feeds in parallel using asyncio.gather
        with semaphore-based concurrency control.

        Parameters
        ----------
        category : str | None, default=None
            Filter feeds by category (None for all feeds)
        max_concurrent : int, default=5
            Maximum number of concurrent fetches (capped at 10)

        Returns
        -------
        list[FetchResult]
            List of fetch results for each feed

        Examples
        --------
        >>> fetcher = FeedFetcher(Path("data/raw/rss"))
        >>> results = await fetcher.fetch_all_async(category="finance")
        >>> successful = [r for r in results if r.success]
        >>> print(f"{len(successful)}/{len(results)} feeds fetched successfully")
        """
        # Cap max_concurrent at MAX_CONCURRENT_LIMIT
        effective_max = min(max_concurrent, MAX_CONCURRENT_LIMIT)
        if max_concurrent > MAX_CONCURRENT_LIMIT:
            logger.warning(
                "max_concurrent capped",
                requested=max_concurrent,
                effective=effective_max,
                limit=MAX_CONCURRENT_LIMIT,
            )

        logger.debug(
            "Starting parallel fetch",
            category=category,
            max_concurrent=effective_max,
        )

        # Get feeds to fetch
        feeds_data = self.storage.load_feeds()
        feeds = feeds_data.feeds

        # Filter by category if specified
        if category is not None:
            feeds = [f for f in feeds if f.category == category]

        # Filter enabled feeds only
        feeds = [f for f in feeds if f.enabled]

        if not feeds:
            logger.info(
                "No feeds to fetch",
                category=category,
                total_feeds=len(feeds_data.feeds),
            )
            return []

        logger.info(
            "Fetching feeds",
            feed_count=len(feeds),
            category=category,
            max_concurrent=effective_max,
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(effective_max)

        async def fetch_with_semaphore(feed_id: str) -> FetchResult:
            """Fetch a feed with semaphore control."""
            async with semaphore:
                return await self.fetch_feed(feed_id)

        # Create tasks for all feeds
        tasks = [fetch_with_semaphore(feed.feed_id) for feed in feeds]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Count successes and failures
        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count

        logger.info(
            "Parallel fetch completed",
            total=len(results),
            success=success_count,
            failure=failure_count,
            category=category,
        )

        return list(results)

    def fetch_all(
        self,
        *,
        category: str | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
    ) -> list[FetchResult]:
        """Fetch all feeds synchronously (wrapper for fetch_all_async).

        This is a convenience method that runs fetch_all_async in the
        event loop for synchronous contexts.

        Parameters
        ----------
        category : str | None, default=None
            Filter feeds by category (None for all feeds)
        max_concurrent : int, default=5
            Maximum number of concurrent fetches (capped at 10)

        Returns
        -------
        list[FetchResult]
            List of fetch results for each feed

        Examples
        --------
        >>> fetcher = FeedFetcher(Path("data/raw/rss"))
        >>> results = fetcher.fetch_all(category="economics")
        >>> for result in results:
        ...     status = "OK" if result.success else "FAIL"
        ...     print(f"{result.feed_id}: {status}")
        """
        logger.debug(
            "Starting synchronous fetch_all",
            category=category,
            max_concurrent=max_concurrent,
        )

        return asyncio.run(
            self.fetch_all_async(category=category, max_concurrent=max_concurrent)
        )

    def _get_feed(self, feed_id: str) -> Feed | None:
        """Get feed by ID from storage.

        Parameters
        ----------
        feed_id : str
            Feed identifier

        Returns
        -------
        Feed | None
            Feed object if found, None otherwise
        """
        feeds_data = self.storage.load_feeds()
        for feed in feeds_data.feeds:
            if feed.feed_id == feed_id:
                return feed
        return None

    def _handle_fetch_error(
        self,
        *,
        feed_id: str,
        error: Exception,
        log_message: str,
        include_traceback: bool,
    ) -> FetchResult:
        """Handle fetch error by logging and updating status.

        Parameters
        ----------
        feed_id : str
            Feed identifier
        error : Exception
            The exception that occurred
        log_message : str
            Log message describing the error
        include_traceback : bool
            Whether to include traceback in logs

        Returns
        -------
        FetchResult
            Failed fetch result with error message
        """
        error_msg = str(error)
        logger.error(
            log_message,
            feed_id=feed_id,
            error=error_msg,
            error_type=type(error).__name__,
            exc_info=include_traceback,
        )
        self._update_feed_status(feed_id, FetchStatus.FAILURE)
        return FetchResult(
            feed_id=feed_id,
            success=False,
            items_count=0,
            new_items=0,
            error_message=error_msg,
        )

    def _update_feed_status(self, feed_id: str, status: FetchStatus) -> None:
        """Update feed's last_fetched and last_status.

        Parameters
        ----------
        feed_id : str
            Feed identifier
        status : FetchStatus
            New fetch status
        """
        try:
            feeds_data = self.storage.load_feeds()

            for i, feed in enumerate(feeds_data.feeds):
                if feed.feed_id == feed_id:
                    feed.last_fetched = datetime.now(UTC).isoformat()
                    feed.last_status = status
                    feed.updated_at = datetime.now(UTC).isoformat()
                    feeds_data.feeds[i] = feed
                    self.storage.save_feeds(feeds_data)

                    logger.debug(
                        "Feed status updated",
                        feed_id=feed_id,
                        status=status.value,
                        last_fetched=feed.last_fetched,
                    )
                    return

            logger.warning(
                "Feed not found for status update",
                feed_id=feed_id,
                status=status.value,
            )

        except Exception as e:
            logger.error(
                "Failed to update feed status",
                feed_id=feed_id,
                status=status.value,
                error=str(e),
                exc_info=True,
            )

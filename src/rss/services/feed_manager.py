"""Feed management service for RSS feeds.

This module provides the FeedManager class for managing RSS feed registration,
listing, updating, and deletion.
"""

import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from ..exceptions import FeedAlreadyExistsError, FeedFetchError, FeedNotFoundError
from ..storage.json_storage import JSONStorage
from ..types import Feed, FetchInterval, FetchStatus
from ..validators.url_validator import URLValidator


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="feed_manager")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class FeedManager:
    """Service for managing RSS feeds.

    This class provides methods for feed registration, listing, retrieval,
    updating, and deletion. All operations are persisted to JSON storage.

    Parameters
    ----------
    data_dir : Path
        Root directory for RSS feed data (e.g., data/raw/rss/)

    Attributes
    ----------
    data_dir : Path
        Root directory for RSS feed data
    storage : JSONStorage
        JSON storage for persistence
    validator : URLValidator
        Validator for URLs, titles, and categories

    Examples
    --------
    >>> from pathlib import Path
    >>> manager = FeedManager(Path("data/raw/rss"))
    >>> feed = manager.add_feed(
    ...     url="https://example.com/feed.xml",
    ...     title="Example Feed",
    ...     category="finance",
    ... )
    >>> print(feed.feed_id)  # UUID v4 format
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize FeedManager.

        Parameters
        ----------
        data_dir : Path
            Root directory for RSS feed data

        Raises
        ------
        ValueError
            If data_dir is not a Path object
        """
        if not isinstance(data_dir, Path):  # type: ignore[reportUnnecessaryIsInstance]
            logger.error(
                "Invalid data_dir type",
                data_dir=str(data_dir),
                expected_type="Path",
                actual_type=type(data_dir).__name__,
            )
            raise ValueError(f"data_dir must be a Path object, got {type(data_dir)}")

        self.data_dir = data_dir
        self.storage = JSONStorage(data_dir)
        self.validator = URLValidator()
        logger.debug("FeedManager initialized", data_dir=str(data_dir))

    def add_feed(
        self,
        url: str,
        title: str,
        category: str,
        *,
        fetch_interval: FetchInterval = FetchInterval.DAILY,
        validate_url: bool = False,
        enabled: bool = True,
    ) -> Feed:
        """Register a new feed.

        Parameters
        ----------
        url : str
            Feed URL (HTTP/HTTPS only)
        title : str
            Feed title (1-200 characters)
        category : str
            Feed category (1-50 characters)
        fetch_interval : FetchInterval, default=FetchInterval.DAILY
            Fetch interval
        validate_url : bool, default=False
            Whether to check URL reachability
        enabled : bool, default=True
            Whether the feed is enabled

        Returns
        -------
        Feed
            Newly registered feed

        Raises
        ------
        InvalidURLError
            If URL is invalid (not HTTP/HTTPS)
        FeedAlreadyExistsError
            If feed with the same URL already exists
        FeedFetchError
            If validate_url is True and URL is unreachable
        ValueError
            If title or category is invalid

        Examples
        --------
        >>> from pathlib import Path
        >>> manager = FeedManager(Path("data/raw/rss"))
        >>> feed = manager.add_feed(
        ...     url="https://example.com/feed.xml",
        ...     title="Example Feed",
        ...     category="finance",
        ... )
        >>> print(feed.feed_id)  # UUID v4 format
        """
        logger.debug(
            "Adding feed",
            url=url,
            title=title,
            category=category,
            fetch_interval=fetch_interval.value,
            validate_url=validate_url,
            enabled=enabled,
        )

        # Validate URL format
        self.validator.validate_url(url)

        # Validate title and category
        self.validator.validate_title(title)
        self.validator.validate_category(category)

        # Load existing feeds and check for duplicates
        feeds_data = self.storage.load_feeds()
        for existing_feed in feeds_data.feeds:
            if existing_feed.url == url:
                logger.warning(
                    "Duplicate feed URL detected",
                    url=url,
                    existing_feed_id=existing_feed.feed_id,
                )
                raise FeedAlreadyExistsError(
                    f"Feed with URL '{url}' already exists (feed_id: {existing_feed.feed_id})"
                )

        # Validate URL reachability if requested
        if validate_url:
            self._check_url_reachability(url)

        # Generate UUID and timestamps
        feed_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        # Create new feed
        feed = Feed(
            feed_id=feed_id,
            url=url,
            title=title,
            category=category,
            fetch_interval=fetch_interval,
            created_at=now,
            updated_at=now,
            last_fetched=None,
            last_status=FetchStatus.PENDING,
            enabled=enabled,
        )

        # Add to feeds list and save
        feeds_data.feeds.append(feed)
        self.storage.save_feeds(feeds_data)

        logger.info(
            "Feed registered successfully",
            feed_id=feed_id,
            url=url,
            title=title,
            category=category,
        )

        return feed

    def _check_url_reachability(self, url: str, timeout: float = 10.0) -> None:
        """Check if URL is reachable via HTTP HEAD request.

        Parameters
        ----------
        url : str
            URL to check
        timeout : float, default=10.0
            Request timeout in seconds

        Raises
        ------
        FeedFetchError
            If URL is unreachable or returns an error status
        """
        logger.debug("Checking URL reachability", url=url, timeout=timeout)

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.head(url)
                response.raise_for_status()

            logger.debug(
                "URL reachability check passed",
                url=url,
                status_code=response.status_code,
            )

        except httpx.TimeoutException as e:
            logger.error(
                "URL reachability check failed: timeout",
                url=url,
                timeout=timeout,
                error=str(e),
            )
            raise FeedFetchError(
                f"Failed to reach URL '{url}': Connection timeout after {timeout}s"
            ) from e

        except httpx.HTTPStatusError as e:
            logger.error(
                "URL reachability check failed: HTTP error",
                url=url,
                status_code=e.response.status_code,
                error=str(e),
            )
            raise FeedFetchError(
                f"Failed to reach URL '{url}': HTTP {e.response.status_code}"
            ) from e

        except httpx.RequestError as e:
            logger.error(
                "URL reachability check failed: request error",
                url=url,
                error=str(e),
                exc_info=True,
            )
            raise FeedFetchError(f"Failed to reach URL '{url}': {e}") from e

    def list_feeds(
        self,
        *,
        category: str | None = None,
        enabled_only: bool = False,
    ) -> list[Feed]:
        """Get list of registered feeds.

        Parameters
        ----------
        category : str | None, default=None
            Filter by category (exact match)
        enabled_only : bool, default=False
            If True, only return enabled feeds

        Returns
        -------
        list[Feed]
            List of feeds matching the filter criteria

        Examples
        --------
        >>> manager = FeedManager(Path("data/raw/rss"))
        >>> all_feeds = manager.list_feeds()
        >>> finance_feeds = manager.list_feeds(category="finance")
        >>> active_feeds = manager.list_feeds(enabled_only=True)
        """
        logger.debug(
            "Listing feeds",
            category=category,
            enabled_only=enabled_only,
        )

        feeds_data = self.storage.load_feeds()
        feeds = feeds_data.feeds

        # Apply category filter
        if category is not None:
            feeds = [f for f in feeds if f.category == category]

        # Apply enabled filter
        if enabled_only:
            feeds = [f for f in feeds if f.enabled]

        logger.info(
            "Feeds listed",
            total_count=len(feeds_data.feeds),
            filtered_count=len(feeds),
            category_filter=category,
            enabled_only=enabled_only,
        )

        return feeds

    def get_feed(self, feed_id: str) -> Feed:
        """Get a feed by its ID.

        Parameters
        ----------
        feed_id : str
            Feed identifier (UUID format)

        Returns
        -------
        Feed
            The feed with the specified ID

        Raises
        ------
        FeedNotFoundError
            If no feed with the specified ID exists

        Examples
        --------
        >>> manager = FeedManager(Path("data/raw/rss"))
        >>> feed = manager.get_feed("550e8400-e29b-41d4-a716-446655440000")
        >>> print(feed.title)
        """
        logger.debug("Getting feed", feed_id=feed_id)

        feeds_data = self.storage.load_feeds()

        for feed in feeds_data.feeds:
            if feed.feed_id == feed_id:
                logger.debug("Feed found", feed_id=feed_id, title=feed.title)
                return feed

        logger.error("Feed not found", feed_id=feed_id)
        raise FeedNotFoundError(f"Feed with ID '{feed_id}' not found")

    def update_feed(
        self,
        feed_id: str,
        *,
        title: str | None = None,
        category: str | None = None,
        fetch_interval: FetchInterval | None = None,
        enabled: bool | None = None,
    ) -> Feed:
        """Update feed information.

        Parameters
        ----------
        feed_id : str
            Feed identifier (UUID format)
        title : str | None, default=None
            New title (1-200 characters)
        category : str | None, default=None
            New category (1-50 characters)
        fetch_interval : FetchInterval | None, default=None
            New fetch interval
        enabled : bool | None, default=None
            New enabled status

        Returns
        -------
        Feed
            The updated feed

        Raises
        ------
        FeedNotFoundError
            If no feed with the specified ID exists
        ValueError
            If title or category is invalid

        Examples
        --------
        >>> manager = FeedManager(Path("data/raw/rss"))
        >>> updated = manager.update_feed(
        ...     "550e8400-e29b-41d4-a716-446655440000",
        ...     title="New Title",
        ...     enabled=False,
        ... )
        """
        logger.debug(
            "Updating feed",
            feed_id=feed_id,
            title=title,
            category=category,
            fetch_interval=fetch_interval.value if fetch_interval else None,
            enabled=enabled,
        )

        # Validate new values if provided
        if title is not None:
            self.validator.validate_title(title)
        if category is not None:
            self.validator.validate_category(category)

        feeds_data = self.storage.load_feeds()

        # Find and update the feed using Early return pattern
        feed_index = next(
            (i for i, feed in enumerate(feeds_data.feeds) if feed.feed_id == feed_id),
            None,
        )

        if feed_index is None:
            logger.error("Feed not found for update", feed_id=feed_id)
            raise FeedNotFoundError(f"Feed with ID '{feed_id}' not found")

        feed = feeds_data.feeds[feed_index]

        # Update fields
        if title is not None:
            feed.title = title
        if category is not None:
            feed.category = category
        if fetch_interval is not None:
            feed.fetch_interval = fetch_interval
        if enabled is not None:
            feed.enabled = enabled

        # Update timestamp
        feed.updated_at = datetime.now(UTC).isoformat()

        # Replace in list and save
        feeds_data.feeds[feed_index] = feed
        self.storage.save_feeds(feeds_data)

        logger.info(
            "Feed updated successfully",
            feed_id=feed_id,
            updated_fields={
                k: v
                for k, v in {
                    "title": title,
                    "category": category,
                    "fetch_interval": (
                        fetch_interval.value if fetch_interval else None
                    ),
                    "enabled": enabled,
                }.items()
                if v is not None
            },
        )

        return feed

    def remove_feed(self, feed_id: str) -> None:
        """Remove a feed and its associated items.

        Parameters
        ----------
        feed_id : str
            Feed identifier (UUID format)

        Raises
        ------
        FeedNotFoundError
            If no feed with the specified ID exists

        Examples
        --------
        >>> manager = FeedManager(Path("data/raw/rss"))
        >>> manager.remove_feed("550e8400-e29b-41d4-a716-446655440000")
        """
        logger.debug("Removing feed", feed_id=feed_id)

        feeds_data = self.storage.load_feeds()

        # Find the feed index using next() with enumerate
        feed_index = next(
            (i for i, feed in enumerate(feeds_data.feeds) if feed.feed_id == feed_id),
            None,
        )

        if feed_index is None:
            logger.error("Feed not found for removal", feed_id=feed_id)
            raise FeedNotFoundError(f"Feed with ID '{feed_id}' not found")

        # Remove from list
        removed_feed = feeds_data.feeds.pop(feed_index)

        # Save updated feeds
        self.storage.save_feeds(feeds_data)

        # Delete items directory if exists
        items_dir = self.data_dir / feed_id
        if items_dir.exists():
            shutil.rmtree(items_dir)
            logger.debug("Items directory deleted", items_dir=str(items_dir))

        logger.info(
            "Feed removed successfully",
            feed_id=feed_id,
            title=removed_feed.title,
            url=removed_feed.url,
        )

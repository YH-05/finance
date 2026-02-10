"""JSON storage for RSS feed data.

This module provides JSON-based persistence for feed registry and feed items.
All operations use file locking to ensure safe concurrent access.
"""

import json
from dataclasses import asdict
from pathlib import Path

from utils_core.errors import log_and_reraise
from utils_core.logging import get_logger

from ..exceptions import RSSError
from ..storage.lock_manager import LockManager
from ..types import FeedItemsData, FeedsData

logger = get_logger(__name__)


class JSONStorage:
    """JSON storage for RSS feed data.

    This class provides methods to save and load feed registry (feeds.json)
    and feed items ({feed_id}/items.json) in JSON format with UTF-8 encoding
    and pretty-printing for manual editability.

    Parameters
    ----------
    data_dir : Path
        Root directory for RSS feed data (e.g., data/raw/rss/)

    Attributes
    ----------
    data_dir : Path
        Root directory for RSS feed data
    lock_manager : LockManager
        File lock manager for concurrent access control

    Examples
    --------
    >>> from pathlib import Path
    >>> from rss.types import FeedsData, FeedItemsData
    >>> storage = JSONStorage(Path("data/raw/rss"))
    >>> feeds_data = FeedsData(version="1.0", feeds=[])
    >>> storage.save_feeds(feeds_data)
    >>> loaded = storage.load_feeds()
    >>> loaded.version
    '1.0'
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize JSONStorage.

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
        self.lock_manager = LockManager(data_dir)
        logger.debug("JSONStorage initialized", data_dir=str(data_dir))

    def save_feeds(self, data: FeedsData) -> None:
        """Save feed registry to feeds.json.

        This method serializes FeedsData to JSON and saves it to feeds.json
        with UTF-8 encoding and indentation for manual editability.
        The operation is protected by file locking.

        Parameters
        ----------
        data : FeedsData
            Feed registry data to save

        Raises
        ------
        RSSError
            If JSON serialization or file write fails

        Examples
        --------
        >>> from pathlib import Path
        >>> from rss.types import FeedsData, Feed, FetchInterval, FetchStatus
        >>> storage = JSONStorage(Path("data/raw/rss"))
        >>> feed = Feed(
        ...     feed_id="550e8400-e29b-41d4-a716-446655440000",
        ...     url="https://example.com/feed.xml",
        ...     title="Example Feed",
        ...     category="finance",
        ...     fetch_interval=FetchInterval.DAILY,
        ...     created_at="2026-01-14T10:00:00Z",
        ...     updated_at="2026-01-14T10:00:00Z",
        ...     last_fetched=None,
        ...     last_status=FetchStatus.PENDING,
        ...     enabled=True,
        ... )
        >>> feeds_data = FeedsData(version="1.0", feeds=[feed])
        >>> storage.save_feeds(feeds_data)
        """
        feeds_file = self.data_dir / "feeds.json"

        logger.debug(
            "Saving feeds",
            feeds_file=str(feeds_file),
            feeds_count=len(data.feeds),
        )

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        with log_and_reraise(
            logger,
            f"save feeds to {feeds_file}",
            context={"feeds_file": str(feeds_file)},
            reraise_as=RSSError,
        ):
            with self.lock_manager.lock_feeds():
                # Convert dataclass to dict and handle Enum serialization
                data_dict = asdict(data)
                # Convert Enum values to strings
                for feed in data_dict["feeds"]:
                    if "fetch_interval" in feed:
                        feed["fetch_interval"] = feed["fetch_interval"]
                    if "last_status" in feed:
                        feed["last_status"] = feed["last_status"]

                # Write JSON with UTF-8 encoding and indentation
                feeds_file.write_text(
                    json.dumps(data_dict, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

            logger.info(
                "Feeds saved successfully",
                feeds_file=str(feeds_file),
                feeds_count=len(data.feeds),
            )

    def load_feeds(self) -> FeedsData:
        """Load feed registry from feeds.json.

        This method reads feeds.json and deserializes it to FeedsData.
        If the file doesn't exist, returns an empty FeedsData with version "1.0".
        The operation is protected by file locking.

        Returns
        -------
        FeedsData
            Loaded feed registry data, or empty data if file doesn't exist

        Raises
        ------
        RSSError
            If JSON deserialization fails

        Examples
        --------
        >>> from pathlib import Path
        >>> storage = JSONStorage(Path("data/raw/rss"))
        >>> feeds_data = storage.load_feeds()
        >>> feeds_data.version
        '1.0'
        >>> len(feeds_data.feeds)
        0
        """
        feeds_file = self.data_dir / "feeds.json"

        logger.debug("Loading feeds", feeds_file=str(feeds_file))

        # Return empty data if file doesn't exist
        if not feeds_file.exists():
            logger.info(
                "Feeds file not found, returning empty data",
                feeds_file=str(feeds_file),
            )
            return FeedsData(version="1.0", feeds=[])

        with log_and_reraise(
            logger,
            f"load feeds from {feeds_file}",
            context={"feeds_file": str(feeds_file)},
            reraise_as=RSSError,
        ):
            with self.lock_manager.lock_feeds():
                content = feeds_file.read_text(encoding="utf-8")
                data_dict = json.loads(content)

                # Import here to avoid circular dependency
                from ..types import Feed, FetchInterval, FetchStatus

                # Reconstruct Feed objects with Enum conversion
                feeds = []
                for feed_dict in data_dict.get("feeds", []):
                    # Convert string values back to Enum
                    if "fetch_interval" in feed_dict:
                        feed_dict["fetch_interval"] = FetchInterval(
                            feed_dict["fetch_interval"]
                        )
                    if "last_status" in feed_dict:
                        feed_dict["last_status"] = FetchStatus(feed_dict["last_status"])
                    feeds.append(Feed(**feed_dict))

                feeds_data = FeedsData(version=data_dict["version"], feeds=feeds)

            logger.info(
                "Feeds loaded successfully",
                feeds_file=str(feeds_file),
                feeds_count=len(feeds_data.feeds),
            )

            return feeds_data

    def save_items(self, feed_id: str, data: FeedItemsData) -> None:
        """Save feed items to {feed_id}/items.json.

        This method serializes FeedItemsData to JSON and saves it to
        {feed_id}/items.json with UTF-8 encoding and indentation.
        The feed directory is created automatically if it doesn't exist.
        The operation is protected by file locking.

        Parameters
        ----------
        feed_id : str
            Feed identifier (UUID format)
        data : FeedItemsData
            Feed items data to save

        Raises
        ------
        ValueError
            If feed_id is empty or data.feed_id doesn't match feed_id
        RSSError
            If JSON serialization or file write fails

        Examples
        --------
        >>> from pathlib import Path
        >>> from rss.types import FeedItemsData, FeedItem
        >>> storage = JSONStorage(Path("data/raw/rss"))
        >>> item = FeedItem(
        ...     item_id="660e8400-e29b-41d4-a716-446655440001",
        ...     title="Article Title",
        ...     link="https://example.com/article",
        ...     published="2026-01-14T09:00:00Z",
        ...     summary="Article summary...",
        ...     content="Full content...",
        ...     author="Author Name",
        ...     fetched_at="2026-01-14T10:00:00Z",
        ... )
        >>> items_data = FeedItemsData(
        ...     version="1.0",
        ...     feed_id="550e8400-e29b-41d4-a716-446655440000",
        ...     items=[item],
        ... )
        >>> storage.save_items("550e8400-e29b-41d4-a716-446655440000", items_data)
        """
        if not feed_id:
            logger.error("Invalid feed_id", feed_id=feed_id)
            raise ValueError("feed_id cannot be empty")

        if data.feed_id != feed_id:
            logger.error(
                "Feed ID mismatch",
                expected=feed_id,
                actual=data.feed_id,
            )
            raise ValueError(
                f"data.feed_id ({data.feed_id}) must match feed_id ({feed_id})"
            )

        feed_dir = self.data_dir / feed_id
        items_file = feed_dir / "items.json"

        logger.debug(
            "Saving items",
            feed_id=feed_id,
            items_file=str(items_file),
            items_count=len(data.items),
        )

        # Ensure feed directory exists
        feed_dir.mkdir(parents=True, exist_ok=True)

        with log_and_reraise(
            logger,
            f"save items for feed {feed_id}",
            context={"feed_id": feed_id, "items_file": str(items_file)},
            reraise_as=RSSError,
        ):
            with self.lock_manager.lock_items(feed_id):
                # Convert dataclass to dict
                data_dict = asdict(data)

                # Write JSON with UTF-8 encoding and indentation
                items_file.write_text(
                    json.dumps(data_dict, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

            logger.info(
                "Items saved successfully",
                feed_id=feed_id,
                items_file=str(items_file),
                items_count=len(data.items),
            )

    def load_items(self, feed_id: str) -> FeedItemsData:
        """Load feed items from {feed_id}/items.json.

        This method reads {feed_id}/items.json and deserializes it to FeedItemsData.
        If the file doesn't exist, returns an empty FeedItemsData with version "1.0".
        The operation is protected by file locking.

        Parameters
        ----------
        feed_id : str
            Feed identifier (UUID format)

        Returns
        -------
        FeedItemsData
            Loaded feed items data, or empty data if file doesn't exist

        Raises
        ------
        ValueError
            If feed_id is empty
        RSSError
            If JSON deserialization fails

        Examples
        --------
        >>> from pathlib import Path
        >>> storage = JSONStorage(Path("data/raw/rss"))
        >>> items_data = storage.load_items("550e8400-e29b-41d4-a716-446655440000")
        >>> items_data.version
        '1.0'
        >>> len(items_data.items)
        0
        """
        if not feed_id:
            logger.error("Invalid feed_id", feed_id=feed_id)
            raise ValueError("feed_id cannot be empty")

        items_file = self.data_dir / feed_id / "items.json"

        logger.debug(
            "Loading items",
            feed_id=feed_id,
            items_file=str(items_file),
        )

        # Return empty data if file doesn't exist
        if not items_file.exists():
            logger.info(
                "Items file not found, returning empty data",
                feed_id=feed_id,
                items_file=str(items_file),
            )
            return FeedItemsData(version="1.0", feed_id=feed_id, items=[])

        with log_and_reraise(
            logger,
            f"load items for feed {feed_id}",
            context={"feed_id": feed_id, "items_file": str(items_file)},
            reraise_as=RSSError,
        ):
            with self.lock_manager.lock_items(feed_id):
                content = items_file.read_text(encoding="utf-8")
                data_dict = json.loads(content)

                # Import here to avoid circular dependency
                from ..types import FeedItem

                # Reconstruct FeedItem objects
                items = [
                    FeedItem(**item_dict) for item_dict in data_dict.get("items", [])
                ]

                items_data = FeedItemsData(
                    version=data_dict["version"],
                    feed_id=data_dict["feed_id"],
                    items=items,
                )

            logger.info(
                "Items loaded successfully",
                feed_id=feed_id,
                items_file=str(items_file),
                items_count=len(items_data.items),
            )

            return items_data

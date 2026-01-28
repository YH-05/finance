"""Feed reading service for RSS feed items.

This module provides the FeedReader class for retrieving, searching,
and filtering feed items from the JSON storage.
"""

from pathlib import Path
from typing import Any

from ..storage.json_storage import JSONStorage
from ..types import FeedItem


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="feed_reader")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class FeedReader:
    """Service for reading and searching RSS feed items.

    This class provides methods for retrieving feed items with pagination
    and keyword search functionality.

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

    Examples
    --------
    >>> from pathlib import Path
    >>> reader = FeedReader(Path("data/raw/rss"))
    >>> items = reader.get_items(feed_id="550e8400-e29b-41d4-a716-446655440000")
    >>> for item in items:
    ...     print(item.title)
    """

    def __init__(self, data_dir: Path) -> None:
        """Initialize FeedReader.

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
        logger.debug("FeedReader initialized", data_dir=str(data_dir))

    def get_items(
        self,
        feed_id: str | None = None,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[FeedItem]:
        """Get feed items with optional pagination.

        Retrieves items from a specific feed or all feeds, sorted by
        published date in descending order (newest first).

        Parameters
        ----------
        feed_id : str | None, default=None
            Feed identifier. If None, returns items from all feeds.
        limit : int | None, default=None
            Maximum number of items to return. If None, returns all items.
        offset : int, default=0
            Number of items to skip before returning results.

        Returns
        -------
        list[FeedItem]
            List of feed items sorted by published date descending

        Examples
        --------
        >>> reader = FeedReader(Path("data/raw/rss"))
        >>> # Get all items from a specific feed
        >>> items = reader.get_items(feed_id="feed-001")
        >>> # Get first 10 items from all feeds
        >>> items = reader.get_items(limit=10)
        >>> # Pagination: skip first 20, get next 10
        >>> items = reader.get_items(limit=10, offset=20)
        """
        logger.debug(
            "Getting items",
            feed_id=feed_id,
            limit=limit,
            offset=offset,
        )

        items: list[FeedItem] = []

        if feed_id is not None:
            # Get items from specific feed
            items_data = self.storage.load_items(feed_id)
            items = list(items_data.items)
        else:
            # Get items from all feeds
            feeds_data = self.storage.load_feeds()
            for feed in feeds_data.feeds:
                items_data = self.storage.load_items(feed.feed_id)
                items.extend(items_data.items)

        # Sort by published date descending (None values go to the end)
        items = self._sort_by_published_desc(items)

        # Apply pagination
        if offset > 0:
            items = items[offset:]
        if limit is not None:
            items = items[:limit]

        logger.info(
            "Items retrieved",
            feed_id=feed_id,
            total_items=len(items),
            limit=limit,
            offset=offset,
        )

        return items

    def search_items(
        self,
        query: str,
        *,
        category: str | None = None,
        fields: list[str] | None = None,
        limit: int | None = None,
    ) -> list[FeedItem]:
        """Search feed items by keyword.

        Performs case-insensitive partial matching on specified fields.
        By default, searches in title, summary, and content fields.

        Parameters
        ----------
        query : str
            Search query string (case-insensitive partial match)
        category : str | None, default=None
            Filter by feed category. If None, searches all categories.
        fields : list[str] | None, default=None
            Fields to search in. If None, defaults to ["title", "summary", "content"].
        limit : int | None, default=None
            Maximum number of results to return.

        Returns
        -------
        list[FeedItem]
            List of matching items sorted by published date descending

        Examples
        --------
        >>> reader = FeedReader(Path("data/raw/rss"))
        >>> # Search in all fields
        >>> items = reader.search_items(query="Bitcoin")
        >>> # Search only in title field
        >>> items = reader.search_items(query="Bitcoin", fields=["title"])
        >>> # Filter by category
        >>> items = reader.search_items(query="market", category="finance")
        """
        logger.debug(
            "Searching items",
            query=query,
            category=category,
            fields=fields,
            limit=limit,
        )

        if fields is None:
            fields = ["title", "summary", "content"]

        # Get feeds filtered by category if specified
        feeds_data = self.storage.load_feeds()
        target_feeds = feeds_data.feeds
        if category is not None:
            target_feeds = [f for f in target_feeds if f.category == category]

        # Collect items from target feeds
        all_items: list[FeedItem] = []
        for feed in target_feeds:
            items_data = self.storage.load_items(feed.feed_id)
            all_items.extend(items_data.items)

        # Filter by query
        query_lower = query.lower()
        matched_items: list[FeedItem] = []

        for item in all_items:
            if self._item_matches_query(item, query_lower, fields):
                matched_items.append(item)

        # Sort by published date descending
        matched_items = self._sort_by_published_desc(matched_items)

        # Apply limit
        if limit is not None:
            matched_items = matched_items[:limit]

        logger.info(
            "Search completed",
            query=query,
            category=category,
            fields=fields,
            matched_count=len(matched_items),
            limit=limit,
        )

        return matched_items

    def _item_matches_query(
        self,
        item: FeedItem,
        query_lower: str,
        fields: list[str],
    ) -> bool:
        """Check if an item matches the search query.

        Parameters
        ----------
        item : FeedItem
            Feed item to check
        query_lower : str
            Lowercase search query
        fields : list[str]
            Fields to search in

        Returns
        -------
        bool
            True if item matches the query in any of the specified fields
        """
        for field in fields:
            value = getattr(item, field, None)
            if value is not None and query_lower in value.lower():
                return True
        return False

    def _sort_by_published_desc(self, items: list[FeedItem]) -> list[FeedItem]:
        """Sort items by published date in descending order.

        Items with None published date are placed at the end.

        Parameters
        ----------
        items : list[FeedItem]
            Items to sort

        Returns
        -------
        list[FeedItem]
            Sorted items (newest first, None published at end)
        """
        # Split into items with and without published date
        with_date = [x for x in items if x.published is not None]
        without_date = [x for x in items if x.published is None]

        # Sort those with dates in descending order
        with_date.sort(key=lambda x: x.published, reverse=True)  # type: ignore[arg-type]

        # Append those without dates at the end
        return with_date + without_date

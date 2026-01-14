"""Diff detector for RSS feed items."""

from typing import Any

from ..types import FeedItem


# ロガーを遅延初期化で循環インポートを回避
def _get_logger() -> Any:
    try:
        from finance.utils.logging_config import get_logger

        return get_logger(__name__, module="diff_detector")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class DiffDetector:
    """Detect new items by comparing existing and fetched items.

    This class identifies new feed items by comparing their link fields.
    Items with links that already exist in the existing items list are
    considered duplicates and excluded.

    Examples
    --------
    >>> detector = DiffDetector()
    >>> existing = [{"link": "https://example.com/1", ...}]
    >>> fetched = [
    ...     {"link": "https://example.com/1", ...},
    ...     {"link": "https://example.com/2", ...}
    ... ]
    >>> new_items = detector.detect_new_items(existing, fetched)
    >>> len(new_items)
    1
    """

    def __init__(self) -> None:
        """Initialize DiffDetector."""
        logger.debug("DiffDetector initialized")

    def detect_new_items(
        self, existing_items: list[FeedItem], fetched_items: list[FeedItem]
    ) -> list[FeedItem]:
        """Detect new items by comparing link fields.

        Parameters
        ----------
        existing_items : list[FeedItem]
            List of existing feed items
        fetched_items : list[FeedItem]
            List of newly fetched feed items

        Returns
        -------
        list[FeedItem]
            List of new items (items in fetched_items that are not in existing_items)

        Examples
        --------
        >>> detector = DiffDetector()
        >>> existing = []
        >>> fetched = [{"link": "https://example.com/1", ...}]
        >>> new_items = detector.detect_new_items(existing, fetched)
        >>> len(new_items)
        1
        """
        logger.debug(
            "差分検出開始",
            existing_count=len(existing_items),
            fetched_count=len(fetched_items),
        )

        # Extract links from existing items for fast lookup
        existing_links = {item["link"] for item in existing_items}

        # Filter fetched items to only include new ones
        new_items = [
            item for item in fetched_items if item["link"] not in existing_links
        ]

        logger.info(
            "差分検出完了",
            existing_count=len(existing_items),
            fetched_count=len(fetched_items),
            new_count=len(new_items),
        )

        return new_items

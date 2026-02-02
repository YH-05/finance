"""Duplicate checker for news articles.

This module provides a URL-based deduplication mechanism that prevents the same
news article from being collected multiple times. It maintains a history of
seen URLs with timestamps and supports time-based expiration.

Classes
-------
DuplicateChecker
    URL-based duplicate detection with file persistence and expiration.

Examples
--------
>>> checker = DuplicateChecker(history_days=7)
>>> article = Article(url="https://example.com/news/1", ...)
>>> checker.is_duplicate(article)
False
>>> checker.mark_seen(article)
>>> checker.is_duplicate(article)
True

>>> new_articles = checker.filter_new(articles)
>>> len(new_articles)  # Only articles not seen before
3
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from utils_core.logging import get_logger

from .article import Article

logger = get_logger(__name__, module="dedup")


class DuplicateChecker:
    """URL-based duplicate checker for news articles.

    Maintains a set of seen article URLs with timestamps. Articles whose URLs
    have been seen within ``history_days`` are considered duplicates. Older
    entries are automatically cleaned up on load and via ``clean_expired``.

    Parameters
    ----------
    history_days : int
        Number of days to retain seen URLs (default: 7).
        Must be a positive integer.

    Attributes
    ----------
    history_days : int
        Number of days to retain seen URLs.
    seen_count : int
        Number of currently tracked URLs (property).

    Raises
    ------
    ValueError
        If ``history_days`` is not a positive integer.

    Examples
    --------
    >>> checker = DuplicateChecker(history_days=7)
    >>> checker.seen_count
    0
    >>> checker.mark_seen(article)
    >>> checker.seen_count
    1
    """

    def __init__(self, history_days: int = 7) -> None:
        """Initialize DuplicateChecker with the given retention period.

        Parameters
        ----------
        history_days : int
            Number of days to retain seen URLs (default: 7).

        Raises
        ------
        ValueError
            If ``history_days`` is not positive.
        """
        if history_days <= 0:
            raise ValueError(f"history_days must be positive, got {history_days}")
        self._history_days = history_days
        self._seen_urls: dict[str, str] = {}
        logger.debug(
            "DuplicateChecker initialized",
            history_days=history_days,
        )

    @property
    def history_days(self) -> int:
        """Return the number of days to retain seen URLs.

        Returns
        -------
        int
            Retention period in days.
        """
        return self._history_days

    @property
    def seen_count(self) -> int:
        """Return the number of currently tracked URLs.

        Returns
        -------
        int
            Number of URLs in the seen set.
        """
        return len(self._seen_urls)

    def is_duplicate(self, article: Article) -> bool:
        """Check whether an article has already been seen.

        An article is considered a duplicate if its URL exists in the seen set
        and the recorded timestamp is within the retention period.

        Parameters
        ----------
        article : Article
            The article to check.

        Returns
        -------
        bool
            True if the article URL has been seen within ``history_days``.

        Examples
        --------
        >>> checker = DuplicateChecker()
        >>> checker.is_duplicate(article)
        False
        >>> checker.mark_seen(article)
        >>> checker.is_duplicate(article)
        True
        """
        url = str(article.url)
        if url not in self._seen_urls:
            return False

        # Check if the entry is still within the retention period
        seen_at_str = self._seen_urls[url]
        try:
            seen_at = datetime.fromisoformat(seen_at_str)
            cutoff = datetime.now(timezone.utc) - timedelta(days=self._history_days)
            if seen_at < cutoff:
                logger.debug(
                    "URL expired from history",
                    url=url,
                    seen_at=seen_at_str,
                )
                return False
        except (ValueError, TypeError):
            logger.warning(
                "Invalid timestamp for seen URL, treating as not duplicate",
                url=url,
                seen_at=seen_at_str,
            )
            return False

        return True

    def mark_seen(self, article: Article) -> None:
        """Mark an article as seen.

        Records the article URL with the current UTC timestamp.
        If the URL is already tracked, updates the timestamp.

        Parameters
        ----------
        article : Article
            The article to mark as seen.

        Examples
        --------
        >>> checker = DuplicateChecker()
        >>> checker.mark_seen(article)
        >>> checker.seen_count
        1
        """
        url = str(article.url)
        now = datetime.now(timezone.utc).isoformat()
        is_new = url not in self._seen_urls
        self._seen_urls[url] = now

        if is_new:
            logger.debug(
                "Article marked as seen",
                url=url,
            )

    def filter_new(self, articles: list[Article]) -> list[Article]:
        """Filter a list of articles, returning only those not seen before.

        Parameters
        ----------
        articles : list[Article]
            List of articles to filter.

        Returns
        -------
        list[Article]
            Articles whose URLs have not been seen within the retention period.

        Examples
        --------
        >>> new_articles = checker.filter_new(articles)
        >>> len(new_articles)
        3
        """
        new_articles = [a for a in articles if not self.is_duplicate(a)]
        logger.info(
            "Filtered articles for duplicates",
            total=len(articles),
            new=len(new_articles),
            duplicates=len(articles) - len(new_articles),
        )
        return new_articles

    def clean_expired(self) -> int:
        """Remove entries older than ``history_days`` from the seen set.

        Returns
        -------
        int
            Number of expired entries removed.

        Examples
        --------
        >>> removed = checker.clean_expired()
        >>> print(f"Removed {removed} expired entries")
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._history_days)
        expired_urls: list[str] = []

        for url, seen_at_str in self._seen_urls.items():
            try:
                seen_at = datetime.fromisoformat(seen_at_str)
                if seen_at < cutoff:
                    expired_urls.append(url)
            except (ValueError, TypeError):
                # Invalid timestamp entries are also cleaned
                expired_urls.append(url)

        for url in expired_urls:
            del self._seen_urls[url]

        if expired_urls:
            logger.info(
                "Expired entries cleaned",
                removed_count=len(expired_urls),
                remaining_count=len(self._seen_urls),
            )

        return len(expired_urls)

    def save(self, path: str | Path) -> None:
        """Save the seen URLs to a JSON file.

        Parameters
        ----------
        path : str | Path
            File path to save to. Parent directories are created if needed.

        Examples
        --------
        >>> checker.save("data/news/.history/seen_urls.json")
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        json_data = json.dumps(self._seen_urls, ensure_ascii=False, indent=2)
        file_path.write_text(json_data, encoding="utf-8")

        logger.info(
            "Seen URLs saved",
            path=str(file_path),
            url_count=len(self._seen_urls),
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
        history_days: int = 7,
    ) -> "DuplicateChecker":
        """Load seen URLs from a JSON file.

        Expired entries (older than ``history_days``) are automatically
        excluded during loading.

        Parameters
        ----------
        path : str | Path
            File path to load from.
        history_days : int
            Number of days to retain seen URLs (default: 7).

        Returns
        -------
        DuplicateChecker
            Loaded checker, or empty checker if file doesn't exist.

        Raises
        ------
        ValueError
            If the file contains invalid JSON.

        Examples
        --------
        >>> checker = DuplicateChecker.load("data/news/.history/seen_urls.json")
        >>> checker.seen_count
        42
        """
        file_path = Path(path)
        checker = cls(history_days=history_days)

        if not file_path.exists():
            logger.debug(
                "Seen URLs file not found, returning empty checker",
                path=str(file_path),
            )
            return checker

        try:
            json_data = file_path.read_text(encoding="utf-8")
            raw_data: dict[str, str] = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to load seen URLs file",
                path=str(file_path),
                error=str(e),
            )
            raise ValueError(f"Invalid JSON in seen URLs file: {e}") from e

        # Filter out expired entries
        cutoff = datetime.now(timezone.utc) - timedelta(days=history_days)
        for url, seen_at_str in raw_data.items():
            try:
                seen_at = datetime.fromisoformat(seen_at_str)
                if seen_at >= cutoff:
                    checker._seen_urls[url] = seen_at_str
            except (ValueError, TypeError):
                logger.warning(
                    "Skipping entry with invalid timestamp",
                    url=url,
                    seen_at=seen_at_str,
                )

        logger.info(
            "Seen URLs loaded",
            path=str(file_path),
            total_in_file=len(raw_data),
            loaded_count=len(checker._seen_urls),
            expired_count=len(raw_data) - len(checker._seen_urls),
        )

        return checker


__all__ = [
    "DuplicateChecker",
]

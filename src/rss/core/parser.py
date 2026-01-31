"""RSS/Atom feed parser module."""

import uuid
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser

from ..exceptions import FeedParseError
from ..types import FeedItem, FeedValidationResult


# Logger lazy initialization to avoid circular imports
def _get_logger() -> Any:
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="parser")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


class FeedParser:
    """RSS 2.0 and Atom feed parser.

    This class parses RSS 2.0 and Atom formatted feeds and converts them
    to a unified FeedItem structure.

    Examples
    --------
    >>> parser = FeedParser()
    >>> items = parser.parse(rss_content)
    >>> len(items)
    10
    """

    def parse(self, content: bytes) -> list[FeedItem]:
        """Parse RSS 2.0 or Atom feed content.

        Parameters
        ----------
        content : bytes
            Raw feed content as bytes

        Returns
        -------
        list[FeedItem]
            List of parsed feed items

        Raises
        ------
        FeedParseError
            If the content cannot be parsed as valid RSS 2.0 or Atom
        """
        logger.debug("Parsing feed content started", content_length=len(content))

        try:
            parsed = feedparser.parse(content)
        except Exception as e:
            logger.error(
                "Feed parsing failed",
                error=str(e),
                content_length=len(content),
                exc_info=True,
            )
            raise FeedParseError(f"Failed to parse feed: {e}") from e

        # Check for bozo errors (malformed feed)
        if parsed.bozo:
            bozo_exception = parsed.get("bozo_exception")
            # feedparser can still parse some malformed feeds, so only raise on critical errors
            if not parsed.entries and bozo_exception:
                error_msg = str(bozo_exception)
                logger.error(
                    "Feed parsing failed due to malformed content",
                    error=error_msg,
                    bozo=True,
                )
                raise FeedParseError(f"Failed to parse feed: {error_msg}")

        # Check if it's a recognized feed format (RSS or Atom)
        # feedparser sets version to empty string for unrecognized formats like HTML
        feed_version = getattr(parsed, "version", "")
        if not feed_version:
            logger.error(
                "Invalid feed format",
                version=feed_version,
                has_entries=bool(parsed.entries),
            )
            raise FeedParseError(
                "Invalid feed format: not a recognized RSS or Atom format"
            )

        # Check if it's a valid feed (has entries or is a recognized format)
        if not parsed.entries and not parsed.feed:
            logger.error(
                "Invalid feed format",
                has_entries=bool(parsed.entries),
                has_feed=bool(parsed.feed),
            )
            raise FeedParseError(
                "Invalid feed format: no entries or feed metadata found"
            )

        fetched_at = datetime.now(timezone.utc).isoformat()
        items: list[FeedItem] = []

        for entry in parsed.entries:
            try:
                item = self._convert_entry(entry, fetched_at)
                items.append(item)
            except Exception as e:
                logger.warning(
                    "Failed to convert entry, skipping",
                    error=str(e),
                    entry_title=entry.get("title", "unknown"),
                )
                continue

        logger.info(
            "Feed parsing completed",
            total_entries=len(parsed.entries),
            converted_items=len(items),
            feed_title=parsed.feed.get("title", "unknown"),
        )

        return items

    def _convert_entry(self, entry: Any, fetched_at: str) -> FeedItem:
        """Convert a feedparser entry to FeedItem.

        Parameters
        ----------
        entry : Any
            A feedparser entry object
        fetched_at : str
            Fetch timestamp in ISO 8601 format

        Returns
        -------
        FeedItem
            Converted feed item
        """
        item_id = str(uuid.uuid4())
        title = entry.get("title", "")
        link = entry.get("link", "")

        # Parse published date
        published = self._parse_published(entry)

        # Get summary (description in RSS, summary in Atom)
        summary = entry.get("summary") or entry.get("description")

        # Get content (content:encoded in RSS, content in Atom)
        content = self._extract_content(entry)

        # Get author
        author = entry.get("author")

        logger.debug(
            "Entry converted",
            item_id=item_id,
            title=title[:50] if title else None,
            has_published=published is not None,
            has_summary=summary is not None,
            has_content=content is not None,
            has_author=author is not None,
        )

        return FeedItem(
            item_id=item_id,
            title=title,
            link=link,
            published=published,
            summary=summary,
            content=content,
            author=author,
            fetched_at=fetched_at,
        )

    def _parse_published(self, entry: Any) -> str | None:
        """Parse published date from entry.

        Parameters
        ----------
        entry : Any
            A feedparser entry object

        Returns
        -------
        str | None
            ISO 8601 formatted date string, or None if not available
        """
        # feedparser provides parsed date as a time tuple
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (ValueError, TypeError):
                pass

        # Try updated_parsed as fallback (common in Atom)
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (ValueError, TypeError):
                pass

        # Try raw published string
        published_str = entry.get("published") or entry.get("updated")
        if published_str:
            try:
                # Try parsing RFC 2822 format
                dt = parsedate_to_datetime(published_str)
                return dt.isoformat()
            except (ValueError, TypeError):
                pass

        return None

    def _extract_content(self, entry: Any) -> str | None:
        """Extract full content from entry.

        Parameters
        ----------
        entry : Any
            A feedparser entry object

        Returns
        -------
        str | None
            Full content, or None if not available
        """
        # Atom content (can be a list)
        if "content" in entry and entry.content:
            contents = entry.content
            if isinstance(contents, list) and contents:
                # Prefer HTML content
                for c in contents:
                    if getattr(c, "type", "") == "text/html":
                        return c.get("value")
                # Fall back to first content
                return contents[0].get("value")
            return None

        return None

    def _validate_feed_content(
        self,
        content: bytes,
        content_type: str | None = None,
    ) -> FeedValidationResult:
        """Validate feed content format.

        Performs early validation of feed content before parsing.
        Checks for empty content, invalid Content-Type, non-XML content,
        and missing RSS/Atom elements.

        Parameters
        ----------
        content : bytes
            Raw feed content as bytes
        content_type : str | None, optional
            Content-Type header from HTTP response, by default None

        Returns
        -------
        FeedValidationResult
            Validation result with is_valid flag and error message

        Examples
        --------
        >>> parser = FeedParser()
        >>> result = parser._validate_feed_content(b"<rss>...</rss>")
        >>> result.is_valid
        True
        """
        # 1. Empty content check
        if not content or not content.strip():
            logger.warning(
                "Feed validation failed: empty content",
                content_length=len(content) if content else 0,
            )
            return FeedValidationResult(
                is_valid=False,
                error="Empty feed content",
            )

        # 2. Content-Type check (if provided)
        if content_type is not None:
            valid_content_types = [
                "application/rss+xml",
                "application/atom+xml",
                "application/xml",
                "text/xml",
                "text/html",  # Some sites return HTML content type
            ]
            content_type_lower = content_type.lower()
            if not any(ct in content_type_lower for ct in valid_content_types):
                logger.warning(
                    "Feed validation failed: invalid Content-Type",
                    content_type=content_type,
                    content_preview=content[:100].decode("utf-8", errors="replace"),
                )
                return FeedValidationResult(
                    is_valid=False,
                    error=f"Invalid Content-Type: {content_type}",
                )

        # 3. XML signature check
        try:
            content_str = content.decode("utf-8", errors="replace").strip()
        except Exception as e:
            logger.warning(
                "Feed validation failed: content decode error",
                error=str(e),
            )
            return FeedValidationResult(
                is_valid=False,
                error="Failed to decode content as UTF-8",
            )

        if not content_str.startswith("<?xml") and not content_str.startswith("<"):
            logger.warning(
                "Feed validation failed: content does not appear to be XML",
                content_preview=content_str[:100],
            )
            return FeedValidationResult(
                is_valid=False,
                error="Content does not appear to be XML",
            )

        # 4. RSS/Atom elements check
        has_rss = "<rss" in content_str or "<channel>" in content_str
        has_atom = "<feed" in content_str and "xmlns" in content_str

        if not has_rss and not has_atom:
            logger.warning(
                "Feed validation failed: no RSS or Atom elements found",
                content_preview=content_str[:200],
            )
            return FeedValidationResult(
                is_valid=False,
                error="No RSS or Atom elements found",
            )

        logger.debug(
            "Feed validation passed",
            content_length=len(content),
            has_rss=has_rss,
            has_atom=has_atom,
        )
        return FeedValidationResult(is_valid=True, error=None)

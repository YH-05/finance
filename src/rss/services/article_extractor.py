"""Article content extractor using trafilatura with httpx fallback.

This module provides an ArticleExtractor class that extracts article content
from web pages using trafilatura as the primary extraction engine, with
httpx + lxml as a fallback for cases where trafilatura fails.

Examples
--------
Single article extraction:
    >>> import asyncio
    >>> from rss.services.article_extractor import ArticleExtractor
    >>> extractor = ArticleExtractor()
    >>> result = asyncio.run(extractor.extract("https://example.com/article"))
    >>> print(result.title)

Batch extraction:
    >>> urls = ["https://example.com/a1", "https://example.com/a2"]
    >>> results = asyncio.run(extractor.extract_batch(urls))
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
import trafilatura
from lxml import html

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 30
"""Default timeout in seconds for HTTP requests."""

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
"""Default User-Agent header for HTTP requests."""

MIN_CONTENT_LENGTH = 100
"""Minimum content length (characters) to consider extraction successful."""


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_logger() -> Any:
    """Get logger with fallback to standard logging.

    Returns
    -------
    Any
        Logger instance (structlog or standard logging)
    """
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="article_extractor")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class ExtractionStatus(Enum):
    """Article extraction status.

    Attributes
    ----------
    SUCCESS : str
        Article content was successfully extracted.
    FAILED : str
        Extraction failed due to an error.
    PAYWALL : str
        Article is behind a paywall.
    TIMEOUT : str
        Request timed out.
    """

    SUCCESS = "success"
    FAILED = "failed"
    PAYWALL = "paywall"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class ExtractedArticle:
    """Result of article extraction.

    Attributes
    ----------
    url : str
        The URL of the article.
    title : str | None
        Article title.
    text : str | None
        Extracted article text content.
    author : str | None
        Author name.
    date : str | None
        Publication date.
    source : str | None
        Source/hostname of the article.
    language : str | None
        Detected language code.
    status : ExtractionStatus
        Extraction status.
    error : str | None
        Error message if extraction failed.
    extraction_method : str
        Method used for extraction ("trafilatura" or "fallback").
    """

    url: str
    title: str | None
    text: str | None
    author: str | None
    date: str | None
    source: str | None
    language: str | None
    status: ExtractionStatus
    error: str | None
    extraction_method: str


# ---------------------------------------------------------------------------
# HTML text extraction (fallback)
# ---------------------------------------------------------------------------

# Article body selectors (ordered by specificity)
ARTICLE_SELECTORS = [
    "//article",
    "//main",
    "//*[contains(@class, 'article-body')]",
    "//*[contains(@class, 'article-content')]",
    "//*[contains(@class, 'story-body')]",
    "//*[contains(@class, 'post-content')]",
    "//*[contains(@class, 'entry-content')]",
    "//*[contains(@id, 'article')]",
    "//*[contains(@id, 'content')]",
    "//*[@role='main']",
]
"""XPath selectors for locating article body in HTML."""


def _extract_text_fallback(html_content: str) -> tuple[str | None, str | None]:
    """Extract article text using lxml as fallback.

    Parameters
    ----------
    html_content : str
        Raw HTML string.

    Returns
    -------
    tuple[str | None, str | None]
        Tuple of (title, text).
    """
    if not html_content:
        return None, None

    try:
        tree = html.fromstring(html_content)
    except Exception:
        logger.debug("Failed to parse HTML with lxml")
        return None, None

    # Extract title
    title_elements = tree.xpath("//title/text()")
    title = title_elements[0].strip() if title_elements else None

    # Remove script and style elements
    for element in tree.xpath("//script | //style | //noscript"):
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

    # Try article-specific selectors
    text = None
    for selector in ARTICLE_SELECTORS:
        elements = tree.xpath(selector)
        if elements:
            raw_text = elements[0].text_content()
            text = _clean_text(raw_text)
            if text and len(text) >= MIN_CONTENT_LENGTH:
                logger.debug(
                    "Text extracted with selector",
                    selector=selector,
                    length=len(text),
                )
                break

    # Fallback: extract from <body>
    if not text or len(text) < MIN_CONTENT_LENGTH:
        body_elements = tree.xpath("//body")
        if body_elements:
            raw_text = body_elements[0].text_content()
            text = _clean_text(raw_text)
            logger.debug(
                "Text extracted from body fallback", length=len(text) if text else 0
            )

    return title, text


def _clean_text(text: str) -> str:
    """Clean extracted text by normalizing whitespace.

    Parameters
    ----------
    text : str
        Raw extracted text.

    Returns
    -------
    str
        Cleaned text with normalized whitespace.
    """
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned_lines)


# ---------------------------------------------------------------------------
# ArticleExtractor class
# ---------------------------------------------------------------------------


class ArticleExtractor:
    """Article content extractor using trafilatura with httpx fallback.

    This class provides methods to extract article content from web pages.
    It uses trafilatura as the primary extraction engine, which is optimized
    for news article extraction, and falls back to httpx + lxml if trafilatura
    fails.

    Attributes
    ----------
    timeout : int
        Request timeout in seconds.
    user_agent : str
        User-Agent header for HTTP requests.

    Examples
    --------
    >>> extractor = ArticleExtractor(timeout=60)
    >>> result = asyncio.run(extractor.extract("https://example.com/article"))
    >>> print(result.status)
    <ExtractionStatus.SUCCESS: 'success'>
    """

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        """Initialize ArticleExtractor.

        Parameters
        ----------
        timeout : int, default=30
            Request timeout in seconds.
        user_agent : str, default=DEFAULT_USER_AGENT
            User-Agent header for HTTP requests.
        """
        logger.debug(
            "Initializing ArticleExtractor",
            timeout=timeout,
            user_agent=user_agent[:50] + "...",
        )
        self.timeout = timeout
        self.user_agent = user_agent

    async def extract(
        self, url: str, user_agent: str | None = None
    ) -> ExtractedArticle:
        """Extract article content from a URL.

        Uses trafilatura as the primary extraction method. If trafilatura
        fails to fetch or extract content, falls back to httpx + lxml.

        Parameters
        ----------
        url : str
            The URL of the article to extract.
        user_agent : str | None, optional
            Custom User-Agent header to use for the request. If None,
            uses the default User-Agent set at initialization.

        Returns
        -------
        ExtractedArticle
            Extraction result containing the article content and metadata.

        Examples
        --------
        >>> extractor = ArticleExtractor()
        >>> result = asyncio.run(extractor.extract("https://example.com"))
        >>> if result.status == ExtractionStatus.SUCCESS:
        ...     print(result.text)
        """
        # Determine the User-Agent to use
        effective_user_agent = user_agent or self.user_agent
        logger.info(
            "Starting article extraction",
            url=url,
            user_agent=effective_user_agent[:50] + "..."
            if len(effective_user_agent) > 50
            else effective_user_agent,
        )

        # Try trafilatura first (run in thread pool to avoid blocking)
        loop = asyncio.get_running_loop()
        html_content: str | None = None

        try:
            html_content = await loop.run_in_executor(
                None,
                lambda: trafilatura.fetch_url(url),
            )
        except Exception as e:
            logger.warning(
                "Trafilatura fetch failed",
                url=url,
                error=str(e),
            )
            html_content = None

        if html_content:
            # Try to extract with trafilatura
            result: dict[str, Any] | None = None
            try:
                raw_result = await loop.run_in_executor(
                    None,
                    lambda: trafilatura.bare_extraction(
                        html_content,
                        include_comments=False,
                        include_tables=True,
                        favor_precision=True,
                    ),
                )
                # bare_extraction returns dict[str, Any] or None
                if isinstance(raw_result, dict):
                    result = raw_result
            except Exception as e:
                logger.warning(
                    "Trafilatura extraction failed",
                    url=url,
                    error=str(e),
                )
                result = None

            if result and result.get("text"):
                text_content = str(result.get("text", ""))
                logger.info(
                    "Trafilatura extraction successful",
                    url=url,
                    title=result.get("title"),
                    text_length=len(text_content),
                )
                return ExtractedArticle(
                    url=url,
                    title=result.get("title"),
                    text=text_content,
                    author=result.get("author"),
                    date=result.get("date"),
                    source=result.get("hostname") or result.get("sitename"),
                    language=result.get("language"),
                    status=ExtractionStatus.SUCCESS,
                    error=None,
                    extraction_method="trafilatura",
                )

        # Fallback to httpx + lxml
        logger.debug("Trying fallback extraction with httpx + lxml", url=url)
        return await self._extract_with_fallback(url, effective_user_agent)

    async def _extract_with_fallback(
        self, url: str, user_agent: str | None = None
    ) -> ExtractedArticle:
        """Extract article content using httpx + lxml as fallback.

        Parameters
        ----------
        url : str
            The URL of the article to extract.
        user_agent : str | None, optional
            Custom User-Agent header to use. If None, uses the default.

        Returns
        -------
        ExtractedArticle
            Extraction result.
        """
        effective_user_agent = user_agent or self.user_agent
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={"User-Agent": effective_user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text

        except httpx.TimeoutException as e:
            logger.warning("Fallback fetch timed out", url=url, error=str(e))
            return ExtractedArticle(
                url=url,
                title=None,
                text=None,
                author=None,
                date=None,
                source=None,
                language=None,
                status=ExtractionStatus.TIMEOUT,
                error=f"Request timed out: {e}",
                extraction_method="fallback",
            )

        except httpx.HTTPStatusError as e:
            logger.warning(
                "Fallback fetch HTTP error",
                url=url,
                status_code=e.response.status_code,
            )
            return ExtractedArticle(
                url=url,
                title=None,
                text=None,
                author=None,
                date=None,
                source=None,
                language=None,
                status=ExtractionStatus.FAILED,
                error=f"HTTP {e.response.status_code}: {e}",
                extraction_method="fallback",
            )

        except httpx.HTTPError as e:
            logger.warning("Fallback fetch failed", url=url, error=str(e))
            return ExtractedArticle(
                url=url,
                title=None,
                text=None,
                author=None,
                date=None,
                source=None,
                language=None,
                status=ExtractionStatus.FAILED,
                error=str(e),
                extraction_method="fallback",
            )

        # Extract text using lxml
        title, text = _extract_text_fallback(html_content)

        if not text or len(text) < MIN_CONTENT_LENGTH:
            logger.warning(
                "Fallback extraction: insufficient content",
                url=url,
                text_length=len(text) if text else 0,
            )
            return ExtractedArticle(
                url=url,
                title=title,
                text=text,
                author=None,
                date=None,
                source=None,
                language=None,
                status=ExtractionStatus.FAILED,
                error="Insufficient content extracted",
                extraction_method="fallback",
            )

        logger.info(
            "Fallback extraction successful",
            url=url,
            title=title,
            text_length=len(text),
        )
        return ExtractedArticle(
            url=url,
            title=title,
            text=text,
            author=None,
            date=None,
            source=None,
            language=None,
            status=ExtractionStatus.SUCCESS,
            error=None,
            extraction_method="fallback",
        )

    async def extract_batch(
        self,
        urls: list[str],
        rate_limit: float = 1.0,
    ) -> list[ExtractedArticle]:
        """Extract article content from multiple URLs with rate limiting.

        Parameters
        ----------
        urls : list[str]
            List of URLs to extract.
        rate_limit : float, default=1.0
            Minimum interval between requests in seconds.

        Returns
        -------
        list[ExtractedArticle]
            List of extraction results in the same order as input URLs.

        Examples
        --------
        >>> extractor = ArticleExtractor()
        >>> urls = ["https://example.com/a1", "https://example.com/a2"]
        >>> results = asyncio.run(extractor.extract_batch(urls, rate_limit=0.5))
        >>> for result in results:
        ...     print(result.status)
        """
        if not urls:
            logger.debug("Empty URL list provided")
            return []

        logger.info(
            "Starting batch extraction",
            url_count=len(urls),
            rate_limit=rate_limit,
        )

        results: list[ExtractedArticle] = []

        for i, url in enumerate(urls):
            if i > 0 and rate_limit > 0:
                await asyncio.sleep(rate_limit)

            result = await self.extract(url)
            results.append(result)

            logger.debug(
                "Batch extraction progress",
                current=i + 1,
                total=len(urls),
                url=url,
                status=result.status.value,
            )

        success_count = sum(1 for r in results if r.status == ExtractionStatus.SUCCESS)
        logger.info(
            "Batch extraction completed",
            total=len(urls),
            success=success_count,
            failed=len(urls) - success_count,
        )

        return results

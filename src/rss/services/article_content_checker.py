"""Article content accessibility checker with 3-tier verification.

Checks whether an article URL's content is accessible by using a
3-tier approach:
- Tier 1: httpx (fast, ~0.5s) - HTTP GET + lxml text extraction
- Tier 2: Playwright (JS-capable, ~3-5s) - headless Chromium rendering
- Tier 3: Paywall indicator analysis - detects paywall patterns

Examples
--------
CLI usage:
    $ uv run python -m rss.services.article_content_checker "https://example.com/article"

Programmatic usage:
    >>> import asyncio
    >>> from rss.services.article_content_checker import check_article_content
    >>> result = asyncio.run(check_article_content("https://example.com/article"))
    >>> print(result.status)
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
from lxml import html

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_CONTENT_LENGTH = 200
"""Minimum content length (characters) to consider article accessible."""

HTTPX_TIMEOUT = 15
"""Timeout in seconds for httpx requests."""

PLAYWRIGHT_TIMEOUT = 30_000
"""Timeout in milliseconds for Playwright page load."""

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
"""User-Agent header for HTTP requests."""

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

# Paywall indicators
PAYWALL_INDICATORS_EN = [
    "subscribe to continue",
    "sign in to read",
    "premium content",
    "members only",
    "paywall",
    "unlock this article",
    "start your free trial",
    "already a subscriber",
    "create an account to read",
]
"""English paywall indicator phrases."""

PAYWALL_INDICATORS_JA = [
    "有料会員限定",
    "続きを読むには",
    "ログインして",
    "会員登録が必要",
    "月額",
    "プレミアム記事",
    "有料プラン",
]
"""Japanese paywall indicator phrases."""


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

        return get_logger(__name__, module="article_content_checker")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class ContentStatus(Enum):
    """Article content accessibility status.

    Attributes
    ----------
    ACCESSIBLE : str
        Article content is fully accessible.
    PAYWALLED : str
        Article is behind a paywall.
    INSUFFICIENT : str
        Article content is insufficient (too short or empty).
    FETCH_ERROR : str
        An error occurred while fetching the article.
    """

    ACCESSIBLE = "accessible"
    PAYWALLED = "paywalled"
    INSUFFICIENT = "insufficient"
    FETCH_ERROR = "fetch_error"


@dataclass(frozen=True)
class ContentCheckResult:
    """Result of an article content accessibility check.

    Attributes
    ----------
    status : ContentStatus
        The accessibility status of the article.
    content_length : int
        Character count of the extracted text.
    raw_text : str
        Extracted article body text. Only meaningful when status is
        ACCESSIBLE; may be partial or empty otherwise.
    reason : str
        Human-readable explanation of the determination.
    tier_used : int
        Which tier produced the final result (1, 2, or 3).
    """

    status: ContentStatus
    content_length: int
    raw_text: str
    reason: str
    tier_used: int


# ---------------------------------------------------------------------------
# HTML text extraction
# ---------------------------------------------------------------------------


def extract_article_text(html_content: str) -> str:
    """Extract article body text from HTML using XPath selectors.

    Tries multiple XPath selectors in order of specificity.
    Falls back to ``<body>`` if no article-specific element is found.

    Parameters
    ----------
    html_content : str
        Raw HTML string.

    Returns
    -------
    str
        Extracted plain text from the article body.
    """
    if not html_content:
        return ""

    try:
        tree = html.fromstring(html_content)
    except Exception:
        logger.debug("Failed to parse HTML with lxml")
        return ""

    # Remove script and style elements
    for element in tree.xpath("//script | //style | //noscript"):
        element.getparent().remove(element)

    # Try article-specific selectors
    for selector in ARTICLE_SELECTORS:
        elements = tree.xpath(selector)
        if elements:
            text = elements[0].text_content()
            cleaned = _clean_text(text)
            if cleaned:
                logger.debug(
                    "Text extracted with selector",
                    selector=selector,
                    length=len(cleaned),
                )
                return cleaned

    # Fallback: extract from <body>
    body_elements = tree.xpath("//body")
    if body_elements:
        text = body_elements[0].text_content()
        cleaned = _clean_text(text)
        logger.debug("Text extracted from body fallback", length=len(cleaned))
        return cleaned

    return ""


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
# Tier 1: httpx
# ---------------------------------------------------------------------------


async def _fetch_with_httpx(url: str) -> tuple[str, int]:
    """Fetch article content using httpx (Tier 1).

    Parameters
    ----------
    url : str
        The article URL to fetch.

    Returns
    -------
    tuple[str, int]
        Tuple of (extracted_text, status_code).

    Raises
    ------
    httpx.HTTPError
        If the HTTP request fails.
    """
    logger.debug("Tier 1: Fetching with httpx", url=url)
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(HTTPX_TIMEOUT),
        headers={"User-Agent": DEFAULT_USER_AGENT},
        follow_redirects=True,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

        text = extract_article_text(response.text)
        logger.debug(
            "Tier 1: Text extracted",
            url=url,
            content_length=len(text),
            status_code=response.status_code,
        )
        return text, response.status_code


# ---------------------------------------------------------------------------
# Tier 2: Playwright
# ---------------------------------------------------------------------------


async def _fetch_with_playwright(url: str) -> str:
    """Fetch article content using Playwright headless browser (Tier 2).

    Uses headless Chromium to render JavaScript-heavy pages and extract
    article text from the rendered DOM.

    Parameters
    ----------
    url : str
        The article URL to fetch.

    Returns
    -------
    str
        Extracted article text from the rendered page.

    Raises
    ------
    Exception
        If Playwright is not installed or browser launch fails.
    """
    logger.debug("Tier 2: Fetching with Playwright", url=url)
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("Playwright not installed, skipping Tier 2")
        return ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(
                user_agent=DEFAULT_USER_AGENT,
            )
            await page.goto(url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)
            html_content = await page.content()
            text = extract_article_text(html_content)
            logger.debug(
                "Tier 2: Text extracted",
                url=url,
                content_length=len(text),
            )
            return text
        finally:
            await browser.close()


# ---------------------------------------------------------------------------
# Tier 3: Paywall detection
# ---------------------------------------------------------------------------


def detect_paywall(text: str, content_length: int) -> bool:
    """Detect paywall indicators in article text.

    Checks for English and Japanese paywall phrases. The detection
    threshold varies based on content length:
    - Short content (< 200 chars) + 1 indicator = paywalled
    - Medium content (200-1500 chars) + 2 indicators = paywalled

    Parameters
    ----------
    text : str
        Article text to analyze.
    content_length : int
        Length of the article text.

    Returns
    -------
    bool
        True if paywall indicators are detected, False otherwise.
    """
    text_lower = text.lower()
    all_indicators = PAYWALL_INDICATORS_EN + PAYWALL_INDICATORS_JA
    matches = sum(1 for indicator in all_indicators if indicator.lower() in text_lower)

    logger.debug(
        "Paywall detection",
        content_length=content_length,
        indicator_matches=matches,
    )

    # Short content + any indicator = paywalled
    if content_length < MIN_CONTENT_LENGTH and matches >= 1:
        return True

    # Medium content + multiple indicators = paywalled
    return content_length < 1500 and matches >= 2


# ---------------------------------------------------------------------------
# Main check function
# ---------------------------------------------------------------------------


async def check_article_content(url: str) -> ContentCheckResult:
    """Check article content accessibility with 3-tier verification.

    Tier 1 (httpx): Fast HTTP fetch + lxml text extraction.
    Tier 2 (Playwright): Headless browser for JS-rendered pages.
    Tier 3 (Paywall check): Indicator-based paywall detection.

    Parameters
    ----------
    url : str
        The article URL to check.

    Returns
    -------
    ContentCheckResult
        The result of the content accessibility check.

    Examples
    --------
    >>> import asyncio
    >>> result = asyncio.run(check_article_content("https://example.com"))
    >>> result.status  # doctest: +SKIP
    <ContentStatus.ACCESSIBLE: 'accessible'>
    """
    logger.info("Starting content check", url=url)

    # --- Tier 1: httpx ---
    try:
        text, _status_code = await _fetch_with_httpx(url)
    except httpx.HTTPStatusError as e:
        reason = f"Tier 1: HTTP {e.response.status_code} error"
        logger.warning(reason, url=url)
        return ContentCheckResult(
            status=ContentStatus.FETCH_ERROR,
            content_length=0,
            raw_text="",
            reason=reason,
            tier_used=1,
        )
    except (httpx.HTTPError, Exception) as e:
        reason = f"Tier 1: {type(e).__name__}: {e}"
        logger.warning(reason, url=url)
        return ContentCheckResult(
            status=ContentStatus.FETCH_ERROR,
            content_length=0,
            raw_text="",
            reason=reason,
            tier_used=1,
        )

    content_length = len(text)

    # If Tier 1 extracted enough text, proceed to Tier 3
    if content_length >= MIN_CONTENT_LENGTH:
        logger.debug(
            "Tier 1: Sufficient content, proceeding to Tier 3", length=content_length
        )
        return _check_paywall(text, content_length, tier_used=1, url=url)

    # --- Tier 2: Playwright (only if Tier 1 insufficient) ---
    logger.debug(
        "Tier 1: Insufficient content, trying Tier 2",
        tier1_length=content_length,
    )

    try:
        playwright_text = await _fetch_with_playwright(url)
    except Exception as e:
        logger.warning(
            "Tier 2: Playwright failed",
            url=url,
            error=str(e),
        )
        playwright_text = ""

    playwright_length = len(playwright_text)

    if playwright_length >= MIN_CONTENT_LENGTH:
        logger.debug(
            "Tier 2: Sufficient content, proceeding to Tier 3",
            length=playwright_length,
        )
        return _check_paywall(playwright_text, playwright_length, tier_used=2, url=url)

    # Both Tier 1 and Tier 2 insufficient
    best_text = playwright_text if playwright_length > content_length else text
    best_length = max(content_length, playwright_length)
    tier_used = 2 if playwright_length > content_length else 1

    reason = (
        f"Tier {tier_used}: 本文不十分 "
        f"(Tier 1: {content_length}文字, Tier 2: {playwright_length}文字, "
        f"閾値: {MIN_CONTENT_LENGTH}文字)"
    )
    logger.info(reason, url=url)
    return ContentCheckResult(
        status=ContentStatus.INSUFFICIENT,
        content_length=best_length,
        raw_text=best_text,
        reason=reason,
        tier_used=tier_used,
    )


def _check_paywall(
    text: str,
    content_length: int,
    *,
    tier_used: int,
    url: str,
) -> ContentCheckResult:
    """Run Tier 3 paywall check on extracted text.

    Parameters
    ----------
    text : str
        Extracted article text.
    content_length : int
        Length of the extracted text.
    tier_used : int
        Which tier extracted the text (1 or 2).
    url : str
        Article URL for logging.

    Returns
    -------
    ContentCheckResult
        PAYWALLED if indicators found, ACCESSIBLE otherwise.
    """
    is_paywalled = detect_paywall(text, content_length)

    if is_paywalled:
        # Find which indicators matched for the reason string
        text_lower = text.lower()
        all_indicators = PAYWALL_INDICATORS_EN + PAYWALL_INDICATORS_JA
        matched = [ind for ind in all_indicators if ind.lower() in text_lower]
        reason = (
            f"Tier 3: ペイウォール検出 "
            f"(Tier {tier_used}で取得, {content_length}文字, "
            f"検出指標: {matched})"
        )
        logger.info(reason, url=url)
        return ContentCheckResult(
            status=ContentStatus.PAYWALLED,
            content_length=content_length,
            raw_text=text,
            reason=reason,
            tier_used=3,
        )

    reason = f"Tier {tier_used}: 本文取得成功 ({content_length}文字)"
    logger.info(reason, url=url)
    return ContentCheckResult(
        status=ContentStatus.ACCESSIBLE,
        content_length=content_length,
        raw_text=text,
        reason=reason,
        tier_used=tier_used,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


async def _main(url: str) -> None:
    """CLI entry point for article content checking.

    Parameters
    ----------
    url : str
        The article URL to check.
    """
    result = await check_article_content(url)
    output = {
        "status": result.status.value,
        "content_length": result.content_length,
        "reason": result.reason,
        "tier_used": result.tier_used,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python -m rss.services.article_content_checker <url>",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(_main(sys.argv[1]))

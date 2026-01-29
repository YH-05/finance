"""URL normalization utilities for duplicate detection in news workflows.

Provides URL normalization functions used to compare article URLs when
checking for duplicates across RSS feeds. The normalization is applied
only during comparison; stored URLs retain their original form.

Examples
--------
>>> from rss.utils.url_normalizer import normalize_url
>>> normalize_url("https://www.cnbc.com/article?utm_source=twitter#section")
'https://cnbc.com/article'

>>> normalize_url("https://EXAMPLE.COM/news/index.html")
'https://example.com/news'
"""

from __future__ import annotations

import urllib.parse
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRACKING_PARAMS: frozenset[str] = frozenset(
    {
        # Prefix-type (ending with "_")
        "utm_",
        "guce_",
        # Exact-match type (existing)
        "ncid",
        "fbclid",
        "gclid",
        # Exact-match type (newly added)
        "ref",
        "source",
        "campaign",
        "si",
        "mc_cid",
        "mc_eid",
        "sref",
        "taid",
        "mod",
        "cmpid",
    }
)
"""Tracking parameters to remove during URL normalization.

Parameters ending with ``_`` are treated as prefix matches (e.g.,
``utm_`` matches ``utm_source``, ``utm_medium``, etc.). All others
are exact matches.
"""

TITLE_SIMILARITY_THRESHOLD: float = 0.85
"""Default Jaccard similarity threshold for title-based duplicate detection."""


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_logger() -> Any:
    """Get logger with fallback to standard logging.

    Returns
    -------
    Any
        Logger instance (structlog or standard logging).
    """
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="url_normalizer")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------


def _is_tracking_param(param_name: str) -> bool:
    """Check if a query parameter is a tracking parameter.

    Parameters
    ----------
    param_name : str
        The query parameter name to check.

    Returns
    -------
    bool
        True if the parameter should be removed during normalization.

    Examples
    --------
    >>> _is_tracking_param("utm_source")
    True
    >>> _is_tracking_param("page")
    False
    """
    return any(
        param_name.startswith(prefix) if prefix.endswith("_") else param_name == prefix
        for prefix in TRACKING_PARAMS
    )


def normalize_url(url: str) -> str:
    """Normalize a URL for duplicate comparison.

    Applies the following transformations for consistent comparison:

    1. Remove trailing slashes
    2. Lowercase the host (netloc)
    3. Remove ``www.`` prefix from host
    4. Remove URL fragment (``#section``)
    5. Remove trailing ``/index.html`` from path
    6. Remove tracking query parameters (see ``TRACKING_PARAMS``)

    Parameters
    ----------
    url : str
        The URL to normalize.

    Returns
    -------
    str
        Normalized URL suitable for comparison.
        Returns empty string if input is empty.

    Notes
    -----
    This function is intended for duplicate detection only.
    When creating GitHub Issues, always use the original RSS ``link``
    URL, not the normalized version.

    Examples
    --------
    >>> normalize_url("https://www.cnbc.com/article/")
    'https://cnbc.com/article'

    >>> normalize_url("https://example.com/news?utm_source=twitter&page=1")
    'https://example.com/news?page=1'

    >>> normalize_url("https://example.com/article#comments")
    'https://example.com/article'

    >>> normalize_url("https://example.com/news/index.html")
    'https://example.com/news'

    >>> normalize_url("")
    ''
    """
    if not url:
        return ""

    # Strip trailing slashes
    url = url.rstrip("/")

    # Parse URL
    parsed = urllib.parse.urlparse(url)

    # Lowercase host + remove www. prefix
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    # Remove fragment
    parsed = parsed._replace(fragment="")

    # Remove trailing /index.html
    path = parsed.path
    if path.endswith("/index.html"):
        path = path[: -len("/index.html")]
    parsed = parsed._replace(path=path)

    # Remove tracking query parameters
    if parsed.query:
        params = urllib.parse.parse_qs(parsed.query)
        filtered_params = {k: v for k, v in params.items() if not _is_tracking_param(k)}
        new_query = urllib.parse.urlencode(filtered_params, doseq=True)
        parsed = parsed._replace(query=new_query)

    # Reassemble
    normalized = urllib.parse.urlunparse(parsed._replace(netloc=netloc))

    logger.debug(
        "URL normalized",
        original=url,
        normalized=normalized,
    )

    return normalized


# ---------------------------------------------------------------------------
# Title similarity
# ---------------------------------------------------------------------------


def calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate Jaccard similarity between two article titles.

    Splits both titles into word sets (lowercased) and computes the
    Jaccard coefficient: ``|intersection| / |union|``.

    Parameters
    ----------
    title1 : str
        First title.
    title2 : str
        Second title.

    Returns
    -------
    float
        Similarity score between 0.0 and 1.0.

    Examples
    --------
    >>> calculate_title_similarity("S&P 500 hits record", "S&P 500 hits record")
    1.0

    >>> calculate_title_similarity("", "Some title")
    0.0
    """
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())

    if not words1 or not words2:
        return 0.0

    common = words1.intersection(words2)
    total = words1.union(words2)

    return len(common) / len(total)


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


def is_duplicate(
    new_item: dict[str, Any],
    existing_issues: list[dict[str, Any]],
    threshold: float = TITLE_SIMILARITY_THRESHOLD,
) -> tuple[bool, int | None, str | None]:
    """Check whether a new RSS item duplicates an existing GitHub Issue.

    Comparison is performed on normalized URLs (exact match) and
    title similarity (Jaccard coefficient above ``threshold``).

    Parameters
    ----------
    new_item : dict[str, Any]
        The new RSS article. Must contain ``'link'`` and ``'title'`` keys.
    existing_issues : list[dict[str, Any]]
        Existing GitHub Issues. Each should contain ``'article_url'``,
        ``'title'``, and ``'number'`` keys.
    threshold : float
        Jaccard similarity threshold for title match (default 0.85).

    Returns
    -------
    tuple[bool, int | None, str | None]
        A 3-tuple of ``(is_dup, issue_number, reason)``.
        ``is_dup`` is True if a duplicate was found.
        ``issue_number`` is the matching Issue number (or None).
        ``reason`` describes why it was flagged (or None).

    Examples
    --------
    >>> item = {"link": "https://example.com/article", "title": "Breaking news"}
    >>> issues = [{"article_url": "https://www.example.com/article",
    ...            "title": "[Index] Breaking news", "number": 42}]
    >>> is_dup, num, reason = is_duplicate(item, issues)
    """
    new_link = new_item.get("link", "")
    new_title = new_item.get("title", "")
    new_link_normalized = normalize_url(new_link)

    for issue in existing_issues:
        # Use article_url field (pre-extracted by orchestrator)
        existing_url = issue.get("article_url", "")
        existing_url_normalized = normalize_url(existing_url)

        # URL exact match (after normalization)
        if (
            new_link_normalized
            and existing_url_normalized
            and new_link_normalized == existing_url_normalized
        ):
            logger.debug(
                "Duplicate detected by URL",
                new_url=new_link,
                existing_issue=issue.get("number"),
            )
            return True, issue.get("number"), "URL一致"

        # Title similarity check
        existing_title = issue.get("title", "")
        # Strip theme prefix like "[株価指数] " from existing title
        if "] " in existing_title:
            existing_title_clean = existing_title.split("] ", 1)[1]
        else:
            existing_title_clean = existing_title

        similarity = calculate_title_similarity(new_title, existing_title_clean)
        if similarity >= threshold:
            logger.debug(
                "Duplicate detected by title similarity",
                new_title=new_title,
                existing_title=existing_title,
                similarity=similarity,
                existing_issue=issue.get("number"),
            )
            return True, issue.get("number"), f"タイトル類似 ({similarity:.2f})"

    return False, None, None

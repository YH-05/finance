"""Custom scraper for Perplexity AI hub pages (Tier 3).

Perplexity AI's hub page (https://perplexity.ai/hub) is SPA/JS-heavy
and requires Playwright for rendering. This scraper provides a custom
``extract_article_list`` implementation that parses the rendered HTML
to extract article metadata using CSS selectors specific to Perplexity's
hub page structure.

Examples
--------
>>> from rss.services.company_scrapers.engine import CompanyScraperEngine
>>> from rss.services.company_scrapers.custom.perplexity import PerplexityScraper
>>> engine = CompanyScraperEngine()
>>> scraper = PerplexityScraper(engine=engine)
>>> scraper.company_key
'perplexity_ai'
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from lxml.html import fromstring

from rss.services.company_scrapers.base import BaseCompanyScraper
from rss.services.company_scrapers.configs.ai_llm import PERPLEXITY_AI
from rss.services.company_scrapers.types import ArticleMetadata

if TYPE_CHECKING:
    from lxml.html import HtmlElement

    from rss.services.company_scrapers.types import CompanyConfig


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="perplexity_scraper")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


# ---------------------------------------------------------------------------
# PerplexityScraper
# ---------------------------------------------------------------------------


class PerplexityScraper(BaseCompanyScraper):
    """Custom scraper for Perplexity AI hub pages.

    Overrides ``extract_article_list`` to handle Perplexity's SPA-rendered
    hub page structure. Uses CSS selectors to extract article cards
    containing titles, URLs, and publication dates.

    The scraper expects the following HTML structure::

        <div class="hub-post">
          <a href="/hub/article-slug">
            <h2 class="hub-post__title">Article Title</h2>
          </a>
          <span class="hub-post__date">2026-01-15</span>
        </div>

    Parameters
    ----------
    engine : CompanyScraperEngine
        The shared scraping engine for page fetching and article processing.

    Examples
    --------
    >>> engine = CompanyScraperEngine()
    >>> scraper = PerplexityScraper(engine=engine)
    >>> scraper.company_key
    'perplexity_ai'
    >>> scraper.config.requires_playwright
    True
    """

    # -- Properties ----------------------------------------------------------

    @property
    def company_key(self) -> str:
        """Unique identifier for Perplexity AI.

        Returns
        -------
        str
            Always returns ``"perplexity_ai"``.
        """
        return "perplexity_ai"

    @property
    def config(self) -> CompanyConfig:
        """Perplexity AI scraping configuration.

        Returns the pre-defined configuration from ``configs.ai_llm``
        which includes ``requires_playwright=True`` and a 5-second
        rate limit.

        Returns
        -------
        CompanyConfig
            Perplexity AI configuration with SPA-specific settings.
        """
        return PERPLEXITY_AI

    # -- Custom extraction ---------------------------------------------------

    async def extract_article_list(self, html: str) -> list[ArticleMetadata]:
        """Extract article metadata from Perplexity's hub listing page.

        Parses the rendered HTML to find article cards matching
        Perplexity's hub page structure. Each card is expected to
        contain a title element, a link, and optionally a date element.

        Parameters
        ----------
        html : str
            Raw HTML of the Perplexity hub page (after JS rendering).

        Returns
        -------
        list[ArticleMetadata]
            List of article metadata extracted from the page.
            Articles missing a title or URL are skipped.
        """
        if not html:
            logger.debug("Empty HTML received, returning empty list")
            return []

        doc = self._parse_html_safe(html)
        if doc is None:
            logger.warning("Failed to parse Perplexity hub HTML")
            return []

        article_elements = doc.cssselect(self.config.article_list_selector)
        if not article_elements:
            logger.debug(
                "No article elements found",
                selector=self.config.article_list_selector,
            )
            return []

        results: list[ArticleMetadata] = []
        for element in article_elements:
            meta = self._extract_single_article(element)
            if meta is not None:
                results.append(meta)

        logger.info(
            "Perplexity articles extracted",
            total_elements=len(article_elements),
            extracted_count=len(results),
        )

        return results

    # -- Internal helpers ----------------------------------------------------

    def _extract_single_article(
        self,
        element: HtmlElement,
    ) -> ArticleMetadata | None:
        """Extract metadata from a single hub-post element.

        Parameters
        ----------
        element : HtmlElement
            A hub-post element from the listing page.

        Returns
        -------
        ArticleMetadata | None
            Extracted metadata, or None if title or URL is missing.
        """
        # Extract title
        title = self._extract_title(element)
        if not title:
            logger.debug("Skipping article: no title found")
            return None

        # Extract URL
        url = self._extract_url(element)
        if not url:
            logger.debug(
                "Skipping article: no URL found",
                title=title,
            )
            return None

        # Extract date (optional)
        date = self._extract_date(element)

        return ArticleMetadata(url=url, title=title, date=date)

    def _extract_title(self, element: HtmlElement) -> str | None:
        """Extract article title from a hub-post element.

        Parameters
        ----------
        element : HtmlElement
            A hub-post element.

        Returns
        -------
        str | None
            Article title, or None if not found or empty.
        """
        title_elements = element.cssselect(self.config.article_title_selector)
        if not title_elements:
            return None

        title = title_elements[0].text_content().strip()
        return title if title else None

    def _extract_url(self, element: HtmlElement) -> str | None:
        """Extract article URL from a hub-post element.

        Looks for ``<a>`` tags within the element and resolves
        relative URLs against the blog URL.

        Parameters
        ----------
        element : HtmlElement
            A hub-post element.

        Returns
        -------
        str | None
            Absolute article URL, or None if no link found.
        """
        # Check <a> children for href
        links = element.cssselect("a")
        for link in links:
            href = link.get("href")
            if href:
                return self._resolve_url(href)

        # Check element itself
        href = element.get("href")
        if href:
            return self._resolve_url(href)

        return None

    def _extract_date(self, element: HtmlElement) -> str | None:
        """Extract publication date from a hub-post element.

        Parameters
        ----------
        element : HtmlElement
            A hub-post element.

        Returns
        -------
        str | None
            Date string, or None if not found or empty.
        """
        date_elements = element.cssselect(self.config.article_date_selector)
        if not date_elements:
            return None

        date_text = date_elements[0].text_content().strip()
        return date_text if date_text else None

    def _resolve_url(self, href: str) -> str:
        """Resolve a potentially relative URL against the blog URL.

        Parameters
        ----------
        href : str
            URL or relative path.

        Returns
        -------
        str
            Absolute URL.
        """
        if href.startswith(("http://", "https://")):
            return href
        return urljoin(self.config.blog_url, href)

    @staticmethod
    def _parse_html_safe(html: str) -> HtmlElement | None:
        """Parse raw HTML into an lxml HtmlElement safely.

        Parameters
        ----------
        html : str
            Raw HTML string.

        Returns
        -------
        HtmlElement | None
            Parsed document, or None if parsing fails.
        """
        try:
            return fromstring(html)
        except Exception:
            return None

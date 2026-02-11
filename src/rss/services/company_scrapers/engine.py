"""Common scraping orchestrator for company blog/newsroom pages.

CompanyScraperEngine combines existing components via composition to provide
a unified scraping pipeline:

1. Rate limiting + UA rotation (ScrapingPolicy)
2. Blog page fetch (httpx)
3. Structure change detection (StructureValidator)
4. Article list extraction (CSS selectors via lxml)
5. Per-article processing (HTML via ArticleExtractor, PDF via PdfHandler)

Designed for concurrent scraping of 70+ company blogs in the AI investment
value chain tracking pipeline.

Examples
--------
>>> import asyncio
>>> from rss.services.company_scrapers.engine import CompanyScraperEngine
>>> from rss.services.company_scrapers.types import CompanyConfig
>>> engine = CompanyScraperEngine()
>>> config = CompanyConfig(
...     key="openai", name="OpenAI", category="ai_llm",
...     blog_url="https://openai.com/news/",
... )
>>> result = asyncio.run(engine.scrape_company(config))
>>> result.company
'openai'
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from lxml.html import HtmlElement, fromstring

from .pdf_handler import PdfHandler, is_pdf_url
from .scraping_policy import ScrapingPolicy
from .structure_validator import StructureValidator
from .types import (
    ArticleMetadata,
    CompanyConfig,
    CompanyScrapeResult,
    ScrapedArticle,
    StructureReport,
    ValidationStatus,
)

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="company_scraper_engine")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HTTPX_TIMEOUT = 30
"""Timeout in seconds for HTTP requests."""

_STRUCTURE_FAIL_THRESHOLD = 0.0
"""Hit rate at or below which structure validation is considered failed."""

_STRUCTURE_PARTIAL_THRESHOLD = 0.5
"""Hit rate below which structure validation is considered partial."""


# ---------------------------------------------------------------------------
# CompanyScraperEngine
# ---------------------------------------------------------------------------


class CompanyScraperEngine:
    """Common scraping orchestrator for company blog/newsroom pages.

    Composes existing components to provide a complete scraping pipeline:

    - ``ScrapingPolicy``: UA rotation, domain rate limiting, 429 retry
    - ``StructureValidator``: CSS selector health monitoring
    - ``PdfHandler``: PDF detection and download
    - Article extraction via lxml CSS selectors

    Parameters
    ----------
    policy : ScrapingPolicy | None
        Scraping policy for UA rotation and rate limiting.
        Created with defaults if None.
    validator : StructureValidator | None
        Structure validator for CSS selector health checks.
        Created with defaults if None.
    pdf_handler : PdfHandler | None
        PDF handler for downloading PDF articles.
        Created with defaults if None.

    Examples
    --------
    >>> engine = CompanyScraperEngine()
    >>> engine.policy is not None
    True
    """

    def __init__(
        self,
        *,
        policy: ScrapingPolicy | None = None,
        validator: StructureValidator | None = None,
        pdf_handler: PdfHandler | None = None,
    ) -> None:
        self.policy = policy if policy is not None else ScrapingPolicy()
        self.validator = validator if validator is not None else StructureValidator()
        self.pdf_handler = pdf_handler if pdf_handler is not None else PdfHandler()

        logger.debug(
            "CompanyScraperEngine initialized",
            policy_type=type(self.policy).__name__,
            validator_type=type(self.validator).__name__,
            pdf_handler_type=type(self.pdf_handler).__name__,
        )

    # -- Public API ----------------------------------------------------------

    async def scrape_company(self, config: CompanyConfig) -> CompanyScrapeResult:
        """Scrape a company's blog/newsroom and return structured results.

        Executes the full scraping pipeline:

        1. Wait for rate limit + get UA
        2. Fetch blog page
        3. Validate page structure (StructureValidator)
        4. Extract article list from blog page (CSS selectors)
        5. Process each article (HTML or PDF)

        Parameters
        ----------
        config : CompanyConfig
            Company configuration with URLs and CSS selectors.

        Returns
        -------
        CompanyScrapeResult
            Scraped articles with validation status. On error,
            returns a result with empty articles and "failed" validation.
        """
        domain = self._extract_domain(config.blog_url)
        logger.info(
            "Starting company scrape",
            company=config.key,
            blog_url=config.blog_url,
            domain=domain,
        )

        # Step 1: Fetch blog page
        try:
            response = await self._fetch_page(config.blog_url, domain=domain)
        except Exception as e:
            logger.error(
                "Failed to fetch blog page",
                company=config.key,
                blog_url=config.blog_url,
                error=str(e),
            )
            return CompanyScrapeResult(
                company=config.key,
                articles=(),
                validation="failed",
            )

        blog_html = response.text

        # Step 2: Validate structure
        report = self.validator.validate(blog_html, config)
        validation_status = self._determine_validation_status(report)

        if validation_status == "failed":
            logger.warning(
                "Structure validation failed, skipping article extraction",
                company=config.key,
                hit_rate=report.hit_rate,
                article_list_hits=report.article_list_hits,
            )
            return CompanyScrapeResult(
                company=config.key,
                articles=(),
                validation="failed",
            )

        # Step 3: Extract article list
        article_metas = self._extract_article_list(blog_html, config)
        if not article_metas:
            logger.info(
                "No articles found on blog page",
                company=config.key,
                blog_url=config.blog_url,
            )
            return CompanyScrapeResult(
                company=config.key,
                articles=(),
                validation=validation_status,
            )

        logger.info(
            "Articles found on blog page",
            company=config.key,
            article_count=len(article_metas),
        )

        # Step 4: Process each article
        scraped_articles: list[ScrapedArticle] = []
        for meta in article_metas:
            try:
                article = await self._process_article(meta, config, domain)
                if article is not None:
                    scraped_articles.append(article)
            except Exception as e:
                logger.warning(
                    "Failed to process article, skipping",
                    company=config.key,
                    url=meta.url,
                    error=str(e),
                )
                continue

        # Determine final validation status based on extraction success
        if scraped_articles and validation_status == "valid":
            final_validation: ValidationStatus = "valid"
        elif scraped_articles:
            final_validation = "partial"
        else:
            final_validation = validation_status

        logger.info(
            "Company scrape completed",
            company=config.key,
            articles_found=len(article_metas),
            articles_scraped=len(scraped_articles),
            validation=final_validation,
        )

        return CompanyScrapeResult(
            company=config.key,
            articles=tuple(scraped_articles),
            validation=final_validation,
        )

    # -- Internal: page fetch ------------------------------------------------

    async def _fetch_page(self, url: str, *, domain: str) -> Any:
        """Fetch a web page with rate limiting and UA rotation.

        Parameters
        ----------
        url : str
            URL to fetch.
        domain : str
            Domain for rate limiting.

        Returns
        -------
        Any
            httpx Response object.

        Raises
        ------
        httpx.HTTPError
            If the HTTP request fails.
        RateLimitError
            If rate limiting is exceeded after retries.
        """
        # Apply rate limiting
        await self.policy.wait_for_domain(domain)

        # Get rotated UA
        user_agent = self.policy.get_user_agent()

        logger.debug(
            "Fetching page",
            url=url,
            domain=domain,
            user_agent=user_agent[:50],
        )

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_HTTPX_TIMEOUT),
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        ) as client:

            async def _do_request() -> httpx.Response:
                return await client.get(url)

            response = await self.policy.execute_with_retry(_do_request, url)
            response.raise_for_status()

        return response

    # -- Internal: article list extraction -----------------------------------

    def _extract_article_list(
        self,
        html: str,
        config: CompanyConfig,
    ) -> list[ArticleMetadata]:
        """Extract article metadata from a blog listing page.

        Uses CSS selectors from the CompanyConfig to find articles,
        extract titles, dates, and URLs.

        Parameters
        ----------
        html : str
            Raw HTML of the blog listing page.
        config : CompanyConfig
            Company configuration with CSS selectors.

        Returns
        -------
        list[ArticleMetadata]
            List of article metadata extracted from the page.
        """
        doc = self._parse_html(html)
        if doc is None:
            logger.warning(
                "Failed to parse blog HTML",
                company=config.key,
            )
            return []

        article_elements = doc.cssselect(config.article_list_selector)
        if not article_elements:
            logger.debug(
                "No article elements found",
                company=config.key,
                selector=config.article_list_selector,
            )
            return []

        results: list[ArticleMetadata] = []
        for element in article_elements:
            meta = self._extract_single_article_meta(element, config)
            if meta is not None:
                results.append(meta)

        logger.debug(
            "Article metadata extracted",
            company=config.key,
            total_elements=len(article_elements),
            extracted_count=len(results),
        )

        return results

    def _extract_single_article_meta(
        self,
        element: HtmlElement,
        config: CompanyConfig,
    ) -> ArticleMetadata | None:
        """Extract metadata from a single article element.

        Parameters
        ----------
        element : HtmlElement
            An article element from the blog listing page.
        config : CompanyConfig
            Company configuration with CSS selectors.

        Returns
        -------
        ArticleMetadata | None
            Extracted metadata, or None if essential fields are missing.
        """
        # Extract title
        title_elements = element.cssselect(config.article_title_selector)
        if not title_elements:
            return None

        title_el = title_elements[0]
        title = title_el.text_content().strip()
        if not title:
            return None

        # Extract URL from title link
        url = self._extract_url_from_element(title_el, config.blog_url)
        if not url:
            return None

        # Extract date (optional)
        date: str | None = None
        date_elements = element.cssselect(config.article_date_selector)
        if date_elements:
            date = date_elements[0].text_content().strip() or None

        return ArticleMetadata(url=url, title=title, date=date)

    # -- Internal: article processing ----------------------------------------

    async def _process_article(
        self,
        meta: ArticleMetadata,
        config: CompanyConfig,
        domain: str,
    ) -> ScrapedArticle | None:
        """Process a single article (HTML or PDF).

        Parameters
        ----------
        meta : ArticleMetadata
            Article metadata from the listing page.
        config : CompanyConfig
            Company configuration.
        domain : str
            Domain for rate limiting.

        Returns
        -------
        ScrapedArticle | None
            Scraped article data, or None if extraction failed.
        """
        if is_pdf_url(meta.url):
            return await self._process_pdf_article(meta, config)

        return await self._process_html_article(meta, config, domain)

    async def _process_html_article(
        self,
        meta: ArticleMetadata,
        config: CompanyConfig,
        domain: str,
    ) -> ScrapedArticle | None:
        """Process an HTML article by fetching and extracting text.

        Parameters
        ----------
        meta : ArticleMetadata
            Article metadata.
        config : CompanyConfig
            Company configuration.
        domain : str
            Domain for rate limiting.

        Returns
        -------
        ScrapedArticle | None
            Scraped article, or None if extraction failed.
        """
        logger.debug(
            "Processing HTML article",
            company=config.key,
            url=meta.url,
            title=meta.title,
        )

        try:
            response = await self._fetch_page(meta.url, domain=domain)
        except Exception as e:
            logger.warning(
                "Failed to fetch article page",
                company=config.key,
                url=meta.url,
                error=str(e),
            )
            return None

        article_html = response.text
        text = self._extract_text_from_html(article_html)

        if not text:
            logger.debug(
                "No text extracted from article",
                company=config.key,
                url=meta.url,
            )
            return None

        # Detect PDF links within the article page
        from .pdf_handler import find_pdf_links

        pdf_links = find_pdf_links(article_html)
        main_pdf = pdf_links[0] if pdf_links else None
        attached_pdfs = tuple(pdf_links[1:]) if len(pdf_links) > 1 else ()

        return ScrapedArticle(
            url=meta.url,
            title=meta.title,
            text=text,
            source_type="blog",
            pdf=main_pdf,
            attached_pdfs=attached_pdfs,
        )

    async def _process_pdf_article(
        self,
        meta: ArticleMetadata,
        config: CompanyConfig,
    ) -> ScrapedArticle | None:
        """Process a PDF article by downloading it.

        Parameters
        ----------
        meta : ArticleMetadata
            Article metadata with a PDF URL.
        config : CompanyConfig
            Company configuration.

        Returns
        -------
        ScrapedArticle | None
            Scraped article with PDF metadata, or None on failure.
        """
        logger.debug(
            "Processing PDF article",
            company=config.key,
            url=meta.url,
            title=meta.title,
        )

        try:
            pdf_metadata = await self.pdf_handler.download(meta.url, config.key)
        except Exception as e:
            logger.warning(
                "Failed to download PDF",
                company=config.key,
                url=meta.url,
                error=str(e),
            )
            return None

        return ScrapedArticle(
            url=meta.url,
            title=meta.title,
            text=f"[PDF: {pdf_metadata.filename}]",
            source_type="press_release",
            pdf=meta.url,
            attached_pdfs=(),
        )

    # -- Internal: HTML parsing utilities ------------------------------------

    @staticmethod
    def _parse_html(html: str) -> HtmlElement | None:
        """Parse raw HTML into an lxml HtmlElement.

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

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """Extract article body text from HTML.

        Uses XPath selectors to find the article body, removes
        script/style elements, and cleans up whitespace.

        Parameters
        ----------
        html : str
            Raw HTML string of the article page.

        Returns
        -------
        str
            Extracted plain text from the article body.
        """
        if not html:
            return ""

        try:
            doc = fromstring(html)
        except Exception:
            return ""

        # Remove script and style elements
        for element in doc.xpath("//script | //style | //noscript"):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)

        # Try article-specific selectors
        article_selectors = [
            "//article",
            "//main",
            "//*[contains(@class, 'article-body')]",
            "//*[contains(@class, 'article-content')]",
            "//*[contains(@class, 'post-content')]",
            "//*[contains(@class, 'entry-content')]",
            "//*[@role='main']",
        ]

        for selector in article_selectors:
            elements = doc.xpath(selector)
            if elements:
                text = elements[0].text_content()
                cleaned = _clean_text(text)
                if cleaned:
                    return cleaned

        # Fallback: extract from <body>
        body_elements = doc.xpath("//body")
        if body_elements:
            text = body_elements[0].text_content()
            return _clean_text(text)

        return ""

    @staticmethod
    def _extract_url_from_element(element: HtmlElement, base_url: str) -> str | None:
        """Extract a URL from an element or its children.

        Looks for ``href`` attributes on the element itself and
        on ``<a>`` child elements.

        Parameters
        ----------
        element : HtmlElement
            HTML element to search for URLs.
        base_url : str
            Base URL for resolving relative URLs.

        Returns
        -------
        str | None
            Absolute URL, or None if no URL found.
        """
        # Check element itself
        href = element.get("href")
        if href:
            return _resolve_url(href, base_url)

        # Check <a> children
        links = element.cssselect("a")
        if links:
            href = links[0].get("href")
            if href:
                return _resolve_url(href, base_url)

        return None

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from a URL.

        Parameters
        ----------
        url : str
            Full URL.

        Returns
        -------
        str
            Domain name.
        """
        return urlparse(url).netloc

    # -- Internal: validation status -----------------------------------------

    @staticmethod
    def _determine_validation_status(report: StructureReport) -> ValidationStatus:
        """Determine validation status from a StructureReport.

        Parameters
        ----------
        report : StructureReport
            Structure validation report.

        Returns
        -------
        ValidationStatus
            "valid", "partial", or "failed" based on hit rate thresholds.
        """
        if report.article_list_hits == 0:
            return "failed"

        if report.hit_rate <= _STRUCTURE_FAIL_THRESHOLD:
            return "failed"

        if report.hit_rate < _STRUCTURE_PARTIAL_THRESHOLD:
            return "partial"

        return "valid"


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


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


def _resolve_url(href: str, base_url: str) -> str:
    """Resolve a potentially relative URL against a base URL.

    Parameters
    ----------
    href : str
        URL or relative path.
    base_url : str
        Base URL for resolution.

    Returns
    -------
    str
        Absolute URL.
    """
    if href.startswith(("http://", "https://")):
        return href
    return urljoin(base_url, href)

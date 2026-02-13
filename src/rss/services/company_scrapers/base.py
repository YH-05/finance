"""Abstract base class for company-specific scrapers (Tier 3).

Provides a common interface and shared scraping flow for companies
that require custom parsing logic (e.g., SPA/JS-heavy sites).
Concrete subclasses override ``extract_article_list`` to implement
company-specific HTML parsing, while the base class handles the
shared orchestration via ``CompanyScraperEngine``.

Examples
--------
>>> class PerplexityScraper(BaseCompanyScraper):
...     @property
...     def company_key(self) -> str:
...         return "perplexity"
...     @property
...     def config(self) -> CompanyConfig:
...         return CompanyConfig(...)
...     async def extract_article_list(self, html: str) -> list[ArticleMetadata]:
...         ...  # Custom HTML parsing
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .engine import CompanyScraperEngine
    from .types import ArticleMetadata, CompanyConfig, CompanyScrapeResult


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="base_company_scraper")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


# ---------------------------------------------------------------------------
# BaseCompanyScraper
# ---------------------------------------------------------------------------


class BaseCompanyScraper(ABC):
    """Abstract base class for company-specific scrapers.

    Provides a common scraping flow that delegates page fetching and
    article processing to ``CompanyScraperEngine``, while allowing
    subclasses to customize article list extraction for sites with
    non-standard HTML structures.

    Parameters
    ----------
    engine : CompanyScraperEngine
        The shared scraping engine for page fetching, rate limiting,
        and article processing.

    Examples
    --------
    >>> class MyScraper(BaseCompanyScraper):
    ...     @property
    ...     def company_key(self) -> str:
    ...         return "my_company"
    ...     @property
    ...     def config(self) -> CompanyConfig:
    ...         return CompanyConfig(...)
    ...     async def extract_article_list(self, html):
    ...         return [...]
    """

    def __init__(self, engine: CompanyScraperEngine) -> None:
        self._engine = engine
        logger.debug(
            "BaseCompanyScraper initialized",
            company_key=self.company_key,
            engine_type=type(engine).__name__,
        )

    # -- Properties ----------------------------------------------------------

    @property
    def engine(self) -> CompanyScraperEngine:
        """The shared scraping engine instance."""
        return self._engine

    @property
    @abstractmethod
    def company_key(self) -> str:
        """Unique identifier for this company (e.g., "perplexity").

        Returns
        -------
        str
            Company key matching the key in CompanyConfig.
        """
        ...

    @property
    @abstractmethod
    def config(self) -> CompanyConfig:
        """Company configuration for scraping.

        Returns
        -------
        CompanyConfig
            Configuration with URLs, CSS selectors, and investment context.
        """
        ...

    # -- Abstract methods ----------------------------------------------------

    @abstractmethod
    async def extract_article_list(self, html: str) -> list[ArticleMetadata]:
        """Extract article metadata from a blog listing page.

        Subclasses implement company-specific HTML parsing logic here.

        Parameters
        ----------
        html : str
            Raw HTML of the company's blog/newsroom listing page.

        Returns
        -------
        list[ArticleMetadata]
            List of article metadata extracted from the page.
        """
        ...

    # -- Default implementations ---------------------------------------------

    async def extract_article_content(self, url: str) -> CompanyScrapeResult | None:
        """Extract article content from a single article URL.

        Default implementation delegates to the engine's ``scrape_company``
        method. Subclasses may override for custom content extraction.

        Parameters
        ----------
        url : str
            URL of the article to extract content from.

        Returns
        -------
        CompanyScrapeResult | None
            Scrape result containing the article, or None on failure.
        """
        from .types import CompanyConfig

        logger.debug(
            "Extracting article content via engine",
            company_key=self.company_key,
            url=url,
        )

        # Create a minimal config pointing to the article URL
        config = CompanyConfig(
            key=self.company_key,
            name=self.config.name,
            category=self.config.category,
            blog_url=url,
            article_list_selector=self.config.article_list_selector,
            article_title_selector=self.config.article_title_selector,
            article_date_selector=self.config.article_date_selector,
            requires_playwright=self.config.requires_playwright,
            rate_limit_seconds=self.config.rate_limit_seconds,
            investment_context=self.config.investment_context,
        )
        return await self._engine.scrape_company(config)

    # -- Common flow ---------------------------------------------------------

    async def scrape_latest(
        self,
        max_articles: int = 10,
    ) -> CompanyScrapeResult:
        """Scrape latest articles using the common flow.

        Delegates to the engine's ``scrape_company`` method, then
        truncates the result to ``max_articles``.

        Parameters
        ----------
        max_articles : int
            Maximum number of articles to return.

        Returns
        -------
        CompanyScrapeResult
            Scrape result with at most ``max_articles`` articles.
        """
        from .types import CompanyScrapeResult

        logger.info(
            "Scraping latest articles",
            company_key=self.company_key,
            max_articles=max_articles,
        )

        result = await self._engine.scrape_company(self.config)

        # Truncate to max_articles
        if len(result.articles) > max_articles:
            truncated = result.articles[:max_articles]
            result = CompanyScrapeResult(
                company=result.company,
                articles=truncated,
                validation=result.validation,
            )

        logger.info(
            "Scrape latest completed",
            company_key=self.company_key,
            article_count=len(result.articles),
            max_articles=max_articles,
        )

        return result

"""Company scraper registry: routes scraping to custom or default engine.

CompanyScraperRegistry manages the mapping between company keys and their
scraping implementations. When a custom ``BaseCompanyScraper`` subclass
is registered for a company key, scraping is delegated to that custom
implementation. Otherwise, the default ``CompanyScraperEngine`` is used.

Examples
--------
>>> from rss.services.company_scrapers.engine import CompanyScraperEngine
>>> from rss.services.company_scrapers.registry import CompanyScraperRegistry
>>> engine = CompanyScraperEngine()
>>> registry = CompanyScraperRegistry(engine=engine)
>>> # Scrape using default engine
>>> result = await registry.scrape(config, max_articles=10)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import BaseCompanyScraper
    from .engine import CompanyScraperEngine
    from .types import CompanyConfig, CompanyScrapeResult


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="company_scraper_registry")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()


# ---------------------------------------------------------------------------
# CompanyScraperRegistry
# ---------------------------------------------------------------------------


class CompanyScraperRegistry:
    """Registry that routes scraping to custom scrapers or the default engine.

    Maintains a mapping of company keys to custom ``BaseCompanyScraper``
    implementations. When ``scrape`` is called, the registry checks if a
    custom scraper exists for the company key. If so, it delegates to the
    custom scraper's ``scrape_latest`` method. Otherwise, it falls back to
    the ``CompanyScraperEngine.scrape_company`` method.

    Parameters
    ----------
    engine : CompanyScraperEngine
        The default scraping engine used when no custom scraper is registered.
    custom_scrapers : dict[str, BaseCompanyScraper] | None
        Initial mapping of company keys to custom scrapers.
        Defaults to an empty dict.

    Examples
    --------
    >>> registry = CompanyScraperRegistry(engine=engine)
    >>> registry.register("perplexity", perplexity_scraper)
    >>> registry.has_custom_scraper("perplexity")
    True
    """

    def __init__(
        self,
        engine: CompanyScraperEngine,
        custom_scrapers: dict[str, BaseCompanyScraper] | None = None,
    ) -> None:
        self._engine = engine
        self._custom_scrapers: dict[str, BaseCompanyScraper] = (
            dict(custom_scrapers) if custom_scrapers else {}
        )

        logger.debug(
            "CompanyScraperRegistry initialized",
            engine_type=type(engine).__name__,
            custom_scraper_count=len(self._custom_scrapers),
            custom_keys=list(self._custom_scrapers.keys()),
        )

    # -- Properties ----------------------------------------------------------

    @property
    def engine(self) -> CompanyScraperEngine:
        """The default scraping engine."""
        return self._engine

    @property
    def custom_scrapers(self) -> dict[str, BaseCompanyScraper]:
        """Read-only copy of the custom scrapers mapping."""
        return dict(self._custom_scrapers)

    # -- Registration --------------------------------------------------------

    def register(self, key: str, scraper: BaseCompanyScraper) -> None:
        """Register a custom scraper for a company key.

        Parameters
        ----------
        key : str
            Company key to associate with the scraper.
        scraper : BaseCompanyScraper
            Custom scraper implementation.
        """
        self._custom_scrapers[key] = scraper
        logger.info(
            "Custom scraper registered",
            company_key=key,
            scraper_type=type(scraper).__name__,
        )

    def unregister(self, key: str) -> None:
        """Unregister a custom scraper for a company key.

        Does nothing if the key is not registered.

        Parameters
        ----------
        key : str
            Company key to unregister.
        """
        if key in self._custom_scrapers:
            del self._custom_scrapers[key]
            logger.info("Custom scraper unregistered", company_key=key)
        else:
            logger.debug(
                "Attempted to unregister non-existent scraper",
                company_key=key,
            )

    def has_custom_scraper(self, key: str) -> bool:
        """Check if a custom scraper is registered for a company key.

        Parameters
        ----------
        key : str
            Company key to check.

        Returns
        -------
        bool
            True if a custom scraper is registered, False otherwise.
        """
        return key in self._custom_scrapers

    # -- Scraping dispatch ---------------------------------------------------

    async def scrape(
        self,
        config: CompanyConfig,
        max_articles: int = 10,
    ) -> CompanyScrapeResult:
        """Scrape a company, routing to custom scraper or default engine.

        If a custom scraper is registered for ``config.key``, delegates
        to that scraper's ``scrape_latest`` method. Otherwise, falls back
        to ``CompanyScraperEngine.scrape_company``.

        Parameters
        ----------
        config : CompanyConfig
            Company configuration with URLs and CSS selectors.
        max_articles : int
            Maximum number of articles to return (passed to custom scraper).

        Returns
        -------
        CompanyScrapeResult
            Scrape result from either the custom scraper or the default engine.
        """
        if config.key in self._custom_scrapers:
            logger.info(
                "Routing to custom scraper",
                company_key=config.key,
                scraper_type=type(self._custom_scrapers[config.key]).__name__,
            )
            return await self._custom_scrapers[config.key].scrape_latest(
                max_articles=max_articles,
            )

        logger.info(
            "Routing to default engine",
            company_key=config.key,
        )
        return await self._engine.scrape_company(config)

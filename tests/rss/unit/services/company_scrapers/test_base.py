"""Unit tests for BaseCompanyScraper (abstract base class for company scrapers).

Tests cover:
- ABC enforcement (cannot instantiate directly)
- Abstract property/method contract
- Concrete subclass instantiation
- scrape_latest common flow (delegates to extract_article_list + engine)
- Default extract_article_content delegates to engine
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from rss.services.company_scrapers.base import BaseCompanyScraper
from rss.services.company_scrapers.engine import CompanyScraperEngine
from rss.services.company_scrapers.types import (
    ArticleMetadata,
    CompanyConfig,
    CompanyScrapeResult,
    InvestmentContext,
    ScrapedArticle,
)

# ---------------------------------------------------------------------------
# Helper: Concrete subclass for testing
# ---------------------------------------------------------------------------


def _make_config(**overrides: object) -> CompanyConfig:
    """Create a CompanyConfig with sensible defaults for testing."""
    defaults: dict[str, object] = {
        "key": "test_company",
        "name": "Test Company",
        "category": "test",
        "blog_url": "https://example.com/blog",
        "article_list_selector": "article",
        "article_title_selector": "h2",
        "article_date_selector": "time",
        "rate_limit_seconds": 0.0,
        "investment_context": InvestmentContext(
            tickers=("TEST",),
            sectors=("Test Sector",),
            keywords=("test",),
        ),
    }
    defaults.update(overrides)
    return CompanyConfig(**defaults)  # type: ignore[arg-type]


class ConcreteCompanyScraper(BaseCompanyScraper):
    """Concrete test implementation of BaseCompanyScraper."""

    @property
    def company_key(self) -> str:
        return "test_company"

    @property
    def config(self) -> CompanyConfig:
        return _make_config()

    async def extract_article_list(self, html: str) -> list[ArticleMetadata]:
        """Extract articles from HTML by finding test markers."""
        articles: list[ArticleMetadata] = []
        if "<test-article>" in html:
            articles.append(
                ArticleMetadata(
                    url="https://example.com/article-1",
                    title="Test Article 1",
                    date="2026-01-01",
                )
            )
        return articles


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_engine() -> CompanyScraperEngine:
    """Create a mock CompanyScraperEngine."""
    engine = MagicMock(spec=CompanyScraperEngine)
    engine.scrape_company = AsyncMock()
    return engine


@pytest.fixture
def scraper(mock_engine: CompanyScraperEngine) -> ConcreteCompanyScraper:
    """Create a ConcreteCompanyScraper with mock engine."""
    return ConcreteCompanyScraper(engine=mock_engine)


# ---------------------------------------------------------------------------
# ABC enforcement
# ---------------------------------------------------------------------------


class TestBaseCompanyScraperABC:
    """Tests for ABC contract enforcement."""

    def test_異常系_直接インスタンス化でTypeError(self) -> None:
        engine = MagicMock(spec=CompanyScraperEngine)
        with pytest.raises(TypeError, match="abstract"):
            BaseCompanyScraper(engine=engine)  # type: ignore[abstract]

    def test_正常系_具象サブクラスをインスタンス化できる(
        self,
        scraper: ConcreteCompanyScraper,
    ) -> None:
        assert isinstance(scraper, BaseCompanyScraper)

    def test_正常系_company_keyプロパティを返す(
        self,
        scraper: ConcreteCompanyScraper,
    ) -> None:
        assert scraper.company_key == "test_company"

    def test_正常系_configプロパティを返す(
        self,
        scraper: ConcreteCompanyScraper,
    ) -> None:
        config = scraper.config
        assert isinstance(config, CompanyConfig)
        assert config.key == "test_company"

    def test_正常系_engineプロパティを返す(
        self,
        scraper: ConcreteCompanyScraper,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        assert scraper.engine is mock_engine


# ---------------------------------------------------------------------------
# extract_article_content (default: delegates to engine)
# ---------------------------------------------------------------------------


class TestExtractArticleContentDefault:
    """Tests for the default extract_article_content method."""

    @pytest.mark.asyncio
    async def test_正常系_デフォルトでengineに委譲する(
        self,
        scraper: ConcreteCompanyScraper,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        mock_article = ScrapedArticle(
            url="https://example.com/article-1",
            title="Test Article",
            text="Article body text",
            source_type="blog",
        )
        mock_engine.scrape_company = AsyncMock(
            return_value=CompanyScrapeResult(
                company="test_company",
                articles=(mock_article,),
                validation="valid",
            )
        )

        result = await scraper.extract_article_content("https://example.com/article-1")

        # Default implementation delegates to engine
        assert result is not None


# ---------------------------------------------------------------------------
# scrape_latest (common flow)
# ---------------------------------------------------------------------------


class TestScrapeLatest:
    """Tests for the scrape_latest common flow."""

    @pytest.mark.asyncio
    async def test_正常系_共通フローで記事を取得できる(
        self,
        scraper: ConcreteCompanyScraper,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        # Mock engine.scrape_company to return a result with blog HTML
        mock_result = CompanyScrapeResult(
            company="test_company",
            articles=(
                ScrapedArticle(
                    url="https://example.com/article-1",
                    title="Test Article 1",
                    text="Article body",
                    source_type="blog",
                ),
            ),
            validation="valid",
        )
        mock_engine.scrape_company = AsyncMock(return_value=mock_result)

        result = await scraper.scrape_latest(max_articles=10)

        assert isinstance(result, CompanyScrapeResult)

    @pytest.mark.asyncio
    async def test_正常系_max_articlesで記事数を制限できる(
        self,
        scraper: ConcreteCompanyScraper,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        articles = tuple(
            ScrapedArticle(
                url=f"https://example.com/article-{i}",
                title=f"Article {i}",
                text="Body",
                source_type="blog",
            )
            for i in range(5)
        )
        mock_result = CompanyScrapeResult(
            company="test_company",
            articles=articles,
            validation="valid",
        )
        mock_engine.scrape_company = AsyncMock(return_value=mock_result)

        result = await scraper.scrape_latest(max_articles=3)

        assert isinstance(result, CompanyScrapeResult)
        assert len(result.articles) <= 3

    @pytest.mark.asyncio
    async def test_エッジケース_記事がない場合空結果を返す(
        self,
        scraper: ConcreteCompanyScraper,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        mock_result = CompanyScrapeResult(
            company="test_company",
            articles=(),
            validation="valid",
        )
        mock_engine.scrape_company = AsyncMock(return_value=mock_result)

        result = await scraper.scrape_latest(max_articles=10)

        assert isinstance(result, CompanyScrapeResult)
        assert result.articles == ()

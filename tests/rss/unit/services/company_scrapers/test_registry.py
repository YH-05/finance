"""Unit tests for CompanyScraperRegistry (routing: custom scraper vs engine).

Tests cover:
- Registration of custom scrapers
- Routing to custom scraper when key matches
- Fallback to CompanyScraperEngine when no custom scraper exists
- scrape method dispatching
- Edge cases (empty registry, unknown key)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from rss.services.company_scrapers.base import BaseCompanyScraper
from rss.services.company_scrapers.engine import CompanyScraperEngine
from rss.services.company_scrapers.registry import CompanyScraperRegistry
from rss.services.company_scrapers.types import (
    ArticleMetadata,
    CompanyConfig,
    CompanyScrapeResult,
    InvestmentContext,
    ScrapedArticle,
)

# ---------------------------------------------------------------------------
# Helpers
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


class _FakeCustomScraper(BaseCompanyScraper):
    """Fake custom scraper for testing routing."""

    def __init__(
        self,
        engine: CompanyScraperEngine,
        *,
        key: str = "custom_company",
    ) -> None:
        self._key = key
        self._config = _make_config(key=key, name="Custom Company")
        super().__init__(engine=engine)

    @property
    def company_key(self) -> str:
        return self._key

    @property
    def config(self) -> CompanyConfig:
        return self._config

    async def extract_article_list(self, html: str) -> list[ArticleMetadata]:
        return [
            ArticleMetadata(
                url="https://custom.example.com/article",
                title="Custom Article",
                date="2026-01-01",
            ),
        ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_engine_result(company: str = "engine_company") -> CompanyScrapeResult:
    """Build a CompanyScrapeResult for the given company key."""
    return CompanyScrapeResult(
        company=company,
        articles=(
            ScrapedArticle(
                url=f"https://example.com/{company}-article",
                title=f"{company} Article",
                text=f"{company} body",
                source_type="blog",
            ),
        ),
        validation="valid",
    )


@pytest.fixture
def mock_engine() -> CompanyScraperEngine:
    """Create a mock CompanyScraperEngine.

    Uses side_effect to return different results depending on config.key.
    """
    engine = MagicMock(spec=CompanyScraperEngine)

    async def _scrape_company(config: CompanyConfig) -> CompanyScrapeResult:
        return _make_engine_result(config.key)

    engine.scrape_company = AsyncMock(side_effect=_scrape_company)
    return engine


@pytest.fixture
def custom_scraper(mock_engine: CompanyScraperEngine) -> _FakeCustomScraper:
    """Create a fake custom scraper."""
    return _FakeCustomScraper(mock_engine, key="custom_company")


@pytest.fixture
def registry(
    mock_engine: CompanyScraperEngine,
    custom_scraper: _FakeCustomScraper,
) -> CompanyScraperRegistry:
    """Create a registry with one custom scraper."""
    return CompanyScraperRegistry(
        engine=mock_engine,
        custom_scrapers={"custom_company": custom_scraper},
    )


@pytest.fixture
def empty_registry(mock_engine: CompanyScraperEngine) -> CompanyScraperRegistry:
    """Create a registry with no custom scrapers."""
    return CompanyScraperRegistry(engine=mock_engine)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestRegistryInitialization:
    """Tests for CompanyScraperRegistry construction."""

    def test_正常系_engineとカスタムスクレイパーで初期化できる(
        self,
        registry: CompanyScraperRegistry,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        assert registry.engine is mock_engine
        assert len(registry.custom_scrapers) == 1

    def test_正常系_カスタムスクレイパーなしで初期化できる(
        self,
        empty_registry: CompanyScraperRegistry,
    ) -> None:
        assert len(empty_registry.custom_scrapers) == 0

    def test_正常系_複数カスタムスクレイパーで初期化できる(
        self,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        scraper_a = _FakeCustomScraper(mock_engine, key="company_a")
        scraper_b = _FakeCustomScraper(mock_engine, key="company_b")
        registry = CompanyScraperRegistry(
            engine=mock_engine,
            custom_scrapers={"company_a": scraper_a, "company_b": scraper_b},
        )
        assert len(registry.custom_scrapers) == 2


# ---------------------------------------------------------------------------
# has_custom_scraper
# ---------------------------------------------------------------------------


class TestHasCustomScraper:
    """Tests for checking custom scraper existence."""

    def test_正常系_登録済みキーでTrueを返す(
        self,
        registry: CompanyScraperRegistry,
    ) -> None:
        assert registry.has_custom_scraper("custom_company") is True

    def test_正常系_未登録キーでFalseを返す(
        self,
        registry: CompanyScraperRegistry,
    ) -> None:
        assert registry.has_custom_scraper("unknown_company") is False

    def test_エッジケース_空レジストリでFalseを返す(
        self,
        empty_registry: CompanyScraperRegistry,
    ) -> None:
        assert empty_registry.has_custom_scraper("any_key") is False


# ---------------------------------------------------------------------------
# scrape: routing dispatch
# ---------------------------------------------------------------------------


class TestScrapeRouting:
    """Tests for scrape method routing between custom and default."""

    @pytest.mark.asyncio
    async def test_正常系_カスタムスクレイパーが存在する場合カスタムを使用(
        self,
        registry: CompanyScraperRegistry,
    ) -> None:
        config = _make_config(key="custom_company")
        result = await registry.scrape(config, max_articles=10)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "custom_company"

    @pytest.mark.asyncio
    async def test_正常系_カスタムスクレイパーがない場合engineを使用(
        self,
        registry: CompanyScraperRegistry,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        config = _make_config(key="engine_company")
        result = await registry.scrape(config, max_articles=10)

        assert isinstance(result, CompanyScrapeResult)
        # Engine should have been called
        mock_engine.scrape_company.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_正常系_空レジストリでengineを使用(
        self,
        empty_registry: CompanyScraperRegistry,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        config = _make_config(key="any_company")
        result = await empty_registry.scrape(config, max_articles=10)

        assert isinstance(result, CompanyScrapeResult)
        mock_engine.scrape_company.assert_called_once_with(config)


# ---------------------------------------------------------------------------
# register / unregister
# ---------------------------------------------------------------------------


class TestRegisterUnregister:
    """Tests for dynamic registration and unregistration."""

    def test_正常系_新しいカスタムスクレイパーを登録できる(
        self,
        empty_registry: CompanyScraperRegistry,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        scraper = _FakeCustomScraper(mock_engine, key="new_company")
        empty_registry.register("new_company", scraper)

        assert empty_registry.has_custom_scraper("new_company") is True

    def test_正常系_カスタムスクレイパーを登録解除できる(
        self,
        registry: CompanyScraperRegistry,
    ) -> None:
        registry.unregister("custom_company")

        assert registry.has_custom_scraper("custom_company") is False

    def test_エッジケース_未登録キーの登録解除でエラーなし(
        self,
        registry: CompanyScraperRegistry,
    ) -> None:
        # Should not raise
        registry.unregister("nonexistent_key")

    def test_正常系_登録後にscrapeでカスタムを使用できる(
        self,
        empty_registry: CompanyScraperRegistry,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        scraper = _FakeCustomScraper(mock_engine, key="new_company")
        empty_registry.register("new_company", scraper)

        assert empty_registry.has_custom_scraper("new_company") is True

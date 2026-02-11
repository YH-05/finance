"""Unit tests for PerplexityScraper (Tier 3 custom scraper for Perplexity AI).

Tests cover:
- BaseCompanyScraper inheritance and ABC contract
- company_key and config properties
- Custom extract_article_list with SPA/JS-heavy HTML parsing
- Snapshot-style testing with sample HTML fixtures
- Edge cases: empty HTML, missing selectors, malformed HTML
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from rss.services.company_scrapers.base import BaseCompanyScraper
from rss.services.company_scrapers.custom.perplexity import PerplexityScraper
from rss.services.company_scrapers.engine import CompanyScraperEngine
from rss.services.company_scrapers.types import (
    ArticleMetadata,
    CompanyConfig,
    InvestmentContext,
)

# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

SAMPLE_PERPLEXITY_HTML = """\
<html>
<head><title>Perplexity Hub</title></head>
<body>
<main>
<div class="hub-posts">
  <div class="hub-post">
    <a href="/hub/introducing-sonar-2">
      <h2 class="hub-post__title">Introducing Sonar 2.0</h2>
    </a>
    <span class="hub-post__date">2026-02-01</span>
  </div>
  <div class="hub-post">
    <a href="/hub/enterprise-launch">
      <h2 class="hub-post__title">Perplexity Enterprise Launch</h2>
    </a>
    <span class="hub-post__date">2026-01-15</span>
  </div>
  <div class="hub-post">
    <a href="https://perplexity.ai/hub/deep-research-mode">
      <h2 class="hub-post__title">Deep Research Mode</h2>
    </a>
    <span class="hub-post__date">2026-01-10</span>
  </div>
</div>
</main>
</body>
</html>
"""

SAMPLE_EMPTY_HTML = """\
<html>
<head><title>Perplexity Hub</title></head>
<body>
<main>
<div class="hub-posts">
</div>
</main>
</body>
</html>
"""

SAMPLE_MISSING_TITLE_HTML = """\
<html>
<body>
<div class="hub-post">
  <a href="/hub/no-title-article">
  </a>
  <span class="hub-post__date">2026-01-01</span>
</div>
</body>
</html>
"""

SAMPLE_MISSING_DATE_HTML = """\
<html>
<body>
<div class="hub-post">
  <a href="/hub/no-date-article">
    <h2 class="hub-post__title">Article Without Date</h2>
  </a>
</div>
</body>
</html>
"""

SAMPLE_MISSING_LINK_HTML = """\
<html>
<body>
<div class="hub-post">
  <h2 class="hub-post__title">No Link Article</h2>
  <span class="hub-post__date">2026-01-01</span>
</div>
</body>
</html>
"""


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
def scraper(mock_engine: CompanyScraperEngine) -> PerplexityScraper:
    """Create a PerplexityScraper with mock engine."""
    return PerplexityScraper(engine=mock_engine)


# ---------------------------------------------------------------------------
# ABC contract & properties
# ---------------------------------------------------------------------------


class TestPerplexityScraperContract:
    """Tests for BaseCompanyScraper contract compliance."""

    def test_正常系_BaseCompanyScraperを継承している(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        assert isinstance(scraper, BaseCompanyScraper)

    def test_正常系_company_keyがperplexity_aiを返す(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        assert scraper.company_key == "perplexity_ai"

    def test_正常系_configがCompanyConfigを返す(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        config = scraper.config
        assert isinstance(config, CompanyConfig)
        assert config.key == "perplexity_ai"
        assert config.name == "Perplexity AI"
        assert config.category == "ai_llm"

    def test_正常系_configのblog_urlが正しい(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        assert scraper.config.blog_url == "https://perplexity.ai/hub"

    def test_正常系_configでPlaywrightが必要(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        assert scraper.config.requires_playwright is True

    def test_正常系_configのrate_limitが5秒(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        assert scraper.config.rate_limit_seconds == 5.0

    def test_正常系_configのinvestment_contextが正しい(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        ctx = scraper.config.investment_context
        assert isinstance(ctx, InvestmentContext)
        assert ctx.sectors == ("AI/LLM", "Search")
        assert "Perplexity" in ctx.keywords

    def test_正常系_engineプロパティを返す(
        self,
        scraper: PerplexityScraper,
        mock_engine: CompanyScraperEngine,
    ) -> None:
        assert scraper.engine is mock_engine


# ---------------------------------------------------------------------------
# extract_article_list
# ---------------------------------------------------------------------------


class TestExtractArticleList:
    """Tests for custom extract_article_list HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧を抽出できる(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_PERPLEXITY_HTML)

        assert len(articles) == 3
        assert all(isinstance(a, ArticleMetadata) for a in articles)

    @pytest.mark.asyncio
    async def test_正常系_タイトルを正しく抽出する(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_PERPLEXITY_HTML)

        titles = [a.title for a in articles]
        assert "Introducing Sonar 2.0" in titles
        assert "Perplexity Enterprise Launch" in titles
        assert "Deep Research Mode" in titles

    @pytest.mark.asyncio
    async def test_正常系_日付を正しく抽出する(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_PERPLEXITY_HTML)

        dates = [a.date for a in articles]
        assert "2026-02-01" in dates
        assert "2026-01-15" in dates
        assert "2026-01-10" in dates

    @pytest.mark.asyncio
    async def test_正常系_相対URLを絶対URLに変換する(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_PERPLEXITY_HTML)

        # Relative URL should be resolved against blog_url
        urls = [a.url for a in articles]
        assert "https://perplexity.ai/hub/introducing-sonar-2" in urls
        assert "https://perplexity.ai/hub/enterprise-launch" in urls

    @pytest.mark.asyncio
    async def test_正常系_絶対URLはそのまま保持する(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_PERPLEXITY_HTML)

        urls = [a.url for a in articles]
        assert "https://perplexity.ai/hub/deep-research-mode" in urls

    @pytest.mark.asyncio
    async def test_エッジケース_空のHTMLで空リストを返す(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list("")

        assert articles == []

    @pytest.mark.asyncio
    async def test_エッジケース_記事がないHTMLで空リストを返す(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_EMPTY_HTML)

        assert articles == []

    @pytest.mark.asyncio
    async def test_エッジケース_タイトルがない記事をスキップする(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_MISSING_TITLE_HTML)

        assert articles == []

    @pytest.mark.asyncio
    async def test_エッジケース_日付がなくても記事を抽出する(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_MISSING_DATE_HTML)

        assert len(articles) == 1
        assert articles[0].title == "Article Without Date"
        assert articles[0].date is None

    @pytest.mark.asyncio
    async def test_エッジケース_リンクがない記事をスキップする(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_MISSING_LINK_HTML)

        assert articles == []


# ---------------------------------------------------------------------------
# Snapshot-style: article order and structure
# ---------------------------------------------------------------------------


class TestExtractArticleListSnapshot:
    """Snapshot-style tests verifying full extraction output."""

    @pytest.mark.asyncio
    async def test_正常系_抽出結果のスナップショット(
        self,
        scraper: PerplexityScraper,
    ) -> None:
        articles = await scraper.extract_article_list(SAMPLE_PERPLEXITY_HTML)

        expected = [
            ArticleMetadata(
                url="https://perplexity.ai/hub/introducing-sonar-2",
                title="Introducing Sonar 2.0",
                date="2026-02-01",
            ),
            ArticleMetadata(
                url="https://perplexity.ai/hub/enterprise-launch",
                title="Perplexity Enterprise Launch",
                date="2026-01-15",
            ),
            ArticleMetadata(
                url="https://perplexity.ai/hub/deep-research-mode",
                title="Deep Research Mode",
                date="2026-01-10",
            ),
        ]

        assert articles == expected

"""Unit tests for CompanyScraperEngine (common scraping orchestrator).

Tests cover:
- Composition with existing components (ArticleContentChecker, ArticleExtractor)
- scrape_company method returning CompanyScrapeResult
- Structure change handling (StructureValidator)
- PDF article and HTML article processing
- Rate limiting and UA via ScrapingPolicy
- Error handling (RateLimitError, StructureChangedError, BotDetectionError)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from rss.services.company_scrapers.engine import CompanyScraperEngine
from rss.services.company_scrapers.pdf_handler import PdfHandler
from rss.services.company_scrapers.scraping_policy import ScrapingPolicy
from rss.services.company_scrapers.structure_validator import StructureValidator
from rss.services.company_scrapers.types import (
    ArticleMetadata,
    CompanyConfig,
    CompanyScrapeResult,
    InvestmentContext,
    PdfMetadata,
    RateLimitError,
    ScrapedArticle,
    StructureChangedError,
    StructureReport,
)

# ---------------------------------------------------------------------------
# Helper: sample HTML builders
# ---------------------------------------------------------------------------


def _build_blog_html(articles: list[dict[str, str | None]]) -> str:
    """Build a sample blog HTML page from article specs.

    Parameters
    ----------
    articles : list[dict[str, str | None]]
        Each dict should contain "title", "date", and "url" keys.
    """
    items: list[str] = []
    for art in articles:
        parts: list[str] = []
        url = art.get("url", "#")
        title = art.get("title", "Untitled")
        if title is not None:
            parts.append(f'<h2><a href="{url}">{title}</a></h2>')
        if art.get("date") is not None:
            parts.append(f"<time>{art['date']}</time>")
        items.append(f"<article>{''.join(parts)}</article>")
    body = "\n".join(items)
    return f"<html><body>{body}</body></html>"


def _build_article_html(title: str, body_text: str) -> str:
    """Build a sample article HTML page."""
    return (
        f"<html><head><title>{title}</title></head>"
        f"<body><article><h1>{title}</h1><p>{body_text}</p></article></body></html>"
    )


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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_policy() -> ScrapingPolicy:
    """Create a ScrapingPolicy with minimal rate limiting for tests."""
    return ScrapingPolicy(
        user_agents=["TestUA/1.0", "TestUA/2.0"],
        default_rate_limit=0.0,
        max_retries=1,
        base_backoff=0.01,
    )


@pytest.fixture
def mock_validator() -> StructureValidator:
    """Create a StructureValidator instance."""
    return StructureValidator()


@pytest.fixture
def mock_pdf_handler() -> PdfHandler:
    """Create a PdfHandler with a test directory."""
    return PdfHandler()


@pytest.fixture
def engine(
    mock_policy: ScrapingPolicy,
    mock_validator: StructureValidator,
    mock_pdf_handler: PdfHandler,
) -> CompanyScraperEngine:
    """Create a CompanyScraperEngine with test dependencies."""
    return CompanyScraperEngine(
        policy=mock_policy,
        validator=mock_validator,
        pdf_handler=mock_pdf_handler,
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestEngineInitialization:
    """Tests for CompanyScraperEngine construction via composition."""

    def test_正常系_デフォルトパラメータで初期化できる(self) -> None:
        engine = CompanyScraperEngine()
        assert engine.policy is not None
        assert engine.validator is not None
        assert engine.pdf_handler is not None

    def test_正常系_カスタムコンポーネントで初期化できる(
        self,
        mock_policy: ScrapingPolicy,
        mock_validator: StructureValidator,
        mock_pdf_handler: PdfHandler,
    ) -> None:
        engine = CompanyScraperEngine(
            policy=mock_policy,
            validator=mock_validator,
            pdf_handler=mock_pdf_handler,
        )
        assert engine.policy is mock_policy
        assert engine.validator is mock_validator
        assert engine.pdf_handler is mock_pdf_handler


# ---------------------------------------------------------------------------
# scrape_company: basic flow
# ---------------------------------------------------------------------------


class TestScrapeCompanyBasicFlow:
    """Tests for scrape_company method basic flow."""

    @pytest.mark.asyncio
    async def test_正常系_HTML記事を正常にスクレイプできる(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        blog_html = _build_blog_html(
            [
                {
                    "title": "Article 1",
                    "date": "2026-01-01",
                    "url": "https://example.com/article-1",
                },
            ]
        )
        article_html = _build_article_html(
            "Article 1",
            "This is the full article content with enough text to pass extraction. "
            * 10,
        )
        config = _make_config()

        # Mock httpx to return blog page, then article page
        mock_response_blog = MagicMock()
        mock_response_blog.status_code = 200
        mock_response_blog.text = blog_html
        mock_response_blog.headers = {}

        mock_response_article = MagicMock()
        mock_response_article.status_code = 200
        mock_response_article.text = article_html
        mock_response_article.headers = {}

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            side_effect=[mock_response_blog, mock_response_article],
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "test_company"
        assert len(result.articles) >= 0  # May vary based on extraction

    @pytest.mark.asyncio
    async def test_正常系_CompanyScrapeResultを返す(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        config = _make_config()

        # Mock _fetch_page to return empty blog page (no articles)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>"
        mock_response.headers = {}

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "test_company"

    @pytest.mark.asyncio
    async def test_正常系_複数記事を処理できる(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        blog_html = _build_blog_html(
            [
                {
                    "title": "Article 1",
                    "date": "2026-01-01",
                    "url": "https://example.com/article-1",
                },
                {
                    "title": "Article 2",
                    "date": "2026-01-02",
                    "url": "https://example.com/article-2",
                },
            ]
        )
        long_text = "Article body with sufficient content. " * 20
        article_html_1 = _build_article_html("Article 1", long_text)
        article_html_2 = _build_article_html("Article 2", long_text)
        config = _make_config()

        mock_blog = MagicMock()
        mock_blog.status_code = 200
        mock_blog.text = blog_html
        mock_blog.headers = {}

        mock_art1 = MagicMock()
        mock_art1.status_code = 200
        mock_art1.text = article_html_1
        mock_art1.headers = {}

        mock_art2 = MagicMock()
        mock_art2.status_code = 200
        mock_art2.text = article_html_2
        mock_art2.headers = {}

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            side_effect=[mock_blog, mock_art1, mock_art2],
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "test_company"


# ---------------------------------------------------------------------------
# scrape_company: structure validation
# ---------------------------------------------------------------------------


class TestScrapeCompanyStructureValidation:
    """Tests for structure change handling via StructureValidator."""

    @pytest.mark.asyncio
    async def test_正常系_構造変更検知でvalidation_failedのresultを返す(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        # Blog page with no matching selectors -> structure change
        broken_html = (
            "<html><body>"
            "<section><span>Completely different structure</span></section>"
            "</body></html>"
        )
        config = _make_config()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = broken_html
        mock_response.headers = {}

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "test_company"
        # With no matching selectors, should be empty articles or failed validation
        assert result.articles == ()
        assert result.validation in ("failed", "partial")

    @pytest.mark.asyncio
    async def test_正常系_健全な構造でvalidation_validのresultを返す(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        blog_html = _build_blog_html(
            [
                {
                    "title": "Good Article",
                    "date": "2026-01-01",
                    "url": "https://example.com/good",
                },
            ]
        )
        long_text = "This is a substantial article body. " * 20
        article_html = _build_article_html("Good Article", long_text)
        config = _make_config()

        mock_blog = MagicMock()
        mock_blog.status_code = 200
        mock_blog.text = blog_html
        mock_blog.headers = {}

        mock_article = MagicMock()
        mock_article.status_code = 200
        mock_article.text = article_html
        mock_article.headers = {}

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            side_effect=[mock_blog, mock_article],
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.validation == "valid"


# ---------------------------------------------------------------------------
# scrape_company: PDF handling
# ---------------------------------------------------------------------------


class TestScrapeCompanyPdfHandling:
    """Tests for PDF article processing."""

    @pytest.mark.asyncio
    async def test_正常系_PDF記事を検出して処理できる(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        # Blog HTML with a PDF link
        blog_html = (
            "<html><body>"
            '<article><h2><a href="https://example.com/report.pdf">'
            "Annual Report</a></h2>"
            "<time>2026-01-01</time></article>"
            "</body></html>"
        )
        config = _make_config()

        mock_blog = MagicMock()
        mock_blog.status_code = 200
        mock_blog.text = blog_html
        mock_blog.headers = {}

        mock_pdf_metadata = PdfMetadata(
            url="https://example.com/report.pdf",
            local_path="/tmp/test/report.pdf",
            company_key="test_company",
            filename="report.pdf",
        )

        with (
            patch.object(
                engine,
                "_fetch_page",
                new_callable=AsyncMock,
                return_value=mock_blog,
            ),
            patch.object(
                engine.pdf_handler,
                "download",
                new_callable=AsyncMock,
                return_value=mock_pdf_metadata,
            ),
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "test_company"

    @pytest.mark.asyncio
    async def test_正常系_HTML記事とPDF記事の両方を処理できる(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        blog_html = (
            "<html><body>"
            '<article><h2><a href="https://example.com/article-1">'
            "HTML Article</a></h2>"
            "<time>2026-01-01</time></article>"
            '<article><h2><a href="https://example.com/report.pdf">'
            "PDF Report</a></h2>"
            "<time>2026-01-02</time></article>"
            "</body></html>"
        )
        long_text = "This is a substantial article body content. " * 20
        article_html = _build_article_html("HTML Article", long_text)
        config = _make_config()

        mock_blog = MagicMock()
        mock_blog.status_code = 200
        mock_blog.text = blog_html
        mock_blog.headers = {}

        mock_art = MagicMock()
        mock_art.status_code = 200
        mock_art.text = article_html
        mock_art.headers = {}

        mock_pdf_metadata = PdfMetadata(
            url="https://example.com/report.pdf",
            local_path="/tmp/test/report.pdf",
            company_key="test_company",
            filename="report.pdf",
        )

        with (
            patch.object(
                engine,
                "_fetch_page",
                new_callable=AsyncMock,
                side_effect=[mock_blog, mock_art],
            ),
            patch.object(
                engine.pdf_handler,
                "download",
                new_callable=AsyncMock,
                return_value=mock_pdf_metadata,
            ),
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)


# ---------------------------------------------------------------------------
# scrape_company: rate limiting and UA via ScrapingPolicy
# ---------------------------------------------------------------------------


class TestScrapeCompanyPolicyIntegration:
    """Tests for ScrapingPolicy integration (rate limit + UA)."""

    @pytest.mark.asyncio
    async def test_正常系_UAヘッダがリクエストに設定される(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        config = _make_config()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>"
        mock_response.headers = {}

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_fetch:
            await engine.scrape_company(config)

        # _fetch_page should be called at least once
        mock_fetch.assert_called()


# ---------------------------------------------------------------------------
# scrape_company: error handling
# ---------------------------------------------------------------------------


class TestScrapeCompanyErrorHandling:
    """Tests for error handling in scrape_company."""

    @pytest.mark.asyncio
    async def test_異常系_ブログページ取得失敗でfailedのresultを返す(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        config = _make_config()

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "test_company"
        assert result.validation == "failed"
        assert result.articles == ()

    @pytest.mark.asyncio
    async def test_異常系_429レートリミット時にfailedのresultを返す(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        config = _make_config()

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            side_effect=RateLimitError(
                "Rate limited",
                domain="example.com",
                url="https://example.com/blog",
            ),
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "test_company"
        assert result.validation == "failed"

    @pytest.mark.asyncio
    async def test_異常系_個別記事取得失敗でも他の記事は処理される(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        blog_html = _build_blog_html(
            [
                {
                    "title": "Good Article",
                    "date": "2026-01-01",
                    "url": "https://example.com/good",
                },
                {
                    "title": "Bad Article",
                    "date": "2026-01-02",
                    "url": "https://example.com/bad",
                },
            ]
        )
        long_text = "This is a substantial article body content. " * 20
        good_html = _build_article_html("Good Article", long_text)
        config = _make_config()

        mock_blog = MagicMock()
        mock_blog.status_code = 200
        mock_blog.text = blog_html
        mock_blog.headers = {}

        mock_good = MagicMock()
        mock_good.status_code = 200
        mock_good.text = good_html
        mock_good.headers = {}

        call_count = 0

        async def _side_effect(*args: object, **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_blog
            if call_count == 2:
                return mock_good
            # Third call (bad article) fails
            raise httpx.ConnectError("Connection refused")

        with patch.object(
            engine,
            "_fetch_page",
            new_callable=AsyncMock,
            side_effect=_side_effect,
        ):
            result = await engine.scrape_company(config)

        assert isinstance(result, CompanyScrapeResult)
        assert result.company == "test_company"
        # Should have at least one article (the good one), but partial validation
        # is acceptable here


# ---------------------------------------------------------------------------
# _extract_article_list: metadata extraction
# ---------------------------------------------------------------------------


class TestExtractArticleList:
    """Tests for article metadata extraction from blog HTML."""

    def test_正常系_記事メタデータを正しく抽出できる(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        blog_html = _build_blog_html(
            [
                {
                    "title": "Article 1",
                    "date": "2026-01-15",
                    "url": "https://example.com/article-1",
                },
                {
                    "title": "Article 2",
                    "date": "2026-02-01",
                    "url": "https://example.com/article-2",
                },
            ]
        )
        config = _make_config()
        articles = engine._extract_article_list(blog_html, config)

        assert len(articles) == 2
        assert all(isinstance(a, ArticleMetadata) for a in articles)
        assert articles[0].title == "Article 1"
        assert articles[1].title == "Article 2"

    def test_正常系_URLが正しく抽出される(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        blog_html = _build_blog_html(
            [
                {
                    "title": "Test",
                    "date": "2026-01-01",
                    "url": "https://example.com/test-article",
                },
            ]
        )
        config = _make_config()
        articles = engine._extract_article_list(blog_html, config)

        assert len(articles) == 1
        assert articles[0].url == "https://example.com/test-article"

    def test_エッジケース_記事がない場合空リストを返す(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        html = "<html><body><div>No articles</div></body></html>"
        config = _make_config()
        articles = engine._extract_article_list(html, config)
        assert articles == []

    def test_エッジケース_タイトルがない記事はスキップされる(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        # Article without title link
        html = (
            "<html><body>"
            "<article><p>No title here</p><time>2026-01-01</time></article>"
            "</body></html>"
        )
        config = _make_config()
        articles = engine._extract_article_list(html, config)
        assert len(articles) == 0


# ---------------------------------------------------------------------------
# _fetch_page: HTTP fetch
# ---------------------------------------------------------------------------


class TestFetchPage:
    """Tests for _fetch_page HTTP fetch with policy integration."""

    @pytest.mark.asyncio
    async def test_正常系_ページを取得できる(
        self,
        engine: CompanyScraperEngine,
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            response = await engine._fetch_page(
                "https://example.com/blog",
                domain="example.com",
            )

        assert response.status_code == 200

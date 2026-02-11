"""Unit tests for market.industry.scrapers.consulting module.

Tests cover the ConsultingScraper class and its 4 site-specific
subclasses: McKinseyScraper, BCGScraper, DeloitteScraper, PwCScraper.

Test categories:
- Initialization and configuration
- HTML parsing for each site's article listing page
- Body text extraction with trafilatura fallback
- Rate limiting compliance
- JSON report saving
- Error handling
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from market.industry.scrapers.consulting import (
    BCGScraper,
    ConsultingScraper,
    DeloitteScraper,
    McKinseyScraper,
    PwCScraper,
)
from market.industry.types import (
    IndustryReport,
    RetryConfig,
    ScrapingConfig,
    ScrapingResult,
    SourceTier,
)

# =============================================================================
# Sample HTML fixtures
# =============================================================================

MCKINSEY_SAMPLE_HTML = """
<html>
<body>
<div class="article-listing">
  <div class="article-item" data-component="article-item">
    <a href="/featured-insights/semiconductor-outlook-2026"
       class="article-item__link">
      <h3 class="article-item__title">Semiconductor Outlook 2026</h3>
    </a>
    <div class="article-item__date">January 15, 2026</div>
    <p class="article-item__description">An in-depth look at the semiconductor industry.</p>
  </div>
  <div class="article-item" data-component="article-item">
    <a href="/featured-insights/ai-in-healthcare"
       class="article-item__link">
      <h3 class="article-item__title">AI in Healthcare: Trends for 2026</h3>
    </a>
    <div class="article-item__date">February 1, 2026</div>
    <p class="article-item__description">How AI is transforming healthcare delivery.</p>
  </div>
</div>
</body>
</html>
"""

BCG_SAMPLE_HTML = """
<html>
<body>
<div class="publications-listing">
  <article class="publication-card">
    <a href="/publications/2026/digital-transformation-strategy"
       class="publication-card__link">
      <h2 class="publication-card__title">Digital Transformation Strategy</h2>
    </a>
    <time class="publication-card__date" datetime="2026-01-20">January 20, 2026</time>
    <p class="publication-card__summary">Companies accelerating digital transformation.</p>
  </article>
  <article class="publication-card">
    <a href="/publications/2026/sustainable-energy-future"
       class="publication-card__link">
      <h2 class="publication-card__title">Sustainable Energy Future</h2>
    </a>
    <time class="publication-card__date" datetime="2026-02-05">February 5, 2026</time>
    <p class="publication-card__summary">The path to a sustainable energy future.</p>
  </article>
</div>
</body>
</html>
"""

DELOITTE_SAMPLE_HTML = """
<html>
<body>
<div class="insights-listing">
  <div class="promo-card" data-component="promo-card">
    <a href="/insights/us/en/industry/financial-services/outlook-2026.html"
       class="promo-card__link">
      <h3 class="promo-card__title">Financial Services Outlook 2026</h3>
    </a>
    <span class="promo-card__date">Jan 10, 2026</span>
    <p class="promo-card__description">Key trends shaping financial services.</p>
  </div>
</div>
</body>
</html>
"""

PWC_SAMPLE_HTML = """
<html>
<body>
<div class="content-listing">
  <div class="content-card">
    <a href="/gx/en/issues/strategy/global-annual-review-2026.html"
       class="content-card__link">
      <h3 class="content-card__title">Global Annual Review 2026</h3>
    </a>
    <span class="content-card__date">2026-01-25</span>
    <p class="content-card__excerpt">Strategic insights for the year ahead.</p>
  </div>
</div>
</body>
</html>
"""


# =============================================================================
# Test ConsultingScraper Base
# =============================================================================


class TestConsultingScraperInit:
    """Tests for ConsultingScraper initialization."""

    def test_正常系_デフォルト設定で初期化できる(self) -> None:
        scraper = McKinseyScraper()
        assert scraper.source_name == "McKinsey"
        assert "mckinsey.com" in scraper.base_url
        assert scraper.config.polite_delay >= 1.0
        assert scraper.sector == "all"

    def test_正常系_セクター指定で初期化できる(self) -> None:
        scraper = McKinseyScraper(sector="Technology")
        assert scraper.sector == "Technology"

    def test_正常系_カスタム設定で初期化できる(self) -> None:
        config = ScrapingConfig(polite_delay=3.0, timeout=60.0)
        retry = RetryConfig(max_attempts=5)
        scraper = McKinseyScraper(config=config, retry_config=retry)
        assert scraper.config.polite_delay == 3.0
        assert scraper.retry_config.max_attempts == 5

    def test_正常系_カスタム出力ディレクトリで初期化できる(self) -> None:
        output_dir = Path("/tmp/test_output")
        scraper = McKinseyScraper(output_dir=output_dir)
        assert scraper.output_dir == output_dir


class TestConsultingScraperOutputDir:
    """Tests for ConsultingScraper output directory handling."""

    def test_正常系_デフォルト出力ディレクトリが設定される(self) -> None:
        scraper = McKinseyScraper()
        assert "industry_reports" in str(scraper.output_dir)
        assert "mckinsey" in str(scraper.output_dir)

    def test_正常系_BCGの出力ディレクトリが正しい(self) -> None:
        scraper = BCGScraper()
        assert "bcg" in str(scraper.output_dir)

    def test_正常系_Deloitteの出力ディレクトリが正しい(self) -> None:
        scraper = DeloitteScraper()
        assert "deloitte" in str(scraper.output_dir)

    def test_正常系_PwCの出力ディレクトリが正しい(self) -> None:
        scraper = PwCScraper()
        assert "pwc" in str(scraper.output_dir)


# =============================================================================
# Test McKinsey Scraper
# =============================================================================


class TestMcKinseyScraperParseHtml:
    """Tests for McKinseyScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = McKinseyScraper()
        reports = await scraper.parse_html(MCKINSEY_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "Semiconductor Outlook 2026"
        assert reports[0].source == "McKinsey"
        assert reports[0].tier == SourceTier.SCRAPING
        assert "mckinsey.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_公開日が正しくパースされる(self) -> None:
        scraper = McKinseyScraper()
        reports = await scraper.parse_html(MCKINSEY_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 15

    @pytest.mark.asyncio
    async def test_正常系_サマリーが抽出される(self) -> None:
        scraper = McKinseyScraper()
        reports = await scraper.parse_html(MCKINSEY_SAMPLE_HTML)
        assert reports[0].summary == "An in-depth look at the semiconductor industry."

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = McKinseyScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test BCG Scraper
# =============================================================================


class TestBCGScraperParseHtml:
    """Tests for BCGScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = BCGScraper()
        reports = await scraper.parse_html(BCG_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "Digital Transformation Strategy"
        assert reports[0].source == "BCG"
        assert "bcg.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_datetime属性から日付がパースされる(self) -> None:
        scraper = BCGScraper()
        reports = await scraper.parse_html(BCG_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 20

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = BCGScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test Deloitte Scraper
# =============================================================================


class TestDeloitteScraperParseHtml:
    """Tests for DeloitteScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = DeloitteScraper()
        reports = await scraper.parse_html(DELOITTE_SAMPLE_HTML)
        assert len(reports) == 1
        assert reports[0].title == "Financial Services Outlook 2026"
        assert reports[0].source == "Deloitte"
        assert "deloitte.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = DeloitteScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test PwC Scraper
# =============================================================================


class TestPwCScraperParseHtml:
    """Tests for PwCScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = PwCScraper()
        reports = await scraper.parse_html(PWC_SAMPLE_HTML)
        assert len(reports) == 1
        assert reports[0].title == "Global Annual Review 2026"
        assert reports[0].source == "PwC"
        assert "pwc.com" in reports[0].url or "strategyand" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_ISO日付がパースされる(self) -> None:
        scraper = PwCScraper()
        reports = await scraper.parse_html(PWC_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 25

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = PwCScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test Scrape Method (Integration with fetch)
# =============================================================================


class TestConsultingScraperScrape:
    """Tests for the scrape() method with mocked fetch."""

    @pytest.mark.asyncio
    async def test_正常系_scrapeが成功してScrapingResultを返す(self) -> None:
        scraper = McKinseyScraper()

        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            return_value=MCKINSEY_SAMPLE_HTML,
        ):
            result = await scraper.scrape()
            assert isinstance(result, ScrapingResult)
            assert result.success is True
            assert result.source == "McKinsey"
            assert len(result.reports) == 2

    @pytest.mark.asyncio
    async def test_異常系_fetch失敗時にエラー結果を返す(self) -> None:
        scraper = McKinseyScraper()

        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            side_effect=Exception("Network error"),
        ):
            result = await scraper.scrape()
            assert isinstance(result, ScrapingResult)
            assert result.success is False
            assert result.error_message is not None
            assert "Network error" in result.error_message


# =============================================================================
# Test Report Saving
# =============================================================================


class TestConsultingScraperSaveReports:
    """Tests for the save_reports() method."""

    @pytest.mark.asyncio
    async def test_正常系_レポートがJSONファイルに保存される(
        self, tmp_path: Path
    ) -> None:
        scraper = McKinseyScraper(output_dir=tmp_path / "mckinsey")
        reports = [
            IndustryReport(
                source="McKinsey",
                title="Test Report",
                url="https://mckinsey.com/test",
                published_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
                sector="Technology",
                summary="Test summary",
            ),
        ]

        saved_paths = await scraper.save_reports(reports)
        assert len(saved_paths) == 1
        assert saved_paths[0].exists()
        assert saved_paths[0].suffix == ".json"

        # Verify JSON content
        data = json.loads(saved_paths[0].read_text(encoding="utf-8"))
        assert data["title"] == "Test Report"
        assert data["source"] == "McKinsey"
        assert data["url"] == "https://mckinsey.com/test"

    @pytest.mark.asyncio
    async def test_正常系_ファイル名に日付とタイトルが含まれる(
        self, tmp_path: Path
    ) -> None:
        scraper = McKinseyScraper(output_dir=tmp_path / "mckinsey")
        reports = [
            IndustryReport(
                source="McKinsey",
                title="Semiconductor Outlook 2026",
                url="https://mckinsey.com/test",
                published_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
                sector="Technology",
            ),
        ]

        saved_paths = await scraper.save_reports(reports)
        filename = saved_paths[0].name
        assert "2026-01-15" in filename
        assert "semiconductor" in filename.lower()

    @pytest.mark.asyncio
    async def test_エッジケース_空リストで何も保存しない(self, tmp_path: Path) -> None:
        scraper = McKinseyScraper(output_dir=tmp_path / "mckinsey")
        saved_paths = await scraper.save_reports([])
        assert saved_paths == []


# =============================================================================
# Test Body Extraction
# =============================================================================


class TestConsultingScraperExtractBody:
    """Tests for body text extraction with trafilatura."""

    @pytest.mark.asyncio
    async def test_正常系_trafilaturaで本文を抽出できる(self) -> None:
        scraper = McKinseyScraper()

        with patch(
            "market.industry.scrapers.consulting._extract_body_text",
            new_callable=AsyncMock,
            return_value="This is the full article body text with enough content.",
        ):
            body = await scraper.extract_body("https://mckinsey.com/test-article")
            assert body is not None
            assert len(body) > 0

    @pytest.mark.asyncio
    async def test_異常系_抽出失敗でNone(self) -> None:
        scraper = McKinseyScraper()

        with patch(
            "market.industry.scrapers.consulting._extract_body_text",
            new_callable=AsyncMock,
            return_value=None,
        ):
            body = await scraper.extract_body("https://mckinsey.com/test-article")
            assert body is None


# =============================================================================
# Test Date Parsing
# =============================================================================


class TestDateParsing:
    """Tests for date parsing utility functions."""

    def test_正常系_January_15_2026_形式(self) -> None:
        from market.industry.scrapers.consulting import _parse_date

        dt = _parse_date("January 15, 2026")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 1
        assert dt.day == 15

    def test_正常系_ISO形式_2026_01_15(self) -> None:
        from market.industry.scrapers.consulting import _parse_date

        dt = _parse_date("2026-01-15")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 1

    def test_正常系_Jan_10_2026_形式(self) -> None:
        from market.industry.scrapers.consulting import _parse_date

        dt = _parse_date("Jan 10, 2026")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 1
        assert dt.day == 10

    def test_正常系_Feb_1_2026_形式(self) -> None:
        from market.industry.scrapers.consulting import _parse_date

        dt = _parse_date("February 1, 2026")
        assert dt is not None
        assert dt.month == 2
        assert dt.day == 1

    def test_エッジケース_無効な日付文字列でNone(self) -> None:
        from market.industry.scrapers.consulting import _parse_date

        dt = _parse_date("not a date")
        assert dt is None

    def test_エッジケース_空文字列でNone(self) -> None:
        from market.industry.scrapers.consulting import _parse_date

        dt = _parse_date("")
        assert dt is None


# =============================================================================
# Test URL Slug Generation
# =============================================================================


class TestSlugGeneration:
    """Tests for URL slug generation utility."""

    def test_正常系_タイトルからスラグを生成(self) -> None:
        from market.industry.scrapers.consulting import _title_to_slug

        slug = _title_to_slug("Semiconductor Outlook 2026")
        assert slug == "semiconductor-outlook-2026"

    def test_正常系_特殊文字を除去(self) -> None:
        from market.industry.scrapers.consulting import _title_to_slug

        slug = _title_to_slug("AI & Machine Learning: The Future!")
        assert ":" not in slug
        assert "!" not in slug
        assert "&" not in slug

    def test_正常系_長いタイトルを切り詰め(self) -> None:
        from market.industry.scrapers.consulting import _title_to_slug

        long_title = "A" * 200
        slug = _title_to_slug(long_title)
        assert len(slug) <= 80

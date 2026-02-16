"""Unit tests for extended consulting scrapers (Bain, Accenture, EY, KPMG).

Tests cover the 4 new ConsultingScraper subclasses added in Issue #3535:
BainScraper, AccentureScraper, EYScraper, KPMGScraper.

Test categories:
- Initialization and configuration
- HTML parsing for each site's article listing page
- Empty HTML edge cases
- URL construction (relative to absolute)
- Date parsing
- Scrape method integration with mocked fetch
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from market.industry.scrapers.consulting import (
    AccentureScraper,
    BainScraper,
    ConsultingScraper,
    EYScraper,
    KPMGScraper,
)
from market.industry.types import (
    RetryConfig,
    ScrapingConfig,
    ScrapingResult,
    SourceTier,
)

# =============================================================================
# Sample HTML fixtures
# =============================================================================

BAIN_SAMPLE_HTML = """
<html>
<body>
<div class="insights-feed">
  <div class="insight-card" data-component="insight-card">
    <a href="/insights/topics/digital-transformation-strategy"
       class="insight-card__link">
      <h3 class="insight-card__title">Digital Transformation Strategy</h3>
    </a>
    <span class="insight-card__date">January 20, 2026</span>
    <p class="insight-card__description">How companies are accelerating digital change.</p>
  </div>
  <div class="insight-card" data-component="insight-card">
    <a href="/insights/topics/private-equity-outlook"
       class="insight-card__link">
      <h3 class="insight-card__title">Private Equity Outlook 2026</h3>
    </a>
    <span class="insight-card__date">February 5, 2026</span>
    <p class="insight-card__description">Key trends shaping private equity markets.</p>
  </div>
</div>
</body>
</html>
"""

ACCENTURE_SAMPLE_HTML = """
<html>
<body>
<div class="insights-listing">
  <div class="rad-card" data-component="rad-card">
    <a href="/us-en/insights/technology/technology-trends-2026"
       class="rad-card__link">
      <h4 class="rad-card__title">Technology Vision 2026</h4>
    </a>
    <span class="rad-card__date">January 15, 2026</span>
    <p class="rad-card__description">Top trends reshaping every industry.</p>
  </div>
  <div class="rad-card" data-component="rad-card">
    <a href="/us-en/insights/consulting/future-of-work"
       class="rad-card__link">
      <h4 class="rad-card__title">Future of Work Report</h4>
    </a>
    <span class="rad-card__date">2026-02-10</span>
    <p class="rad-card__description">How organizations are reimagining work.</p>
  </div>
</div>
</body>
</html>
"""

EY_SAMPLE_HTML = """
<html>
<body>
<div class="cmp-container">
  <article class="insight-article" data-component="insight-article">
    <a href="/en_us/insights/strategy/ceo-outlook-2026"
       class="insight-article__link">
      <h3 class="insight-article__title">CEO Outlook 2026</h3>
    </a>
    <span class="insight-article__date">Jan 18, 2026</span>
    <p class="insight-article__description">How CEOs are navigating uncertainty.</p>
  </article>
  <article class="insight-article" data-component="insight-article">
    <a href="/en_us/insights/tax/tax-policy-trends"
       class="insight-article__link">
      <h3 class="insight-article__title">Global Tax Policy Trends</h3>
    </a>
    <span class="insight-article__date">February 12, 2026</span>
    <p class="insight-article__description">Key tax policy developments worldwide.</p>
  </article>
</div>
</body>
</html>
"""

KPMG_SAMPLE_HTML = """
<html>
<body>
<div class="insights-listing">
  <div class="kpmg-card" data-component="kpmg-card">
    <a href="/us/en/articles/2026/global-economic-outlook.html"
       class="kpmg-card__link">
      <h3 class="kpmg-card__title">Global Economic Outlook 2026</h3>
    </a>
    <span class="kpmg-card__date">January 22, 2026</span>
    <p class="kpmg-card__description">Our view on the global economy in 2026.</p>
  </div>
  <div class="kpmg-card" data-component="kpmg-card">
    <a href="/us/en/articles/2026/ai-in-audit.html"
       class="kpmg-card__link">
      <h3 class="kpmg-card__title">AI in Audit: Transforming Assurance</h3>
    </a>
    <span class="kpmg-card__date">2026-02-08</span>
    <p class="kpmg-card__description">How AI is reshaping audit practices.</p>
  </div>
</div>
</body>
</html>
"""


# =============================================================================
# Test Bain Scraper - Initialization
# =============================================================================


class TestBainScraperInit:
    """Tests for BainScraper initialization."""

    def test_正常系_デフォルト設定で初期化できる(self) -> None:
        scraper = BainScraper()
        assert scraper.source_name == "Bain"
        assert "bain.com" in scraper.base_url
        assert scraper.config.polite_delay >= 1.0
        assert scraper.sector == "all"

    def test_正常系_セクター指定で初期化できる(self) -> None:
        scraper = BainScraper(sector="Technology")
        assert scraper.sector == "Technology"

    def test_正常系_カスタム設定で初期化できる(self) -> None:
        config = ScrapingConfig(polite_delay=3.0, timeout=60.0)
        retry = RetryConfig(max_attempts=5)
        scraper = BainScraper(config=config, retry_config=retry)
        assert scraper.config.polite_delay == 3.0
        assert scraper.retry_config.max_attempts == 5

    def test_正常系_カスタム出力ディレクトリで初期化できる(self) -> None:
        output_dir = Path("/tmp/test_output")
        scraper = BainScraper(output_dir=output_dir)
        assert scraper.output_dir == output_dir

    def test_正常系_ConsultingScraperのサブクラス(self) -> None:
        scraper = BainScraper()
        assert isinstance(scraper, ConsultingScraper)

    def test_正常系_デフォルト出力ディレクトリが正しい(self) -> None:
        scraper = BainScraper()
        assert "industry_reports" in str(scraper.output_dir)
        assert "bain" in str(scraper.output_dir)


# =============================================================================
# Test Bain Scraper - HTML Parsing
# =============================================================================


class TestBainScraperParseHtml:
    """Tests for BainScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = BainScraper()
        reports = await scraper.parse_html(BAIN_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "Digital Transformation Strategy"
        assert reports[0].source == "Bain"
        assert reports[0].tier == SourceTier.SCRAPING
        assert "bain.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_公開日が正しくパースされる(self) -> None:
        scraper = BainScraper()
        reports = await scraper.parse_html(BAIN_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 20

    @pytest.mark.asyncio
    async def test_正常系_サマリーが抽出される(self) -> None:
        scraper = BainScraper()
        reports = await scraper.parse_html(BAIN_SAMPLE_HTML)
        assert reports[0].summary == "How companies are accelerating digital change."

    @pytest.mark.asyncio
    async def test_正常系_相対URLが絶対URLに変換される(self) -> None:
        scraper = BainScraper()
        reports = await scraper.parse_html(BAIN_SAMPLE_HTML)
        assert reports[0].url.startswith("https://")

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = BainScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test Accenture Scraper - Initialization
# =============================================================================


class TestAccentureScraperInit:
    """Tests for AccentureScraper initialization."""

    def test_正常系_デフォルト設定で初期化できる(self) -> None:
        scraper = AccentureScraper()
        assert scraper.source_name == "Accenture"
        assert "accenture.com" in scraper.base_url
        assert scraper.config.polite_delay >= 1.0
        assert scraper.sector == "all"

    def test_正常系_ConsultingScraperのサブクラス(self) -> None:
        scraper = AccentureScraper()
        assert isinstance(scraper, ConsultingScraper)

    def test_正常系_デフォルト出力ディレクトリが正しい(self) -> None:
        scraper = AccentureScraper()
        assert "industry_reports" in str(scraper.output_dir)
        assert "accenture" in str(scraper.output_dir)


# =============================================================================
# Test Accenture Scraper - HTML Parsing
# =============================================================================


class TestAccentureScraperParseHtml:
    """Tests for AccentureScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = AccentureScraper()
        reports = await scraper.parse_html(ACCENTURE_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "Technology Vision 2026"
        assert reports[0].source == "Accenture"
        assert reports[0].tier == SourceTier.SCRAPING
        assert "accenture.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_公開日が正しくパースされる(self) -> None:
        scraper = AccentureScraper()
        reports = await scraper.parse_html(ACCENTURE_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 15

    @pytest.mark.asyncio
    async def test_正常系_ISO日付がパースされる(self) -> None:
        scraper = AccentureScraper()
        reports = await scraper.parse_html(ACCENTURE_SAMPLE_HTML)
        assert reports[1].published_at.year == 2026
        assert reports[1].published_at.month == 2
        assert reports[1].published_at.day == 10

    @pytest.mark.asyncio
    async def test_正常系_サマリーが抽出される(self) -> None:
        scraper = AccentureScraper()
        reports = await scraper.parse_html(ACCENTURE_SAMPLE_HTML)
        assert reports[0].summary == "Top trends reshaping every industry."

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = AccentureScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test EY Scraper - Initialization
# =============================================================================


class TestEYScraperInit:
    """Tests for EYScraper initialization."""

    def test_正常系_デフォルト設定で初期化できる(self) -> None:
        scraper = EYScraper()
        assert scraper.source_name == "EY"
        assert "ey.com" in scraper.base_url
        assert scraper.config.polite_delay >= 1.0
        assert scraper.sector == "all"

    def test_正常系_ConsultingScraperのサブクラス(self) -> None:
        scraper = EYScraper()
        assert isinstance(scraper, ConsultingScraper)

    def test_正常系_デフォルト出力ディレクトリが正しい(self) -> None:
        scraper = EYScraper()
        assert "industry_reports" in str(scraper.output_dir)
        assert "ey" in str(scraper.output_dir)


# =============================================================================
# Test EY Scraper - HTML Parsing
# =============================================================================


class TestEYScraperParseHtml:
    """Tests for EYScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = EYScraper()
        reports = await scraper.parse_html(EY_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "CEO Outlook 2026"
        assert reports[0].source == "EY"
        assert reports[0].tier == SourceTier.SCRAPING
        assert "ey.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_公開日が正しくパースされる(self) -> None:
        scraper = EYScraper()
        reports = await scraper.parse_html(EY_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 18

    @pytest.mark.asyncio
    async def test_正常系_サマリーが抽出される(self) -> None:
        scraper = EYScraper()
        reports = await scraper.parse_html(EY_SAMPLE_HTML)
        assert reports[0].summary == "How CEOs are navigating uncertainty."

    @pytest.mark.asyncio
    async def test_正常系_相対URLが絶対URLに変換される(self) -> None:
        scraper = EYScraper()
        reports = await scraper.parse_html(EY_SAMPLE_HTML)
        assert reports[0].url.startswith("https://")

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = EYScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test KPMG Scraper - Initialization
# =============================================================================


class TestKPMGScraperInit:
    """Tests for KPMGScraper initialization."""

    def test_正常系_デフォルト設定で初期化できる(self) -> None:
        scraper = KPMGScraper()
        assert scraper.source_name == "KPMG"
        assert "kpmg.com" in scraper.base_url
        assert scraper.config.polite_delay >= 1.0
        assert scraper.sector == "all"

    def test_正常系_ConsultingScraperのサブクラス(self) -> None:
        scraper = KPMGScraper()
        assert isinstance(scraper, ConsultingScraper)

    def test_正常系_デフォルト出力ディレクトリが正しい(self) -> None:
        scraper = KPMGScraper()
        assert "industry_reports" in str(scraper.output_dir)
        assert "kpmg" in str(scraper.output_dir)


# =============================================================================
# Test KPMG Scraper - HTML Parsing
# =============================================================================


class TestKPMGScraperParseHtml:
    """Tests for KPMGScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = KPMGScraper()
        reports = await scraper.parse_html(KPMG_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "Global Economic Outlook 2026"
        assert reports[0].source == "KPMG"
        assert reports[0].tier == SourceTier.SCRAPING
        assert "kpmg.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_公開日が正しくパースされる(self) -> None:
        scraper = KPMGScraper()
        reports = await scraper.parse_html(KPMG_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 22

    @pytest.mark.asyncio
    async def test_正常系_ISO日付がパースされる(self) -> None:
        scraper = KPMGScraper()
        reports = await scraper.parse_html(KPMG_SAMPLE_HTML)
        assert reports[1].published_at.year == 2026
        assert reports[1].published_at.month == 2
        assert reports[1].published_at.day == 8

    @pytest.mark.asyncio
    async def test_正常系_サマリーが抽出される(self) -> None:
        scraper = KPMGScraper()
        reports = await scraper.parse_html(KPMG_SAMPLE_HTML)
        assert reports[0].summary == "Our view on the global economy in 2026."

    @pytest.mark.asyncio
    async def test_正常系_相対URLが絶対URLに変換される(self) -> None:
        scraper = KPMGScraper()
        reports = await scraper.parse_html(KPMG_SAMPLE_HTML)
        assert reports[0].url.startswith("https://")

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = KPMGScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test Scrape Method (Integration with mocked fetch)
# =============================================================================


class TestExtendedConsultingScraperScrape:
    """Tests for the scrape() method with mocked fetch for new scrapers."""

    @pytest.mark.asyncio
    async def test_正常系_BainのscrapeがScrapingResultを返す(self) -> None:
        scraper = BainScraper()
        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            return_value=BAIN_SAMPLE_HTML,
        ):
            result = await scraper.scrape()
            assert isinstance(result, ScrapingResult)
            assert result.success is True
            assert result.source == "Bain"
            assert len(result.reports) == 2

    @pytest.mark.asyncio
    async def test_正常系_AccentureのscrapeがScrapingResultを返す(self) -> None:
        scraper = AccentureScraper()
        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            return_value=ACCENTURE_SAMPLE_HTML,
        ):
            result = await scraper.scrape()
            assert isinstance(result, ScrapingResult)
            assert result.success is True
            assert result.source == "Accenture"
            assert len(result.reports) == 2

    @pytest.mark.asyncio
    async def test_正常系_EYのscrapeがScrapingResultを返す(self) -> None:
        scraper = EYScraper()
        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            return_value=EY_SAMPLE_HTML,
        ):
            result = await scraper.scrape()
            assert isinstance(result, ScrapingResult)
            assert result.success is True
            assert result.source == "EY"
            assert len(result.reports) == 2

    @pytest.mark.asyncio
    async def test_正常系_KPMGのscrapeがScrapingResultを返す(self) -> None:
        scraper = KPMGScraper()
        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            return_value=KPMG_SAMPLE_HTML,
        ):
            result = await scraper.scrape()
            assert isinstance(result, ScrapingResult)
            assert result.success is True
            assert result.source == "KPMG"
            assert len(result.reports) == 2

    @pytest.mark.asyncio
    async def test_異常系_fetch失敗時にエラー結果を返す(self) -> None:
        scraper = BainScraper()
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

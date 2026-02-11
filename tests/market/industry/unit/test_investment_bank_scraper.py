"""Unit tests for market.industry.scrapers.investment_bank module.

Tests cover the InvestmentBankScraper class and its 3 site-specific
subclasses: GoldmanSachsScraper, MorganStanleyScraper, JPMorganScraper.

Test categories:
- Initialization and configuration
- HTML parsing for each site's article listing page
- Body text extraction with trafilatura fallback
- Report saving to JSON files
- robots.txt compliance
- Scrape method integration with mocked fetch
- Error handling
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from market.industry.scrapers.investment_bank import (
    GoldmanSachsScraper,
    InvestmentBankScraper,
    JPMorganScraper,
    MorganStanleyScraper,
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

GOLDMAN_SAMPLE_HTML = """
<html>
<body>
<div class="insights-listing">
  <article class="article-card" data-testid="article-card">
    <a href="/insights/articles/global-macro-outlook-2026"
       class="article-card__link">
      <h3 class="article-card__title">Global Macro Outlook 2026</h3>
    </a>
    <time class="article-card__date" datetime="2026-01-18">January 18, 2026</time>
    <p class="article-card__description">Our economists present the global macro outlook.</p>
  </article>
  <article class="article-card" data-testid="article-card">
    <a href="/insights/articles/top-of-mind-ai-investment"
       class="article-card__link">
      <h3 class="article-card__title">Top of Mind: AI Investment Trends</h3>
    </a>
    <time class="article-card__date" datetime="2026-02-03">February 3, 2026</time>
    <p class="article-card__description">How AI is reshaping investment strategies.</p>
  </article>
</div>
</body>
</html>
"""

MORGAN_STANLEY_SAMPLE_HTML = """
<html>
<body>
<div class="ideas-listing">
  <div class="thought-leadership-card">
    <a href="/ideas/global-investment-outlook-2026"
       class="thought-leadership-card__link">
      <h3 class="thought-leadership-card__title">Global Investment Outlook 2026</h3>
    </a>
    <span class="thought-leadership-card__date">January 22, 2026</span>
    <p class="thought-leadership-card__summary">Key themes for investors in the year ahead.</p>
  </div>
  <div class="thought-leadership-card">
    <a href="/ideas/semiconductors-supply-chain-analysis"
       class="thought-leadership-card__link">
      <h3 class="thought-leadership-card__title">Semiconductors: Supply Chain Analysis</h3>
    </a>
    <span class="thought-leadership-card__date">February 8, 2026</span>
    <p class="thought-leadership-card__summary">Deep dive into semiconductor supply chains.</p>
  </div>
</div>
</body>
</html>
"""

JPMORGAN_SAMPLE_HTML = """
<html>
<body>
<div class="research-listing">
  <div class="research-card" data-type="research">
    <a href="/insights/research/global-data-watch-q1-2026"
       class="research-card__link">
      <h3 class="research-card__title">Global Data Watch Q1 2026</h3>
    </a>
    <span class="research-card__date">January 25, 2026</span>
    <p class="research-card__excerpt">Weekly economic and market commentary.</p>
  </div>
  <div class="research-card" data-type="research">
    <a href="/insights/research/us-equity-strategy-update"
       class="research-card__link">
      <h3 class="research-card__title">US Equity Strategy Update</h3>
    </a>
    <span class="research-card__date">2026-02-01</span>
    <p class="research-card__excerpt">Our updated view on US equities.</p>
  </div>
</div>
</body>
</html>
"""


# =============================================================================
# Test InvestmentBankScraper Base
# =============================================================================


class TestInvestmentBankScraperInit:
    """Tests for InvestmentBankScraper initialization."""

    def test_正常系_GoldmanSachsがデフォルト設定で初期化できる(self) -> None:
        scraper = GoldmanSachsScraper()
        assert scraper.source_name == "Goldman Sachs"
        assert "goldmansachs.com" in scraper.base_url
        assert scraper.config.polite_delay >= 1.0
        assert scraper.sector == "all"

    def test_正常系_MorganStanleyがデフォルト設定で初期化できる(self) -> None:
        scraper = MorganStanleyScraper()
        assert scraper.source_name == "Morgan Stanley"
        assert "morganstanley.com" in scraper.base_url

    def test_正常系_JPMorganがデフォルト設定で初期化できる(self) -> None:
        scraper = JPMorganScraper()
        assert scraper.source_name == "JP Morgan"
        assert "jpmorgan.com" in scraper.base_url

    def test_正常系_セクター指定で初期化できる(self) -> None:
        scraper = GoldmanSachsScraper(sector="Technology")
        assert scraper.sector == "Technology"

    def test_正常系_カスタム設定で初期化できる(self) -> None:
        config = ScrapingConfig(polite_delay=3.0, timeout=60.0)
        retry = RetryConfig(max_attempts=5)
        scraper = GoldmanSachsScraper(config=config, retry_config=retry)
        assert scraper.config.polite_delay == 3.0
        assert scraper.retry_config.max_attempts == 5

    def test_正常系_カスタム出力ディレクトリで初期化できる(self) -> None:
        output_dir = Path("/tmp/test_output")
        scraper = GoldmanSachsScraper(output_dir=output_dir)
        assert scraper.output_dir == output_dir


class TestInvestmentBankScraperOutputDir:
    """Tests for InvestmentBankScraper output directory handling."""

    def test_正常系_GoldmanSachsの出力ディレクトリが正しい(self) -> None:
        scraper = GoldmanSachsScraper()
        assert "industry_reports" in str(scraper.output_dir)
        assert "goldman" in str(scraper.output_dir)

    def test_正常系_MorganStanleyの出力ディレクトリが正しい(self) -> None:
        scraper = MorganStanleyScraper()
        assert "morgan_stanley" in str(scraper.output_dir)

    def test_正常系_JPMorganの出力ディレクトリが正しい(self) -> None:
        scraper = JPMorganScraper()
        assert "jpmorgan" in str(scraper.output_dir)


class TestInvestmentBankScraperIsSubclass:
    """Tests to verify inheritance from ConsultingScraper pattern."""

    def test_正常系_GoldmanSachsはInvestmentBankScraperのサブクラス(self) -> None:
        scraper = GoldmanSachsScraper()
        assert isinstance(scraper, InvestmentBankScraper)

    def test_正常系_MorganStanleyはInvestmentBankScraperのサブクラス(self) -> None:
        scraper = MorganStanleyScraper()
        assert isinstance(scraper, InvestmentBankScraper)

    def test_正常系_JPMorganはInvestmentBankScraperのサブクラス(self) -> None:
        scraper = JPMorganScraper()
        assert isinstance(scraper, InvestmentBankScraper)


# =============================================================================
# Test Goldman Sachs Scraper
# =============================================================================


class TestGoldmanSachsScraperParseHtml:
    """Tests for GoldmanSachsScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = GoldmanSachsScraper()
        reports = await scraper.parse_html(GOLDMAN_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "Global Macro Outlook 2026"
        assert reports[0].source == "Goldman Sachs"
        assert reports[0].tier == SourceTier.SCRAPING
        assert "goldmansachs.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_公開日が正しくパースされる(self) -> None:
        scraper = GoldmanSachsScraper()
        reports = await scraper.parse_html(GOLDMAN_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 18

    @pytest.mark.asyncio
    async def test_正常系_サマリーが抽出される(self) -> None:
        scraper = GoldmanSachsScraper()
        reports = await scraper.parse_html(GOLDMAN_SAMPLE_HTML)
        assert reports[0].summary == "Our economists present the global macro outlook."

    @pytest.mark.asyncio
    async def test_正常系_相対URLが絶対URLに変換される(self) -> None:
        scraper = GoldmanSachsScraper()
        reports = await scraper.parse_html(GOLDMAN_SAMPLE_HTML)
        assert reports[0].url.startswith("https://")

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = GoldmanSachsScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test Morgan Stanley Scraper
# =============================================================================


class TestMorganStanleyScraperParseHtml:
    """Tests for MorganStanleyScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = MorganStanleyScraper()
        reports = await scraper.parse_html(MORGAN_STANLEY_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "Global Investment Outlook 2026"
        assert reports[0].source == "Morgan Stanley"
        assert "morganstanley.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_公開日が正しくパースされる(self) -> None:
        scraper = MorganStanleyScraper()
        reports = await scraper.parse_html(MORGAN_STANLEY_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 22

    @pytest.mark.asyncio
    async def test_正常系_サマリーが抽出される(self) -> None:
        scraper = MorganStanleyScraper()
        reports = await scraper.parse_html(MORGAN_STANLEY_SAMPLE_HTML)
        assert reports[0].summary == "Key themes for investors in the year ahead."

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = MorganStanleyScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test JP Morgan Scraper
# =============================================================================


class TestJPMorganScraperParseHtml:
    """Tests for JPMorganScraper HTML parsing."""

    @pytest.mark.asyncio
    async def test_正常系_記事一覧からレポートを抽出できる(self) -> None:
        scraper = JPMorganScraper()
        reports = await scraper.parse_html(JPMORGAN_SAMPLE_HTML)
        assert len(reports) == 2
        assert reports[0].title == "Global Data Watch Q1 2026"
        assert reports[0].source == "JP Morgan"
        assert "jpmorgan.com" in reports[0].url

    @pytest.mark.asyncio
    async def test_正常系_公開日が正しくパースされる(self) -> None:
        scraper = JPMorganScraper()
        reports = await scraper.parse_html(JPMORGAN_SAMPLE_HTML)
        assert reports[0].published_at.year == 2026
        assert reports[0].published_at.month == 1
        assert reports[0].published_at.day == 25

    @pytest.mark.asyncio
    async def test_正常系_ISO日付がパースされる(self) -> None:
        scraper = JPMorganScraper()
        reports = await scraper.parse_html(JPMORGAN_SAMPLE_HTML)
        # Second article uses ISO format
        assert reports[1].published_at.year == 2026
        assert reports[1].published_at.month == 2
        assert reports[1].published_at.day == 1

    @pytest.mark.asyncio
    async def test_正常系_サマリーが抽出される(self) -> None:
        scraper = JPMorganScraper()
        reports = await scraper.parse_html(JPMORGAN_SAMPLE_HTML)
        assert reports[0].summary == "Weekly economic and market commentary."

    @pytest.mark.asyncio
    async def test_エッジケース_空HTMLで空リスト(self) -> None:
        scraper = JPMorganScraper()
        reports = await scraper.parse_html("<html><body></body></html>")
        assert reports == []


# =============================================================================
# Test Scrape Method (Integration with fetch)
# =============================================================================


class TestInvestmentBankScraperScrape:
    """Tests for the scrape() method with mocked fetch."""

    @pytest.mark.asyncio
    async def test_正常系_GoldmanSachsのscrapeが成功してScrapingResultを返す(
        self,
    ) -> None:
        scraper = GoldmanSachsScraper()

        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            return_value=GOLDMAN_SAMPLE_HTML,
        ):
            result = await scraper.scrape()
            assert isinstance(result, ScrapingResult)
            assert result.success is True
            assert result.source == "Goldman Sachs"
            assert len(result.reports) == 2

    @pytest.mark.asyncio
    async def test_正常系_MorganStanleyのscrapeが成功する(self) -> None:
        scraper = MorganStanleyScraper()

        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            return_value=MORGAN_STANLEY_SAMPLE_HTML,
        ):
            result = await scraper.scrape()
            assert result.success is True
            assert result.source == "Morgan Stanley"
            assert len(result.reports) == 2

    @pytest.mark.asyncio
    async def test_正常系_JPMorganのscrapeが成功する(self) -> None:
        scraper = JPMorganScraper()

        with patch.object(
            scraper,
            "_fetch_html_with_retry",
            new_callable=AsyncMock,
            return_value=JPMORGAN_SAMPLE_HTML,
        ):
            result = await scraper.scrape()
            assert result.success is True
            assert result.source == "JP Morgan"
            assert len(result.reports) == 2

    @pytest.mark.asyncio
    async def test_異常系_fetch失敗時にエラー結果を返す(self) -> None:
        scraper = GoldmanSachsScraper()

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


class TestInvestmentBankScraperSaveReports:
    """Tests for the save_reports() method."""

    @pytest.mark.asyncio
    async def test_正常系_レポートがJSONファイルに保存される(
        self, tmp_path: Path
    ) -> None:
        scraper = GoldmanSachsScraper(output_dir=tmp_path / "goldman")
        reports = [
            IndustryReport(
                source="Goldman Sachs",
                title="Test Report",
                url="https://goldmansachs.com/test",
                published_at=datetime(2026, 1, 18, tzinfo=timezone.utc),
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
        assert data["source"] == "Goldman Sachs"
        assert data["url"] == "https://goldmansachs.com/test"

    @pytest.mark.asyncio
    async def test_エッジケース_空リストで何も保存しない(self, tmp_path: Path) -> None:
        scraper = GoldmanSachsScraper(output_dir=tmp_path / "goldman")
        saved_paths = await scraper.save_reports([])
        assert saved_paths == []


# =============================================================================
# Test Body Extraction
# =============================================================================


class TestInvestmentBankScraperExtractBody:
    """Tests for body text extraction with trafilatura."""

    @pytest.mark.asyncio
    async def test_正常系_trafilaturaで本文を抽出できる(self) -> None:
        scraper = GoldmanSachsScraper()

        with patch(
            "market.industry.scrapers.investment_bank._extract_body_text",
            new_callable=AsyncMock,
            return_value="This is the full article body text with enough content.",
        ):
            body = await scraper.extract_body("https://goldmansachs.com/test-article")
            assert body is not None
            assert len(body) > 0

    @pytest.mark.asyncio
    async def test_異常系_抽出失敗でNone(self) -> None:
        scraper = GoldmanSachsScraper()

        with patch(
            "market.industry.scrapers.investment_bank._extract_body_text",
            new_callable=AsyncMock,
            return_value=None,
        ):
            body = await scraper.extract_body("https://goldmansachs.com/test-article")
            assert body is None


# =============================================================================
# Test Robots.txt Compliance
# =============================================================================


class TestRobotsTxtCompliance:
    """Tests for robots.txt compliance functionality."""

    def test_正常系_GoldmanSachsのrobots_txt_urlが正しい(self) -> None:
        scraper = GoldmanSachsScraper()
        assert hasattr(scraper, "robots_txt_url")
        assert "goldmansachs.com/robots.txt" in scraper.robots_txt_url

    def test_正常系_MorganStanleyのrobots_txt_urlが正しい(self) -> None:
        scraper = MorganStanleyScraper()
        assert "morganstanley.com/robots.txt" in scraper.robots_txt_url

    def test_正常系_JPMorganのrobots_txt_urlが正しい(self) -> None:
        scraper = JPMorganScraper()
        assert "jpmorgan.com/robots.txt" in scraper.robots_txt_url

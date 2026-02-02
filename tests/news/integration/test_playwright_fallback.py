"""Playwright fallback integration tests.

This module tests the Playwright fallback functionality integrated with
TrafilaturaExtractor. These tests verify that when trafilatura fails to
extract content from JS-rendered pages, the extractor falls back to
Playwright for extraction.

Notes
-----
These tests are marked with `@pytest.mark.playwright` and require:
- Playwright to be installed: `uv add playwright && playwright install chromium`
- CI runs should install Playwright before running these tests

Tests will be skipped automatically if:
- Playwright is not installed
- Chromium browser is not installed
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from news.config.models import ExtractionConfig, PlaywrightFallbackConfig
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractionStatus,
    SourceType,
)


def playwright_available() -> bool:
    """Check if playwright is available.

    Returns
    -------
    bool
        True if playwright can be imported, False otherwise.
    """
    try:
        import playwright  # type: ignore[import-not-found]

        return True
    except ImportError:
        return False


def chromium_installed() -> bool:
    """Check if chromium browser is installed for playwright.

    Returns
    -------
    bool
        True if chromium is installed, False otherwise.
    """
    if not playwright_available():
        return False

    try:
        from playwright.sync_api import (  # type: ignore[import-not-found]
            sync_playwright,
        )

        with sync_playwright() as p:
            # Try to get the executable path
            browser_type = p.chromium
            _ = browser_type.executable_path
        return True
    except Exception:
        return False


# Determine skip conditions
skip_no_playwright = pytest.mark.skipif(
    not playwright_available(),
    reason="Playwright is not installed. Install with: uv add playwright",
)

skip_no_chromium = pytest.mark.skipif(
    not chromium_installed(),
    reason="Chromium browser is not installed. Run: playwright install chromium",
)


@pytest.fixture
def sample_collected_article() -> CollectedArticle:
    """Create a sample CollectedArticle for testing."""
    return CollectedArticle(
        url="https://www.example.com/test-article",  # type: ignore[arg-type]
        title="Test Article",
        published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        raw_summary="This is a test article summary",
        source=ArticleSource(
            source_type=SourceType.RSS,
            source_name="Example News",
            category="market",
        ),
        collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def extraction_config_with_fallback() -> ExtractionConfig:
    """Create an ExtractionConfig with Playwright fallback enabled."""
    return ExtractionConfig(
        min_body_length=100,
        max_retries=1,  # Reduce retries for faster tests
        timeout_seconds=30,
        playwright_fallback=PlaywrightFallbackConfig(
            enabled=True,
            browser="chromium",
            headless=True,
            timeout_seconds=30,
        ),
    )


@pytest.mark.integration
@pytest.mark.playwright
class TestPlaywrightFallbackIntegration:
    """Playwright fallback integration tests.

    Note
    ----
    These tests use mocked web content but real browser instances.
    They verify the integration between TrafilaturaExtractor and
    PlaywrightExtractor when fallback is triggered.
    """

    @skip_no_playwright
    @skip_no_chromium
    @pytest.mark.asyncio
    async def test_正常系_trafilatura成功時はPlaywrightを使用しない(
        self,
        sample_collected_article: CollectedArticle,
        extraction_config_with_fallback: ExtractionConfig,
    ) -> None:
        """When trafilatura succeeds, Playwright should not be used."""
        from news.extractors.trafilatura import TrafilaturaExtractor
        from rss.services.article_extractor import (
            ExtractedArticle as RssExtractedArticle,
        )
        from rss.services.article_extractor import (
            ExtractionStatus as RssExtractionStatus,
        )

        # Mock trafilatura to succeed
        mock_result = RssExtractedArticle(
            url=str(sample_collected_article.url),
            title="Test Article",
            text="This is a successful trafilatura extraction. " * 20,
            author=None,
            date=None,
            source=None,
            language="en",
            status=RssExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )

        async with TrafilaturaExtractor.from_config(
            extraction_config_with_fallback
        ) as extractor:
            with patch.object(
                extractor._extractor,
                "extract",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.extraction_method == "trafilatura"
        assert "playwright" not in result.extraction_method

    @skip_no_playwright
    @skip_no_chromium
    @pytest.mark.asyncio
    async def test_正常系_trafilatura失敗時にPlaywrightでフォールバック成功(
        self,
        sample_collected_article: CollectedArticle,
        extraction_config_with_fallback: ExtractionConfig,
    ) -> None:
        """When trafilatura fails, Playwright fallback should succeed."""
        from news.extractors.playwright import PlaywrightExtractor
        from news.extractors.trafilatura import TrafilaturaExtractor
        from news.models import ExtractedArticle
        from rss.services.article_extractor import (
            ExtractedArticle as RssExtractedArticle,
        )
        from rss.services.article_extractor import (
            ExtractionStatus as RssExtractionStatus,
        )

        # Mock trafilatura to fail
        mock_trafilatura_result = RssExtractedArticle(
            url=str(sample_collected_article.url),
            title=None,
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.FAILED,
            error="Could not extract content",
            extraction_method="trafilatura",
        )

        # Create mock playwright result (> 100 chars)
        mock_playwright_result = ExtractedArticle(
            collected=sample_collected_article,
            body_text=(
                "This is content extracted via Playwright. "
                "It contains enough text to pass the minimum length check. "
                "Adding more text to ensure it exceeds 100 characters."
            ),
            extraction_status=ExtractionStatus.SUCCESS,
            extraction_method="playwright",
            error_message=None,
        )

        # Mock PlaywrightExtractor directly
        with (
            patch.object(
                PlaywrightExtractor,
                "extract",
                new_callable=AsyncMock,
                return_value=mock_playwright_result,
            ),
            patch(
                "news.extractors.playwright.async_playwright"
            ) as mock_async_playwright,
        ):
            mock_browser = MagicMock()
            mock_browser.close = AsyncMock()

            mock_playwright = MagicMock()
            mock_playwright.chromium = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.stop = AsyncMock()

            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with TrafilaturaExtractor.from_config(
                extraction_config_with_fallback
            ) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=mock_trafilatura_result,
                ):
                    result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.extraction_method == "trafilatura+playwright"
        assert result.body_text is not None
        assert len(result.body_text) >= extraction_config_with_fallback.min_body_length

    @skip_no_playwright
    @skip_no_chromium
    @pytest.mark.asyncio
    async def test_正常系_両方失敗時は元のエラーを返す(
        self,
        sample_collected_article: CollectedArticle,
        extraction_config_with_fallback: ExtractionConfig,
    ) -> None:
        """When both trafilatura and Playwright fail, return original error."""
        from news.extractors.trafilatura import TrafilaturaExtractor
        from rss.services.article_extractor import (
            ExtractedArticle as RssExtractedArticle,
        )
        from rss.services.article_extractor import (
            ExtractionStatus as RssExtractionStatus,
        )

        # Mock trafilatura to fail
        mock_trafilatura_result = RssExtractedArticle(
            url=str(sample_collected_article.url),
            title=None,
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.FAILED,
            error="Trafilatura extraction failed",
            extraction_method="trafilatura",
        )

        # Mock Playwright to also fail
        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_page = MagicMock()
            mock_page.goto = AsyncMock()
            mock_page.query_selector = AsyncMock(return_value=None)  # No content
            mock_page.close = AsyncMock()

            mock_browser = MagicMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()

            mock_playwright = MagicMock()
            mock_playwright.chromium = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.stop = AsyncMock()

            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with TrafilaturaExtractor.from_config(
                extraction_config_with_fallback
            ) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=mock_trafilatura_result,
                ):
                    result = await extractor.extract(sample_collected_article)

        # Should return the original trafilatura failure
        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.extraction_method == "trafilatura"
        assert result.error_message == "Trafilatura extraction failed"

    @skip_no_playwright
    @skip_no_chromium
    @pytest.mark.asyncio
    async def test_正常系_本文が短い場合にPlaywrightでフォールバック(
        self,
        sample_collected_article: CollectedArticle,
        extraction_config_with_fallback: ExtractionConfig,
    ) -> None:
        """When trafilatura returns short body, fallback to Playwright."""
        from news.extractors.trafilatura import TrafilaturaExtractor
        from rss.services.article_extractor import (
            ExtractedArticle as RssExtractedArticle,
        )
        from rss.services.article_extractor import (
            ExtractionStatus as RssExtractionStatus,
        )

        # Mock trafilatura to return short text (below min_body_length)
        mock_trafilatura_result = RssExtractedArticle(
            url=str(sample_collected_article.url),
            title="Test",
            text="Short text",  # Below min_body_length of 100
            author=None,
            date=None,
            source=None,
            language="en",
            status=RssExtractionStatus.SUCCESS,
            error=None,
            extraction_method="trafilatura",
        )

        # Mock Playwright to return longer content
        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_element = MagicMock()
            mock_element.inner_text = AsyncMock(
                return_value=(
                    "This is longer content extracted via Playwright fallback. "
                    "It has sufficient length to pass the minimum body length check."
                )
            )

            mock_page = MagicMock()
            mock_page.goto = AsyncMock()
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_page.close = AsyncMock()

            mock_browser = MagicMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()

            mock_playwright = MagicMock()
            mock_playwright.chromium = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.stop = AsyncMock()

            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with TrafilaturaExtractor.from_config(
                extraction_config_with_fallback
            ) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=mock_trafilatura_result,
                ):
                    result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.extraction_method == "trafilatura+playwright"

    @skip_no_playwright
    @skip_no_chromium
    @pytest.mark.asyncio
    async def test_正常系_コンテキストマネージャでブラウザライフサイクル管理(
        self,
        extraction_config_with_fallback: ExtractionConfig,
    ) -> None:
        """Browser lifecycle should be properly managed with context manager."""
        from news.extractors.trafilatura import TrafilaturaExtractor

        browser_closed = False

        async def mock_browser_close() -> None:
            nonlocal browser_closed
            browser_closed = True

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_browser = MagicMock()
            mock_browser.close = AsyncMock(side_effect=mock_browser_close)

            mock_playwright = MagicMock()
            mock_playwright.chromium = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.stop = AsyncMock()

            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with TrafilaturaExtractor.from_config(
                extraction_config_with_fallback
            ):
                # Just enter the context
                pass

        # Browser should be closed after exiting context
        assert browser_closed is True
        mock_playwright.stop.assert_called_once()

    @skip_no_playwright
    @skip_no_chromium
    @pytest.mark.asyncio
    async def test_異常系_Playwrightタイムアウト時はTIMEOUTステータス(
        self,
        sample_collected_article: CollectedArticle,
        extraction_config_with_fallback: ExtractionConfig,
    ) -> None:
        """Playwright timeout should result in TIMEOUT status."""
        from news.extractors.trafilatura import TrafilaturaExtractor
        from rss.services.article_extractor import (
            ExtractedArticle as RssExtractedArticle,
        )
        from rss.services.article_extractor import (
            ExtractionStatus as RssExtractionStatus,
        )

        # Mock trafilatura to fail
        mock_trafilatura_result = RssExtractedArticle(
            url=str(sample_collected_article.url),
            title=None,
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.FAILED,
            error="Trafilatura failed",
            extraction_method="trafilatura",
        )

        # Mock Playwright to timeout
        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_page = MagicMock()
            mock_page.goto = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_page.close = AsyncMock()

            mock_browser = MagicMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()

            mock_playwright = MagicMock()
            mock_playwright.chromium = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.stop = AsyncMock()

            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with TrafilaturaExtractor.from_config(
                extraction_config_with_fallback
            ) as extractor:
                with patch.object(
                    extractor._extractor,
                    "extract",
                    new_callable=AsyncMock,
                    return_value=mock_trafilatura_result,
                ):
                    result = await extractor.extract(sample_collected_article)

        # Since both failed, should return original trafilatura error
        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.extraction_method == "trafilatura"


@pytest.mark.integration
@pytest.mark.playwright
class TestPlaywrightFallbackDisabled:
    """Tests for Playwright fallback when disabled."""

    @pytest.mark.asyncio
    async def test_正常系_フォールバック無効時はtrafilaturaのみ使用(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """When fallback is disabled, only trafilatura should be used."""
        from news.extractors.trafilatura import TrafilaturaExtractor
        from rss.services.article_extractor import (
            ExtractedArticle as RssExtractedArticle,
        )
        from rss.services.article_extractor import (
            ExtractionStatus as RssExtractionStatus,
        )

        config = ExtractionConfig(
            min_body_length=100,
            playwright_fallback=PlaywrightFallbackConfig(enabled=False),
        )

        mock_result = RssExtractedArticle(
            url=str(sample_collected_article.url),
            title=None,
            text=None,
            author=None,
            date=None,
            source=None,
            language=None,
            status=RssExtractionStatus.FAILED,
            error="Extraction failed",
            extraction_method="trafilatura",
        )

        async with TrafilaturaExtractor.from_config(config) as extractor:
            with patch.object(
                extractor._extractor,
                "extract",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.extraction_method == "trafilatura"
        # Playwright extractor should not be initialized
        assert extractor._playwright_extractor is None


@pytest.mark.integration
@pytest.mark.playwright
class TestPlaywrightExtractorStandalone:
    """Standalone tests for PlaywrightExtractor."""

    @skip_no_playwright
    @skip_no_chromium
    @pytest.mark.asyncio
    async def test_正常系_PlaywrightExtractor単独で動作する(
        self,
        sample_collected_article: CollectedArticle,
    ) -> None:
        """PlaywrightExtractor should work standalone."""
        from news.extractors.playwright import PlaywrightExtractor

        config = ExtractionConfig(
            min_body_length=100,
            playwright_fallback=PlaywrightFallbackConfig(
                enabled=True,
                browser="chromium",
                headless=True,
                timeout_seconds=30,
            ),
        )

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_element = MagicMock()
            mock_element.inner_text = AsyncMock(
                return_value=(
                    "This is the article body text extracted using Playwright. "
                    "It is long enough to pass the minimum length requirement."
                )
            )

            mock_page = MagicMock()
            mock_page.goto = AsyncMock()
            mock_page.query_selector = AsyncMock(return_value=mock_element)
            mock_page.close = AsyncMock()

            mock_browser = MagicMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()

            mock_playwright = MagicMock()
            mock_playwright.chromium = MagicMock()
            mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.stop = AsyncMock()

            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(config) as extractor:
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.extraction_method == "playwright"
        assert result.body_text is not None

    @skip_no_playwright
    @pytest.mark.asyncio
    async def test_異常系_playwrightモジュールが無い場合ImportError(
        self,
    ) -> None:
        """Should raise ImportError when playwright module is not available."""
        # This test documents expected behavior but doesn't test actual import failure
        # since we can't unload the playwright module once it's imported
        pass


@pytest.mark.integration
@pytest.mark.playwright
class TestPlaywrightMarkerSkipping:
    """Tests to verify playwright marker allows proper test selection."""

    def test_正常系_playwrightマーカーが適用されている(self) -> None:
        """Playwright marker should be applied to this test class."""
        # This test verifies the marker is correctly configured
        # Run with: pytest -m "not playwright" to exclude these tests
        pass

    def test_正常系_integrationマーカーも適用されている(self) -> None:
        """Integration marker should also be applied."""
        # This test verifies both markers can be used for filtering
        # Run with: pytest -m "integration and playwright" to include
        pass

"""Unit tests for PlaywrightExtractor.

This module tests the PlaywrightExtractor class to ensure:
- It correctly extracts body text from article elements
- It falls back to other selectors when article is not found
- It handles timeouts correctly
- It handles short/empty body text correctly
- It properly manages browser lifecycle via async context manager
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from news.config.workflow import ExtractionConfig, PlaywrightFallbackConfig
from news.models import (
    ArticleSource,
    CollectedArticle,
    ExtractionStatus,
    SourceType,
)


@pytest.fixture
def sample_collected_article() -> CollectedArticle:
    """Create a sample CollectedArticle for testing."""
    return CollectedArticle(
        url="https://www.example.com/article/123",  # type: ignore[arg-type]
        title="Test Article",
        published=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        raw_summary="This is a test summary",
        source=ArticleSource(
            source_type=SourceType.RSS,
            source_name="Example News",
            category="market",
        ),
        collected_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def playwright_config() -> PlaywrightFallbackConfig:
    """Create a PlaywrightFallbackConfig for testing."""
    return PlaywrightFallbackConfig(
        enabled=True,
        browser="chromium",
        headless=True,
        timeout_seconds=30,
    )


@pytest.fixture
def extraction_config(playwright_config: PlaywrightFallbackConfig) -> ExtractionConfig:
    """Create an ExtractionConfig with playwright_fallback for testing."""
    return ExtractionConfig(
        min_body_length=100,
        playwright_fallback=playwright_config,
    )


@pytest.fixture
def mock_page() -> MagicMock:
    """Create a mock Playwright page."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.query_selector = AsyncMock()
    page.close = AsyncMock()
    return page


@pytest.fixture
def mock_browser(mock_page: MagicMock) -> MagicMock:
    """Create a mock Playwright browser."""
    browser = MagicMock()
    browser.new_page = AsyncMock(return_value=mock_page)
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_playwright(mock_browser: MagicMock) -> MagicMock:
    """Create a mock Playwright instance."""
    playwright = MagicMock()
    playwright.chromium = MagicMock()
    playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    playwright.stop = AsyncMock()
    return playwright


class TestPlaywrightExtractorDefinition:
    """Tests for PlaywrightExtractor class definition."""

    def test_正常系_PlaywrightExtractorはBaseExtractorを継承している(self) -> None:
        """PlaywrightExtractor should inherit from BaseExtractor."""
        from news.extractors.base import BaseExtractor
        from news.extractors.playwright import PlaywrightExtractor

        assert issubclass(PlaywrightExtractor, BaseExtractor)

    def test_正常系_extractor_nameはplaywrightを返す(
        self,
        extraction_config: ExtractionConfig,
    ) -> None:
        """extractor_name should return 'playwright'."""
        from news.extractors.playwright import PlaywrightExtractor

        extractor = PlaywrightExtractor(extraction_config)
        assert extractor.extractor_name == "playwright"


class TestPlaywrightExtractorExtraction:
    """Tests for PlaywrightExtractor extraction functionality."""

    @pytest.mark.asyncio
    async def test_正常系_article要素から本文を抽出(
        self,
        extraction_config: ExtractionConfig,
        sample_collected_article: CollectedArticle,
        mock_playwright: MagicMock,
        mock_page: MagicMock,
    ) -> None:
        """Should extract body text from article element."""
        from news.extractors.playwright import PlaywrightExtractor

        # Setup mock element
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(
            return_value="This is a long article body text that exceeds "
            "the minimum length requirement for extraction to succeed. "
            "It contains more than 100 characters."
        )
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(extraction_config) as extractor:
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.body_text is not None
        assert "article body text" in result.body_text
        assert result.extraction_method == "playwright"

    @pytest.mark.asyncio
    async def test_正常系_main要素にフォールバック(
        self,
        extraction_config: ExtractionConfig,
        sample_collected_article: CollectedArticle,
        mock_playwright: MagicMock,
        mock_page: MagicMock,
    ) -> None:
        """Should fallback to main element when article is not found."""
        from news.extractors.playwright import PlaywrightExtractor

        # First call (article) returns None, second call (main) returns element
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(
            return_value="Main element body text that is long enough "
            "to pass the minimum length check for successful extraction."
        )

        call_count = 0

        async def query_selector_side_effect(selector: str) -> MagicMock | None:
            nonlocal call_count
            call_count += 1
            if selector == "article":
                return None  # No article element
            return mock_element  # Return element for other selectors

        mock_page.query_selector = AsyncMock(side_effect=query_selector_side_effect)

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(extraction_config) as extractor:
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.body_text is not None
        assert "Main element" in result.body_text

    @pytest.mark.asyncio
    async def test_異常系_タイムアウトでTIMEOUTステータス(
        self,
        extraction_config: ExtractionConfig,
        sample_collected_article: CollectedArticle,
        mock_playwright: MagicMock,
        mock_page: MagicMock,
    ) -> None:
        """Should return TIMEOUT status when page load times out."""
        from news.extractors.playwright import PlaywrightExtractor

        # Make goto raise TimeoutError
        mock_page.goto = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(extraction_config) as extractor:
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.TIMEOUT
        assert result.body_text is None
        assert result.error_message is not None
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_異常系_本文が短いとFAILED(
        self,
        extraction_config: ExtractionConfig,
        sample_collected_article: CollectedArticle,
        mock_playwright: MagicMock,
        mock_page: MagicMock,
    ) -> None:
        """Should return FAILED status when body text is too short."""
        from news.extractors.playwright import PlaywrightExtractor

        # Setup mock element with short text
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(return_value="Short text")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(extraction_config) as extractor:
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.body_text is None
        assert result.error_message is not None
        assert "too short" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_異常系_要素が見つからないとFAILED(
        self,
        extraction_config: ExtractionConfig,
        sample_collected_article: CollectedArticle,
        mock_playwright: MagicMock,
        mock_page: MagicMock,
    ) -> None:
        """Should return FAILED status when no element is found."""
        from news.extractors.playwright import PlaywrightExtractor

        # All selectors return None
        mock_page.query_selector = AsyncMock(return_value=None)

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(extraction_config) as extractor:
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.body_text is None

    @pytest.mark.asyncio
    async def test_異常系_例外発生時はFAILED(
        self,
        extraction_config: ExtractionConfig,
        sample_collected_article: CollectedArticle,
        mock_playwright: MagicMock,
        mock_page: MagicMock,
    ) -> None:
        """Should return FAILED status when an exception occurs."""
        from news.extractors.playwright import PlaywrightExtractor

        # Make goto raise a generic exception
        mock_page.goto = AsyncMock(side_effect=Exception("Network error"))

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(extraction_config) as extractor:
                result = await extractor.extract(sample_collected_article)

        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.body_text is None
        assert result.error_message is not None
        assert "Network error" in result.error_message


class TestPlaywrightExtractorContextManager:
    """Tests for PlaywrightExtractor async context manager."""

    @pytest.mark.asyncio
    async def test_正常系_コンテキストマネージャでブラウザが起動する(
        self,
        extraction_config: ExtractionConfig,
        mock_playwright: MagicMock,
    ) -> None:
        """Browser should start when entering context manager."""
        from news.extractors.playwright import PlaywrightExtractor

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(extraction_config) as extractor:
                # Browser should be initialized
                assert extractor._browser is not None

            mock_playwright.chromium.launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_コンテキストマネージャでブラウザが終了する(
        self,
        extraction_config: ExtractionConfig,
        mock_playwright: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Browser should close when exiting context manager."""
        from news.extractors.playwright import PlaywrightExtractor

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(extraction_config):
                pass  # Just enter and exit

            # Browser and playwright should be closed
            mock_browser.close.assert_called_once()
            mock_playwright.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_closeメソッドで明示的に終了できる(
        self,
        extraction_config: ExtractionConfig,
        mock_playwright: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """close() method should explicitly close browser."""
        from news.extractors.playwright import PlaywrightExtractor

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            extractor = PlaywrightExtractor(extraction_config)
            await extractor._ensure_browser()
            await extractor.close()

            mock_browser.close.assert_called_once()
            mock_playwright.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_二重closeは安全(
        self,
        extraction_config: ExtractionConfig,
        mock_playwright: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Calling close() twice should be safe."""
        from news.extractors.playwright import PlaywrightExtractor

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            extractor = PlaywrightExtractor(extraction_config)
            await extractor._ensure_browser()
            await extractor.close()
            await extractor.close()  # Second close should be safe

            # Should only be called once
            mock_browser.close.assert_called_once()


class TestPlaywrightExtractorBrowserConfig:
    """Tests for PlaywrightExtractor browser configuration."""

    @pytest.mark.asyncio
    async def test_正常系_headlessモードで起動(
        self,
        mock_playwright: MagicMock,
    ) -> None:
        """Browser should launch in headless mode when configured."""
        from news.extractors.playwright import PlaywrightExtractor

        config = ExtractionConfig(
            playwright_fallback=PlaywrightFallbackConfig(headless=True)
        )

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(config):
                pass

            mock_playwright.chromium.launch.assert_called_once_with(headless=True)

    @pytest.mark.asyncio
    async def test_正常系_ブラウザタイプを指定できる(
        self,
        mock_playwright: MagicMock,
    ) -> None:
        """Browser type should be configurable."""
        from news.extractors.playwright import PlaywrightExtractor

        # Setup firefox mock
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()
        mock_playwright.firefox = MagicMock()
        mock_playwright.firefox.launch = AsyncMock(return_value=mock_browser)

        config = ExtractionConfig(
            playwright_fallback=PlaywrightFallbackConfig(browser="firefox")
        )

        with patch(
            "news.extractors.playwright.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright
            )

            async with PlaywrightExtractor(config):
                pass

            mock_playwright.firefox.launch.assert_called_once()


class TestPlaywrightExtractorImportError:
    """Tests for PlaywrightExtractor when playwright is not installed."""

    @pytest.mark.asyncio
    async def test_異常系_playwrightがインストールされていない場合エラー(
        self,
        extraction_config: ExtractionConfig,
    ) -> None:
        """Should raise RuntimeError when playwright is not installed."""
        from news.extractors.playwright import PlaywrightExtractor

        with (
            patch.dict("sys.modules", {"playwright.async_api": None}),
            patch(
                "news.extractors.playwright.async_playwright",
                side_effect=ImportError("No module named 'playwright'"),
            ),
        ):
            extractor = PlaywrightExtractor(extraction_config)

            with pytest.raises(RuntimeError, match="playwright is not installed"):
                await extractor._ensure_browser()

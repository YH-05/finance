"""Unit tests for market.industry.scrapers.base module.

Tests cover BaseScraper abstract interface, configuration handling,
2-layer fallback logic (curl_cffi -> Playwright), retry behaviour,
and resource management (context manager protocol).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from market.industry.scrapers.base import BaseScraper
from market.industry.types import (
    IndustryReport,
    RetryConfig,
    ScrapingConfig,
    ScrapingResult,
)


class ConcreteScraper(BaseScraper):
    """Concrete implementation of BaseScraper for testing."""

    def __init__(
        self,
        config: ScrapingConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        super().__init__(
            source_name="TestSource",
            base_url="https://test.example.com",
            config=config,
            retry_config=retry_config,
        )

    async def scrape(self) -> ScrapingResult:
        """Implement abstract scrape method."""
        return ScrapingResult(
            success=True,
            source=self.source_name,
            url=self.base_url,
            reports=[],
        )

    async def parse_html(self, html: str) -> list[IndustryReport]:
        """Implement abstract parse_html method."""
        return []


class TestBaseScraperInit:
    """Tests for BaseScraper initialization."""

    def test_正常系_デフォルト設定で初期化できる(self) -> None:
        scraper = ConcreteScraper()
        assert scraper.source_name == "TestSource"
        assert scraper.base_url == "https://test.example.com"
        assert scraper.config.polite_delay == 2.0
        assert scraper.retry_config.max_attempts == 3

    def test_正常系_カスタム設定で初期化できる(self) -> None:
        config = ScrapingConfig(polite_delay=5.0, timeout=60.0)
        retry = RetryConfig(max_attempts=5)
        scraper = ConcreteScraper(config=config, retry_config=retry)
        assert scraper.config.polite_delay == 5.0
        assert scraper.config.timeout == 60.0
        assert scraper.retry_config.max_attempts == 5


class TestBaseScraperAbstract:
    """Tests for BaseScraper abstract methods."""

    def test_異常系_抽象メソッド未実装でTypeError(self) -> None:
        with pytest.raises(TypeError):
            BaseScraper(  # type: ignore[abstract]
                source_name="Test",
                base_url="https://test.com",
            )


class TestBaseScraperFetchHtml:
    """Tests for BaseScraper._fetch_html with 2-layer fallback."""

    @pytest.mark.asyncio
    async def test_正常系_curl_cffiで成功する場合(self) -> None:
        scraper = ConcreteScraper()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"

        with patch.object(
            scraper, "_fetch_with_session", new_callable=AsyncMock
        ) as mock_session:
            mock_session.return_value = "<html><body>Test</body></html>"
            html = await scraper._fetch_html("https://test.example.com/page")
            assert html == "<html><body>Test</body></html>"
            mock_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_curl_cffi失敗時にPlaywrightにフォールバック(self) -> None:
        scraper = ConcreteScraper()

        with (
            patch.object(
                scraper,
                "_fetch_with_session",
                new_callable=AsyncMock,
                side_effect=Exception("curl_cffi failed"),
            ),
            patch.object(
                scraper,
                "_fetch_with_browser",
                new_callable=AsyncMock,
                return_value="<html>Browser content</html>",
            ) as mock_browser,
        ):
            html = await scraper._fetch_html("https://test.example.com/page")
            assert html == "<html>Browser content</html>"
            mock_browser.assert_called_once()

    @pytest.mark.asyncio
    async def test_異常系_両方失敗時にScrapingResultでエラー返却(self) -> None:
        scraper = ConcreteScraper()

        with (
            patch.object(
                scraper,
                "_fetch_with_session",
                new_callable=AsyncMock,
                side_effect=Exception("curl_cffi failed"),
            ),
            patch.object(
                scraper,
                "_fetch_with_browser",
                new_callable=AsyncMock,
                side_effect=Exception("Playwright failed"),
            ),
            pytest.raises(Exception, match="Playwright failed"),
        ):
            await scraper._fetch_html("https://test.example.com/page")


class TestBaseScraperContextManager:
    """Tests for BaseScraper async context manager protocol."""

    @pytest.mark.asyncio
    async def test_正常系_asyncコンテキストマネージャで使用できる(self) -> None:
        scraper = ConcreteScraper()
        with (
            patch.object(scraper, "close", new_callable=AsyncMock) as mock_close,
        ):
            async with scraper as s:
                assert s is scraper
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_closeで全リソースが解放される(self) -> None:
        scraper = ConcreteScraper()
        # Simulate having resources open
        mock_session = MagicMock()
        mock_session.close = MagicMock()
        scraper._session = mock_session
        scraper._browser = None
        scraper._playwright = None
        await scraper.close()
        mock_session.close.assert_called_once()
        assert scraper._session is None


class TestBaseScraperFetchWithRetry:
    """Tests for BaseScraper._fetch_html_with_retry."""

    @pytest.mark.asyncio
    async def test_正常系_最初の試行で成功(self) -> None:
        scraper = ConcreteScraper()
        with patch.object(
            scraper,
            "_fetch_html",
            new_callable=AsyncMock,
            return_value="<html>OK</html>",
        ):
            html = await scraper._fetch_html_with_retry("https://test.com/page")
            assert html == "<html>OK</html>"

    @pytest.mark.asyncio
    async def test_正常系_リトライ後に成功(self) -> None:
        scraper = ConcreteScraper(
            retry_config=RetryConfig(max_attempts=3, initial_delay=0.01),
        )
        call_count = 0

        async def _fetch_side_effect(url: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "<html>Recovered</html>"

        with patch.object(
            scraper,
            "_fetch_html",
            new_callable=AsyncMock,
            side_effect=_fetch_side_effect,
        ):
            html = await scraper._fetch_html_with_retry("https://test.com/page")
            assert html == "<html>Recovered</html>"
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_異常系_全リトライ失敗で例外(self) -> None:
        scraper = ConcreteScraper(
            retry_config=RetryConfig(max_attempts=2, initial_delay=0.01),
        )
        with (
            patch.object(
                scraper,
                "_fetch_html",
                new_callable=AsyncMock,
                side_effect=Exception("Persistent failure"),
            ),
            pytest.raises(Exception, match="Persistent failure"),
        ):
            await scraper._fetch_html_with_retry("https://test.com/page")

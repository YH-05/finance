"""Playwright-based article extractor for JS-rendered content.

This module provides a PlaywrightExtractor class that uses Playwright
to extract article body text from JavaScript-rendered pages. It is
designed to be used as a fallback when trafilatura fails to extract
content from dynamically rendered pages.

Features
--------
- Async context manager support for proper resource management
- Multiple CSS selector fallback for body text extraction
- Configurable browser type and timeout
- Graceful timeout and error handling

Examples
--------
>>> from news.extractors.playwright import PlaywrightExtractor
>>> from news.config.models import ExtractionConfig
>>>
>>> config = ExtractionConfig()
>>> async with PlaywrightExtractor(config) as extractor:
...     result = await extractor.extract(article)
...     if result.extraction_status == ExtractionStatus.SUCCESS:
...         print(result.body_text)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from news.extractors.base import BaseExtractor
from news.models import (
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
)
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from news.config.models import ExtractionConfig

logger = get_logger(__name__, module="extractors.playwright")


def async_playwright() -> Any:
    """Import and return async_playwright from playwright.

    Returns
    -------
    Any
        The async_playwright context manager from playwright.

    Raises
    ------
    ImportError
        If playwright is not installed.
    """
    try:
        from playwright.async_api import async_playwright as _async_playwright

        return _async_playwright()
    except ImportError as e:
        raise ImportError(
            "playwright is not installed. "
            "Install with: uv add playwright && playwright install chromium"
        ) from e


class PlaywrightExtractor(BaseExtractor):
    """Playwrightを使用したJS対応本文抽出。

    JavaScriptで動的にレンダリングされるページからコンテンツを抽出する。
    trafilaturaのフォールバックとして使用。

    Parameters
    ----------
    config : ExtractionConfig
        抽出設定。playwright_fallback設定を含む。

    Notes
    -----
    - ブラウザインスタンスは初回使用時に起動
    - 抽出完了後は `close()` で明示的に終了が必要
    - async context manager として使用することを推奨

    Examples
    --------
    >>> async with PlaywrightExtractor(config) as extractor:
    ...     result = await extractor.extract(article)
    """

    # CSS selectors to try in order of priority
    _selectors: list[str] = [
        "article",
        "main",
        "[role='main']",
        ".article-body",
        ".post-content",
        "#content",
        "body",
    ]

    def __init__(self, config: ExtractionConfig) -> None:
        """Initialize the PlaywrightExtractor.

        Parameters
        ----------
        config : ExtractionConfig
            Extraction configuration containing playwright_fallback settings.
        """
        self._config = config
        self._playwright_config = config.playwright_fallback
        self._browser: Any = None
        self._playwright: Any = None

    @property
    def extractor_name(self) -> str:
        """Return the name of this extractor.

        Returns
        -------
        str
            The string "playwright".

        Examples
        --------
        >>> extractor = PlaywrightExtractor(config)
        >>> extractor.extractor_name
        'playwright'
        """
        return "playwright"

    async def __aenter__(self) -> PlaywrightExtractor:
        """非同期コンテキストマネージャ開始。

        Returns
        -------
        PlaywrightExtractor
            Self for use in async with statement.
        """
        await self._ensure_browser()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """非同期コンテキストマネージャ終了。

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if an exception was raised.
        exc_val : BaseException | None
            Exception value if an exception was raised.
        exc_tb : Any
            Exception traceback if an exception was raised.
        """
        await self.close()

    async def _ensure_browser(self) -> None:
        """ブラウザインスタンスを確保。

        Raises
        ------
        RuntimeError
            If playwright is not installed.
        """
        if self._browser is not None:
            return

        try:
            self._playwright = await async_playwright().start()
        except ImportError as e:
            raise RuntimeError(
                "playwright is not installed. "
                "Install with: uv add playwright && playwright install chromium"
            ) from e

        browser_type = self._playwright_config.browser
        browser_launcher = getattr(self._playwright, browser_type)

        self._browser = await browser_launcher.launch(
            headless=self._playwright_config.headless,
        )

        logger.debug(
            "Playwright browser started",
            browser=browser_type,
            headless=self._playwright_config.headless,
        )

    async def close(self) -> None:
        """ブラウザを終了。

        Safely closes the browser and playwright instances.
        Can be called multiple times safely.
        """
        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.debug("Playwright browser closed")

    async def extract(self, article: CollectedArticle) -> ExtractedArticle:
        """記事本文を抽出。

        Parameters
        ----------
        article : CollectedArticle
            収集済み記事。

        Returns
        -------
        ExtractedArticle
            抽出結果。
        """
        await self._ensure_browser()

        url = str(article.url)
        timeout_ms = self._playwright_config.timeout_seconds * 1000

        try:
            page = await self._browser.new_page()

            try:
                # ページ読み込み
                await page.goto(url, timeout=timeout_ms, wait_until="networkidle")

                # 本文抽出（複数のセレクタを優先度順に探索）
                body_text = await self._extract_body_text(page)

                if not body_text or len(body_text) < self._config.min_body_length:
                    return ExtractedArticle(
                        collected=article,
                        body_text=None,
                        extraction_status=ExtractionStatus.FAILED,
                        extraction_method=self.extractor_name,
                        error_message="Body text too short after JS rendering",
                    )

                return ExtractedArticle(
                    collected=article,
                    body_text=body_text,
                    extraction_status=ExtractionStatus.SUCCESS,
                    extraction_method=self.extractor_name,
                    error_message=None,
                )

            finally:
                await page.close()

        except asyncio.TimeoutError:
            return ExtractedArticle(
                collected=article,
                body_text=None,
                extraction_status=ExtractionStatus.TIMEOUT,
                extraction_method=self.extractor_name,
                error_message=f"Page load timeout: {self._playwright_config.timeout_seconds}s",
            )

        except Exception as e:
            logger.warning(
                "Playwright extraction failed",
                url=url,
                error=str(e),
            )
            return ExtractedArticle(
                collected=article,
                body_text=None,
                extraction_status=ExtractionStatus.FAILED,
                extraction_method=self.extractor_name,
                error_message=str(e),
            )

    async def _extract_body_text(self, page: Any) -> str | None:
        """ページから本文テキストを抽出。

        記事本文のセレクタを優先度順に試行:
        1. article要素
        2. main要素
        3. [role="main"]
        4. .article-body
        5. .post-content
        6. #content
        7. body全体

        Parameters
        ----------
        page : Any
            Playwright page object.

        Returns
        -------
        str | None
            Extracted body text, or None if no suitable content found.
        """
        for selector in self._selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 100:
                        return text.strip()
            except Exception:  # nosec B112
                # Continue to next selector on any error (intentional broad catch)
                continue

        return None


__all__ = ["PlaywrightExtractor"]

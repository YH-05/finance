# P10-011: PlaywrightExtractor基盤クラス

## 概要

Playwrightを使用した本文抽出の基盤クラスを実装する。

## 変更内容

### 新規ファイル

| ファイル | 説明 |
|----------|------|
| `src/news/extractors/playwright.py` | PlaywrightExtractor実装 |

### 実装詳細

```python
# src/news/extractors/playwright.py

"""Playwright-based article extractor for JS-rendered content."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from news.extractors.base import BaseExtractor
from news.models import (
    CollectedArticle,
    ExtractedArticle,
    ExtractionStatus,
)
from news.utils.logging_config import get_logger

if TYPE_CHECKING:
    from news.config.workflow import NewsWorkflowConfig

logger = get_logger(__name__, module="extractors.playwright")


class PlaywrightExtractor(BaseExtractor):
    """Playwrightを使用したJS対応本文抽出。

    JavaScriptで動的にレンダリングされるページからコンテンツを抽出する。
    trafilaturaのフォールバックとして使用。

    Parameters
    ----------
    config : NewsWorkflowConfig
        ワークフロー設定。

    Notes
    -----
    - ブラウザインスタンスは初回使用時に起動
    - 抽出完了後は `close()` で明示的に終了が必要

    Examples
    --------
    >>> async with PlaywrightExtractor(config) as extractor:
    ...     result = await extractor.extract(article)
    """

    def __init__(self, config: NewsWorkflowConfig) -> None:
        self._config = config
        self._playwright_config = config.extraction.playwright_fallback
        self._browser = None
        self._playwright = None

    @property
    def extractor_name(self) -> str:
        return "playwright"

    async def __aenter__(self) -> PlaywrightExtractor:
        """非同期コンテキストマネージャ開始。"""
        await self._ensure_browser()
        return self

    async def __aexit__(self, *args) -> None:
        """非同期コンテキストマネージャ終了。"""
        await self.close()

    async def _ensure_browser(self) -> None:
        """ブラウザインスタンスを確保。"""
        if self._browser is not None:
            return

        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise RuntimeError(
                "playwright is not installed. "
                "Install with: uv add playwright && playwright install chromium"
            ) from e

        self._playwright = await async_playwright().start()

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
        """ブラウザを終了。"""
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

                # 本文抽出（article, main, bodyの順で探索）
                body_text = await self._extract_body_text(page)

                if not body_text or len(body_text) < self._config.extraction.min_body_length:
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

    async def _extract_body_text(self, page) -> str | None:
        """ページから本文テキストを抽出。

        記事本文のセレクタを優先度順に試行:
        1. article要素
        2. main要素
        3. [role="main"]
        4. body全体
        """
        selectors = [
            "article",
            "main",
            "[role='main']",
            ".article-body",
            ".post-content",
            "#content",
            "body",
        ]

        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 100:
                        return text.strip()
            except Exception:
                continue

        return None
```

## 受け入れ条件

- [ ] `PlaywrightExtractor` クラスが実装される
- [ ] 非同期コンテキストマネージャ（`async with`）をサポート
- [ ] 複数のCSSセレクタで本文探索
- [ ] タイムアウト処理が正しく動作
- [ ] 単体テストが通る

## テストケース

```python
class TestPlaywrightExtractor:
    @pytest.mark.asyncio
    async def test_extracts_body_from_article_tag(self, extractor, mock_page):
        """article要素から本文を抽出する。"""
        mock_page.query_selector.return_value.inner_text.return_value = "Article body..."

        result = await extractor.extract(article)

        assert result.extraction_status == ExtractionStatus.SUCCESS
        assert result.body_text == "Article body..."

    @pytest.mark.asyncio
    async def test_timeout_returns_timeout_status(self, extractor):
        """タイムアウト時はTIMEOUTステータスを返す。"""
        # タイムアウトをシミュレート

        result = await extractor.extract(article)

        assert result.extraction_status == ExtractionStatus.TIMEOUT
```

## 依存関係

- 依存先: P10-010
- ブロック: P10-012

## 見積もり

- 作業時間: 45分
- 複雑度: 高

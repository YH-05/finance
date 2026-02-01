"""Unit tests for article_content_checker module.

Tests cover:
- ContentStatus enum values
- ContentCheckResult dataclass
- HTML text extraction (extract_article_text)
- Paywall detection (detect_paywall)
- Tier 1: httpx-based fetching (mocked)
- Tier 2: Playwright-based fetching (mocked)
- Tier 3: Paywall indicator analysis
- Main check_article_content orchestration (mocked)
- CLI entry point
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rss.services.article_content_checker import (
    ARTICLE_SELECTORS,
    MIN_CONTENT_LENGTH,
    PAYWALL_INDICATORS_EN,
    PAYWALL_INDICATORS_JA,
    ContentCheckResult,
    ContentStatus,
    _check_paywall,
    _fetch_with_httpx,
    _fetch_with_playwright,
    _main,
    check_article_content,
    detect_paywall,
    extract_article_text,
)

# ---------------------------------------------------------------------------
# ContentStatus enum tests
# ---------------------------------------------------------------------------


class TestContentStatus:
    """Test ContentStatus enum."""

    def test_正常系_ACCESSIBLE値が正しい(self) -> None:
        assert ContentStatus.ACCESSIBLE.value == "accessible"

    def test_正常系_PAYWALLED値が正しい(self) -> None:
        assert ContentStatus.PAYWALLED.value == "paywalled"

    def test_正常系_INSUFFICIENT値が正しい(self) -> None:
        assert ContentStatus.INSUFFICIENT.value == "insufficient"

    def test_正常系_FETCH_ERROR値が正しい(self) -> None:
        assert ContentStatus.FETCH_ERROR.value == "fetch_error"

    def test_正常系_全ステータスが4つ存在する(self) -> None:
        assert len(ContentStatus) == 4


# ---------------------------------------------------------------------------
# ContentCheckResult dataclass tests
# ---------------------------------------------------------------------------


class TestContentCheckResult:
    """Test ContentCheckResult frozen dataclass."""

    def test_正常系_データクラスが正しく作成される(self) -> None:
        result = ContentCheckResult(
            status=ContentStatus.ACCESSIBLE,
            content_length=1500,
            raw_text="Article body text",
            reason="Tier 1: 本文取得成功 (1500文字)",
            tier_used=1,
        )
        assert result.status == ContentStatus.ACCESSIBLE
        assert result.content_length == 1500
        assert result.raw_text == "Article body text"
        assert result.reason == "Tier 1: 本文取得成功 (1500文字)"
        assert result.tier_used == 1

    def test_正常系_frozenでイミュータブル(self) -> None:
        result = ContentCheckResult(
            status=ContentStatus.ACCESSIBLE,
            content_length=100,
            raw_text="text",
            reason="reason",
            tier_used=1,
        )
        with pytest.raises(AttributeError):
            result.status = ContentStatus.PAYWALLED

    def test_正常系_FETCH_ERROR結果(self) -> None:
        result = ContentCheckResult(
            status=ContentStatus.FETCH_ERROR,
            content_length=0,
            raw_text="",
            reason="Tier 1: HTTP 403 error",
            tier_used=1,
        )
        assert result.status == ContentStatus.FETCH_ERROR
        assert result.content_length == 0
        assert result.raw_text == ""


# ---------------------------------------------------------------------------
# extract_article_text tests
# ---------------------------------------------------------------------------


class TestExtractArticleText:
    """Test HTML text extraction."""

    def test_正常系_article要素からテキスト抽出(self) -> None:
        html_content = """
        <html><body>
            <nav>Navigation</nav>
            <article>
                <h1>Title</h1>
                <p>This is the article body content with enough text.</p>
            </article>
            <footer>Footer</footer>
        </body></html>
        """
        text = extract_article_text(html_content)
        assert "article body content" in text
        assert "Navigation" not in text
        assert "Footer" not in text

    def test_正常系_main要素からテキスト抽出(self) -> None:
        html_content = """
        <html><body>
            <header>Header</header>
            <main>
                <p>Main content paragraph.</p>
            </main>
        </body></html>
        """
        text = extract_article_text(html_content)
        assert "Main content paragraph" in text

    def test_正常系_articleクラスからテキスト抽出(self) -> None:
        html_content = """
        <html><body>
            <div class="article-body">
                <p>Article body class content.</p>
            </div>
        </body></html>
        """
        text = extract_article_text(html_content)
        assert "Article body class content" in text

    def test_正常系_entryコンテンツクラスからテキスト抽出(self) -> None:
        html_content = """
        <html><body>
            <div class="entry-content">
                <p>Entry content text.</p>
            </div>
        </body></html>
        """
        text = extract_article_text(html_content)
        assert "Entry content text" in text

    def test_正常系_script_style要素を除外(self) -> None:
        html_content = """
        <html><body>
            <article>
                <p>Real content.</p>
                <script>var x = 1;</script>
                <style>.hidden { display: none; }</style>
                <noscript>Enable JS</noscript>
            </article>
        </body></html>
        """
        text = extract_article_text(html_content)
        assert "Real content" in text
        assert "var x" not in text
        assert "display: none" not in text
        assert "Enable JS" not in text

    def test_正常系_bodyフォールバック(self) -> None:
        html_content = """
        <html><body>
            <div>Some text in body with no article tags.</div>
        </body></html>
        """
        text = extract_article_text(html_content)
        assert "Some text in body" in text

    def test_エッジケース_空のHTML(self) -> None:
        assert extract_article_text("") == ""

    def test_エッジケース_不正なHTML(self) -> None:
        # lxml is fairly tolerant, but we test with badly formed HTML
        text = extract_article_text("<not valid><><<>")
        # Should not raise, may return empty or partial text
        assert isinstance(text, str)

    def test_正常系_空白の正規化(self) -> None:
        html_content = """
        <html><body>
            <article>
                <p>  Line one  </p>

                <p>  Line two  </p>

            </article>
        </body></html>
        """
        text = extract_article_text(html_content)
        assert "Line one" in text
        assert "Line two" in text
        # Should not have leading/trailing whitespace on lines
        for line in text.splitlines():
            assert line == line.strip()


# ---------------------------------------------------------------------------
# detect_paywall tests
# ---------------------------------------------------------------------------


class TestDetectPaywall:
    """Test paywall indicator detection."""

    def test_正常系_ペイウォール指標なしで本文長い場合はFalse(self) -> None:
        text = "This is a normal article with lots of content. " * 50
        assert detect_paywall(text, len(text)) is False

    def test_正常系_短い本文に英語ペイウォール指標でTrue(self) -> None:
        text = "subscribe to continue reading this premium article"
        assert detect_paywall(text, len(text)) is True

    def test_正常系_短い本文に日本語ペイウォール指標でTrue(self) -> None:
        text = "この記事は有料会員限定です。続きを読むにはログインしてください。"
        assert detect_paywall(text, len(text)) is True

    def test_正常系_中程度の本文に複数指標でTrue(self) -> None:
        # 200-1500 chars with 2+ indicators
        text = (
            "This article is premium content. Already a subscriber? Sign in. "
            + "x" * 600
        )
        assert detect_paywall(text, len(text)) is True

    def test_正常系_中程度の本文に1つの指標でFalse(self) -> None:
        # 200-1500 chars with only 1 indicator should be False
        text = "This article mentions premium content. " + "x" * 600
        assert detect_paywall(text, len(text)) is False

    def test_正常系_長い本文に指標があってもFalse(self) -> None:
        # >= 1500 chars, even with indicators
        text = "subscribe to continue and premium content. " + "x" * 1600
        assert detect_paywall(text, len(text)) is False

    def test_エッジケース_空テキスト(self) -> None:
        assert detect_paywall("", 0) is False

    def test_正常系_大文字小文字を区別しない(self) -> None:
        text = "SUBSCRIBE TO CONTINUE reading"
        assert detect_paywall(text, len(text)) is True

    def test_正常系_月額指標の検出(self) -> None:
        text = "月額980円で全記事が読み放題"
        assert detect_paywall(text, len(text)) is True


# ---------------------------------------------------------------------------
# _fetch_with_httpx tests (mocked)
# ---------------------------------------------------------------------------


class TestFetchWithHttpx:
    """Test Tier 1 httpx fetching."""

    @pytest.mark.asyncio
    async def test_正常系_HTMLからテキスト抽出(self) -> None:
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
            <article><p>Long article content. </p></article>
        </body></html>
        """
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "rss.services.article_content_checker.httpx.AsyncClient",
            return_value=mock_client,
        ):
            text, status_code = await _fetch_with_httpx("https://example.com/article")

        assert "Long article content" in text
        assert status_code == 200

    @pytest.mark.asyncio
    async def test_異常系_HTTPエラーで例外送出(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "403 Forbidden",
                request=MagicMock(),
                response=mock_response,
            )
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "rss.services.article_content_checker.httpx.AsyncClient",
                return_value=mock_client,
            ),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await _fetch_with_httpx("https://example.com/paywalled")


# ---------------------------------------------------------------------------
# _fetch_with_playwright tests (mocked)
# ---------------------------------------------------------------------------


class TestFetchWithPlaywright:
    """Test Tier 2 Playwright fetching."""

    @pytest.mark.asyncio
    async def test_正常系_JSレンダリング後にテキスト抽出(self) -> None:
        html_content = """
        <html><body>
            <article><p>JS rendered article content.</p></article>
        </body></html>
        """

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value=html_content)

        mock_browser = AsyncMock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)
        mock_browser.close = AsyncMock()

        mock_playwright_context = AsyncMock()
        mock_playwright_context.chromium = MagicMock()
        mock_playwright_context.chromium.launch = AsyncMock(return_value=mock_browser)

        mock_pw = AsyncMock()
        mock_pw.__aenter__ = AsyncMock(return_value=mock_playwright_context)
        mock_pw.__aexit__ = AsyncMock(return_value=False)

        mock_async_playwright = MagicMock(return_value=mock_pw)

        with patch(
            "playwright.async_api.async_playwright",
            mock_async_playwright,
        ):
            text = await _fetch_with_playwright("https://example.com/js-article")

        assert "JS rendered article content" in text

    @pytest.mark.asyncio
    async def test_異常系_Playwrightインポートエラーで空文字返却(self) -> None:
        # Simulate playwright not being installed by making the import raise
        # We patch the function's internal import by making the module unavailable
        import importlib
        import sys

        # Save original module references
        saved_modules: dict[str, object] = {}
        pw_keys = [k for k in sys.modules if k.startswith("playwright")]
        for key in pw_keys:
            saved_modules[key] = sys.modules.pop(key)

        # Insert a broken module entry to force ImportError
        sys.modules["playwright"] = None  # type: ignore[assignment]
        sys.modules["playwright.async_api"] = None  # type: ignore[assignment]

        try:
            text = await _fetch_with_playwright("https://example.com")
            assert text == ""
        finally:
            # Restore original modules
            del sys.modules["playwright"]
            del sys.modules["playwright.async_api"]
            sys.modules.update(saved_modules)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _check_paywall tests
# ---------------------------------------------------------------------------


class TestCheckPaywall:
    """Test Tier 3 paywall check integration."""

    def test_正常系_アクセス可能な記事(self) -> None:
        text = "Normal article content. " * 100
        result = _check_paywall(
            text,
            len(text),
            tier_used=1,
            url="https://example.com",
        )
        assert result.status == ContentStatus.ACCESSIBLE
        assert result.tier_used == 1
        assert result.content_length == len(text)

    def test_正常系_ペイウォール検出(self) -> None:
        text = "subscribe to continue reading this premium content"
        result = _check_paywall(
            text,
            len(text),
            tier_used=1,
            url="https://example.com",
        )
        assert result.status == ContentStatus.PAYWALLED
        assert result.tier_used == 3
        assert "ペイウォール検出" in result.reason

    def test_正常系_Tier2経由のアクセス可能記事(self) -> None:
        text = "JS rendered content. " * 100
        result = _check_paywall(
            text,
            len(text),
            tier_used=2,
            url="https://example.com",
        )
        assert result.status == ContentStatus.ACCESSIBLE
        assert result.tier_used == 2


# ---------------------------------------------------------------------------
# check_article_content integration tests (mocked)
# ---------------------------------------------------------------------------


class TestCheckArticleContent:
    """Test main check_article_content function."""

    @pytest.mark.asyncio
    async def test_正常系_Tier1で十分な本文取得(self) -> None:
        long_text = "Article content. " * 100  # > 200 chars
        with patch(
            "rss.services.article_content_checker._fetch_with_httpx",
            return_value=(long_text, 200),
        ):
            result = await check_article_content("https://example.com/article")

        assert result.status == ContentStatus.ACCESSIBLE
        assert result.tier_used == 1
        assert result.content_length >= MIN_CONTENT_LENGTH

    @pytest.mark.asyncio
    async def test_正常系_Tier1不十分でTier2で成功(self) -> None:
        short_text = "Short."
        long_text = "JS rendered content. " * 100

        with (
            patch(
                "rss.services.article_content_checker._fetch_with_httpx",
                return_value=(short_text, 200),
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value=long_text,
            ),
        ):
            result = await check_article_content("https://example.com/js-article")

        assert result.status == ContentStatus.ACCESSIBLE
        assert result.tier_used == 2

    @pytest.mark.asyncio
    async def test_正常系_Tier1とTier2両方不十分(self) -> None:
        short_text = "Short content."

        with (
            patch(
                "rss.services.article_content_checker._fetch_with_httpx",
                return_value=(short_text, 200),
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value="Even shorter",
            ),
        ):
            result = await check_article_content("https://example.com/empty")

        assert result.status == ContentStatus.INSUFFICIENT
        assert "本文不十分" in result.reason

    @pytest.mark.asyncio
    async def test_異常系_HTTPステータスエラー(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch(
            "rss.services.article_content_checker._fetch_with_httpx",
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=mock_response,
            ),
        ):
            result = await check_article_content("https://example.com/not-found")

        assert result.status == ContentStatus.FETCH_ERROR
        assert "HTTP 404" in result.reason
        assert result.tier_used == 1

    @pytest.mark.asyncio
    async def test_異常系_ネットワークエラー(self) -> None:
        with patch(
            "rss.services.article_content_checker._fetch_with_httpx",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = await check_article_content("https://unreachable.example.com")

        assert result.status == ContentStatus.FETCH_ERROR
        assert result.tier_used == 1

    @pytest.mark.asyncio
    async def test_正常系_Tier1十分だがペイウォール検出(self) -> None:
        text = (
            "subscribe to continue reading. Already a subscriber? "
            "Premium content for members only. "
        ) + "x" * 600
        with patch(
            "rss.services.article_content_checker._fetch_with_httpx",
            return_value=(text, 200),
        ):
            result = await check_article_content("https://example.com/paywalled")

        assert result.status == ContentStatus.PAYWALLED
        assert result.tier_used == 3

    @pytest.mark.asyncio
    async def test_正常系_Tier2失敗時はTier1のテキストを使用(self) -> None:
        short_text = "Short content from Tier 1."

        with (
            patch(
                "rss.services.article_content_checker._fetch_with_httpx",
                return_value=(short_text, 200),
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                side_effect=Exception("Browser crashed"),
            ),
        ):
            result = await check_article_content("https://example.com")

        assert result.status == ContentStatus.INSUFFICIENT
        assert result.content_length == len(short_text)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


class TestCLI:
    """Test CLI entry point."""

    @pytest.mark.asyncio
    async def test_正常系_JSON出力(self, capsys: pytest.CaptureFixture[str]) -> None:
        long_text = "Article body. " * 100
        with patch(
            "rss.services.article_content_checker._fetch_with_httpx",
            return_value=(long_text, 200),
        ):
            await _main("https://example.com/article")

        captured = capsys.readouterr()
        import json

        output = json.loads(captured.out)
        assert output["status"] == "accessible"
        assert "content_length" in output
        assert "reason" in output
        assert "tier_used" in output


# ---------------------------------------------------------------------------
# Constants validation tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Test module constants."""

    def test_正常系_最小コンテンツ長が200(self) -> None:
        assert MIN_CONTENT_LENGTH == 200

    def test_正常系_XPathセレクタが存在する(self) -> None:
        assert len(ARTICLE_SELECTORS) > 0
        # All selectors should start with //
        for selector in ARTICLE_SELECTORS:
            assert selector.startswith("//"), f"Invalid selector: {selector}"

    def test_正常系_英語ペイウォール指標が存在する(self) -> None:
        assert len(PAYWALL_INDICATORS_EN) > 0

    def test_正常系_日本語ペイウォール指標が存在する(self) -> None:
        assert len(PAYWALL_INDICATORS_JA) > 0


# ---------------------------------------------------------------------------
# Fallback feature tests (Issue #1853)
# ---------------------------------------------------------------------------


class TestFallbackFeature:
    """Test automatic fallback from Tier 1 to Tier 2."""

    @pytest.mark.asyncio
    async def test_正常系_Tier1不十分でTier2自動フォールバック発生(self) -> None:
        """Tier 1 が不十分な場合、自動的に Tier 2 が試行されることを確認。"""
        short_text = "Short."
        long_text = "JS rendered content with sufficient length. " * 20

        with (
            patch(
                "rss.services.article_content_checker._fetch_with_httpx",
                return_value=(short_text, 200),
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value=long_text,
            ) as mock_playwright,
        ):
            result = await check_article_content("https://example.com/js-article")

        # Tier 2 が呼び出されたことを確認
        mock_playwright.assert_called_once_with("https://example.com/js-article")
        assert result.status == ContentStatus.ACCESSIBLE
        assert result.tier_used == 2

    @pytest.mark.asyncio
    async def test_正常系_フォールバック発生時にログ記録(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """フォールバック発生時にログが記録されることを確認。"""
        import logging

        short_text = "Short."
        long_text = "Long enough content for testing. " * 20

        with (
            patch(
                "rss.services.article_content_checker._fetch_with_httpx",
                return_value=(short_text, 200),
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value=long_text,
            ),
            caplog.at_level(logging.DEBUG),
        ):
            result = await check_article_content("https://example.com/article")

        # フォールバック関連のログが記録されていることを確認
        assert any(
            "Tier 2" in record.message or "Tier 1" in record.message
            for record in caplog.records
        )
        assert result.status == ContentStatus.ACCESSIBLE

    @pytest.mark.asyncio
    async def test_正常系_フォールバック回数の制限(self) -> None:
        """フォールバックは最大回数を超えないことを確認。

        現在の実装では Tier 1 → Tier 2 の1回のフォールバックのみ。
        将来的に複数のフォールバック層が追加された場合に備えて、
        無限ループが発生しないことを確認する。
        """
        short_text = "Short."

        with (
            patch(
                "rss.services.article_content_checker._fetch_with_httpx",
                return_value=(short_text, 200),
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value="Also short.",
            ),
        ):
            # 無限ループせずに結果が返されることを確認
            result = await check_article_content("https://example.com/article")

        # フォールバック後も結果が返される（無限ループしない）
        assert result.status in (
            ContentStatus.INSUFFICIENT,
            ContentStatus.ACCESSIBLE,
            ContentStatus.PAYWALLED,
        )
        # tier_used が有効な値であることを確認
        assert result.tier_used in (1, 2, 3)

    @pytest.mark.asyncio
    async def test_正常系_ContentCheckResult_fallback_countフィールド(self) -> None:
        """ContentCheckResult にフォールバック回数が記録されることを確認。"""
        short_text = "Short."
        long_text = "Long enough content for testing. " * 20

        with (
            patch(
                "rss.services.article_content_checker._fetch_with_httpx",
                return_value=(short_text, 200),
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value=long_text,
            ),
        ):
            result = await check_article_content("https://example.com/article")

        # fallback_count フィールドが存在し、フォールバックが発生した場合は1以上
        assert hasattr(result, "fallback_count")
        assert result.fallback_count >= 1  # Tier 1 → Tier 2 のフォールバックが発生

    @pytest.mark.asyncio
    async def test_正常系_Tier1成功時はフォールバックなし(self) -> None:
        """Tier 1 で十分なコンテンツが取得できた場合、フォールバックしないことを確認。"""
        long_text = "Long enough content directly from Tier 1. " * 20

        with (
            patch(
                "rss.services.article_content_checker._fetch_with_httpx",
                return_value=(long_text, 200),
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
            ) as mock_playwright,
        ):
            result = await check_article_content("https://example.com/article")

        # Tier 2 が呼び出されていないことを確認
        mock_playwright.assert_not_called()
        assert result.status == ContentStatus.ACCESSIBLE
        assert result.tier_used == 1
        assert hasattr(result, "fallback_count")
        assert result.fallback_count == 0  # フォールバックなし

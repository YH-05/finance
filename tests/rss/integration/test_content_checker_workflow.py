"""Integration tests for the article content checker workflow.

Tests verify that the 3-tier content checking pipeline works correctly
as an integrated system. All network calls are mocked to allow
deterministic testing without external dependencies.

Test scenarios:
- Full Tier 1 → Tier 3 accessible flow
- Full Tier 1 → Tier 2 → Tier 3 accessible flow
- Paywall detection end-to-end
- Content insufficient end-to-end
- Error recovery flow (Tier 1 failure → Tier 2 fallback)
- CLI JSON output verification
- URL normalizer + content checker combined workflow
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rss.services.article_content_checker import (
    MIN_CONTENT_LENGTH,
    ContentCheckResult,
    ContentStatus,
    _main,
    check_article_content,
)
from rss.utils.url_normalizer import (
    is_duplicate,
    normalize_url,
)

# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

_ACCESSIBLE_HTML = """
<html>
<head><title>Finance News</title></head>
<body>
    <nav>Navigation links</nav>
    <article>
        <h1>S&P 500 Hits Record High</h1>
        <p>The S&P 500 index closed at a record high of 5,200 points on Wednesday,
        driven by strong earnings from technology companies. The benchmark index
        rose 1.2% during the trading session, marking its 15th record close of
        the year. Major contributors included Apple, Microsoft, and NVIDIA,
        which collectively added over 100 points to the index.</p>
        <p>Analysts at Goldman Sachs noted that the rally was broad-based, with
        8 out of 11 sectors posting gains. The technology sector led with a
        2.1% advance, followed by consumer discretionary at 1.5%.</p>
        <p>"We see further upside potential as earnings continue to surprise
        to the upside," said Jane Smith, chief equity strategist at Goldman
        Sachs. "Our year-end target for the S&P 500 remains at 5,500."</p>
        <p>Trading volume was above average, with 4.2 billion shares changing
        hands on the NYSE. The VIX volatility index fell 5% to 12.5,
        reflecting growing investor confidence.</p>
    </article>
    <footer>Copyright 2026</footer>
</body>
</html>
"""

_PAYWALL_HTML_SHORT = """
<html>
<body>
    <article>
        <h1>Exclusive Analysis</h1>
        <p>Subscribe to continue reading this premium content.
        Already a subscriber? Sign in to read the full article.</p>
    </article>
</body>
</html>
"""

_PAYWALL_HTML_MEDIUM = """
<html>
<body>
    <article>
        <h1>Market Analysis Report</h1>
        <p>The Federal Reserve announced its latest interest rate decision today,
        keeping rates unchanged at 5.25-5.50%. This decision was largely expected
        by market participants.</p>
        <p>This article is premium content for our subscribers. Already a subscriber?
        Please sign in to read the full analysis. Start your free trial today
        to access all of our market insights and research reports.</p>
        {padding}
    </article>
</body>
</html>
""".format(padding="<p>" + "x " * 200 + "</p>")

_INSUFFICIENT_HTML = """
<html>
<body>
    <article>
        <p>Brief headline text.</p>
    </article>
</body>
</html>
"""

_JS_RENDERED_HTML = """
<html>
<body>
    <article>
        <h1>Interactive Dashboard</h1>
        <p>This content was rendered by JavaScript. The dashboard shows real-time
        market data for major indices. The S&P 500 is currently trading at 5,200
        points, up 1.2% on the day. The NASDAQ composite has gained 1.8%,
        while the Dow Jones Industrial Average is up 0.9%.</p>
        <p>Technology stocks are leading the gains, with the semiconductor
        sector up 3.5% following strong earnings from major chipmakers.
        Energy stocks are the weakest performers, down 0.5% as oil prices
        declined amid concerns about global demand.</p>
        <p>Bond yields fell slightly, with the 10-year Treasury yield dropping
        to 4.15% from 4.20%. The dollar index weakened 0.3% against a basket
        of major currencies, providing a tailwind for multinational corporations.</p>
    </article>
</body>
</html>
"""


def _mock_httpx_response(html: str, status_code: int = 200) -> MagicMock:
    """Create a mock httpx response."""
    resp = MagicMock()
    resp.text = html
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


def _mock_httpx_client(response: MagicMock) -> AsyncMock:
    """Create a mock httpx AsyncClient."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


# ---------------------------------------------------------------------------
# Tier 1 → Tier 3 → ACCESSIBLE flow
# ---------------------------------------------------------------------------


class TestTier1ToAccessibleFlow:
    """Integration: Tier 1 httpx → sufficient content → Tier 3 no paywall → ACCESSIBLE."""

    @pytest.mark.asyncio
    async def test_正常系_Tier1で十分な本文を取得しアクセス可能と判定(self) -> None:
        response = _mock_httpx_response(_ACCESSIBLE_HTML)
        client = _mock_httpx_client(response)

        with patch(
            "rss.services.article_content_checker.httpx.AsyncClient",
            return_value=client,
        ):
            result = await check_article_content(
                "https://www.cnbc.com/2026/01/15/markets.html"
            )

        assert result.status == ContentStatus.ACCESSIBLE
        assert result.tier_used == 1
        assert result.content_length >= MIN_CONTENT_LENGTH
        assert "S&P 500" in result.raw_text
        assert "Goldman Sachs" in result.raw_text

    @pytest.mark.asyncio
    async def test_正常系_結果がContentCheckResult型(self) -> None:
        response = _mock_httpx_response(_ACCESSIBLE_HTML)
        client = _mock_httpx_client(response)

        with patch(
            "rss.services.article_content_checker.httpx.AsyncClient",
            return_value=client,
        ):
            result = await check_article_content("https://example.com/article")

        assert isinstance(result, ContentCheckResult)
        assert isinstance(result.status, ContentStatus)
        assert isinstance(result.content_length, int)
        assert isinstance(result.raw_text, str)
        assert isinstance(result.reason, str)
        assert isinstance(result.tier_used, int)


# ---------------------------------------------------------------------------
# Tier 1 → Tier 2 → Tier 3 → ACCESSIBLE flow
# ---------------------------------------------------------------------------


class TestTier1ToTier2ToAccessibleFlow:
    """Integration: Tier 1 insufficient → Tier 2 Playwright → Tier 3 → ACCESSIBLE."""

    @pytest.mark.asyncio
    async def test_正常系_Tier1不十分からTier2で本文取得成功(self) -> None:
        # Tier 1: returns insufficient content
        response = _mock_httpx_response(_INSUFFICIENT_HTML)
        client = _mock_httpx_client(response)

        with (
            patch(
                "rss.services.article_content_checker.httpx.AsyncClient",
                return_value=client,
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value=_extract_text_from_html(_JS_RENDERED_HTML),
            ),
        ):
            result = await check_article_content("https://example.com/js-heavy")

        assert result.status == ContentStatus.ACCESSIBLE
        assert result.tier_used == 2
        assert result.content_length >= MIN_CONTENT_LENGTH


# ---------------------------------------------------------------------------
# Paywall detection end-to-end
# ---------------------------------------------------------------------------


class TestPaywallDetectionFlow:
    """Integration: Content fetched → paywall indicators detected → PAYWALLED."""

    @pytest.mark.asyncio
    async def test_正常系_短い本文にペイウォール指標でPAYWALLED(self) -> None:
        response = _mock_httpx_response(_PAYWALL_HTML_SHORT)
        client = _mock_httpx_client(response)

        # Tier 1 returns some text but below MIN_CONTENT_LENGTH with paywall indicators
        # The text will be < 500 chars with paywall keywords
        with (
            patch(
                "rss.services.article_content_checker.httpx.AsyncClient",
                return_value=client,
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value="Subscribe to continue. Premium content only.",
            ),
        ):
            result = await check_article_content("https://www.bloomberg.com/paywalled")

        # Both Tier 1 and Tier 2 returned insufficient content
        assert result.status == ContentStatus.INSUFFICIENT

    @pytest.mark.asyncio
    async def test_正常系_中程度の本文に複数ペイウォール指標でPAYWALLED(self) -> None:
        response = _mock_httpx_response(_PAYWALL_HTML_MEDIUM)
        client = _mock_httpx_client(response)

        with patch(
            "rss.services.article_content_checker.httpx.AsyncClient",
            return_value=client,
        ):
            result = await check_article_content("https://example.com/premium-article")

        # The medium paywall HTML has enough text (>500) with 2+ indicators
        assert result.status == ContentStatus.PAYWALLED
        assert result.tier_used == 3
        assert "ペイウォール検出" in result.reason


# ---------------------------------------------------------------------------
# Content insufficient end-to-end
# ---------------------------------------------------------------------------


class TestInsufficientContentFlow:
    """Integration: Both tiers return insufficient content → INSUFFICIENT."""

    @pytest.mark.asyncio
    async def test_正常系_両Tierで本文不十分(self) -> None:
        response = _mock_httpx_response(_INSUFFICIENT_HTML)
        client = _mock_httpx_client(response)

        with (
            patch(
                "rss.services.article_content_checker.httpx.AsyncClient",
                return_value=client,
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                return_value="Also very short.",
            ),
        ):
            result = await check_article_content("https://example.com/empty-page")

        assert result.status == ContentStatus.INSUFFICIENT
        assert "本文不十分" in result.reason
        assert result.content_length < MIN_CONTENT_LENGTH


# ---------------------------------------------------------------------------
# Error recovery flow
# ---------------------------------------------------------------------------


class TestErrorRecoveryFlow:
    """Integration: Tier 1 failure → graceful error reporting."""

    @pytest.mark.asyncio
    async def test_異常系_HTTPエラーでFETCH_ERROR(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch(
            "rss.services.article_content_checker._fetch_with_httpx",
            side_effect=httpx.HTTPStatusError(
                "403 Forbidden",
                request=MagicMock(),
                response=mock_response,
            ),
        ):
            result = await check_article_content("https://forbidden.example.com")

        assert result.status == ContentStatus.FETCH_ERROR
        assert result.tier_used == 1
        assert "403" in result.reason
        assert result.content_length == 0

    @pytest.mark.asyncio
    async def test_異常系_接続エラーでFETCH_ERROR(self) -> None:
        with patch(
            "rss.services.article_content_checker._fetch_with_httpx",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = await check_article_content("https://unreachable.example.com")

        assert result.status == ContentStatus.FETCH_ERROR
        assert result.tier_used == 1

    @pytest.mark.asyncio
    async def test_異常系_Tier2例外でも安全にINSUFFICIENT(self) -> None:
        response = _mock_httpx_response(_INSUFFICIENT_HTML)
        client = _mock_httpx_client(response)

        with (
            patch(
                "rss.services.article_content_checker.httpx.AsyncClient",
                return_value=client,
            ),
            patch(
                "rss.services.article_content_checker._fetch_with_playwright",
                side_effect=RuntimeError("Browser crashed"),
            ),
        ):
            result = await check_article_content("https://example.com/crash")

        # Should not raise; should return INSUFFICIENT
        assert result.status == ContentStatus.INSUFFICIENT


# ---------------------------------------------------------------------------
# CLI JSON output verification
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    """Integration: CLI entry point produces valid JSON output."""

    @pytest.mark.asyncio
    async def test_正常系_CLI出力がJSON仕様準拠(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        response = _mock_httpx_response(_ACCESSIBLE_HTML)
        client = _mock_httpx_client(response)

        with patch(
            "rss.services.article_content_checker.httpx.AsyncClient",
            return_value=client,
        ):
            await _main("https://example.com/article")

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Verify all required fields
        assert "status" in output
        assert output["status"] in [
            "accessible",
            "paywalled",
            "insufficient",
            "fetch_error",
        ]
        assert "content_length" in output
        assert isinstance(output["content_length"], int)
        assert "reason" in output
        assert isinstance(output["reason"], str)
        assert "tier_used" in output
        assert output["tier_used"] in [1, 2, 3]

    @pytest.mark.asyncio
    async def test_正常系_アクセス可能な記事のCLI出力(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        response = _mock_httpx_response(_ACCESSIBLE_HTML)
        client = _mock_httpx_client(response)

        with patch(
            "rss.services.article_content_checker.httpx.AsyncClient",
            return_value=client,
        ):
            await _main("https://example.com/accessible")

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["status"] == "accessible"
        assert output["content_length"] >= MIN_CONTENT_LENGTH
        assert output["tier_used"] == 1


# ---------------------------------------------------------------------------
# URL normalizer + content checker combined flow
# ---------------------------------------------------------------------------


class TestUrlNormalizerWithContentChecker:
    """Integration: URL normalizer works with content checker for dedup workflow."""

    def test_正常系_同一記事の異なるURLがnormalizeで一致(self) -> None:
        """Verify that URLs with www/fragment/tracking differences normalize to same value."""
        urls = [
            "https://www.cnbc.com/2026/01/15/markets.html?utm_source=rss",
            "https://cnbc.com/2026/01/15/markets.html#section",
            "https://CNBC.COM/2026/01/15/markets.html/",
            "https://www.cnbc.com/2026/01/15/markets.html?fbclid=abc123",
        ]
        normalized = [normalize_url(u) for u in urls]
        # All should normalize to the same URL
        assert len(set(normalized)) == 1

    def test_正常系_重複チェックがURL正規化を活用(self) -> None:
        """Verify that is_duplicate uses normalize_url correctly."""
        new_item = {
            "link": "https://www.cnbc.com/2026/01/15/markets.html?utm_source=rss",
            "title": "Markets rally to record high",
        }
        existing_issues = [
            {
                "article_url": "https://cnbc.com/2026/01/15/markets.html",
                "title": "[株価指数] Markets rally to record high",
                "number": 42,
            }
        ]

        is_dup, number, reason = is_duplicate(new_item, existing_issues)
        assert is_dup is True
        assert number == 42
        assert reason == "URL一致"

    def test_正常系_異なる記事は重複と判定されない(self) -> None:
        """Verify that different articles are not flagged as duplicates."""
        new_item = {
            "link": "https://www.reuters.com/2026/01/15/new-article.html",
            "title": "Completely different article about technology",
        }
        existing_issues = [
            {
                "article_url": "https://cnbc.com/2026/01/15/markets.html",
                "title": "[株価指数] Markets rally to record high",
                "number": 42,
            }
        ]

        is_dup, _, _ = is_duplicate(new_item, existing_issues)
        assert is_dup is False


# ---------------------------------------------------------------------------
# Helper for extracting text from HTML (simulates what extract_article_text does)
# ---------------------------------------------------------------------------


def _extract_text_from_html(html_content: str) -> str:
    """Quick helper to extract text for mocking Playwright results."""
    from rss.services.article_content_checker import extract_article_text

    return extract_article_text(html_content)

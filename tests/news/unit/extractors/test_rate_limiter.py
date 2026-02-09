"""Unit tests for DomainRateLimiter.

This module tests the DomainRateLimiter class which enforces
per-domain rate limiting for HTTP requests to avoid being blocked
by anti-scraping measures.

Tests cover:
- Basic instantiation and configuration
- Rate limiting enforcement (minimum delay between same-domain requests)
- Jitter (random additional delay) for bot detection avoidance
- Domain extraction from URLs
- Session-fixed User-Agent per domain
- Concurrent request handling
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from news.extractors.rate_limiter import DomainRateLimiter


class TestDomainRateLimiterInstantiation:
    """Tests for DomainRateLimiter instantiation."""

    def test_正常系_デフォルト設定でインスタンス化できる(self) -> None:
        """DomainRateLimiter can be instantiated with default settings."""
        limiter = DomainRateLimiter()
        assert limiter is not None
        assert limiter._min_delay == 2.0
        assert limiter._max_delay == 5.0

    def test_正常系_カスタム設定でインスタンス化できる(self) -> None:
        """DomainRateLimiter can be instantiated with custom settings."""
        limiter = DomainRateLimiter(min_delay=3.0, max_delay=10.0)
        assert limiter._min_delay == 3.0
        assert limiter._max_delay == 10.0

    def test_異常系_min_delayがmax_delayより大きい場合ValueError(self) -> None:
        """ValueError should be raised when min_delay > max_delay."""
        with pytest.raises(ValueError, match="min_delay must be <= max_delay"):
            DomainRateLimiter(min_delay=10.0, max_delay=5.0)

    def test_異常系_min_delayが負の場合ValueError(self) -> None:
        """ValueError should be raised when min_delay is negative."""
        with pytest.raises(ValueError, match="min_delay must be >= 0"):
            DomainRateLimiter(min_delay=-1.0, max_delay=5.0)


class TestDomainRateLimiterExtractDomain:
    """Tests for domain extraction from URLs."""

    def test_正常系_HTTPSのURLからドメインを抽出できる(self) -> None:
        """Domain can be extracted from HTTPS URL."""
        limiter = DomainRateLimiter()
        assert (
            limiter._extract_domain("https://www.cnbc.com/article/test")
            == "www.cnbc.com"
        )

    def test_正常系_HTTPのURLからドメインを抽出できる(self) -> None:
        """Domain can be extracted from HTTP URL."""
        limiter = DomainRateLimiter()
        assert limiter._extract_domain("http://example.com/path") == "example.com"

    def test_正常系_ポート付きURLからドメインを抽出できる(self) -> None:
        """Domain can be extracted from URL with port."""
        limiter = DomainRateLimiter()
        assert limiter._extract_domain("https://example.com:8080/path") == "example.com"

    def test_正常系_サブドメイン付きURLからドメインを抽出できる(self) -> None:
        """Domain can be extracted from URL with subdomain."""
        limiter = DomainRateLimiter()
        assert (
            limiter._extract_domain("https://search.cnbc.com/rs/search/view.xml")
            == "search.cnbc.com"
        )


class TestDomainRateLimiterWait:
    """Tests for rate limiting wait behavior."""

    @pytest.mark.asyncio
    async def test_正常系_初回リクエストは待機しない(self) -> None:
        """First request to a domain should not wait."""
        limiter = DomainRateLimiter(min_delay=2.0, max_delay=2.0)

        start = time.monotonic()
        await limiter.wait("https://www.cnbc.com/article/1")
        elapsed = time.monotonic() - start

        # First request should complete quickly (no delay)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_正常系_同一ドメインへの連続リクエストに最小遅延が適用される(
        self,
    ) -> None:
        """Consecutive requests to the same domain should have minimum delay."""
        limiter = DomainRateLimiter(min_delay=0.2, max_delay=0.2)

        await limiter.wait("https://www.cnbc.com/article/1")
        start = time.monotonic()
        await limiter.wait("https://www.cnbc.com/article/2")
        elapsed = time.monotonic() - start

        # Second request should have at least min_delay
        assert elapsed >= 0.15  # Allow small tolerance

    @pytest.mark.asyncio
    async def test_正常系_異なるドメインへのリクエストは待機しない(self) -> None:
        """Requests to different domains should not wait for each other."""
        limiter = DomainRateLimiter(min_delay=2.0, max_delay=2.0)

        await limiter.wait("https://www.cnbc.com/article/1")
        start = time.monotonic()
        await limiter.wait("https://www.reuters.com/article/1")
        elapsed = time.monotonic() - start

        # Different domain should complete quickly
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_正常系_十分な時間が経過していれば待機しない(self) -> None:
        """No wait needed if enough time has passed since last request."""
        limiter = DomainRateLimiter(min_delay=0.1, max_delay=0.1)

        await limiter.wait("https://www.cnbc.com/article/1")
        await asyncio.sleep(0.15)  # Wait longer than min_delay

        start = time.monotonic()
        await limiter.wait("https://www.cnbc.com/article/2")
        elapsed = time.monotonic() - start

        # Should not need to wait
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_正常系_ジッターが追加される(self) -> None:
        """Jitter should add random additional delay."""
        limiter = DomainRateLimiter(min_delay=0.1, max_delay=0.3)

        await limiter.wait("https://www.cnbc.com/article/1")
        start = time.monotonic()
        await limiter.wait("https://www.cnbc.com/article/2")
        elapsed = time.monotonic() - start

        # Should have at least min_delay but could be up to max_delay
        assert elapsed >= 0.05  # Allow tolerance

    @pytest.mark.asyncio
    async def test_正常系_last_requestが更新される(self) -> None:
        """Last request timestamp should be updated after wait."""
        limiter = DomainRateLimiter(min_delay=0.1, max_delay=0.1)

        await limiter.wait("https://www.cnbc.com/article/1")
        first_time = limiter._last_request.get("www.cnbc.com")
        assert first_time is not None

        await asyncio.sleep(0.15)
        await limiter.wait("https://www.cnbc.com/article/2")
        second_time = limiter._last_request.get("www.cnbc.com")
        assert second_time is not None
        assert second_time > first_time


class TestDomainRateLimiterSessionUA:
    """Tests for session-fixed User-Agent per domain."""

    def test_正常系_同一ドメインで同じUAを返す(self) -> None:
        """Same domain should always return the same User-Agent."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605",
            "Mozilla/5.0 (Linux; Android 13) Mobile Chrome/120",
        ]
        limiter = DomainRateLimiter()

        ua1 = limiter.get_session_user_agent("www.cnbc.com", user_agents)
        ua2 = limiter.get_session_user_agent("www.cnbc.com", user_agents)

        assert ua1 == ua2
        assert ua1 in user_agents

    def test_正常系_異なるドメインで異なるUAが割り当てられうる(self) -> None:
        """Different domains may get different User-Agents."""
        user_agents = [
            "UA1",
            "UA2",
            "UA3",
            "UA4",
            "UA5",
        ]
        limiter = DomainRateLimiter()

        # With enough different domains, at least some should get different UAs
        uas = set()
        for i in range(20):
            ua = limiter.get_session_user_agent(f"domain{i}.com", user_agents)
            uas.add(ua)

        # At least 2 different UAs should be assigned across 20 domains
        assert len(uas) >= 2

    def test_正常系_空のUA_リストでNoneを返す(self) -> None:
        """Empty user_agents list should return None."""
        limiter = DomainRateLimiter()
        result = limiter.get_session_user_agent("www.cnbc.com", [])
        assert result is None

    def test_正常系_一度割り当てられたUAはリスト変更後も保持される(self) -> None:
        """Once assigned, UA should persist even if list changes."""
        limiter = DomainRateLimiter()

        ua1 = limiter.get_session_user_agent("www.cnbc.com", ["UA1", "UA2"])
        # Call with different list
        ua2 = limiter.get_session_user_agent("www.cnbc.com", ["UA3", "UA4"])

        # Should still return the originally assigned UA
        assert ua1 == ua2

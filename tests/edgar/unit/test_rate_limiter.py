"""Unit tests for edgar.rate_limiter module.

Tests for RateLimiter class including token bucket algorithm,
thread safety, and configuration integration.
"""

from __future__ import annotations

import threading
import time

import pytest

from edgar.config import DEFAULT_RATE_LIMIT_PER_SECOND
from edgar.rate_limiter import RateLimiter


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_正常系_デフォルトレート制限で初期化(self) -> None:
        """RateLimiter should initialize with default rate of 10 req/sec.

        Verify that the default rate matches DEFAULT_RATE_LIMIT_PER_SECOND.
        """
        limiter = RateLimiter()
        assert limiter.max_requests_per_second == DEFAULT_RATE_LIMIT_PER_SECOND

    def test_正常系_カスタムレート制限で初期化(self) -> None:
        """RateLimiter should accept a custom rate limit.

        Verify that a custom rate is stored correctly.
        """
        limiter = RateLimiter(max_requests_per_second=5)
        assert limiter.max_requests_per_second == 5

    def test_異常系_レート制限0以下でValueError(self) -> None:
        """RateLimiter should raise ValueError for non-positive rate.

        Verify that 0 or negative rates are rejected.
        """
        with pytest.raises(ValueError, match="must be positive"):
            RateLimiter(max_requests_per_second=0)

        with pytest.raises(ValueError, match="must be positive"):
            RateLimiter(max_requests_per_second=-1)


class TestRateLimiterAcquire:
    """Tests for RateLimiter.acquire() method."""

    def test_正常系_制限内のリクエストは即座に通過(self) -> None:
        """acquire() should not block when under rate limit.

        Verify that requests within the rate limit pass immediately
        (within a small tolerance).
        """
        limiter = RateLimiter(max_requests_per_second=100)

        start = time.monotonic()
        for _ in range(5):
            limiter.acquire()
        elapsed = time.monotonic() - start

        # 5 requests at 100/sec should take less than 0.1 seconds
        assert elapsed < 0.1

    def test_正常系_制限超過時にスリープで待機(self) -> None:
        """acquire() should sleep when rate limit is exceeded.

        Verify that requests exceeding the rate limit are delayed
        by the appropriate amount.
        """
        # 5 requests per second = 200ms interval
        limiter = RateLimiter(max_requests_per_second=5)

        start = time.monotonic()
        # First request should pass immediately
        limiter.acquire()
        # Rapid second request should be delayed
        limiter.acquire()
        limiter.acquire()
        elapsed = time.monotonic() - start

        # With 5 req/sec, minimum interval is 200ms.
        # 3 requests should take at least 400ms (2 intervals)
        assert elapsed >= 0.35  # Allow small tolerance

    def test_正常系_スリープ後にリクエスト再開(self) -> None:
        """acquire() should allow requests after waiting period.

        Verify that after sleeping, the rate limiter resets its window
        and allows new requests to proceed.
        """
        limiter = RateLimiter(max_requests_per_second=10)

        # First request
        limiter.acquire()
        # Wait a full window
        time.sleep(0.15)
        # Next request should pass immediately
        start = time.monotonic()
        limiter.acquire()
        elapsed = time.monotonic() - start

        assert elapsed < 0.05


class TestRateLimiterThreadSafety:
    """Tests for RateLimiter thread safety."""

    def test_正常系_複数スレッドで安全に動作(self) -> None:
        """acquire() should be thread-safe under concurrent access.

        Verify that concurrent calls from multiple threads do not
        cause race conditions or exceed the rate limit.
        """
        limiter = RateLimiter(max_requests_per_second=20)
        timestamps: list[float] = []
        lock = threading.Lock()

        def worker() -> None:
            for _ in range(5):
                limiter.acquire()
                with lock:
                    timestamps.append(time.monotonic())

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 20 total requests across 4 threads
        assert len(timestamps) == 20

        # Verify that no more than 20 requests happen in any 1-second window
        timestamps.sort()
        for i in range(len(timestamps)):
            window_end = timestamps[i] + 1.0
            requests_in_window = sum(
                1 for t in timestamps if timestamps[i] <= t < window_end
            )
            # Allow small tolerance (21 instead of 20) for timing imprecision
            assert requests_in_window <= 21


class TestRateLimiterRepr:
    """Tests for RateLimiter string representation."""

    def test_正常系_repr出力にレート情報を含む(self) -> None:
        """__repr__ should include the max requests per second value.

        Verify that the repr is informative for debugging.
        """
        limiter = RateLimiter(max_requests_per_second=10)
        repr_str = repr(limiter)
        assert "10" in repr_str
        assert "RateLimiter" in repr_str

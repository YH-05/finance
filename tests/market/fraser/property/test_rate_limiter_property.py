"""Property-based tests for ``market.fraser.rate_limiter``.

The FRASER rate limiter re-exports
:class:`market.alphavantage.rate_limiter.DualWindowRateLimiter`, which
implements a sliding-window algorithm. These property tests assert two
invariants that callers depend on:

1. After at most ``requests_per_minute`` acquisitions, the deque length
   never exceeds ``requests_per_minute`` and
   ``available_minute >= 0``.
2. The :func:`get_fraser_rate_limiter` factory honours the limits set
   on a :class:`FraserConfig`.

See Also
--------
market.fraser.rate_limiter : Module under test.
market.alphavantage.rate_limiter : Underlying implementation.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from market.fraser.rate_limiter import (
    DualWindowRateLimiter,
    get_fraser_rate_limiter,
)
from market.fraser.types import FraserConfig

# =============================================================================
# Strategies
# =============================================================================

minute_limits = st.integers(min_value=1, max_value=30)
hour_limits = st.integers(min_value=1, max_value=300)
acquire_counts = st.integers(min_value=0, max_value=20)


# =============================================================================
# Property tests on the re-exported limiter
# =============================================================================


class TestSlidingWindowInvariantProperty:
    """Sliding-window upper-bound invariants under bounded contention."""

    @given(
        per_minute=minute_limits,
        per_hour=hour_limits,
        n=acquire_counts,
    )
    @settings(max_examples=100)
    def test_プロパティ_acquireのタイムスタンプ数がper_minute以下(
        self,
        per_minute: int,
        per_hour: int,
        n: int,
    ) -> None:
        per_hour = max(per_hour, per_minute)
        # Cap ``n`` so we never block waiting for a slot (tests must be fast).
        safe_n = min(n, per_minute, per_hour)

        limiter = DualWindowRateLimiter(
            requests_per_minute=per_minute,
            requests_per_hour=per_hour,
        )
        for _ in range(safe_n):
            limiter.acquire()

        # Sliding-window invariant: stored timestamps cannot exceed the
        # per-minute budget that has been consumed.
        assert len(limiter._timestamps) <= per_minute
        # Available capacity stays in ``[0, requests_per_minute]``.
        assert 0 <= limiter.available_minute <= per_minute

    @given(
        per_minute=minute_limits,
        per_hour=hour_limits,
        n=acquire_counts,
    )
    @settings(max_examples=100)
    def test_プロパティ_使用済み数_available_minuteの和が制限数(
        self,
        per_minute: int,
        per_hour: int,
        n: int,
    ) -> None:
        per_hour = max(per_hour, per_minute)
        safe_n = min(n, per_minute, per_hour)

        limiter = DualWindowRateLimiter(
            requests_per_minute=per_minute,
            requests_per_hour=per_hour,
        )
        for _ in range(safe_n):
            limiter.acquire()

        # Since the test executes in well under 60 seconds, all
        # timestamps still fall inside the minute window.
        assert limiter.available_minute + safe_n == per_minute


class TestFactoryProperty:
    """``get_fraser_rate_limiter`` honours config-supplied limits."""

    @given(
        per_minute=minute_limits,
        per_hour=hour_limits,
    )
    @settings(max_examples=100)
    def test_プロパティ_factoryが設定値の上限を継承(
        self,
        per_minute: int,
        per_hour: int,
    ) -> None:
        per_hour = max(per_hour, per_minute)
        config = FraserConfig(
            api_key="dummy",
            requests_per_minute=per_minute,
            requests_per_hour=per_hour,
        )
        limiter = get_fraser_rate_limiter(config)

        # Fresh limiter -> available counts equal the configured caps.
        assert limiter.available_minute == per_minute
        assert limiter.available_hour == per_hour


class TestNonNegativeWaitProperty:
    """``acquire()`` always returns a non-negative wait time."""

    @given(
        per_minute=minute_limits,
        per_hour=hour_limits,
    )
    @settings(max_examples=50)
    def test_プロパティ_acquire返り値は常に非負float(
        self,
        per_minute: int,
        per_hour: int,
    ) -> None:
        per_hour = max(per_hour, per_minute)
        limiter = DualWindowRateLimiter(
            requests_per_minute=per_minute,
            requests_per_hour=per_hour,
        )
        waited = limiter.acquire()
        assert isinstance(waited, float)
        assert waited >= 0.0

"""Unit tests for ``market.fraser.rate_limiter`` module.

Covers:

- ``DualWindowRateLimiter`` is re-exported from
  ``market.alphavantage.rate_limiter`` (identity check, not a copy).
- ``get_fraser_rate_limiter`` returns a ``DualWindowRateLimiter``
  instance configured with the per-minute / per-hour values from
  ``FraserConfig``.
- Acquired slots reduce ``available_minute`` / ``available_hour`` by
  one (sanity check for the underlying behaviour).
- Time-controlled blocking uses ``monkeypatch.setattr(time,
  "monotonic", ...)`` to verify the limiter blocks when full and
  unblocks when the window slides.
"""

import time
from collections.abc import Iterator

import pytest

from market.alphavantage.rate_limiter import (
    DualWindowRateLimiter as AlphaVantageDualWindowRateLimiter,
)
from market.fraser import rate_limiter as fraser_rate_limiter
from market.fraser.rate_limiter import (
    DualWindowRateLimiter,
    get_fraser_rate_limiter,
)
from market.fraser.types import FraserConfig


class TestReExport:
    """Tests verifying re-export semantics."""

    def test_正常系_DualWindowRateLimiterはalphavantageからの再エクスポート(
        self,
    ) -> None:
        """The re-exported class must be the *same* object."""
        assert DualWindowRateLimiter is AlphaVantageDualWindowRateLimiter

    def test_正常系_rate_limiterモジュールに新規実装なし(self) -> None:
        """``rate_limiter.py`` must not define its own limiter class.

        Confirms HF1 directive (re-use, no re-implementation).
        """
        assert "DualWindowRateLimiter" not in fraser_rate_limiter.__dict__ or (
            fraser_rate_limiter.DualWindowRateLimiter
            is AlphaVantageDualWindowRateLimiter
        )


class TestGetFraserRateLimiter:
    """Tests for ``get_fraser_rate_limiter``."""

    def test_正常系_戻り値型がDualWindowRateLimiter(self) -> None:
        config = FraserConfig(api_key="x")
        limiter = get_fraser_rate_limiter(config)
        assert isinstance(limiter, DualWindowRateLimiter)

    def test_正常系_デフォルトFraserConfigで30毎分1800毎時(self) -> None:
        config = FraserConfig(api_key="x")
        limiter = get_fraser_rate_limiter(config)
        assert limiter.available_minute == 30
        assert limiter.available_hour == 1800

    def test_正常系_カスタム設定が反映される(self) -> None:
        config = FraserConfig(
            api_key="x",
            requests_per_minute=10,
            requests_per_hour=600,
        )
        limiter = get_fraser_rate_limiter(config)
        assert limiter.available_minute == 10
        assert limiter.available_hour == 600


class TestAcquireBehaviour:
    """Tests for ``DualWindowRateLimiter.acquire`` behaviour through the factory."""

    def test_正常系_acquireで毎分残数が減少(self) -> None:
        config = FraserConfig(api_key="x", requests_per_minute=5, requests_per_hour=100)
        limiter = get_fraser_rate_limiter(config)

        waited = limiter.acquire()

        assert waited == pytest.approx(0.0, abs=1e-9)
        assert limiter.available_minute == 4
        assert limiter.available_hour == 99

    def test_正常系_複数回acquireで残数が正しく減少(self) -> None:
        config = FraserConfig(api_key="x", requests_per_minute=5, requests_per_hour=100)
        limiter = get_fraser_rate_limiter(config)

        for _ in range(3):
            assert limiter.acquire() == pytest.approx(0.0, abs=1e-9)

        assert limiter.available_minute == 2
        assert limiter.available_hour == 97


class TestTimeControlledBlocking:
    """Tests using ``monkeypatch.setattr(time, 'monotonic', ...)``."""

    @pytest.fixture
    def fake_clock(self, monkeypatch: pytest.MonkeyPatch) -> Iterator[list[float]]:
        """Provide a manually-controllable monotonic clock.

        Yields a mutable ``[current_time]`` list. The
        ``time.monotonic`` and ``time.sleep`` patches read / advance
        the first element. ``time.sleep(s)`` does not actually sleep
        – it simply moves the clock forward, keeping the test fast.
        """
        clock = [1000.0]

        def fake_monotonic() -> float:
            return clock[0]

        def fake_sleep(seconds: float) -> None:
            clock[0] += seconds

        monkeypatch.setattr(time, "monotonic", fake_monotonic)
        # ``DualWindowRateLimiter`` uses ``time.sleep`` from the
        # imported module reference; patch the same name on the
        # original alphavantage module so that the patched sleep is
        # picked up regardless of how the limiter resolves ``time``.
        monkeypatch.setattr("market.alphavantage.rate_limiter.time.sleep", fake_sleep)
        yield clock

    def test_正常系_毎分制限到達で待機が必要になる(
        self, fake_clock: list[float]
    ) -> None:
        """After consuming the per-minute quota, the limiter must block."""
        config = FraserConfig(api_key="x", requests_per_minute=2, requests_per_hour=100)
        limiter = get_fraser_rate_limiter(config)

        # Consume the two allowed slots at t=1000.
        assert limiter.acquire() == pytest.approx(0.0, abs=1e-9)
        assert limiter.acquire() == pytest.approx(0.0, abs=1e-9)

        # The third acquire should wait until t = 1000 + 60 = 1060.
        waited = limiter.acquire()
        assert waited == pytest.approx(60.0, abs=0.5)
        # The clock advanced by the wait amount.
        assert fake_clock[0] == pytest.approx(1060.0, abs=0.5)

    def test_正常系_時間経過後にスロットが回復する(
        self, fake_clock: list[float]
    ) -> None:
        """Advancing time past the minute window restores availability."""
        config = FraserConfig(api_key="x", requests_per_minute=2, requests_per_hour=100)
        limiter = get_fraser_rate_limiter(config)

        limiter.acquire()
        limiter.acquire()
        assert limiter.available_minute == 0

        # Advance the fake clock past the minute window.
        fake_clock[0] += 61.0
        assert limiter.available_minute == 2

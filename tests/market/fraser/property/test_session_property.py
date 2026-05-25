"""Property tests for ``FraserSession._calculate_backoff_delay``.

Asserts the two invariants the production retry path relies on:

1. ``delay >= 0`` — never schedules a sleep with a negative wait.
2. ``delay <= max_wait * 1.5`` — the jitter scale (`[0.5, 1.5)`) keeps
   the post-jitter delay bounded by 1.5 * the configured max_wait.

Together these prevent both negative sleeps (would raise on ``time.sleep``)
and runaway waits that exceed the retry config envelope.
"""

from __future__ import annotations

import random

from hypothesis import given, settings
from hypothesis import strategies as st

from market.fraser.session import FraserSession
from market.fraser.types import FraserConfig, RetryConfig


def _make_session(base_wait: float, max_wait: float) -> FraserSession:
    config = FraserConfig(
        api_key="dummy",
        retry_config=RetryConfig(
            max_attempts=5,
            base_wait=base_wait,
            max_wait=max_wait,
        ),
    )
    return FraserSession(config=config)


class TestCalculateBackoffDelayProperty:
    """Property tests for the exponential-backoff + jitter formula."""

    @given(
        attempt=st.integers(min_value=0, max_value=20),
        base_wait=st.floats(min_value=0.01, max_value=10.0, allow_nan=False),
        max_wait=st.floats(min_value=0.1, max_value=120.0, allow_nan=False),
        seed=st.integers(min_value=0, max_value=10_000),
    )
    @settings(max_examples=100)
    def test_プロパティ_delayは常に非負(
        self,
        attempt: int,
        base_wait: float,
        max_wait: float,
        seed: int,
    ) -> None:
        random.seed(seed)
        session = _make_session(base_wait=base_wait, max_wait=max_wait)

        delay = session._calculate_backoff_delay(attempt)

        assert delay >= 0.0
        session.close()

    @given(
        attempt=st.integers(min_value=0, max_value=20),
        base_wait=st.floats(min_value=0.01, max_value=10.0, allow_nan=False),
        max_wait=st.floats(min_value=0.1, max_value=120.0, allow_nan=False),
        seed=st.integers(min_value=0, max_value=10_000),
    )
    @settings(max_examples=100)
    def test_プロパティ_delayはmax_waitの1_5倍以下(
        self,
        attempt: int,
        base_wait: float,
        max_wait: float,
        seed: int,
    ) -> None:
        random.seed(seed)
        session = _make_session(base_wait=base_wait, max_wait=max_wait)

        delay = session._calculate_backoff_delay(attempt)

        # Jitter scales the capped value by [0.5, 1.5); the upper bound is
        # therefore < max_wait * 1.5. We compare against <= to tolerate
        # floating-point rounding.
        assert delay <= max_wait * 1.5 + 1e-9
        session.close()

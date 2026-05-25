"""Rate limiter for the FRASER REST API module.

This module re-exports ``DualWindowRateLimiter`` from
``market.alphavantage.rate_limiter`` to avoid duplicating the
dual-window sliding-window implementation. The
``get_fraser_rate_limiter`` factory constructs a limiter using values
from a ``FraserConfig`` instance, which keeps callers from having to
thread the per-minute / per-hour limits separately.

Notes
-----
The FRASER limiter is intentionally implemented as a thin wrapper
around the Alpha Vantage implementation. New token-bucket or
sliding-window code is not added here (HF1 confirmed re-use over
re-implementation).

See Also
--------
market.alphavantage.rate_limiter : Underlying ``DualWindowRateLimiter``
    implementation (timestamp-deque based, thread-safe).
market.fraser.types : ``FraserConfig`` definition referenced by the
    factory function.
"""

from market.alphavantage.rate_limiter import (
    AsyncDualWindowRateLimiter,
    DualWindowRateLimiter,
)
from market.fraser.types import FraserConfig


def get_fraser_rate_limiter(config: FraserConfig) -> DualWindowRateLimiter:
    """Construct a ``DualWindowRateLimiter`` from a ``FraserConfig``.

    Parameters
    ----------
    config : FraserConfig
        FRASER configuration carrying the per-minute and per-hour
        request limits.

    Returns
    -------
    DualWindowRateLimiter
        Limiter initialised with ``config.requests_per_minute`` and
        ``config.requests_per_hour``.

    Examples
    --------
    >>> from market.fraser.types import FraserConfig
    >>> limiter = get_fraser_rate_limiter(FraserConfig(api_key="x"))
    >>> limiter.available_minute
    30
    """
    return DualWindowRateLimiter(
        requests_per_minute=config.requests_per_minute,
        requests_per_hour=config.requests_per_hour,
    )


__all__ = [
    "AsyncDualWindowRateLimiter",
    "DualWindowRateLimiter",
    "get_fraser_rate_limiter",
]

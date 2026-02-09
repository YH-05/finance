"""Domain-based rate limiter for HTTP requests.

This module provides a DomainRateLimiter class that enforces per-domain
rate limiting for HTTP requests. This helps avoid being blocked by
anti-scraping measures and respects server resources.

Features
--------
- Per-domain minimum delay between consecutive requests
- Jitter (random additional delay) to avoid bot detection
- Session-fixed User-Agent assignment per domain
- Thread-safe with asyncio.Lock per domain

Examples
--------
>>> from news.extractors.rate_limiter import DomainRateLimiter
>>> limiter = DomainRateLimiter(min_delay=2.0, max_delay=5.0)
>>> await limiter.wait("https://www.cnbc.com/article/1")
>>> await limiter.wait("https://www.cnbc.com/article/2")  # waits 2-5s
"""

from __future__ import annotations

import asyncio
import hashlib
import random
import time
from urllib.parse import urlparse

from utils_core.logging import get_logger

logger = get_logger(__name__)


class DomainRateLimiter:
    """Domain-based rate limiter for HTTP requests.

    Enforces a minimum delay between consecutive requests to the same domain.
    An optional jitter (random additional delay) is added to avoid bot detection.

    Parameters
    ----------
    min_delay : float, optional
        Minimum delay in seconds between requests to the same domain.
        Default is 2.0.
    max_delay : float, optional
        Maximum delay in seconds (min_delay + jitter). Default is 5.0.

    Raises
    ------
    ValueError
        If min_delay is negative or min_delay > max_delay.

    Attributes
    ----------
    _last_request : dict[str, float]
        Mapping of domain to the monotonic timestamp of the last request.
    _domain_locks : dict[str, asyncio.Lock]
        Per-domain locks for thread-safe operation.
    _domain_user_agents : dict[str, str]
        Session-fixed User-Agent mapping per domain.

    Examples
    --------
    >>> limiter = DomainRateLimiter(min_delay=2.0, max_delay=5.0)
    >>> await limiter.wait("https://www.cnbc.com/article/1")
    >>> # First request - no delay
    >>> await limiter.wait("https://www.cnbc.com/article/2")
    >>> # Second request - waits 2-5 seconds
    """

    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
    ) -> None:
        """Initialize the DomainRateLimiter.

        Parameters
        ----------
        min_delay : float, optional
            Minimum delay in seconds between requests to the same domain.
            Default is 2.0.
        max_delay : float, optional
            Maximum delay in seconds (min_delay + jitter). Default is 5.0.

        Raises
        ------
        ValueError
            If min_delay is negative or min_delay > max_delay.
        """
        if min_delay < 0:
            msg = f"min_delay must be >= 0, got {min_delay}"
            raise ValueError(msg)
        if min_delay > max_delay:
            msg = f"min_delay must be <= max_delay, got min_delay={min_delay}, max_delay={max_delay}"
            raise ValueError(msg)

        self._min_delay = min_delay
        self._max_delay = max_delay
        self._last_request: dict[str, float] = {}
        self._domain_locks: dict[str, asyncio.Lock] = {}
        self._domain_user_agents: dict[str, str] = {}

    def _extract_domain(self, url: str) -> str:
        """Extract the domain (hostname) from a URL.

        Parameters
        ----------
        url : str
            The full URL to extract the domain from.

        Returns
        -------
        str
            The hostname portion of the URL.

        Examples
        --------
        >>> limiter = DomainRateLimiter()
        >>> limiter._extract_domain("https://www.cnbc.com/article/test")
        'www.cnbc.com'
        """
        parsed = urlparse(url)
        return parsed.hostname or ""

    def _get_domain_lock(self, domain: str) -> asyncio.Lock:
        """Get or create an asyncio.Lock for the given domain.

        Parameters
        ----------
        domain : str
            The domain to get the lock for.

        Returns
        -------
        asyncio.Lock
            The lock for the domain.
        """
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        return self._domain_locks[domain]

    async def wait(self, url: str) -> None:
        """Wait for rate limiting before making a request.

        Enforces a minimum delay between consecutive requests to the same
        domain. On the first request to a domain, no delay is applied.

        Parameters
        ----------
        url : str
            The URL about to be requested. The domain is extracted to
            determine rate limiting scope.

        Examples
        --------
        >>> limiter = DomainRateLimiter(min_delay=2.0, max_delay=5.0)
        >>> await limiter.wait("https://www.cnbc.com/article/1")  # no delay
        >>> await limiter.wait("https://www.cnbc.com/article/2")  # waits 2-5s
        """
        domain = self._extract_domain(url)
        if not domain:
            return

        lock = self._get_domain_lock(domain)
        async with lock:
            now = time.monotonic()
            last = self._last_request.get(domain)

            if last is not None:
                # Calculate required delay with jitter
                delay = self._min_delay
                if self._max_delay > self._min_delay:
                    delay += random.uniform(0, self._max_delay - self._min_delay)

                elapsed = now - last
                remaining = delay - elapsed

                if remaining > 0:
                    logger.debug(
                        "Rate limiting: waiting before request",
                        domain=domain,
                        delay_seconds=round(remaining, 2),
                    )
                    await asyncio.sleep(remaining)

            # Update last request time
            self._last_request[domain] = time.monotonic()

    def get_session_user_agent(
        self,
        domain: str,
        user_agents: list[str],
    ) -> str | None:
        """Get a session-fixed User-Agent for the given domain.

        Once a User-Agent is assigned to a domain, it remains fixed for the
        lifetime of this limiter instance. This avoids detection by servers
        that track User-Agent changes within a session.

        Parameters
        ----------
        domain : str
            The domain to get the User-Agent for.
        user_agents : list[str]
            List of available User-Agent strings to choose from.

        Returns
        -------
        str | None
            The assigned User-Agent, or None if the list is empty.

        Examples
        --------
        >>> limiter = DomainRateLimiter()
        >>> ua = limiter.get_session_user_agent("www.cnbc.com", ["UA1", "UA2"])
        >>> ua in ["UA1", "UA2"]
        True
        >>> # Same domain always returns same UA
        >>> limiter.get_session_user_agent("www.cnbc.com", ["UA1", "UA2"]) == ua
        True
        """
        if not user_agents:
            return None

        if domain in self._domain_user_agents:
            return self._domain_user_agents[domain]

        # Use domain hash for deterministic-but-varied assignment (not for security)
        domain_hash = hashlib.md5(domain.encode(), usedforsecurity=False).hexdigest()
        index = int(domain_hash, 16) % len(user_agents)
        ua = user_agents[index]

        self._domain_user_agents[domain] = ua
        logger.debug(
            "Assigned session User-Agent for domain",
            domain=domain,
            user_agent=ua[:50] + "..." if len(ua) > 50 else ua,
        )
        return ua


__all__ = ["DomainRateLimiter"]

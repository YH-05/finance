"""Scraping policy for bot-countermeasure: UA rotation, rate limiting, 429 retry.

Provides a unified policy object that handles:
1. User-Agent rotation with previous-UA avoidance
2. Domain-based rate limiting with asyncio.Lock mutual exclusion
3. HTTP 429 retry with Retry-After header support + exponential backoff

Designed for concurrent scraping of 70+ company blogs with responsible
request behavior.
"""

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="scraping_policy")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()

# ---------------------------------------------------------------------------
# Default User-Agent list (7 variants: Chrome, Firefox, Edge, Safari + custom)
# ---------------------------------------------------------------------------

DEFAULT_USER_AGENTS: list[str] = [
    # Chrome (Windows)
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    # Chrome (macOS)
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    # Firefox (Windows)
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    # Firefox (macOS)
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    # Edge (Windows)
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
    ),
    # Safari (macOS)
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.4 Safari/605.1.15"
    ),
    # Chrome (Linux)
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
]


def _extract_domain(url: str) -> str:
    """Extract domain from a URL.

    Parameters
    ----------
    url : str
        Full URL (e.g., "https://api.example.com/v1/data")

    Returns
    -------
    str
        Domain name (e.g., "api.example.com")
    """
    return urlparse(url).netloc


# ---------------------------------------------------------------------------
# ScrapingPolicy
# ---------------------------------------------------------------------------


class ScrapingPolicy:
    """Bot-countermeasure policy for responsible web scraping.

    Combines UA rotation, domain-based rate limiting, and 429 retry
    into a single policy object used by RobustScraper.

    Parameters
    ----------
    user_agents : list[str] | None
        Custom User-Agent strings. Defaults to DEFAULT_USER_AGENTS (7 variants).
    domain_rate_limits : dict[str, float] | None
        Per-domain minimum interval in seconds (e.g., {"openai.com": 5.0}).
    default_rate_limit : float
        Default rate limit for domains not in domain_rate_limits.
    max_retries : int
        Maximum number of retries on HTTP 429 responses.
    base_backoff : float
        Base backoff time in seconds for exponential backoff (doubles each retry).

    Raises
    ------
    ValueError
        If user_agents is an empty list.

    Examples
    --------
    >>> policy = ScrapingPolicy(
    ...     domain_rate_limits={"openai.com": 5.0, "nvidia.com": 3.0},
    ...     max_retries=3,
    ... )
    >>> ua = policy.get_user_agent()
    >>> await policy.wait_for_domain("openai.com")
    """

    def __init__(
        self,
        *,
        user_agents: list[str] | None = None,
        domain_rate_limits: dict[str, float] | None = None,
        default_rate_limit: float = 3.0,
        max_retries: int = 3,
        base_backoff: float = 2.0,
    ) -> None:
        if user_agents is not None and len(user_agents) == 0:
            msg = "user_agents must not be empty"
            raise ValueError(msg)

        self._user_agents = (
            list(user_agents) if user_agents else list(DEFAULT_USER_AGENTS)
        )
        self._previous_ua: str | None = None
        self._domain_rate_limits = (
            dict(domain_rate_limits) if domain_rate_limits else {}
        )
        self._default_rate_limit = default_rate_limit
        self._max_retries = max_retries
        self._base_backoff = base_backoff

        # Domain locks for mutual exclusion (created lazily per domain)
        self._domain_locks: dict[str, asyncio.Lock] = {}
        # Last request timestamps per domain
        self._domain_last_request: dict[str, float] = {}

        logger.debug(
            "ScrapingPolicy initialized",
            ua_count=len(self._user_agents),
            domain_limits=len(self._domain_rate_limits),
            default_rate_limit=self._default_rate_limit,
            max_retries=self._max_retries,
            base_backoff=self._base_backoff,
        )

    # -- Properties ----------------------------------------------------------

    @property
    def user_agents(self) -> list[str]:
        """List of User-Agent strings available for rotation."""
        return list(self._user_agents)

    @property
    def max_retries(self) -> int:
        """Maximum number of retries on HTTP 429."""
        return self._max_retries

    @property
    def base_backoff(self) -> float:
        """Base backoff time in seconds for exponential backoff."""
        return self._base_backoff

    # -- UA Rotation ---------------------------------------------------------

    def get_user_agent(self) -> str:
        """Return a random User-Agent, avoiding the previous one.

        When only one UA is available, always returns that UA.

        Returns
        -------
        str
            A User-Agent string different from the previously returned one.
        """
        if len(self._user_agents) == 1:
            ua = self._user_agents[0]
            self._previous_ua = ua
            return ua

        candidates = [ua for ua in self._user_agents if ua != self._previous_ua]
        ua = random.choice(candidates)
        self._previous_ua = ua
        logger.debug("UA selected", ua=ua[:50])
        return ua

    # -- Domain Rate Limiting ------------------------------------------------

    def _get_domain_lock(self, domain: str) -> asyncio.Lock:
        """Get or create an asyncio.Lock for the given domain.

        Parameters
        ----------
        domain : str
            Domain name.

        Returns
        -------
        asyncio.Lock
            Lock for the domain.
        """
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        return self._domain_locks[domain]

    def _get_rate_limit(self, domain: str) -> float:
        """Get the rate limit for a domain.

        Parameters
        ----------
        domain : str
            Domain name.

        Returns
        -------
        float
            Minimum interval in seconds between requests to this domain.
        """
        return self._domain_rate_limits.get(domain, self._default_rate_limit)

    @asynccontextmanager
    async def domain_lock(self, domain: str):
        """Async context manager for domain-level mutual exclusion.

        Ensures only one request to a given domain is in-flight at a time.

        Parameters
        ----------
        domain : str
            Domain name to lock.

        Yields
        ------
        None
        """
        lock = self._get_domain_lock(domain)
        async with lock:
            yield

    async def wait_for_domain(self, domain: str) -> None:
        """Wait until the rate limit for a domain has elapsed.

        On the first request to a domain, returns immediately.
        On subsequent requests, waits until the configured minimum interval
        has elapsed since the last request.

        Parameters
        ----------
        domain : str
            Domain name to rate-limit.
        """
        rate_limit = self._get_rate_limit(domain)
        now = time.monotonic()

        if domain in self._domain_last_request:
            elapsed = now - self._domain_last_request[domain]
            remaining = rate_limit - elapsed
            if remaining > 0:
                logger.debug(
                    "Rate limit wait",
                    domain=domain,
                    wait_seconds=remaining,
                )
                await asyncio.sleep(remaining)

        self._domain_last_request[domain] = time.monotonic()

    # -- 429 Retry -----------------------------------------------------------

    async def execute_with_retry(
        self,
        request_fn: Callable[[], Awaitable[Any]],
        url: str,
    ) -> Any:
        """Execute a request function with 429 retry and exponential backoff.

        Calls request_fn and if the response has status_code 429,
        retries up to max_retries times with exponential backoff.
        Respects the Retry-After header when present.

        Parameters
        ----------
        request_fn : Callable[[], Awaitable[Any]]
            Async function that returns a response object with
            ``status_code`` (int) and ``headers`` (dict) attributes.
        url : str
            The URL being requested (used for logging and error reporting).

        Returns
        -------
        Any
            The response object from request_fn.

        Raises
        ------
        RateLimitError
            If max_retries is exceeded and the server still returns 429.
        """
        from .types import RateLimitError

        domain = _extract_domain(url)
        response = await request_fn()

        for attempt in range(1, self._max_retries + 1):
            if response.status_code != 429:
                return response

            # Calculate wait time
            wait_time = self._calculate_wait_time(response, attempt)

            logger.warning(
                "429 rate limited, retrying",
                domain=domain,
                url=url,
                attempt=attempt,
                max_retries=self._max_retries,
                wait_seconds=wait_time,
            )

            await asyncio.sleep(wait_time)
            response = await request_fn()

        if response.status_code == 429:
            retry_after = self._parse_retry_after(response)
            raise RateLimitError(
                f"Max retries ({self._max_retries}) exceeded for {domain}",
                domain=domain,
                url=url,
                retry_after=retry_after,
            )

        return response

    def _calculate_wait_time(self, response: Any, attempt: int) -> float:
        """Calculate wait time from Retry-After header or exponential backoff.

        Parameters
        ----------
        response : Any
            Response object with headers dict.
        attempt : int
            Current retry attempt number (1-based).

        Returns
        -------
        float
            Number of seconds to wait before the next retry.
        """
        retry_after = self._parse_retry_after(response)
        if retry_after is not None:
            return retry_after

        # Exponential backoff: base * 2^(attempt-1)
        return self._base_backoff * (2 ** (attempt - 1))

    @staticmethod
    def _parse_retry_after(response: Any) -> float | None:
        """Parse the Retry-After header value.

        Parameters
        ----------
        response : Any
            Response object with headers dict.

        Returns
        -------
        float | None
            Parsed delay in seconds, or None if header is absent or invalid.
        """
        retry_after_str = response.headers.get("Retry-After")
        if retry_after_str is None:
            return None

        try:
            return float(retry_after_str)
        except (ValueError, TypeError):
            logger.debug(
                "Invalid Retry-After header, ignoring",
                retry_after=retry_after_str,
            )
            return None

"""HTTP session abstraction for NSE API access.

This module provides the ``NseSession`` class, an httpx-based HTTP session
with User-Agent rotation, polite delays (monotonic-clock-based),
SSRF prevention via host whitelist, NSE-specific Cookie lifecycle management
(5-minute TTL + monotonic-clock + 403 auto-refresh), and exponential
backoff retry logic.

The design integrates patterns from:

- ``market.bse.session.BseSession`` (polite delay, retry, SSRF prevention)
- NSE cookie-based session: requires visiting the home page before API calls.

Notes
-----
NSE uses a cookie-based authentication mechanism.  Before any API request
can succeed, a GET request must be sent to ``BASE_URL`` (the NSE home page)
to obtain session cookies.  Cookies expire after approximately
``COOKIE_REFRESH_INTERVAL`` seconds (300 s = 5 minutes).

The ``_ensure_cookies()`` method handles cookie acquisition and TTL-based
refresh automatically.  When a 403 response is received during an API call,
``_handle_response()`` raises ``NseCookieError``, which is caught by
``get_with_retry()`` to force a cookie refresh before retrying.

Examples
--------
Basic GET usage:

>>> with NseSession() as session:
...     response = session.get(
...         "https://www.nseindia.com/api/equity-stockIndices",
...         params={"index": "NIFTY 50"},
...     )
...     print(response.status_code)
200

With retry:

>>> with NseSession() as session:
...     response = session.get_with_retry(
...         "https://www.nseindia.com/api/quote-equity",
...         params={"symbol": "RELIANCE"},
...     )

See Also
--------
market.bse.session : httpx-based session reference implementation.
market.nse.constants : Default values, allowed hosts, headers, and cookie TTL.
market.nse.types : NseConfig and RetryConfig dataclasses.
market.nse.errors : NseCookieError, NseRateLimitError, NseAPIError exceptions.
"""

import random
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from market.nse.constants import (
    ALLOWED_HOSTS,
    BASE_URL,
    DEFAULT_HEADERS,
    DEFAULT_USER_AGENTS,
)
from market.nse.errors import NseAPIError, NseCookieError, NseRateLimitError
from market.nse.types import NseConfig, RetryConfig
from utils_core.logging import get_logger

logger = get_logger(__name__)

# HTTP status code indicating rate limiting
_RATE_LIMIT_STATUS_CODE = 429

# Maximum length of response body stored in NseAPIError (CWE-209 mitigation)
_MAX_RESPONSE_BODY_LOG = 200


class NseSession:
    """httpx-based HTTP session for NSE API with Cookie lifecycle management.

    Provides User-Agent rotation, polite delays between requests
    (using ``time.monotonic()`` to measure elapsed time), SSRF
    prevention via host whitelist, NSE-specific Cookie lifecycle
    management (5-minute TTL + 403 auto-refresh), response status
    handling (403 -> ``NseCookieError``, 429 -> ``NseRateLimitError``,
    5xx -> ``NseAPIError``), and exponential backoff retry logic.

    Cookie Lifecycle
    ----------------
    NSE requires a valid session cookie obtained by visiting ``BASE_URL``
    (the NSE home page) before any API request.  The session automatically:

    1. Acquires cookies on the first API request via ``_ensure_cookies()``.
    2. Refreshes cookies when the TTL (``cookie_refresh_interval`` seconds,
       default 300 s) has elapsed since the last acquisition.
    3. Forces a cookie refresh and retries when a 403 response is received
       during ``get_with_retry()``.

    Parameters
    ----------
    config : NseConfig | None
        NSE configuration.  If ``None``, defaults are used.
    retry_config : RetryConfig | None
        Retry configuration.  If ``None``, defaults are used.

    Attributes
    ----------
    _config : NseConfig
        The NSE configuration.
    _retry_config : RetryConfig
        The retry configuration.
    _client : httpx.Client
        The underlying httpx client instance (``follow_redirects=True``).
    _user_agents : list[str]
        User-Agent strings for rotation.
    _last_request_time : float
        Monotonic timestamp of the last request (for polite delay).
    _cookie_acquired_at : float
        Monotonic timestamp when the session cookie was last acquired.
        ``0.0`` means no cookie has been acquired yet.

    Examples
    --------
    >>> session = NseSession()
    >>> response = session.get(
    ...     "https://www.nseindia.com/api/equity-stockIndices",
    ...     params={"index": "NIFTY 50"},
    ... )
    >>> session.close()

    >>> with NseSession() as session:
    ...     response = session.get_with_retry(
    ...         "https://www.nseindia.com/api/quote-equity",
    ...         params={"symbol": "RELIANCE"},
    ...     )
    """

    def __init__(
        self,
        config: NseConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize NseSession with configuration.

        Parameters
        ----------
        config : NseConfig | None
            NSE configuration. Defaults to ``NseConfig()``.
        retry_config : RetryConfig | None
            Retry configuration. Defaults to ``RetryConfig()``.
        """
        self._config: NseConfig = config or NseConfig()
        self._retry_config: RetryConfig = retry_config or RetryConfig()
        self._last_request_time: float = 0.0
        self._cookie_acquired_at: float = 0.0

        # Resolve user agents: use config value or fall back to defaults
        self._user_agents: list[str] = (
            list(self._config.user_agents)
            if self._config.user_agents
            else list(DEFAULT_USER_AGENTS)
        )

        # Create httpx client with timeout, SSL verification, and redirect following
        self._client: httpx.Client = httpx.Client(
            timeout=httpx.Timeout(self._config.timeout),
            verify=True,
            follow_redirects=True,
        )

        logger.info(
            "NseSession initialized",
            polite_delay=self._config.polite_delay,
            delay_jitter=self._config.delay_jitter,
            timeout=self._config.timeout,
            cookie_refresh_interval=self._config.cookie_refresh_interval,
            max_retry_attempts=self._retry_config.max_attempts,
        )

    # =========================================================================
    # Public API
    # =========================================================================

    def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Send a GET request with Cookie management, polite delay, and header rotation.

        Applies the following before each request:

        1. URL whitelist validation (SSRF prevention)
        2. Cookie acquisition / refresh (``_ensure_cookies()``)
        3. Polite delay (monotonic-clock-based interval control)
        4. Random User-Agent header selection
        5. Default browser-like headers

        After receiving a response, checks for error status codes:

        - 403 -> ``NseCookieError`` (cookie expired or invalid)
        - 429 -> ``NseRateLimitError``
        - 5xx -> ``NseAPIError``

        Parameters
        ----------
        url : str
            The URL to send the GET request to.
        params : dict[str, str] | None
            Optional query parameters for the request.

        Returns
        -------
        httpx.Response
            The HTTP response object.

        Raises
        ------
        ValueError
            If the URL host is not in the allowed hosts whitelist.
        NseCookieError
            If the response status code is 403 (cookie expired).
        NseRateLimitError
            If the response status code is 429.
        NseAPIError
            If the response status code is 5xx.

        Examples
        --------
        >>> response = session.get(
        ...     "https://www.nseindia.com/api/equity-stockIndices",
        ...     params={"index": "NIFTY 50"},
        ... )
        >>> response.status_code
        200
        """
        # 0. URL whitelist validation (SSRF prevention, CWE-918)
        self._validate_url(url)

        # 1. Ensure valid session cookies
        self._ensure_cookies()

        # 2. Apply polite delay (monotonic-clock-based)
        self._polite_delay()

        # 3. Build headers with User-Agent rotation
        user_agent = self._rotate_user_agent()
        headers: dict[str, str] = {
            **DEFAULT_HEADERS,
            "User-Agent": user_agent,
        }

        logger.debug(
            "Sending GET request",
            url=url,
            user_agent=user_agent[:50],
        )

        # 4. Execute request
        response: httpx.Response = self._client.get(
            url,
            headers=headers,
            params=params,
            timeout=self._config.timeout,
        )

        # 5. Handle response status
        self._handle_response(response, url)

        logger.debug(
            "GET request completed",
            url=url,
            status_code=response.status_code,
        )
        return response

    def get_with_retry(
        self,
        url: str,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Send a GET request with exponential backoff retry.

        On each failed attempt:

        - ``NseRateLimitError`` (429): retried after exponentially increasing delay.
        - ``NseCookieError`` (403): cookie is refreshed (``_cookie_acquired_at``
          reset to 0.0 to force re-acquisition on next ``_ensure_cookies()``
          call) and the request is retried immediately (without backoff delay).

        Parameters
        ----------
        url : str
            The URL to send the GET request to.
        params : dict[str, str] | None
            Optional query parameters for the request.

        Returns
        -------
        httpx.Response
            The HTTP response object.

        Raises
        ------
        NseRateLimitError
            If all retry attempts fail due to rate limiting.
        NseCookieError
            If all retry attempts fail due to cookie errors.

        Examples
        --------
        >>> response = session.get_with_retry(
        ...     "https://www.nseindia.com/api/equity-stockIndices",
        ...     params={"index": "NIFTY 50"},
        ... )
        >>> response.status_code
        200
        """
        last_error: NseRateLimitError | NseCookieError | None = None

        for attempt in range(self._retry_config.max_attempts):
            try:
                response = self.get(url, params=params)

                if attempt > 0:
                    logger.info(
                        "Request succeeded after retry",
                        url=url,
                        attempt=attempt + 1,
                    )
                return response

            except NseCookieError as e:
                last_error = e
                logger.warning(
                    "Cookie error detected, refreshing cookies and retrying",
                    url=url,
                    attempt=attempt + 1,
                    max_attempts=self._retry_config.max_attempts,
                )
                # Force cookie re-acquisition on next _ensure_cookies() call
                self._cookie_acquired_at = 0.0
                # Immediately retry (no backoff for cookie refresh)
                continue

            except NseRateLimitError as e:
                last_error = e
                logger.warning(
                    "Request rate-limited, will retry",
                    url=url,
                    attempt=attempt + 1,
                    max_attempts=self._retry_config.max_attempts,
                )

                # If this is not the last attempt, apply backoff
                if attempt < self._retry_config.max_attempts - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.debug(
                        "Backoff before retry",
                        delay_seconds=delay,
                        next_attempt=attempt + 2,
                    )
                    time.sleep(delay)

        # All attempts exhausted
        logger.error(
            "All retry attempts failed",
            url=url,
            max_attempts=self._retry_config.max_attempts,
        )
        if last_error is None:
            raise NseAPIError(
                message="All retry attempts failed with no recorded error",
                url=url,
                status_code=0,
                response_body="",
            )
        raise last_error

    # =========================================================================
    # Context Manager
    # =========================================================================

    def close(self) -> None:
        """Close the session and release resources.

        Examples
        --------
        >>> session.close()
        """
        self._client.close()
        logger.debug("NseSession closed")

    def __enter__(self) -> "NseSession":
        """Support context manager protocol.

        Returns
        -------
        NseSession
            Self for use in with statement.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Close session on context exit.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if an exception was raised.
        exc_val : BaseException | None
            Exception instance if an exception was raised.
        exc_tb : Any
            Traceback if an exception was raised.
        """
        self.close()

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _ensure_cookies(self) -> None:
        """Acquire or refresh the NSE session cookie.

        Sends a GET request to ``BASE_URL`` (the NSE home page) to obtain
        session cookies.  The request is skipped when a valid cookie already
        exists (i.e., ``time.monotonic() - _cookie_acquired_at`` is less than
        ``config.cookie_refresh_interval``).

        After a successful cookie acquisition, ``_cookie_acquired_at`` is
        updated to the current monotonic clock value.

        Notes
        -----
        This method does *not* validate the cookie or check the response
        body—it relies on the httpx cookie jar being populated automatically
        by the home-page response.
        """
        now = time.monotonic()
        elapsed_since_cookie = now - self._cookie_acquired_at

        if (
            self._cookie_acquired_at > 0.0
            and elapsed_since_cookie < self._config.cookie_refresh_interval
        ):
            # Cookie is still valid; no refresh needed
            logger.debug(
                "Cookie still valid, skipping refresh",
                elapsed_seconds=elapsed_since_cookie,
                ttl=self._config.cookie_refresh_interval,
            )
            return

        logger.info(
            "Acquiring NSE session cookies",
            reason="initial" if self._cookie_acquired_at == 0.0 else "ttl_expired",
        )

        # Apply polite delay before cookie request to avoid rate limiting
        self._polite_delay()
        response = self._client.get(BASE_URL)

        if response.status_code not in range(200, 300):
            logger.warning(
                "Cookie acquisition failed, skipping cookie update",
                status_code=response.status_code,
            )
            return

        self._cookie_acquired_at = time.monotonic()

        logger.info(
            "NSE session cookies acquired",
            status_code=response.status_code,
        )

    def _validate_url(self, url: str) -> None:
        """Validate URL against the allowed hosts whitelist (SSRF prevention).

        Parameters
        ----------
        url : str
            The URL to validate.

        Raises
        ------
        ValueError
            If the URL host is not in ``ALLOWED_HOSTS``.
        """
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"URL scheme must be 'http' or 'https', got '{parsed.scheme}'"
            )
        parsed_host = parsed.netloc
        if parsed_host not in ALLOWED_HOSTS:
            logger.warning(
                "Request blocked: host not in allowed hosts",
                url=url,
                host=parsed_host,
                allowed_hosts=list(ALLOWED_HOSTS),
            )
            raise ValueError(
                f"Host '{parsed_host}' is not in allowed hosts: {sorted(ALLOWED_HOSTS)}"
            )

    def _polite_delay(self) -> None:
        """Apply polite delay between consecutive requests.

        Uses ``time.monotonic()`` to measure elapsed time since the
        last request.  Sleeps for the remaining delay if not enough
        time has passed.  Adds random jitter to appear more human-like.
        """
        now = time.monotonic()

        if self._last_request_time > 0:
            elapsed = now - self._last_request_time
            required_delay = self._config.polite_delay + random.uniform(  # nosec B311 (cryptographic randomness not required for delay jitter)
                0, self._config.delay_jitter
            )
            remaining = required_delay - elapsed
            if remaining > 0:
                time.sleep(remaining)
                logger.debug("Polite delay applied", delay_seconds=remaining)

        self._last_request_time = time.monotonic()

    def _rotate_user_agent(self) -> str:
        """Select a random User-Agent string for rotation.

        Returns
        -------
        str
            A randomly selected User-Agent string.
        """
        return random.choice(self._user_agents)  # nosec B311 (cryptographic randomness not required for UA rotation)

    def _handle_response(self, response: httpx.Response, url: str) -> None:
        """Check response status and raise appropriate exceptions.

        Parameters
        ----------
        response : httpx.Response
            The HTTP response to check.
        url : str
            The request URL for error context.

        Raises
        ------
        NseCookieError
            If HTTP 403 is returned (cookie expired or invalid).
        NseRateLimitError
            If HTTP 429 is returned.
        NseAPIError
            If HTTP 5xx is returned.
        """
        status = response.status_code

        # 403: cookie expired / bot block — NSE returns 403 when cookie is invalid
        if status == 403:
            logger.warning(
                "Access forbidden - NSE cookie may have expired",
                url=url,
                status_code=status,
            )
            raise NseCookieError(
                message=f"NSE session cookie expired or invalid: HTTP {status}",
                url=url,
            )

        # 429: rate limit
        if status == _RATE_LIMIT_STATUS_CODE:
            logger.warning(
                "Rate limit detected",
                url=url,
                status_code=status,
            )
            raise NseRateLimitError(
                message=f"Rate limit detected: HTTP {status}",
                url=url,
                retry_after=None,
            )

        # 5xx: server error
        if status >= 500:
            logger.warning(
                "Server error",
                url=url,
                status_code=status,
            )
            raise NseAPIError(
                message=f"Server error: HTTP {status}",
                url=url,
                status_code=status,
                response_body=response.text[:_MAX_RESPONSE_BODY_LOG],
            )

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay.

        Parameters
        ----------
        attempt : int
            Current attempt number (0-indexed).

        Returns
        -------
        float
            Delay in seconds.
        """
        delay = min(
            self._retry_config.initial_delay
            * (self._retry_config.exponential_base**attempt),
            self._retry_config.max_delay,
        )
        if self._retry_config.jitter:
            delay *= 0.5 + random.random()  # nosec B311 (cryptographic randomness not required for retry jitter)
        return delay


__all__ = ["NseSession"]

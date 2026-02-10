"""HTTP session abstraction for NASDAQ API access with bot-blocking countermeasures.

This module provides the ``NasdaqSession`` class, a curl_cffi-based HTTP session
with TLS fingerprint impersonation, User-Agent rotation, polite delays,
bot-block detection, and exponential backoff retry logic.

The session supports only GET requests, as the NASDAQ Screener API is read-only.

Examples
--------
Basic GET usage:

>>> with NasdaqSession() as session:
...     response = session.get("https://api.nasdaq.com/api/screener/stocks")
...     print(response.status_code)
200

With retry:

>>> with NasdaqSession() as session:
...     response = session.get_with_retry(
...         "https://api.nasdaq.com/api/screener/stocks",
...         params={"exchange": "nasdaq", "limit": "0"},
...     )
...     print(response.status_code)
200

See Also
--------
market.etfcom.session : Similar session pattern for ETF.com module.
market.nasdaq.constants : Default values, impersonation targets, and headers.
market.nasdaq.types : NasdaqConfig and RetryConfig dataclasses.
market.nasdaq.errors : NasdaqRateLimitError for rate limit detection.
"""

import random
import time
from typing import Any, cast

from curl_cffi import requests as curl_requests
from curl_cffi.requests import BrowserTypeLiteral

from market.nasdaq.constants import (
    BROWSER_IMPERSONATE_TARGETS,
    DEFAULT_HEADERS,
    DEFAULT_USER_AGENTS,
    NASDAQ_SCREENER_URL,
)
from market.nasdaq.errors import NasdaqRateLimitError
from market.nasdaq.types import NasdaqConfig, RetryConfig
from utils_core.logging import get_logger

logger = get_logger(__name__)

# HTTP status codes indicating rate limiting / bot blocking
_BLOCKED_STATUS_CODES: frozenset[int] = frozenset({403, 429})


class NasdaqSession:
    """curl_cffi-based HTTP session with bot-blocking countermeasures.

    Provides TLS fingerprint impersonation via curl_cffi's ``impersonate``
    parameter, random User-Agent rotation, polite delays between requests,
    rate limit detection (HTTP 403/429), and exponential backoff retry logic
    with session rotation on failure.

    Only GET requests are supported, as the NASDAQ Screener API is read-only.

    Parameters
    ----------
    config : NasdaqConfig | None
        NASDAQ configuration. If None, defaults are used.
    retry_config : RetryConfig | None
        Retry configuration. If None, defaults are used.

    Attributes
    ----------
    _config : NasdaqConfig
        The NASDAQ configuration.
    _retry_config : RetryConfig
        The retry configuration.
    _session : curl_requests.Session
        The underlying curl_cffi session instance.
    _user_agents : list[str]
        User-Agent strings for rotation.

    Examples
    --------
    >>> session = NasdaqSession()
    >>> response = session.get("https://api.nasdaq.com/api/screener/stocks")
    >>> session.close()

    >>> with NasdaqSession() as session:
    ...     response = session.get_with_retry(
    ...         "https://api.nasdaq.com/api/screener/stocks",
    ...         params={"exchange": "nasdaq"},
    ...     )
    """

    def __init__(
        self,
        config: NasdaqConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize NasdaqSession with configuration.

        Parameters
        ----------
        config : NasdaqConfig | None
            NASDAQ configuration. Defaults to ``NasdaqConfig()``.
        retry_config : RetryConfig | None
            Retry configuration. Defaults to ``RetryConfig()``.
        """
        self._config: NasdaqConfig = config or NasdaqConfig()
        self._retry_config: RetryConfig = retry_config or RetryConfig()

        # Resolve user agents: use config value or fall back to defaults
        self._user_agents: list[str] = (
            list(self._config.user_agents)
            if self._config.user_agents
            else list(DEFAULT_USER_AGENTS)
        )

        # Create curl_cffi session with TLS fingerprint impersonation
        self._session: curl_requests.Session = curl_requests.Session(
            impersonate=cast("BrowserTypeLiteral", self._config.impersonate),
        )

        logger.info(
            "NasdaqSession initialized",
            impersonate=self._config.impersonate,
            polite_delay=self._config.polite_delay,
            delay_jitter=self._config.delay_jitter,
            timeout=self._config.timeout,
            max_retry_attempts=self._retry_config.max_attempts,
        )

    def get(
        self, url: str, params: dict[str, str] | None = None, **kwargs: Any
    ) -> curl_requests.Response:
        """Send a GET request with polite delay, header rotation, and block detection.

        Applies the following before each request:

        1. Polite delay (``config.polite_delay`` + random jitter)
        2. Random User-Agent header selection
        3. Referer header set to ``NASDAQ_SCREENER_URL``
        4. Default browser-like headers from ``DEFAULT_HEADERS``

        After receiving a response, checks for rate-limiting status codes
        (403, 429) and raises ``NasdaqRateLimitError`` if detected.

        Parameters
        ----------
        url : str
            The URL to send the GET request to.
        params : dict[str, str] | None
            Optional query parameters for the request.
        **kwargs : Any
            Additional keyword arguments passed to
            ``curl_cffi.Session.request()``.

        Returns
        -------
        curl_requests.Response
            The HTTP response object.

        Raises
        ------
        NasdaqRateLimitError
            If the response status code is 403 or 429.

        Examples
        --------
        >>> response = session.get(
        ...     "https://api.nasdaq.com/api/screener/stocks",
        ...     params={"exchange": "nasdaq", "limit": "0"},
        ... )
        >>> response.status_code
        200
        """
        # 1. Apply polite delay
        delay = self._config.polite_delay + random.uniform(  # nosec B311
            0, self._config.delay_jitter
        )
        time.sleep(delay)
        logger.debug("Polite delay applied", delay_seconds=delay, url=url)

        # 2. Build headers with User-Agent rotation and Referer
        user_agent = random.choice(self._user_agents)  # nosec B311
        headers: dict[str, str] = {
            **DEFAULT_HEADERS,
            "User-Agent": user_agent,
            "Referer": NASDAQ_SCREENER_URL,
        }

        # Merge any caller-provided headers
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        logger.debug(
            "Sending GET request",
            url=url,
            user_agent=user_agent[:50],
        )

        # 3. Execute request
        response: curl_requests.Response = self._session.request(
            "GET",
            url,
            headers=headers,
            params=params,
            timeout=self._config.timeout,
            **kwargs,
        )

        # 4. Check for rate limiting / bot blocking
        if response.status_code in _BLOCKED_STATUS_CODES:
            logger.warning(
                "Rate limit detected",
                url=url,
                status_code=response.status_code,
            )
            raise NasdaqRateLimitError(
                f"Rate limit detected: HTTP {response.status_code}",
                url=url,
                retry_after=None,
            )

        logger.debug(
            "GET request completed",
            url=url,
            status_code=response.status_code,
        )
        return response

    def get_with_retry(
        self, url: str, params: dict[str, str] | None = None, **kwargs: Any
    ) -> curl_requests.Response:
        """Send a GET request with exponential backoff retry and session rotation.

        On each failed attempt (``NasdaqRateLimitError``), the session is
        rotated to a new TLS fingerprint via ``rotate_session()`` and the
        request is retried after an exponentially increasing delay.

        Parameters
        ----------
        url : str
            The URL to send the GET request to.
        params : dict[str, str] | None
            Optional query parameters for the request.
        **kwargs : Any
            Additional keyword arguments passed to ``get()``.

        Returns
        -------
        curl_requests.Response
            The HTTP response object.

        Raises
        ------
        NasdaqRateLimitError
            If all retry attempts fail due to rate limiting.

        Examples
        --------
        >>> response = session.get_with_retry(
        ...     "https://api.nasdaq.com/api/screener/stocks",
        ...     params={"exchange": "nasdaq", "limit": "0"},
        ... )
        >>> response.status_code
        200
        """
        last_error: NasdaqRateLimitError | None = None

        for attempt in range(self._retry_config.max_attempts):
            try:
                response = self.get(url, params=params, **kwargs)

                if attempt > 0:
                    logger.info(
                        "Request succeeded after retry",
                        url=url,
                        attempt=attempt + 1,
                    )
                return response

            except NasdaqRateLimitError as e:
                last_error = e
                logger.warning(
                    "Request rate-limited, will retry",
                    url=url,
                    attempt=attempt + 1,
                    max_attempts=self._retry_config.max_attempts,
                )

                # If this is not the last attempt, apply backoff and rotate
                if attempt < self._retry_config.max_attempts - 1:
                    # Calculate exponential backoff delay
                    delay = min(
                        self._retry_config.initial_delay
                        * (self._retry_config.exponential_base**attempt),
                        self._retry_config.max_delay,
                    )

                    # Add jitter if configured
                    if self._retry_config.jitter:
                        delay *= 0.5 + random.random()  # nosec B311

                    logger.debug(
                        "Backoff before retry",
                        delay_seconds=delay,
                        next_attempt=attempt + 2,
                    )
                    time.sleep(delay)

                    # Rotate browser fingerprint
                    self.rotate_session()

        # All attempts exhausted
        logger.error(
            "All retry attempts failed",
            url=url,
            max_attempts=self._retry_config.max_attempts,
        )
        assert last_error is not None
        raise last_error

    def rotate_session(self) -> None:
        """Rotate to a new browser impersonation target.

        Closes the current curl_cffi session and creates a new one with
        a randomly selected browser impersonation target from
        ``BROWSER_IMPERSONATE_TARGETS``.

        Examples
        --------
        >>> session.rotate_session()
        """
        self._session.close()

        new_target: str = random.choice(BROWSER_IMPERSONATE_TARGETS)  # nosec B311
        self._session = curl_requests.Session(
            impersonate=cast("BrowserTypeLiteral", new_target),
        )

        logger.info(
            "Session rotated",
            new_impersonate=new_target,
        )

    def close(self) -> None:
        """Close the session and release resources.

        Examples
        --------
        >>> session.close()
        """
        self._session.close()
        logger.debug("NasdaqSession closed")

    def __enter__(self) -> "NasdaqSession":
        """Support context manager protocol.

        Returns
        -------
        NasdaqSession
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


__all__ = ["NasdaqSession"]

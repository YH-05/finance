"""HTTP session abstraction for FRASER REST API access.

This module provides the :class:`FraserSession` class, an httpx-based HTTP
session with X-API-Key header authentication, polite delays
(monotonic-clock-based), SSRF prevention via host whitelist, rate limiter
integration, and exponential backoff retry logic.

Unlike Alpha Vantage, FRASER uses standard HTTP status codes to signal
errors (no HTTP 200 + JSON error body pattern). The HTTP 429 response is
expected to include a ``Retry-After`` header whose value is parsed and
attached to the raised :class:`FraserRateLimitError`.

See Also
--------
market.alphavantage.session : Reference implementation (1:1 adapted with
    three FRASER-specific modifications applied).
market.fraser.constants : Default values, allowed hosts.
market.fraser.types : :class:`FraserConfig`, :class:`RetryConfig`
    dataclasses.
market.fraser.errors : :class:`FraserAuthError`, :class:`FraserAPIError`,
    :class:`FraserRateLimitError`, :class:`FraserNotFoundError`,
    :class:`FraserValidationError` exceptions.
market.fraser.rate_limiter : :class:`DualWindowRateLimiter` for request
    throttling.
"""

from __future__ import annotations

import os
import random
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse, urlsplit

import httpx

from market.fraser.constants import (
    ALLOWED_HOSTS,
    BASE_URL,
    FRASER_API_KEY_ENV,
    MAX_RESPONSE_BODY_LOG,
)
from market.fraser.errors import (
    FraserAPIError,
    FraserAuthError,
    FraserNotFoundError,
    FraserRateLimitError,
    FraserValidationError,
)
from market.fraser.rate_limiter import DualWindowRateLimiter
from market.fraser.types import FraserConfig, RetryConfig
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = get_logger(__name__)

# HTTP status code indicating rate limiting
_RATE_LIMIT_STATUS_CODE = 429
# HTTP status codes indicating authentication / authorisation failure
_AUTH_ERROR_STATUS_CODES = frozenset({401, 403})
# HTTP status code indicating resource not found
_NOT_FOUND_STATUS_CODE = 404

# Default polite delay (seconds) — FRASER does not document a minimum, so we
# use a conservative value compatible with 30 req/min (2 s/request).
_DEFAULT_POLITE_DELAY = 2.0
# Default jitter (seconds) — small random offset to avoid synchronised bursts.
_DEFAULT_DELAY_JITTER = 0.5


class FraserSession:
    """httpx-based HTTP session for the FRASER REST API.

    Provides X-API-Key header authentication, SSRF prevention via host
    whitelist (``fraser.stlouisfed.org`` only), HTTPS enforcement, polite
    delays between requests (using :func:`time.monotonic`),
    :class:`DualWindowRateLimiter` integration (30 req/min default), 429
    ``Retry-After`` honouring, and exponential backoff retry logic.

    Parameters
    ----------
    config : FraserConfig | None
        FRASER configuration. If ``None``, :class:`FraserConfig` defaults
        are used. The API key falls back to ``FRASER_API_KEY``
        environment variable when ``config.api_key`` is empty.
    rate_limiter : DualWindowRateLimiter | None
        Dual-window rate limiter. If ``None``, a fresh limiter is
        constructed from ``config.requests_per_minute`` and
        ``config.requests_per_hour``.
    retry_config : RetryConfig | None
        Retry configuration. If ``None``, ``config.retry_config`` is used.

    Examples
    --------
    >>> with FraserSession() as session:  # doctest: +SKIP
    ...     response = session.get_with_retry(
    ...         "/items",
    ...         params={"titleId": 677, "limit": 1},
    ...     )
    ...     data = response.json()
    """

    def __init__(
        self,
        config: FraserConfig | None = None,
        rate_limiter: DualWindowRateLimiter | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialise :class:`FraserSession` with configuration.

        Parameters
        ----------
        config : FraserConfig | None
            FRASER configuration. Defaults to ``FraserConfig()``.
        rate_limiter : DualWindowRateLimiter | None
            Optional pre-built rate limiter. When ``None``, a fresh
            limiter is constructed from ``config.requests_per_minute``
            and ``config.requests_per_hour``.
        retry_config : RetryConfig | None
            Optional retry configuration. When ``None``, the value of
            ``config.retry_config`` is used.
        """
        self._config: FraserConfig = config or FraserConfig()
        self._retry_config: RetryConfig = retry_config or self._config.retry_config
        self._last_request_time: float = 0.0

        # Initialize rate limiter with config values (or accept injected one)
        self._rate_limiter: DualWindowRateLimiter = (
            rate_limiter
            if rate_limiter is not None
            else DualWindowRateLimiter(
                requests_per_minute=self._config.requests_per_minute,
                requests_per_hour=self._config.requests_per_hour,
            )
        )

        # Resolve the API key once per session so repeated requests do
        # not hit ``os.environ.get`` on every call (PR review LOW perf).
        # ``_resolve_api_key`` raises ``FraserAuthError`` when missing,
        # turning a hot-path error into a clear startup failure.
        self._resolved_api_key: str = self._resolve_api_key()

        # Create httpx client with timeout and explicit SSL verification
        self._client: httpx.Client = httpx.Client(
            timeout=httpx.Timeout(self._config.timeout),
            verify=True,
        )

        logger.info(
            "FraserSession initialized",
            timeout=self._config.timeout,
            requests_per_minute=self._config.requests_per_minute,
            requests_per_hour=self._config.requests_per_hour,
            max_retry_attempts=self._retry_config.max_attempts,
            base_url=self._config.base_url,
        )

    # =========================================================================
    # Public API
    # =========================================================================

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send a GET request with X-API-Key header injection.

        Applies the following before each request:

        1. URL construction (``base_url + path`` when ``path`` is relative).
        2. URL whitelist + HTTPS validation (SSRF prevention, CWE-918).
        3. API key resolution and X-API-Key header injection.
        4. Rate limiter acquisition.
        5. Polite delay (monotonic-clock-based interval control).
        6. HTTP request execution.
        7. Response status code error mapping.

        Parameters
        ----------
        path : str
            API endpoint path (e.g. ``"/items"``) or absolute URL.
            Relative paths are joined to ``config.base_url``.
        params : dict[str, Any] | None
            Optional query parameters for the request.

        Returns
        -------
        httpx.Response
            The HTTP response object.

        Raises
        ------
        FraserValidationError
            If the URL host is not in :data:`ALLOWED_HOSTS` or the scheme
            is not ``https``.
        FraserAuthError
            If the API key is missing or the API returns 401 / 403.
        FraserNotFoundError
            If the API returns HTTP 404.
        FraserRateLimitError
            If the API returns HTTP 429.
        FraserAPIError
            If the API returns any other 4xx or 5xx response.
        """
        # 0. Build absolute URL (support both relative paths and absolute URLs).
        url = self._build_url(path)

        # 1. URL whitelist + HTTPS validation (SSRF prevention, CWE-918).
        self._validate_url(url)

        # 2. Inject API key (resolved once in __init__) into headers.
        headers = {"X-API-Key": self._resolved_api_key}

        # 3. Acquire rate limiter slot.
        self._rate_limiter.acquire()

        # 4. Apply polite delay (monotonic-clock-based).
        self._polite_delay()

        logger.debug("Sending GET request", url=url)

        # 5. Execute request.
        response: httpx.Response = self._client.get(
            url,
            params=params,
            headers=headers,
        )

        # 6. Handle response status codes.
        self._handle_response_status(response, url)

        logger.debug(
            "GET request completed",
            url=url,
            status_code=response.status_code,
        )
        return response

    def get_with_retry(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send a GET request with exponential backoff retry.

        Retries on rate-limit (HTTP 429) and server-side (HTTP 5xx)
        errors. Client errors other than 429 are *not* retried.

        When the server returns 429 with a ``Retry-After`` header, the
        parsed delay is preferred over the computed exponential backoff
        for the following attempt.

        Parameters
        ----------
        path : str
            API endpoint path (e.g. ``"/items"``) or absolute URL.
        params : dict[str, Any] | None
            Optional query parameters for the request.

        Returns
        -------
        httpx.Response
            The HTTP response object on success.

        Raises
        ------
        FraserRateLimitError
            If all retry attempts fail due to rate limiting.
        FraserAPIError
            If all retry attempts fail due to server errors.
        """
        last_error: FraserRateLimitError | FraserAPIError | None = None

        for attempt in range(self._retry_config.max_attempts):
            try:
                response = self.get(path, params=params)

                if attempt > 0:
                    logger.info(
                        "Request succeeded after retry",
                        path=path,
                        attempt=attempt + 1,
                    )
                return response

            except (FraserRateLimitError, FraserAPIError) as e:
                # 4xx (except 429) should not be retried.
                if (
                    isinstance(e, FraserAPIError)
                    and 400 <= e.status_code < 500
                    and e.status_code != _RATE_LIMIT_STATUS_CODE
                ):
                    raise

                last_error = e

                # Drop the query string before logging — paths embed item_id
                # or future PII; only the routing path is useful here (CWE-532).
                safe_path = urlsplit(path).path
                logger.warning(
                    "Request failed, will retry",
                    path=safe_path,
                    attempt=attempt + 1,
                    max_attempts=self._retry_config.max_attempts,
                    error=str(e),
                )

                # If this is not the last attempt, apply backoff.
                if attempt < self._retry_config.max_attempts - 1:
                    # Prefer server-suggested Retry-After when present, but
                    # cap by max_wait so a hostile server cannot lock the
                    # process up with ``Retry-After: 999999`` (CWE-400).
                    retry_after: float | None = (
                        e.retry_after
                        if isinstance(e, FraserRateLimitError) and e.retry_after
                        else None
                    )
                    delay = (
                        min(retry_after, self._retry_config.max_wait)
                        if retry_after is not None
                        else self._calculate_backoff_delay(attempt)
                    )
                    logger.debug(
                        "Backoff before retry",
                        delay_seconds=delay,
                        next_attempt=attempt + 2,
                        used_retry_after=retry_after is not None,
                    )
                    time.sleep(delay)

        # All attempts exhausted.
        logger.error(
            "All retry attempts failed",
            path=path,
            max_attempts=self._retry_config.max_attempts,
        )
        if last_error is None:
            raise RuntimeError("Unexpected: no error recorded after exhausting retries")
        raise last_error

    # =========================================================================
    # Context Manager
    # =========================================================================

    def close(self) -> None:
        """Close the session and release underlying HTTP resources."""
        self._client.close()
        logger.debug("FraserSession closed")

    def __enter__(self) -> FraserSession:
        """Support the context manager protocol.

        Returns
        -------
        FraserSession
            ``self`` for use in ``with`` statements.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Close session on context exit."""
        self.close()

    # =========================================================================
    # Streaming (used by FraserDownloader)
    # =========================================================================

    @contextmanager
    def stream(self, url: str) -> Iterator[httpx.Response]:
        """Open a streaming GET response after enforcing SSRF guards.

        Wraps :meth:`httpx.Client.stream` so that downloaders share the same
        host whitelist and HTTPS enforcement as regular API calls
        (CWE-918). Polite delays and rate limiting are intentionally **not**
        applied here because streaming downloads of multi-megabyte PDFs
        should not be billed against the 30 req/min budget for JSON calls.

        Parameters
        ----------
        url : str
            Absolute URL to stream. Validated by :meth:`_validate_url`.

        Yields
        ------
        httpx.Response
            Streaming response. The caller is responsible for iterating
            ``response.iter_bytes`` inside the ``with`` block.

        Raises
        ------
        FraserValidationError
            When the URL fails SSRF / HTTPS validation.
        """
        self._validate_url(url)
        with self._client.stream("GET", url) as response:
            yield response

    # =========================================================================
    # Internal Methods
    # =========================================================================

    def _build_url(self, path: str) -> str:
        """Build an absolute URL from a relative path or pass through absolute URLs.

        Any input containing a ``"://"`` separator is treated as an
        already-absolute URL and passed through unchanged so that scheme
        validation (e.g. for ``http://``, ``ftp://``) is performed on
        the URL the caller actually supplied.

        Parameters
        ----------
        path : str
            Path (e.g. ``"/items"``) or already-absolute URL.

        Returns
        -------
        str
            Absolute URL.
        """
        if "://" in path:
            return path
        # Strip trailing '/' from base_url and leading '/' duplication from
        # path to avoid producing ``//``.
        base = self._config.base_url.rstrip("/")
        suffix = path if path.startswith("/") else "/" + path
        return base + suffix

    def _resolve_api_key(self) -> str:
        """Resolve the API key from config or environment variable.

        Returns
        -------
        str
            The resolved API key.

        Raises
        ------
        FraserAuthError
            If no API key is configured.
        """
        api_key = self._config.api_key or os.environ.get(FRASER_API_KEY_ENV, "")

        if not api_key:
            raise FraserAuthError(
                f"FRASER API key not provided. "
                f"Set {FRASER_API_KEY_ENV} environment variable "
                f"or pass it via FraserConfig(api_key=...)."
            )

        return api_key

    def _validate_url(self, url: str) -> None:
        """Validate URL against the allowed hosts whitelist (SSRF prevention).

        Parameters
        ----------
        url : str
            The URL to validate.

        Raises
        ------
        FraserValidationError
            If the URL scheme is not ``https`` or the host is not in
            :data:`ALLOWED_HOSTS` (CWE-918).
        """
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise FraserValidationError(
                f"URL scheme must be 'https', got '{parsed.scheme}'. "
                "FRASER API requires HTTPS.",
                field="url.scheme",
                value=parsed.scheme,
            )
        # ``hostname`` strips the optional ``:port`` so that
        # ``https://fraser.stlouisfed.org:443/...`` (explicit port form)
        # is treated as the same host as the allow-listed bare name.
        parsed_host = parsed.hostname or ""
        if parsed_host not in ALLOWED_HOSTS:
            logger.warning(
                "Request blocked: host not in allowed hosts",
                url=url,
                host=parsed_host,
                allowed_hosts=list(ALLOWED_HOSTS),
            )
            raise FraserValidationError(
                f"Host '{parsed_host}' is not in allowed hosts: "
                f"{sorted(ALLOWED_HOSTS)}",
                field="url.host",
                value=parsed_host,
            )

    def _polite_delay(self) -> None:
        """Apply polite delay between consecutive requests.

        Uses :func:`time.monotonic` to measure elapsed time since the
        last request and sleeps for the remaining delay if not enough
        time has passed. Adds random jitter to avoid thundering herd.
        """
        now = time.monotonic()

        if self._last_request_time > 0:
            elapsed = now - self._last_request_time
            required_delay = _DEFAULT_POLITE_DELAY + random.uniform(  # nosec B311
                0, _DEFAULT_DELAY_JITTER
            )
            remaining = required_delay - elapsed
            if remaining > 0:
                time.sleep(remaining)
                logger.debug("Polite delay applied", delay_seconds=remaining)

        self._last_request_time = time.monotonic()

    def _handle_response_status(self, response: httpx.Response, url: str) -> None:
        """Inspect HTTP status code and raise the appropriate FRASER exception.

        Parameters
        ----------
        response : httpx.Response
            The HTTP response to check.
        url : str
            The request URL (used for error context).

        Raises
        ------
        FraserRateLimitError
            On HTTP 429. ``retry_after`` is populated from the
            ``Retry-After`` header when present.
        FraserAuthError
            On HTTP 401 / 403.
        FraserNotFoundError
            On HTTP 404.
        FraserAPIError
            On any other 4xx or 5xx response.
        """
        status = response.status_code

        # 429: rate limit (honour Retry-After header).
        if status == _RATE_LIMIT_STATUS_CODE:
            retry_after_seconds = self._parse_retry_after(
                response.headers.get("Retry-After")
            )
            logger.warning(
                "Rate limit detected (HTTP 429)",
                url=url,
                status_code=status,
                retry_after=retry_after_seconds,
            )
            raise FraserRateLimitError(
                message=f"Rate limit exceeded: HTTP {status}",
                retry_after=retry_after_seconds,
            )

        # 401 / 403: authentication / authorisation failure.
        if status in _AUTH_ERROR_STATUS_CODES:
            logger.warning(
                "Authentication / authorisation error",
                url=url,
                status_code=status,
            )
            raise FraserAuthError(f"Authentication failed: HTTP {status} for {url}")

        # 404: resource not found.
        if status == _NOT_FOUND_STATUS_CODE:
            logger.warning(
                "Resource not found",
                url=url,
                status_code=status,
            )
            raise FraserNotFoundError(f"Resource not found: HTTP {status} for {url}")

        # Other 4xx: client error.
        if 400 <= status < 500:
            logger.warning(
                "Client error",
                url=url,
                status_code=status,
            )
            raise FraserAPIError(
                message=f"Client error: HTTP {status}",
                url=url,
                status_code=status,
                response_body=response.text[:MAX_RESPONSE_BODY_LOG],
            )

        # 5xx: server error.
        if status >= 500:
            logger.warning(
                "Server error",
                url=url,
                status_code=status,
            )
            raise FraserAPIError(
                message=f"Server error: HTTP {status}",
                url=url,
                status_code=status,
                response_body=response.text[:MAX_RESPONSE_BODY_LOG],
            )

    @staticmethod
    def _parse_retry_after(header_value: str | None) -> float | None:
        """Parse a ``Retry-After`` header value into seconds.

        Supports the integer "delta-seconds" form. The HTTP-date form is
        intentionally not supported because FRASER's API documentation
        specifies the integer form, and parsing dates without a reliable
        clock skew adjustment is brittle.

        Parameters
        ----------
        header_value : str | None
            Raw ``Retry-After`` header value (e.g. ``"5"``).

        Returns
        -------
        float | None
            Parsed delay in seconds, or ``None`` when the header is
            missing or cannot be parsed.
        """
        if not header_value:
            return None
        try:
            return float(header_value.strip())
        except (TypeError, ValueError):
            logger.debug(
                "Failed to parse Retry-After header as integer seconds",
                header_value=header_value,
            )
            return None

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with optional jitter.

        Parameters
        ----------
        attempt : int
            Current attempt number (0-indexed).

        Returns
        -------
        float
            Delay in seconds, bounded by ``retry_config.max_wait``.
        """
        # Exponential growth: base_wait * 2 ** attempt, capped at max_wait.
        delay = min(
            self._retry_config.base_wait * (2.0**attempt),
            self._retry_config.max_wait,
        )
        # Jitter: scale by [0.5, 1.5) to spread retries.
        delay *= 0.5 + random.random()  # nosec B311
        return delay


__all__ = ["FraserSession"]

"""HTTP/HTTPS client with retry mechanism."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from ..exceptions import FeedFetchError
from ..types import HTTPResponse


def _get_logger() -> Any:
    """Get logger with fallback to standard logging.

    Returns
    -------
    Any
        Logger instance (structlog or standard logging)
    """
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="http_client")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()

DEFAULT_USER_AGENT = "rss-feed-collector/0.1.0"
DEFAULT_TIMEOUT = 10
DEFAULT_MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


class HTTPClient:
    """Async HTTP client with retry mechanism.

    This client provides HTTP/HTTPS content fetching with:
    - HTTPS certificate verification (verify=True)
    - Custom User-Agent header
    - Configurable timeout
    - Exponential backoff retry (1s, 2s, 4s)
    - Retry on timeout, connection error, and 5xx errors
    - No retry on 4xx errors

    Attributes
    ----------
    user_agent : str
        User-Agent header value
    verify_ssl : bool
        Whether to verify SSL certificates

    Examples
    --------
    >>> async def example():
    ...     client = HTTPClient()
    ...     response = await client.fetch("https://example.com")
    ...     print(response.status_code)
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize HTTPClient.

        Parameters
        ----------
        user_agent : str, default="rss-feed-collector/0.1.0"
            User-Agent header value
        verify_ssl : bool, default=True
            Whether to verify SSL certificates
        """
        logger.debug(
            "Initializing HTTPClient",
            user_agent=user_agent,
            verify_ssl=verify_ssl,
        )
        self.user_agent = user_agent
        self.verify_ssl = verify_ssl

    async def fetch(
        self,
        url: str,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> HTTPResponse:
        """Fetch content from URL with retry mechanism.

        Parameters
        ----------
        url : str
            URL to fetch
        timeout : int, default=10
            Request timeout in seconds
        max_retries : int, default=3
            Maximum number of retry attempts

        Returns
        -------
        HTTPResponse
            Response containing status_code, content, and headers

        Raises
        ------
        FeedFetchError
            If fetch fails after all retries
        """
        logger.debug(
            "Starting fetch",
            url=url,
            timeout=timeout,
            max_retries=max_retries,
        )

        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            is_last_attempt = attempt >= max_retries

            try:
                response = await self._make_request(url, timeout)
                result = await self._handle_response(
                    response, url, attempt, max_retries, is_last_attempt
                )
                if result is not None:
                    return result
                # result is None means retry needed, continue loop

            except FeedFetchError:
                raise
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                should_continue = await self._handle_connection_error(
                    e, url, attempt, max_retries, is_last_attempt
                )
                if not should_continue:
                    break

        error_msg = str(last_error) if last_error else "Unknown error"
        raise FeedFetchError(f"Failed to fetch {url}: {error_msg}")

    async def _handle_response(
        self,
        response: HTTPResponse,
        url: str,
        attempt: int,
        max_retries: int,
        is_last_attempt: bool,
    ) -> HTTPResponse | None:
        """Handle HTTP response and determine if retry is needed.

        Parameters
        ----------
        response : HTTPResponse
            Response from the request
        url : str
            Request URL for logging
        attempt : int
            Current attempt number (0-indexed)
        max_retries : int
            Maximum retry attempts
        is_last_attempt : bool
            Whether this is the final attempt

        Returns
        -------
        HTTPResponse | None
            Response if successful, None if retry needed

        Raises
        ------
        FeedFetchError
            If 4xx error or 5xx on last attempt
        """
        # Server error (5xx): retry if attempts remain
        if response.status_code >= 500:
            if is_last_attempt:
                logger.error(
                    "Fetch failed: server error",
                    url=url,
                    status_code=response.status_code,
                    attempts=attempt + 1,
                )
                raise FeedFetchError(
                    f"Failed to fetch {url}: HTTP {response.status_code}"
                )

            delay = self._calculate_backoff_delay(attempt)
            logger.warning(
                "Server error, retrying",
                url=url,
                status_code=response.status_code,
                attempt=attempt + 1,
                max_retries=max_retries,
                delay_seconds=delay,
            )
            await asyncio.sleep(delay)
            return None

        # Client error (4xx): no retry
        if 400 <= response.status_code < 500:
            logger.error(
                "Fetch failed: client error",
                url=url,
                status_code=response.status_code,
            )
            raise FeedFetchError(f"Failed to fetch {url}: HTTP {response.status_code}")

        # Success
        logger.debug(
            "Fetch completed successfully",
            url=url,
            status_code=response.status_code,
            content_length=len(response.content),
        )
        return response

    async def _handle_connection_error(
        self,
        error: httpx.TimeoutException | httpx.ConnectError,
        url: str,
        attempt: int,
        max_retries: int,
        is_last_attempt: bool,
    ) -> bool:
        """Handle connection errors and determine if retry is needed.

        Parameters
        ----------
        error : httpx.TimeoutException | httpx.ConnectError
            The connection error
        url : str
            Request URL for logging
        attempt : int
            Current attempt number (0-indexed)
        max_retries : int
            Maximum retry attempts
        is_last_attempt : bool
            Whether this is the final attempt

        Returns
        -------
        bool
            True if should continue retrying, False otherwise
        """
        error_type = type(error).__name__

        if is_last_attempt:
            logger.error(
                "Fetch failed: exhausted retries",
                url=url,
                error_type=error_type,
                error=str(error),
                attempts=attempt + 1,
            )
            return False

        delay = self._calculate_backoff_delay(attempt)
        logger.warning(
            "Request failed, retrying",
            url=url,
            error_type=error_type,
            error=str(error),
            attempt=attempt + 1,
            max_retries=max_retries,
            delay_seconds=delay,
        )
        await asyncio.sleep(delay)
        return True

    async def validate_url(
        self,
        url: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:
        """Validate URL reachability.

        Performs a HEAD request to check if the URL is reachable.

        Parameters
        ----------
        url : str
            URL to validate
        timeout : int, default=10
            Request timeout in seconds

        Returns
        -------
        bool
            True if URL is reachable, False otherwise
        """
        logger.debug("Validating URL reachability", url=url, timeout=timeout)

        try:
            async with httpx.AsyncClient(
                verify=self.verify_ssl,
                timeout=httpx.Timeout(timeout),
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = await client.head(url, follow_redirects=True)
                is_reachable = response.status_code < 400

                logger.debug(
                    "URL validation completed",
                    url=url,
                    status_code=response.status_code,
                    is_reachable=is_reachable,
                )
                return is_reachable

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError) as e:
            logger.debug(
                "URL validation failed",
                url=url,
                error_type=type(e).__name__,
                error=str(e),
            )
            return False

    async def _make_request(
        self,
        url: str,
        timeout: int,
    ) -> HTTPResponse:
        """Make HTTP GET request.

        Parameters
        ----------
        url : str
            URL to fetch
        timeout : int
            Request timeout in seconds

        Returns
        -------
        HTTPResponse
            Response object
        """
        async with httpx.AsyncClient(
            verify=self.verify_ssl,
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": self.user_agent},
        ) as client:
            response = await client.get(url, follow_redirects=True)
            return HTTPResponse(
                status_code=response.status_code,
                content=response.text,
                headers=dict(response.headers),
            )

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay.

        Parameters
        ----------
        attempt : int
            Current attempt number (0-indexed)

        Returns
        -------
        float
            Delay in seconds (1, 2, 4, ...)
        """
        return RETRY_BASE_DELAY * (2**attempt)

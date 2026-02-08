"""Custom exception classes for the ETF.com scraping module.

This module provides a hierarchy of exception classes for handling
various error conditions specific to ETF.com scraping operations,
including HTML parse failures, page load timeouts, and bot-blocking
detection (HTTP 403/429, CAPTCHA redirects).

Exception Hierarchy
-------------------
ETFComError (base, inherits Exception)
    ETFComScrapingError (HTML parse failure)
    ETFComTimeoutError (page load / navigation timeout)
    ETFComBlockedError (bot-blocking detection)

Notes
-----
This follows the same ``Exception``-direct-inheritance pattern used by
``market.errors.FREDError`` and ``market.errors.BloombergError``.

See Also
--------
market.errors : Unified error hierarchy for the market package.
market.etfcom.constants : Default timeout values referenced by callers.
"""


class ETFComError(Exception):
    """Base exception for all ETF.com scraping operations.

    All ETF.com-specific exceptions inherit from this class,
    providing a single catch point for callers that need to handle
    any ETF.com-related failure generically.

    Parameters
    ----------
    message : str
        Human-readable error message describing the failure.

    Attributes
    ----------
    message : str
        The error message.

    Examples
    --------
    >>> try:
    ...     raise ETFComError("ETF.com operation failed")
    ... except ETFComError as e:
    ...     print(e.message)
    ETF.com operation failed
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ETFComScrapingError(ETFComError):
    """Exception raised when HTML parsing / data extraction fails.

    This exception is raised when the expected DOM structure is not
    found on an ETF.com page, typically because:

    - The CSS selector no longer matches (site redesign).
    - The page returned an unexpected format (e.g. error page).
    - Required data fields are missing from the parsed HTML.

    Parameters
    ----------
    message : str
        Human-readable error message describing the parse failure.
    url : str | None
        The URL of the page that failed to parse.
    selector : str | None
        The CSS selector that failed to match.

    Attributes
    ----------
    message : str
        The error message.
    url : str | None
        The URL of the page that failed to parse.
    selector : str | None
        The CSS selector that failed to match.

    Examples
    --------
    >>> raise ETFComScrapingError(
    ...     "Element not found on profile page",
    ...     url="https://www.etf.com/SPY",
    ...     selector="[data-testid='summary-data']",
    ... )
    """

    def __init__(
        self,
        message: str,
        url: str | None,
        selector: str | None,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.selector = selector


class ETFComTimeoutError(ETFComError):
    """Exception raised when a page load or navigation times out.

    This exception is raised when Playwright or an HTTP client
    exceeds the configured timeout while waiting for an ETF.com
    page to load or for a specific element to appear.

    Parameters
    ----------
    message : str
        Human-readable error message describing the timeout.
    url : str | None
        The URL that timed out.
    timeout_seconds : float
        The timeout threshold in seconds that was exceeded.

    Attributes
    ----------
    message : str
        The error message.
    url : str | None
        The URL that timed out.
    timeout_seconds : float
        The timeout threshold in seconds.

    Examples
    --------
    >>> raise ETFComTimeoutError(
    ...     "Page load timed out",
    ...     url="https://www.etf.com/SPY",
    ...     timeout_seconds=30.0,
    ... )
    """

    def __init__(
        self,
        message: str,
        url: str | None,
        timeout_seconds: float,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.timeout_seconds = timeout_seconds


class ETFComBlockedError(ETFComError):
    """Exception raised when bot-blocking is detected.

    This exception is raised when ETF.com returns an HTTP 403
    (Forbidden), 429 (Too Many Requests), or redirects to a
    CAPTCHA verification page, indicating that the scraping
    request has been identified as automated traffic.

    Parameters
    ----------
    message : str
        Human-readable error message describing the block.
    url : str | None
        The URL that triggered the block.
    status_code : int
        The HTTP status code returned (e.g. 403, 429).

    Attributes
    ----------
    message : str
        The error message.
    url : str | None
        The URL that triggered the block.
    status_code : int
        The HTTP status code.

    Examples
    --------
    >>> raise ETFComBlockedError(
    ...     "Bot detected: HTTP 403",
    ...     url="https://www.etf.com/SPY",
    ...     status_code=403,
    ... )
    """

    def __init__(
        self,
        message: str,
        url: str | None,
        status_code: int,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.status_code = status_code


__all__ = [
    "ETFComBlockedError",
    "ETFComError",
    "ETFComScrapingError",
    "ETFComTimeoutError",
]

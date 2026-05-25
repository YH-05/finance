"""Custom exception classes for the FRASER REST API module.

This module provides a hierarchy of exception classes for handling
various error conditions specific to FRASER API operations,
including authentication failures, rate limiting, document not found
errors, generic API errors, response parsing errors, download errors,
and validation errors.

Exception Hierarchy
-------------------
FraserError (base, inherits ``Exception`` directly)
    FraserAuthError (401 / 403 - authentication / authorisation)
    FraserRateLimitError (429 - rate limit exceeded, holds Retry-After)
    FraserNotFoundError (404 - resource not found)
    FraserAPIError (generic 4xx / 5xx - holds url, status_code, body)
    FraserParseError (response parsing failure)
    FraserDownloadError (file download failure)
    FraserValidationError (configuration / input validation failure)

Notes
-----
This follows the ``Exception``-direct-inheritance pattern used by
``market.alphavantage.errors.AlphaVantageError`` to avoid circular
imports with ``market.errors.MarketError``. The choice was confirmed
during PR1 HF1 review.

See Also
--------
market.alphavantage.errors : Reference implementation (direct
    ``Exception`` inheritance, same rationale).
"""


class FraserError(Exception):
    """Base exception for all FRASER API operations.

    All FRASER-specific exceptions inherit from this class, providing
    a single catch point for callers that need to handle any
    FRASER-related failure generically.

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
    ...     raise FraserError("FRASER API operation failed")
    ... except FraserError as e:
    ...     print(e.message)
    FRASER API operation failed
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class FraserAuthError(FraserError):
    """Exception raised when FRASER authentication / authorisation fails.

    Raised when the API returns HTTP 401 (unauthorised) or 403
    (forbidden), typically because the API key is missing, invalid,
    or revoked.

    Parameters
    ----------
    message : str
        Human-readable error message describing the auth failure.

    Examples
    --------
    >>> raise FraserAuthError("Invalid API key (HTTP 401)")
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class FraserRateLimitError(FraserError):
    """Exception raised when the FRASER API rate limit is exceeded.

    Raised when the API returns HTTP 429. The ``retry_after`` attribute
    captures the ``Retry-After`` header value (in seconds) when the
    server provides it, allowing callers to back off appropriately.

    Parameters
    ----------
    message : str
        Human-readable error message describing the rate limit.
    retry_after : float | None
        Suggested delay in seconds before retrying (parsed from the
        ``Retry-After`` response header), or ``None`` when absent.

    Attributes
    ----------
    retry_after : float | None
        The suggested retry delay in seconds.

    Examples
    --------
    >>> raise FraserRateLimitError("Rate limit exceeded", retry_after=60.0)
    """

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class FraserNotFoundError(FraserError):
    """Exception raised when a FRASER resource is not found.

    Raised when the API returns HTTP 404, indicating the requested
    title, item, or other resource does not exist.

    Parameters
    ----------
    message : str
        Human-readable error message describing the missing resource.

    Examples
    --------
    >>> raise FraserNotFoundError("Title 999999 not found")
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class FraserAPIError(FraserError):
    """Exception raised for generic FRASER API errors (4xx / 5xx).

    Used when the API returns a non-success status code that is not
    handled by the more specific ``FraserAuthError``,
    ``FraserRateLimitError``, or ``FraserNotFoundError``.

    Parameters
    ----------
    message : str
        Human-readable error message describing the API failure.
    url : str
        The API endpoint URL that returned the error.
    status_code : int
        The HTTP status code returned by the API.
    response_body : str
        The raw response body (truncated by ``MAX_RESPONSE_BODY_LOG``
        in the session layer to avoid CWE-209 information leakage).

    Attributes
    ----------
    url : str
        The API endpoint URL.
    status_code : int
        The HTTP status code.
    response_body : str
        The raw response body.

    Examples
    --------
    >>> raise FraserAPIError(
    ...     "API returned HTTP 500",
    ...     url="https://fraser.stlouisfed.org/api/title/677",
    ...     status_code=500,
    ...     response_body='{"error": "Internal Server Error"}',
    ... )
    """

    def __init__(
        self,
        message: str,
        url: str,
        status_code: int,
        response_body: str,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.response_body = response_body


class FraserParseError(FraserError):
    """Exception raised when FRASER response parsing fails.

    Raised when the API returns a response that cannot be parsed into
    the expected data structure (e.g., missing expected fields,
    malformed JSON, unexpected schema).

    Parameters
    ----------
    message : str
        Human-readable error message describing the parse failure.
    raw_data : str
        The raw data that could not be parsed.
    field : str
        The field or key that was expected but missing or malformed.
    cause : Exception | None
        The underlying exception that caused the parse failure,
        when applicable.

    Attributes
    ----------
    raw_data : str
        The raw data that could not be parsed.
    field : str
        The expected field or key.
    cause : Exception | None
        The underlying cause, if any.

    Examples
    --------
    >>> raise FraserParseError(
    ...     "Missing 'items' key in response",
    ...     raw_data='{"meta": {...}}',
    ...     field="items",
    ... )
    """

    def __init__(
        self,
        message: str,
        raw_data: str,
        field: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.raw_data = raw_data
        self.field = field
        self.cause = cause


class FraserDownloadError(FraserError):
    """Exception raised when a FRASER file download fails.

    Raised when the downloader cannot fetch a binary asset (PDF, TXT)
    from FRASER (e.g., network failure, partial response, write error).

    Parameters
    ----------
    message : str
        Human-readable error message describing the download failure.
    url : str
        The asset URL that failed to download.
    cause : Exception | None
        The underlying exception that caused the download failure,
        when applicable.

    Attributes
    ----------
    url : str
        The asset URL.
    cause : Exception | None
        The underlying cause, if any.

    Examples
    --------
    >>> raise FraserDownloadError(
    ...     "Failed to download PDF",
    ...     url="https://fraser.stlouisfed.org/files/docs/...",
    ... )
    """

    def __init__(
        self,
        message: str,
        url: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.cause = cause


class FraserValidationError(FraserError):
    """Exception raised when FRASER configuration or input validation fails.

    Raised by ``FraserConfig.__post_init__`` and other validation paths
    when a parameter is outside its valid range.

    Parameters
    ----------
    message : str
        Human-readable error message describing the validation failure.
    field : str
        The field that failed validation.
    value : object
        The invalid value that caused the validation failure.

    Attributes
    ----------
    field : str
        The field that failed validation.
    value : object
        The invalid value.

    Examples
    --------
    >>> raise FraserValidationError(
    ...     "timeout must be positive",
    ...     field="timeout",
    ...     value=0,
    ... )
    """

    def __init__(
        self,
        message: str,
        field: str,
        value: object,
    ) -> None:
        super().__init__(message)
        self.field = field
        self.value = value


__all__ = [
    "FraserAPIError",
    "FraserAuthError",
    "FraserDownloadError",
    "FraserError",
    "FraserNotFoundError",
    "FraserParseError",
    "FraserRateLimitError",
    "FraserValidationError",
]

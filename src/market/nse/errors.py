"""Custom exception classes for the NSE API module.

This module provides a hierarchy of exception classes for handling
various error conditions specific to NSE API operations,
including API response failures, rate limiting, cookie expiration,
response parsing errors, and data validation errors.

Exception Hierarchy
-------------------
NseError (base, inherits Exception)
    NseAPIError (API response error - 4xx, 5xx)
    NseRateLimitError (rate limit exceeded - 429)
    NseCookieError (session cookie expired/invalid — NSE-specific)
    NseParseError (response parse failure)
    NseValidationError (data validation failure)

Notes
-----
This follows the same ``Exception``-direct-inheritance pattern used by
``market.bse.errors.BseError``.

``NseCookieError`` is NSE-specific: NSE requires a valid session cookie
obtained by visiting ``https://www.nseindia.com`` before making any API
request. When the cookie expires, all subsequent API requests return
an HTML login redirect rather than JSON data.

See Also
--------
market.bse.errors : BSE error hierarchy (reference implementation).
"""


class NseError(Exception):
    """Base exception for all NSE API operations.

    All NSE-specific exceptions inherit from this class,
    providing a single catch point for callers that need to handle
    any NSE-related failure generically.

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
    ...     raise NseError("NSE API operation failed")
    ... except NseError as e:
    ...     print(e.message)
    NSE API operation failed
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NseAPIError(NseError):
    """Exception raised when the NSE API returns an error response.

    This exception is raised when a request to the NSE API
    returns a non-success HTTP status code (4xx or 5xx). It provides
    contextual attributes to aid debugging and error handling.

    Parameters
    ----------
    message : str
        Human-readable error message describing the API failure.
    url : str
        The API endpoint URL that returned the error.
    status_code : int
        The HTTP status code returned by the API (e.g. 400, 403, 500).
    response_body : str
        The raw response body returned by the API, useful for
        diagnosing unexpected response formats.

    Attributes
    ----------
    message : str
        The error message.
    url : str
        The API endpoint URL.
    status_code : int
        The HTTP status code.
    response_body : str
        The raw response body.

    Examples
    --------
    >>> raise NseAPIError(
    ...     "API returned HTTP 500",
    ...     url="https://www.nseindia.com/api/equity-stockIndices",
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


class NseRateLimitError(NseError):
    """Exception raised when the NSE API rate limit is exceeded.

    This exception is raised when the NSE API returns a rate
    limiting response (HTTP 429), indicating that too many requests have
    been sent in a given time period.

    Parameters
    ----------
    message : str
        Human-readable error message describing the rate limit.
    url : str | None
        The URL that triggered the rate limit.
    retry_after : float | None
        The number of seconds to wait before retrying, as suggested
        by the API response (e.g. from a Retry-After header).

    Attributes
    ----------
    message : str
        The error message.
    url : str | None
        The URL that triggered the rate limit.
    retry_after : float | None
        The suggested retry delay in seconds.

    Examples
    --------
    >>> raise NseRateLimitError(
    ...     "Rate limit exceeded",
    ...     url="https://www.nseindia.com/api/equity-stockIndices",
    ...     retry_after=60.0,
    ... )
    """

    def __init__(
        self,
        message: str,
        url: str | None,
        retry_after: float | None,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.retry_after = retry_after


class NseCookieError(NseError):
    """Exception raised when the NSE session cookie is expired or invalid.

    This exception is NSE-specific. NSE requires a valid session cookie
    obtained by visiting ``https://www.nseindia.com`` before making any
    API request. When the cookie expires or is missing, API requests
    return an HTML login redirect rather than JSON data.

    Parameters
    ----------
    message : str
        Human-readable error message describing the cookie failure.
    url : str | None
        The API endpoint URL that detected the cookie issue.

    Attributes
    ----------
    message : str
        The error message.
    url : str | None
        The API endpoint URL that detected the cookie issue.

    Examples
    --------
    >>> raise NseCookieError(
    ...     "NSE session cookie expired. Re-initialise the session.",
    ...     url="https://www.nseindia.com/api/equity-stockIndices",
    ... )
    """

    def __init__(
        self,
        message: str,
        url: str | None,
    ) -> None:
        super().__init__(message)
        self.url = url


class NseParseError(NseError):
    """Exception raised when NSE API response parsing fails.

    This exception is raised when the response from the NSE API
    cannot be parsed as expected, typically because:

    - The JSON structure does not match the expected schema.
    - A required field is missing or has an unexpected type.
    - The response body is not valid JSON (e.g. HTML redirect returned).

    Parameters
    ----------
    message : str
        Human-readable error message describing the parse failure.
    raw_data : str | None
        The raw response data that failed to parse.
    field : str | None
        The specific field that caused the parse failure.

    Attributes
    ----------
    message : str
        The error message.
    raw_data : str | None
        The raw response data.
    field : str | None
        The field that caused the failure.

    Examples
    --------
    >>> raise NseParseError(
    ...     "Failed to parse equity indices response",
    ...     raw_data='{"data": null}',
    ...     field="data",
    ... )
    """

    def __init__(
        self,
        message: str,
        raw_data: str | None,
        field: str | None,
    ) -> None:
        super().__init__(message)
        self.raw_data = raw_data
        self.field = field


class NseValidationError(NseError):
    """Exception raised when NSE data validation fails.

    This exception is raised when data retrieved from the NSE API
    fails validation checks, such as invalid symbol names, unexpected
    field values, or data integrity issues.

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
    message : str
        The error message.
    field : str
        The field that failed validation.
    value : object
        The invalid value.

    Examples
    --------
    >>> raise NseValidationError(
    ...     "Invalid symbol: must be a non-empty uppercase string",
    ...     field="symbol",
    ...     value="",
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
    "NseAPIError",
    "NseCookieError",
    "NseError",
    "NseParseError",
    "NseRateLimitError",
    "NseValidationError",
]

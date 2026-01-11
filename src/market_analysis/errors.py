"""Custom exception classes for the market_analysis package.

This module provides a hierarchy of exception classes for handling
various error conditions in market data fetching, analysis, and export.

All exceptions inherit from MarketAnalysisError and include:
- Error codes for programmatic handling
- Detailed error messages with context
- Optional cause chaining
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Error codes for categorizing exceptions.

    Attributes
    ----------
    UNKNOWN : str
        Unknown or unclassified error
    NETWORK_ERROR : str
        Network connectivity issues
    API_ERROR : str
        External API errors
    RATE_LIMIT : str
        API rate limit exceeded
    INVALID_SYMBOL : str
        Invalid ticker symbol
    INVALID_DATE : str
        Invalid date format or range
    INVALID_PARAMETER : str
        Invalid function parameter
    DATA_NOT_FOUND : str
        Requested data not found
    CACHE_ERROR : str
        Cache read/write errors
    ANALYSIS_ERROR : str
        Error during analysis
    EXPORT_ERROR : str
        Error during export
    TIMEOUT : str
        Operation timeout
    """

    UNKNOWN = "UNKNOWN"
    NETWORK_ERROR = "NETWORK_ERROR"
    API_ERROR = "API_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    INVALID_DATE = "INVALID_DATE"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    CACHE_ERROR = "CACHE_ERROR"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"
    EXPORT_ERROR = "EXPORT_ERROR"
    TIMEOUT = "TIMEOUT"


class MarketAnalysisError(Exception):
    """Base exception for all market_analysis errors.

    All custom exceptions in this package inherit from this class,
    providing a consistent interface for error handling.

    Parameters
    ----------
    message : str
        Human-readable error message
    code : ErrorCode
        Error code for programmatic handling
    details : dict[str, Any] | None
        Additional context about the error
    cause : Exception | None
        The underlying exception that caused this error

    Attributes
    ----------
    message : str
        The error message
    code : ErrorCode
        The error code
    details : dict[str, Any]
        Additional error details
    cause : Exception | None
        The original exception if available

    Examples
    --------
    >>> try:
    ...     raise MarketAnalysisError(
    ...         "Failed to fetch data",
    ...         code=ErrorCode.NETWORK_ERROR,
    ...         details={"symbol": "AAPL"},
    ...     )
    ... except MarketAnalysisError as e:
    ...     print(e.code)
    NETWORK_ERROR
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        """Return a formatted error message."""
        parts = [f"[{self.code.value}] {self.message}"]

        if self.details:
            details_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            parts.append(f"Details: {details_str}")

        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {self.cause}")

        return " | ".join(parts)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"details={self.details!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the error
        """
        result: dict[str, Any] = {
            "error_type": self.__class__.__name__,
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }

        if self.cause:
            result["cause"] = {
                "type": type(self.cause).__name__,
                "message": str(self.cause),
            }

        return result


class DataFetchError(MarketAnalysisError):
    """Exception raised when data fetching fails.

    This exception is raised for errors during data retrieval from
    external sources (yfinance, FRED, etc.).

    Parameters
    ----------
    message : str
        Human-readable error message
    symbol : str | None
        The symbol that failed to fetch
    source : str | None
        The data source that was used
    code : ErrorCode
        Error code (defaults to API_ERROR)
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise DataFetchError(
    ...     "Failed to fetch price data for AAPL",
    ...     symbol="AAPL",
    ...     source="yfinance",
    ... )
    """

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        source: str | None = None,
        code: ErrorCode = ErrorCode.API_ERROR,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if symbol:
            details["symbol"] = symbol
        if source:
            details["source"] = source

        super().__init__(message, code=code, details=details, cause=cause)
        self.symbol = symbol
        self.source = source


class ValidationError(MarketAnalysisError):
    """Exception raised when input validation fails.

    This exception is raised when function parameters or input data
    fail validation checks.

    Parameters
    ----------
    message : str
        Human-readable error message
    field : str | None
        The field that failed validation
    value : Any
        The invalid value
    code : ErrorCode
        Error code (defaults to INVALID_PARAMETER)
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise ValidationError(
    ...     "Start date must be before end date",
    ...     field="start_date",
    ...     value="2024-12-31",
    ... )
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        code: ErrorCode = ErrorCode.INVALID_PARAMETER,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = repr(value)

        super().__init__(message, code=code, details=details, cause=cause)
        self.field = field
        self.value = value


class AnalysisError(MarketAnalysisError):
    """Exception raised when analysis operations fail.

    This exception is raised for errors during data analysis,
    indicator calculation, or statistical computations.

    Parameters
    ----------
    message : str
        Human-readable error message
    symbol : str | None
        The symbol being analyzed
    indicator : str | None
        The indicator that failed
    code : ErrorCode
        Error code (defaults to ANALYSIS_ERROR)
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise AnalysisError(
    ...     "Insufficient data for SMA calculation",
    ...     symbol="AAPL",
    ...     indicator="sma_200",
    ... )
    """

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        indicator: str | None = None,
        code: ErrorCode = ErrorCode.ANALYSIS_ERROR,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if symbol:
            details["symbol"] = symbol
        if indicator:
            details["indicator"] = indicator

        super().__init__(message, code=code, details=details, cause=cause)
        self.symbol = symbol
        self.indicator = indicator


class ExportError(MarketAnalysisError):
    """Exception raised when data export fails.

    This exception is raised for errors during data serialization
    or file writing operations.

    Parameters
    ----------
    message : str
        Human-readable error message
    format : str | None
        The export format that failed
    path : str | None
        The output path
    code : ErrorCode
        Error code (defaults to EXPORT_ERROR)
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise ExportError(
    ...     "Failed to write CSV file",
    ...     format="csv",
    ...     path="/data/output.csv",
    ... )
    """

    def __init__(
        self,
        message: str,
        format: str | None = None,
        path: str | None = None,
        code: ErrorCode = ErrorCode.EXPORT_ERROR,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if format:
            details["format"] = format
        if path:
            details["path"] = path

        super().__init__(message, code=code, details=details, cause=cause)
        self.format = format
        self.path = path


class CacheError(MarketAnalysisError):
    """Exception raised when cache operations fail.

    This exception is raised for errors during cache read/write
    operations with SQLite.

    Parameters
    ----------
    message : str
        Human-readable error message
    operation : str | None
        The cache operation that failed ("get", "set", "clear")
    key : str | None
        The cache key involved
    code : ErrorCode
        Error code (defaults to CACHE_ERROR)
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise CacheError(
    ...     "Failed to read from cache",
    ...     operation="get",
    ...     key="AAPL:2024-01-01:2024-12-31",
    ... )
    """

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        key: str | None = None,
        code: ErrorCode = ErrorCode.CACHE_ERROR,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if operation:
            details["operation"] = operation
        if key:
            details["key"] = key

        super().__init__(message, code=code, details=details, cause=cause)
        self.operation = operation
        self.key = key


class RateLimitError(DataFetchError):
    """Exception raised when API rate limit is exceeded.

    This is a specialized DataFetchError for rate limiting scenarios.

    Parameters
    ----------
    message : str
        Human-readable error message
    retry_after : int | None
        Seconds to wait before retrying
    source : str | None
        The data source
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise RateLimitError(
    ...     "Rate limit exceeded for yfinance",
    ...     retry_after=60,
    ...     source="yfinance",
    ... )
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        source: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if retry_after:
            details["retry_after_seconds"] = retry_after

        super().__init__(
            message,
            symbol=None,
            source=source,
            code=ErrorCode.RATE_LIMIT,
            details=details,
            cause=cause,
        )
        self.retry_after = retry_after


class TimeoutError(MarketAnalysisError):
    """Exception raised when an operation times out.

    Parameters
    ----------
    message : str
        Human-readable error message
    timeout_seconds : float | None
        The timeout duration that was exceeded
    operation : str | None
        The operation that timed out
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise TimeoutError(
    ...     "Data fetch timed out after 30 seconds",
    ...     timeout_seconds=30.0,
    ...     operation="fetch_data",
    ... )
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: float | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation

        super().__init__(message, code=ErrorCode.TIMEOUT, details=details, cause=cause)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


__all__ = [
    "AnalysisError",
    "CacheError",
    "DataFetchError",
    "ErrorCode",
    "ExportError",
    "MarketAnalysisError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
]

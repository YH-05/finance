"""Error definitions for market.yfinance module.

This module provides a hierarchy of exception classes for handling
various error conditions in market data fetching.

All exceptions inherit from MarketError and include:
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
    TIMEOUT = "TIMEOUT"


class MarketError(Exception):
    """Base exception for all market.yfinance errors.

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
    ...     raise MarketError(
    ...         "Failed to fetch data",
    ...         code=ErrorCode.NETWORK_ERROR,
    ...         details={"symbol": "AAPL"},
    ...     )
    ... except MarketError as e:
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


class DataFetchError(MarketError):
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


class ValidationError(MarketError):
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


__all__ = [
    "DataFetchError",
    "ErrorCode",
    "MarketError",
    "ValidationError",
]

"""Custom exception classes for the market package.

This module provides a hierarchy of exception classes for handling
various error conditions in market data handling and export operations.

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
    EXPORT_ERROR : str
        Error during export
    INVALID_PARAMETER : str
        Invalid function parameter
    """

    UNKNOWN = "UNKNOWN"
    EXPORT_ERROR = "EXPORT_ERROR"
    INVALID_PARAMETER = "INVALID_PARAMETER"


class MarketError(Exception):
    """Base exception for all market package errors.

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
    ...         "Failed to process data",
    ...         code=ErrorCode.UNKNOWN,
    ...         details={"symbol": "AAPL"},
    ...     )
    ... except MarketError as e:
    ...     print(e.code)
    UNKNOWN
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


class ExportError(MarketError):
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


__all__ = [
    "ErrorCode",
    "ExportError",
    "MarketError",
]

"""Error definitions for market.bloomberg module.

This module provides error classes for Bloomberg API operations using the
rich pattern with error codes, detailed context, and exception chaining.

Error Classes
-------------
- ErrorCode: Enum of all Bloomberg error codes
- BloombergError: Base exception with code, details, cause
- BloombergConnectionError: Connection failures
- BloombergSessionError: Session management failures
- BloombergDataError: Data fetching failures
- BloombergValidationError: Input validation failures

Examples
--------
>>> from market.bloomberg.errors import BloombergError, ErrorCode
>>> error = BloombergError("Connection failed", code=ErrorCode.CONNECTION_FAILED)
>>> error.to_dict()
{'message': 'Connection failed', 'code': 'CONNECTION_FAILED', 'details': {}}
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Bloomberg API error codes.

    Attributes
    ----------
    CONNECTION_FAILED : str
        Failed to connect to Bloomberg Terminal
    SESSION_ERROR : str
        Session management error
    SERVICE_ERROR : str
        Service startup error
    INVALID_SECURITY : str
        Invalid or unknown security identifier
    INVALID_FIELD : str
        Invalid Bloomberg field
    DATA_NOT_FOUND : str
        Requested data not found
    INVALID_PARAMETER : str
        Invalid parameter value
    INVALID_DATE_RANGE : str
        Invalid date range specified
    """

    CONNECTION_FAILED = "CONNECTION_FAILED"
    SESSION_ERROR = "SESSION_ERROR"
    SERVICE_ERROR = "SERVICE_ERROR"
    INVALID_SECURITY = "INVALID_SECURITY"
    INVALID_FIELD = "INVALID_FIELD"
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"


class BloombergError(Exception):
    """Base exception for Bloomberg operations.

    Parameters
    ----------
    message : str
        Error message
    code : ErrorCode
        Error code (default: INVALID_PARAMETER)
    details : dict[str, Any] | None
        Additional error details
    cause : Exception | None
        Original exception that caused this error

    Attributes
    ----------
    message : str
        Error message
    code : ErrorCode
        Error code
    details : dict[str, Any]
        Additional error details
    cause : Exception | None
        Original exception

    Examples
    --------
    >>> error = BloombergError("Connection failed", code=ErrorCode.CONNECTION_FAILED)
    >>> error.code
    <ErrorCode.CONNECTION_FAILED: 'CONNECTION_FAILED'>
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_PARAMETER,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary representation.

        Returns
        -------
        dict[str, Any]
            Dictionary containing error information

        Examples
        --------
        >>> error = BloombergError("Test", code=ErrorCode.CONNECTION_FAILED)
        >>> error.to_dict()
        {'message': 'Test', 'code': 'CONNECTION_FAILED', 'details': {}}
        """
        result = {
            "message": self.message,
            "code": self.code.value,
            "details": self.details,
        }
        if self.cause is not None:
            result["cause"] = str(self.cause)
        return result


class BloombergConnectionError(BloombergError):
    """Exception for Bloomberg connection failures.

    Parameters
    ----------
    message : str
        Error message
    host : str | None
        Host that connection was attempted to
    port : int | None
        Port that connection was attempted to
    cause : Exception | None
        Original exception

    Attributes
    ----------
    host : str | None
        Host that connection was attempted to
    port : int | None
        Port that connection was attempted to

    Examples
    --------
    >>> error = BloombergConnectionError(
    ...     "Connection refused",
    ...     host="localhost",
    ...     port=8194,
    ... )
    >>> error.host
    'localhost'
    """

    def __init__(
        self,
        message: str,
        host: str | None = None,
        port: int | None = None,
        cause: Exception | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if host is not None:
            details["host"] = host
        if port is not None:
            details["port"] = port

        super().__init__(
            message,
            code=ErrorCode.CONNECTION_FAILED,
            details=details,
            cause=cause,
        )
        self.host = host
        self.port = port


class BloombergSessionError(BloombergError):
    """Exception for Bloomberg session management failures.

    Parameters
    ----------
    message : str
        Error message
    service : str | None
        Bloomberg service that failed
    cause : Exception | None
        Original exception

    Attributes
    ----------
    service : str | None
        Bloomberg service that failed

    Examples
    --------
    >>> error = BloombergSessionError(
    ...     "Service not available",
    ...     service="//blp/refdata",
    ... )
    >>> error.service
    '//blp/refdata'
    """

    def __init__(
        self,
        message: str,
        service: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if service is not None:
            details["service"] = service

        super().__init__(
            message,
            code=ErrorCode.SESSION_ERROR,
            details=details,
            cause=cause,
        )
        self.service = service


class BloombergDataError(BloombergError):
    """Exception for Bloomberg data fetching failures.

    Parameters
    ----------
    message : str
        Error message
    security : str | None
        Security that caused the error
    fields : list[str] | None
        Fields that caused the error
    code : ErrorCode
        Error code (default: INVALID_SECURITY)
    cause : Exception | None
        Original exception

    Attributes
    ----------
    security : str | None
        Security that caused the error
    fields : list[str] | None
        Fields that caused the error

    Examples
    --------
    >>> error = BloombergDataError(
    ...     "Invalid security",
    ...     security="INVALID US Equity",
    ... )
    >>> error.security
    'INVALID US Equity'
    """

    def __init__(
        self,
        message: str,
        security: str | None = None,
        fields: list[str] | None = None,
        code: ErrorCode = ErrorCode.INVALID_SECURITY,
        cause: Exception | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if security is not None:
            details["security"] = security
        if fields is not None:
            details["fields"] = fields

        super().__init__(
            message,
            code=code,
            details=details,
            cause=cause,
        )
        self.security = security
        self.fields = fields


class BloombergValidationError(BloombergError):
    """Exception for Bloomberg input validation failures.

    Parameters
    ----------
    message : str
        Error message
    field : str | None
        Field that failed validation
    value : Any
        Invalid value
    code : ErrorCode
        Error code (default: INVALID_PARAMETER)
    cause : Exception | None
        Original exception

    Attributes
    ----------
    field : str | None
        Field that failed validation
    value : Any
        Invalid value

    Examples
    --------
    >>> error = BloombergValidationError(
    ...     "Invalid date format",
    ...     field="start_date",
    ...     value="not-a-date",
    ... )
    >>> error.field
    'start_date'
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        code: ErrorCode = ErrorCode.INVALID_PARAMETER,
        cause: Exception | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if field is not None:
            details["field"] = field
        if value is not None:
            details["value"] = value

        super().__init__(
            message,
            code=code,
            details=details,
            cause=cause,
        )
        self.field = field
        self.value = value


__all__ = [
    "BloombergConnectionError",
    "BloombergDataError",
    "BloombergError",
    "BloombergSessionError",
    "BloombergValidationError",
    "ErrorCode",
]

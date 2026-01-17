"""Custom exception classes for the factor package.

This module provides a hierarchy of exception classes for handling
various error conditions in factor analysis operations.

All exceptions inherit from FactorError and include:
- Detailed error messages with context
- Optional cause chaining
"""

from typing import Any


class FactorError(Exception):
    """Base exception for all factor package errors.

    All custom exceptions in this package inherit from this class,
    providing a consistent interface for error handling.

    Parameters
    ----------
    message : str
        Human-readable error message
    details : dict[str, Any] | None
        Additional context about the error
    cause : Exception | None
        The underlying exception that caused this error

    Attributes
    ----------
    message : str
        The error message
    details : dict[str, Any]
        Additional error details
    cause : Exception | None
        The original exception if available

    Examples
    --------
    >>> try:
    ...     raise FactorError(
    ...         "Failed to calculate factor",
    ...         details={"factor": "momentum"},
    ...     )
    ... except FactorError as e:
    ...     print(e.message)
    Failed to calculate factor
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        """Return a formatted error message."""
        parts = [self.message]

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
            "message": self.message,
            "details": self.details,
        }

        if self.cause:
            result["cause"] = {
                "type": type(self.cause).__name__,
                "message": str(self.cause),
            }

        return result


class InsufficientDataError(FactorError):
    """Exception raised when there is insufficient data for calculation.

    This exception is raised when the available data points are fewer
    than the minimum required for a factor calculation.

    Parameters
    ----------
    message : str
        Human-readable error message
    required : int | None
        Minimum number of data points required
    available : int | None
        Number of data points available
    factor_name : str | None
        Name of the factor being calculated
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise InsufficientDataError(
    ...     "Not enough data points for SMA calculation",
    ...     required=200,
    ...     available=150,
    ...     factor_name="sma_200",
    ... )
    """

    def __init__(
        self,
        message: str,
        required: int | None = None,
        available: int | None = None,
        factor_name: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if required is not None:
            details["required"] = required
        if available is not None:
            details["available"] = available
        if factor_name:
            details["factor_name"] = factor_name

        super().__init__(message, details=details, cause=cause)
        self.required = required
        self.available = available
        self.factor_name = factor_name


class OrthogonalizationError(FactorError):
    """Exception raised when factor orthogonalization fails.

    This exception is raised for errors during the orthogonalization
    process, such as singular matrices or numerical instability.

    Parameters
    ----------
    message : str
        Human-readable error message
    factor_name : str | None
        Name of the factor being orthogonalized
    control_factors : list[str] | None
        List of control factors
    method : str | None
        Orthogonalization method used
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise OrthogonalizationError(
    ...     "Singular matrix encountered during orthogonalization",
    ...     factor_name="momentum",
    ...     control_factors=["size", "value"],
    ...     method="gram_schmidt",
    ... )
    """

    def __init__(
        self,
        message: str,
        factor_name: str | None = None,
        control_factors: list[str] | None = None,
        method: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if factor_name:
            details["factor_name"] = factor_name
        if control_factors:
            details["control_factors"] = control_factors
        if method:
            details["method"] = method

        super().__init__(message, details=details, cause=cause)
        self.factor_name = factor_name
        self.control_factors = control_factors
        self.method = method


class NormalizationError(FactorError):
    """Exception raised when factor normalization fails.

    This exception is raised for errors during the normalization
    process, such as zero variance or invalid percentile bounds.

    Parameters
    ----------
    message : str
        Human-readable error message
    factor_name : str | None
        Name of the factor being normalized
    method : str | None
        Normalization method used
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise NormalizationError(
    ...     "Cannot compute z-score: zero variance detected",
    ...     factor_name="value_factor",
    ...     method="zscore",
    ... )
    """

    def __init__(
        self,
        message: str,
        factor_name: str | None = None,
        method: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if factor_name:
            details["factor_name"] = factor_name
        if method:
            details["method"] = method

        super().__init__(message, details=details, cause=cause)
        self.factor_name = factor_name
        self.method = method


class ValidationError(FactorError):
    """Exception raised when input validation fails.

    This exception is raised when function parameters or input data
    fail validation checks in factor operations.

    Parameters
    ----------
    message : str
        Human-readable error message
    field : str | None
        The field that failed validation
    value : Any
        The invalid value
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception

    Examples
    --------
    >>> raise ValidationError(
    ...     "Window size must be positive",
    ...     field="window",
    ...     value=-10,
    ... )
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = repr(value)

        super().__init__(message, details=details, cause=cause)
        self.field = field
        self.value = value


__all__ = [
    "FactorError",
    "InsufficientDataError",
    "NormalizationError",
    "OrthogonalizationError",
    "ValidationError",
]

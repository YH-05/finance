"""Custom exception and warning classes for the strategy package.

This module provides a hierarchy of exception and warning classes
for handling various error conditions in strategy analysis.

All exceptions inherit from StrategyError and include:
- Human-readable error messages
- Optional error codes for programmatic handling
- Optional cause chaining for debugging

All warnings inherit from StrategyWarning and can be filtered
using Python's standard warnings module.

Examples
--------
>>> # Raising an error
>>> raise StrategyError("Analysis failed", code="STRATEGY_001")

>>> # Chaining exceptions
>>> try:
...     result = external_api_call()
... except ApiError as e:
...     raise DataProviderError("Failed to fetch data", cause=e) from e

>>> # Issuing a warning
>>> import warnings
>>> warnings.warn("Data may be incomplete", DataWarning)
"""

from __future__ import annotations


class StrategyError(Exception):
    """Base exception for all strategy package errors.

    All custom exceptions in this package inherit from this class,
    providing a consistent interface for error handling.

    Parameters
    ----------
    message : str
        Human-readable error message
    code : str | None
        Error code for programmatic handling (e.g., "STRATEGY_001")
    cause : Exception | None
        The underlying exception that caused this error

    Attributes
    ----------
    message : str
        The error message
    code : str | None
        The error code, if provided
    cause : Exception | None
        The original exception if available

    Examples
    --------
    >>> try:
    ...     raise StrategyError(
    ...         "Analysis failed",
    ...         code="STRATEGY_001",
    ...     )
    ... except StrategyError as e:
    ...     print(e.code)
    STRATEGY_001

    >>> # With cause chaining
    >>> try:
    ...     result = 1 / 0
    ... except ZeroDivisionError as e:
    ...     raise StrategyError("Calculation failed", cause=e) from e
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize StrategyError.

        Parameters
        ----------
        message : str
            Human-readable error message
        code : str | None
            Error code for programmatic handling
        cause : Exception | None
            The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.cause = cause

    def __str__(self) -> str:
        """Return a formatted error message.

        Returns
        -------
        str
            Formatted error message including code and cause if present
        """
        parts = [self.message]

        if self.code:
            parts.insert(0, f"[{self.code}]")

        if self.cause:
            parts.append(f"(caused by: {type(self.cause).__name__}: {self.cause})")

        return " ".join(parts)

    def __repr__(self) -> str:
        """Return a developer-friendly representation.

        Returns
        -------
        str
            String representation for debugging
        """
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"cause={self.cause!r})"
        )


class DataProviderError(StrategyError):
    """Exception raised when data provider operations fail.

    This exception is raised for errors during data retrieval
    from external data sources (e.g., yfinance, APIs).

    Parameters
    ----------
    message : str
        Human-readable error message
    code : str | None
        Error code for programmatic handling
    cause : Exception | None
        The underlying exception that caused this error

    Examples
    --------
    >>> raise DataProviderError(
    ...     "Failed to fetch data from yfinance",
    ...     code="PROVIDER_001",
    ... )
    """


class InvalidTickerError(StrategyError):
    """Exception raised when an invalid ticker symbol is provided.

    This exception is raised when a ticker symbol is not recognized
    or is in an invalid format.

    Parameters
    ----------
    message : str
        Human-readable error message
    code : str | None
        Error code for programmatic handling
    cause : Exception | None
        The underlying exception that caused this error

    Examples
    --------
    >>> raise InvalidTickerError(
    ...     "Invalid ticker symbol: XXXXX",
    ...     code="TICKER_001",
    ... )
    """


class InsufficientDataError(StrategyError):
    """Exception raised when there is insufficient data for analysis.

    This exception is raised when the available data is not enough
    to perform the requested analysis or calculation.

    Parameters
    ----------
    message : str
        Human-readable error message
    code : str | None
        Error code for programmatic handling
    cause : Exception | None
        The underlying exception that caused this error

    Examples
    --------
    >>> raise InsufficientDataError(
    ...     "Need at least 200 data points, got 50",
    ...     code="DATA_001",
    ... )
    """


class ConfigurationError(StrategyError):
    """Exception raised when configuration is invalid.

    This exception is raised for errors related to configuration,
    such as missing required fields or invalid values.

    Parameters
    ----------
    message : str
        Human-readable error message
    code : str | None
        Error code for programmatic handling
    cause : Exception | None
        The underlying exception that caused this error

    Examples
    --------
    >>> raise ConfigurationError(
    ...     "Invalid configuration: missing required field 'api_key'",
    ...     code="CONFIG_001",
    ... )
    """


class ValidationError(StrategyError):
    """Exception raised when input validation fails.

    This exception is raised when function parameters or input data
    fail validation checks.

    Parameters
    ----------
    message : str
        Human-readable error message
    code : str | None
        Error code for programmatic handling
    cause : Exception | None
        The underlying exception that caused this error

    Examples
    --------
    >>> raise ValidationError(
    ...     "Expected positive number, got -5",
    ...     code="VALIDATION_001",
    ... )
    """


class StrategyWarning(UserWarning):
    """Base warning for all strategy package warnings.

    All custom warnings in this package inherit from this class,
    allowing them to be filtered together using Python's warnings module.

    Examples
    --------
    >>> import warnings
    >>> warnings.warn("Something to note", StrategyWarning)

    >>> # Filter all strategy warnings
    >>> warnings.filterwarnings("ignore", category=StrategyWarning)
    """


class DataWarning(StrategyWarning):
    """Warning for data-related issues.

    This warning is issued when there are non-critical issues
    with the data, such as missing values or unusual patterns.

    Examples
    --------
    >>> import warnings
    >>> warnings.warn("Missing data for some dates", DataWarning)
    """


class NormalizationWarning(StrategyWarning):
    """Warning for normalization-related issues.

    This warning is issued when data normalization is applied
    or when there are potential issues with normalization.

    Examples
    --------
    >>> import warnings
    >>> warnings.warn("Data normalized to 0-1 range", NormalizationWarning)
    """


__all__ = [
    "ConfigurationError",
    "DataProviderError",
    "DataWarning",
    "InsufficientDataError",
    "InvalidTickerError",
    "NormalizationWarning",
    "StrategyError",
    "StrategyWarning",
    "ValidationError",
]

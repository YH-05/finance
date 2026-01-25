"""FRED-specific exception classes.

This module provides exception classes for FRED data fetching operations.
Uses the simple exception pattern (inheritance only, no additional fields).

Exception Hierarchy
-------------------
FREDError (base)
    FREDValidationError (input validation failures)
    FREDFetchError (data fetching failures)
"""


class FREDError(Exception):
    """Base exception for FRED operations.

    All FRED-specific exceptions inherit from this class.

    Parameters
    ----------
    message : str
        Human-readable error message
    """


class FREDValidationError(FREDError):
    """Exception raised when input validation fails.

    This exception is raised when:
    - API key is not provided or invalid
    - Series ID format is invalid
    - Required parameters are missing or malformed

    Parameters
    ----------
    message : str
        Human-readable error message describing the validation failure

    Examples
    --------
    >>> raise FREDValidationError("FRED API key not provided")
    >>> raise FREDValidationError("Invalid series ID: gdp (must be uppercase)")
    """


class FREDFetchError(FREDError):
    """Exception raised when data fetching fails.

    This exception is raised when:
    - FRED API returns an error
    - Network connectivity issues occur
    - Requested data is not found
    - API rate limits are exceeded

    Parameters
    ----------
    message : str
        Human-readable error message describing the fetch failure

    Examples
    --------
    >>> raise FREDFetchError("Failed to fetch FRED series GDP: API Error")
    >>> raise FREDFetchError("No data found for FRED series: INVALID")
    """


__all__ = [
    "FREDError",
    "FREDFetchError",
    "FREDValidationError",
]

"""Custom exception classes for the edgar package.

This module provides a hierarchy of exception classes for handling
various error conditions when interacting with SEC EDGAR data.

All exceptions include:
- Error messages with context
- Optional context dictionary for additional details

Exception Hierarchy
-------------------
EdgarError (base)
    FilingNotFoundError (filing retrieval failures)
    SectionNotFoundError (section extraction failures)
    CacheError (cache operation failures)
    RateLimitError (SEC EDGAR rate limiting)
"""

from typing import Any

from utils_core.logging import get_logger

logger = get_logger(__name__)


class EdgarError(Exception):
    """Base exception for all edgar package errors.

    All custom exceptions in this package inherit from this class,
    providing a consistent interface for error handling.

    Parameters
    ----------
    message : str
        Human-readable error message
    context : dict[str, Any]
        Additional context about the error

    Attributes
    ----------
    message : str
        The error message
    context : dict[str, Any]
        Additional error context

    Examples
    --------
    >>> try:
    ...     raise EdgarError(
    ...         "Failed to fetch filing",
    ...         context={"cik": "0001234567", "form_type": "10-K"},
    ...     )
    ... except EdgarError as e:
    ...     print(e.context)
    {'cik': '0001234567', 'form_type': '10-K'}
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class FilingNotFoundError(EdgarError):
    """Exception raised when a filing cannot be found or retrieved.

    This exception is raised when:
    - A filing with the specified CIK/accession number does not exist
    - The filing data cannot be downloaded from EDGAR
    - Network errors prevent filing retrieval

    Parameters
    ----------
    message : str
        Human-readable error message
    context : dict[str, Any]
        Additional context (e.g., CIK, form type, date range)

    Examples
    --------
    >>> raise FilingNotFoundError(
    ...     "Filing not found for CIK 0001234567",
    ...     context={"cik": "0001234567", "form_type": "10-K"},
    ... )
    """


class SectionNotFoundError(EdgarError):
    """Exception raised when a section cannot be extracted from a filing.

    This exception is raised when:
    - The requested section key does not exist in the filing
    - The section content cannot be parsed or extracted
    - The filing format is not supported for section extraction

    Parameters
    ----------
    message : str
        Human-readable error message
    context : dict[str, Any]
        Additional context (e.g., section key, filing ID)

    Examples
    --------
    >>> raise SectionNotFoundError(
    ...     "Section item_1 not found in filing",
    ...     context={"section_key": "item_1", "filing_id": "0001234567-24-000001"},
    ... )
    """


class CacheError(EdgarError):
    """Exception raised when cache operations fail.

    This exception is raised when:
    - Cache read/write operations fail
    - Cache directory cannot be created
    - Cache files are corrupted

    Parameters
    ----------
    message : str
        Human-readable error message
    context : dict[str, Any]
        Additional context (e.g., operation type, cache path)

    Examples
    --------
    >>> raise CacheError(
    ...     "Failed to write cache entry",
    ...     context={"operation": "write", "path": "/cache/filing.json"},
    ... )
    """


class RateLimitError(EdgarError):
    """Exception raised when SEC EDGAR rate limit is exceeded.

    SEC EDGAR enforces rate limits on API requests. This exception
    is raised when the rate limit is hit and requests are being throttled.

    Parameters
    ----------
    message : str
        Human-readable error message
    context : dict[str, Any]
        Additional context (e.g., retry_after, request_count)

    Examples
    --------
    >>> raise RateLimitError(
    ...     "SEC EDGAR rate limit exceeded",
    ...     context={"retry_after": 10, "requests_per_second": 10},
    ... )
    """


__all__ = [
    "CacheError",
    "EdgarError",
    "FilingNotFoundError",
    "RateLimitError",
    "SectionNotFoundError",
]

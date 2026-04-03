"""Custom exception classes for the pipeline package.

This module provides a hierarchy of exception classes for handling
various error conditions during market data pipeline execution.

All exceptions include:
- Error messages with context
- Optional context dictionary for additional details

Exception Hierarchy
-------------------
PipelineError (base)
    PhaseError (phase execution failures)
    StorageError (database / persistence failures)
    CollectorError (data collection / API failures)
    QueueError (queue management failures)
    TickerNormalizationError (ticker symbol normalisation failures)

See Also
--------
edgar.errors : Reference implementation pattern (BaseError → subclasses).
market.pipeline.models : PhaseResult / PipelineResult used with these errors.
"""

from typing import Any

from utils_core.logging import get_logger

logger = get_logger(__name__)


class PipelineError(Exception):
    """Base exception for all pipeline package errors.

    All custom exceptions in this package inherit from this class,
    providing a consistent interface for error handling across the
    multi-phase market data pipeline.

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Optional additional context about the error.

    Attributes
    ----------
    message : str
        The error message.
    context : dict[str, Any]
        Additional error context (empty dict when not provided).

    Examples
    --------
    >>> try:
    ...     raise PipelineError(
    ...         "Pipeline execution failed",
    ...         context={"phase": 1, "symbol": "AAPL"},
    ...     )
    ... except PipelineError as e:
    ...     print(e.context)
    {'phase': 1, 'symbol': 'AAPL'}
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict[str, Any] = context or {}


class PhaseError(PipelineError):
    """Exception raised when a pipeline phase fails during execution.

    This exception is raised when:
    - A pipeline phase encounters an unrecoverable error
    - Phase prerequisites are not met
    - Phase output validation fails

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., phase number, symbol, error details).

    Examples
    --------
    >>> raise PhaseError(
    ...     "Phase 2 failed: no queue entries found",
    ...     context={"phase": 2, "queue_count": 0},
    ... )
    """


class StorageError(PipelineError):
    """Exception raised when database or persistence operations fail.

    This exception is raised when:
    - SQLite read/write operations fail
    - Database connection cannot be established
    - Schema migration fails
    - Data serialisation/deserialisation fails

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., operation type, table name, db path).

    Examples
    --------
    >>> raise StorageError(
    ...     "Failed to upsert earnings calendar record",
    ...     context={"table": "nc_earnings_calendar", "symbol": "AAPL"},
    ... )
    """


class CollectorError(PipelineError):
    """Exception raised when data collection or external API calls fail.

    This exception is raised when:
    - An external API returns an unexpected response
    - Network errors prevent data retrieval
    - Rate limits are exceeded during collection
    - Parsing of API responses fails

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., source, symbol, status code).

    Examples
    --------
    >>> raise CollectorError(
    ...     "NASDAQ API returned 429",
    ...     context={"source": "nasdaq", "symbol": "AAPL", "status_code": 429},
    ... )
    """


class QueueError(PipelineError):
    """Exception raised when queue management operations fail.

    This exception is raised when:
    - Queue entry creation or update fails
    - Queue state transitions are invalid
    - Queue polling encounters an error
    - Duplicate queue entries are detected

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., queue table, symbol, current state).

    Examples
    --------
    >>> raise QueueError(
    ...     "Invalid state transition: pending -> completed",
    ...     context={"symbol": "AAPL", "from_state": "pending", "to_state": "completed"},
    ... )
    """


class TickerNormalizationError(PipelineError):
    """Exception raised when ticker symbol normalisation fails.

    This exception is raised when:
    - An unknown normalisation target is specified
    - The input symbol cannot be parsed

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., symbol, target, reason).

    Examples
    --------
    >>> raise TickerNormalizationError(
    ...     "Unknown normalisation target: 'unknown_exchange'",
    ...     context={"symbol": "AAPL", "target": "unknown_exchange"},
    ... )
    """


__all__ = [
    "CollectorError",
    "PhaseError",
    "PipelineError",
    "QueueError",
    "StorageError",
    "TickerNormalizationError",
]

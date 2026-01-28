"""Logging configuration for the market package.

This module provides a simple logging interface that wraps
the finance package's logging configuration.
"""

from typing import Any

from structlog import BoundLogger

from utils_core.logging import get_logger as _get_logger


def get_logger(name: str, **context: Any) -> BoundLogger:
    """Get a structured logger instance with optional context.

    Parameters
    ----------
    name : str
        Name of the logger (typically __name__)
    **context : Any
        Initial context to bind to the logger

    Returns
    -------
    BoundLogger
        Configured structlog logger instance

    Example
    -------
    >>> logger = get_logger(__name__)
    >>> logger.info("Processing started", items_count=100)
    """
    return _get_logger(name, **context)

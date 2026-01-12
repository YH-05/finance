"""Logger factory with lazy initialization to avoid circular imports.

This module provides a centralized logger creation function that handles
import errors gracefully with a standard library fallback.
"""

from logging import Logger


def create_logger(name: str, *, module: str | None = None) -> Logger:
    """Create a logger with lazy initialization to avoid circular imports.

    This function attempts to use the structured logging configuration from
    logging_config. If that import fails (e.g., during circular import scenarios),
    it falls back to Python's standard logging.

    Parameters
    ----------
    name : str
        Logger name, typically __name__ of the calling module
    module : str | None, default=None
        Optional module identifier for structured logging context

    Returns
    -------
    Logger
        Configured logger instance

    Examples
    --------
    >>> from market_analysis.utils.logger_factory import create_logger
    >>> logger = create_logger(__name__, module="visualization")
    >>> logger.info("Processing data", item_count=10)
    """
    try:
        from .logging_config import get_logger

        return get_logger(name, module=module)  # type: ignore[return-value]
    except ImportError:
        import logging

        fallback_logger = logging.getLogger(name)
        if not fallback_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(levelname)s - %(name)s - %(message)s")
            )
            fallback_logger.addHandler(handler)
        return fallback_logger


__all__ = ["create_logger"]

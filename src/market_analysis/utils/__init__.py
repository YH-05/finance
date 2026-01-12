"""Utility functions for the market_analysis package."""

from .cache import (
    DEFAULT_CACHE_CONFIG,
    DEFAULT_CACHE_DB_PATH,
    PERSISTENT_CACHE_CONFIG,
    SQLiteCache,
    create_persistent_cache,
    generate_cache_key,
    get_cache,
    reset_cache,
)
from .logger_factory import create_logger
from .logging_config import get_logger, log_context, set_log_level, setup_logging
from .retry import (
    DEFAULT_RETRY_CONFIG,
    RETRYABLE_EXCEPTIONS,
    RetryableOperation,
    create_retry_decorator,
    retry_on_rate_limit,
    retry_with_fallback,
    with_retry,
)
from .ticker_registry import (
    PRESET_GROUPS,
    TickerInfo,
    TickerRegistry,
    get_ticker_registry,
)
from .validators import (
    DATE_FORMATS,
    SYMBOL_PATTERN,
    Validator,
    validate_fetch_options,
)

__all__ = [
    "DATE_FORMATS",
    "DEFAULT_CACHE_CONFIG",
    "DEFAULT_CACHE_DB_PATH",
    "DEFAULT_RETRY_CONFIG",
    "PERSISTENT_CACHE_CONFIG",
    "PRESET_GROUPS",
    "RETRYABLE_EXCEPTIONS",
    "SYMBOL_PATTERN",
    "RetryableOperation",
    "SQLiteCache",
    "TickerInfo",
    "TickerRegistry",
    "Validator",
    "create_logger",
    "create_persistent_cache",
    "create_retry_decorator",
    "generate_cache_key",
    "get_cache",
    "get_logger",
    "get_ticker_registry",
    "log_context",
    "reset_cache",
    "retry_on_rate_limit",
    "retry_with_fallback",
    "set_log_level",
    "setup_logging",
    "validate_fetch_options",
    "with_retry",
]

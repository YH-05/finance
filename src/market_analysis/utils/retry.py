"""Retry utilities with exponential backoff using tenacity.

This module provides retry decorators and utilities for handling
transient failures in data fetching operations.
"""

import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ..errors import DataFetchError, RateLimitError
from ..types import RetryConfig
from .logging_config import get_logger

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")

# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
)

# Exceptions that should trigger a retry
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    DataFetchError,
    RateLimitError,
)


def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log information about a retry attempt.

    Parameters
    ----------
    retry_state : RetryCallState
        State information from tenacity
    """
    attempt = retry_state.attempt_number
    outcome = retry_state.outcome

    if outcome is None:
        return

    exception = outcome.exception()
    if exception:
        logger.warning(
            "Retry attempt failed",
            attempt=attempt,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            next_wait=getattr(retry_state, "next_action", None),
        )


def _log_retry_success(retry_state: RetryCallState) -> None:
    """Log when a retry eventually succeeds.

    Parameters
    ----------
    retry_state : RetryCallState
        State information from tenacity
    """
    if retry_state.attempt_number > 1:
        logger.info(
            "Operation succeeded after retry",
            total_attempts=retry_state.attempt_number,
        )


def _log_retry_exhausted(retry_state: RetryCallState) -> None:
    """Log when all retries are exhausted and re-raise the exception.

    Parameters
    ----------
    retry_state : RetryCallState
        State information from tenacity

    Raises
    ------
    Exception
        The original exception that caused the retry to fail
    """
    outcome = retry_state.outcome
    exception = outcome.exception() if outcome else None

    logger.error(
        "All retry attempts exhausted",
        total_attempts=retry_state.attempt_number,
        final_exception=type(exception).__name__ if exception else None,
        final_message=str(exception) if exception else None,
    )

    # Re-raise the original exception
    if exception:
        raise exception


def create_retry_decorator(
    config: RetryConfig | None = None,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Create a retry decorator with the specified configuration.

    Parameters
    ----------
    config : RetryConfig | None
        Retry configuration. Uses DEFAULT_RETRY_CONFIG if not specified.
    retryable_exceptions : tuple[type[Exception], ...] | None
        Exception types that should trigger a retry.
        Uses RETRYABLE_EXCEPTIONS if not specified.

    Returns
    -------
    Callable
        A decorator that adds retry behavior to a function

    Examples
    --------
    >>> @create_retry_decorator(RetryConfig(max_attempts=5))
    ... def fetch_data():
    ...     # API call that might fail
    ...     pass
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG

    if retryable_exceptions is None:
        retryable_exceptions = RETRYABLE_EXCEPTIONS

    return retry(
        stop=stop_after_attempt(config.max_attempts),
        wait=wait_exponential_jitter(
            initial=config.initial_delay,
            max=config.max_delay,
            exp_base=config.exponential_base,
            jitter=config.max_delay / 4 if config.jitter else 0,
        ),
        retry=retry_if_exception_type(retryable_exceptions),
        before_sleep=_log_retry_attempt,
        after=_log_retry_success,
        retry_error_callback=_log_retry_exhausted,
        reraise=True,
    )


def with_retry(
    config: RetryConfig | None = None,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to add retry behavior with exponential backoff.

    This is a convenience wrapper around create_retry_decorator
    for use as a decorator factory.

    Parameters
    ----------
    config : RetryConfig | None
        Retry configuration
    retryable_exceptions : tuple[type[Exception], ...] | None
        Exception types that should trigger a retry

    Returns
    -------
    Callable
        A decorator that adds retry behavior

    Examples
    --------
    >>> @with_retry(RetryConfig(max_attempts=3))
    ... def fetch_price(symbol: str) -> float:
    ...     return api.get_price(symbol)

    >>> @with_retry()  # Uses default config
    ... def fetch_data():
    ...     pass
    """
    decorator = create_retry_decorator(config, retryable_exceptions)

    def wrapper(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def inner(*args: P.args, **kwargs: P.kwargs) -> T:
            logger.debug(
                "Starting retryable operation",
                function=func.__name__,
                max_attempts=config.max_attempts
                if config
                else DEFAULT_RETRY_CONFIG.max_attempts,
            )
            return decorator(func)(*args, **kwargs)

        return inner

    return wrapper


def retry_on_rate_limit(
    max_attempts: int = 5,
    initial_delay: float = 2.0,
    max_delay: float = 120.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator specifically for handling rate limit errors.

    Uses longer delays appropriate for API rate limiting.

    Parameters
    ----------
    max_attempts : int
        Maximum number of retry attempts (default: 5)
    initial_delay : float
        Initial delay in seconds (default: 2.0)
    max_delay : float
        Maximum delay in seconds (default: 120.0)

    Returns
    -------
    Callable
        A decorator that adds rate-limit-aware retry behavior

    Examples
    --------
    >>> @retry_on_rate_limit(max_attempts=3)
    ... def call_api():
    ...     # API call that might be rate limited
    ...     pass
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=2.0,
        jitter=True,
    )

    return with_retry(config=config, retryable_exceptions=(RateLimitError,))


def retry_with_fallback(
    fallback_value: T,
    config: RetryConfig | None = None,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that returns a fallback value if all retries fail.

    Parameters
    ----------
    fallback_value : T
        Value to return if all retries fail
    config : RetryConfig | None
        Retry configuration
    retryable_exceptions : tuple[type[Exception], ...] | None
        Exception types that should trigger a retry

    Returns
    -------
    Callable
        A decorator that adds retry behavior with fallback

    Examples
    --------
    >>> @retry_with_fallback(fallback_value=None)
    ... def fetch_optional_data():
    ...     return api.get_data()
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG

    if retryable_exceptions is None:
        retryable_exceptions = RETRYABLE_EXCEPTIONS

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retry_decorator = create_retry_decorator(config, retryable_exceptions)

            try:
                return retry_decorator(func)(*args, **kwargs)
            except retryable_exceptions:
                logger.warning(
                    "Returning fallback value after retry exhaustion",
                    function=func.__name__,
                    fallback_value=fallback_value,
                )
                return fallback_value

        return wrapper

    return decorator


class RetryableOperation:
    """Context manager for retryable operations.

    Provides a way to retry a block of code without using decorators.

    Parameters
    ----------
    config : RetryConfig | None
        Retry configuration
    operation_name : str
        Name of the operation for logging

    Examples
    --------
    >>> with RetryableOperation(config, "fetch_price") as op:
    ...     for attempt in op:
    ...         try:
    ...             result = api.get_price("AAPL")
    ...             break
    ...         except ConnectionError:
    ...             op.retry(attempt)
    """

    def __init__(
        self,
        config: RetryConfig | None = None,
        operation_name: str = "operation",
    ) -> None:
        self.config = config or DEFAULT_RETRY_CONFIG
        self.operation_name = operation_name
        self._attempt = 0
        self._last_exception: Exception | None = None

    def __enter__(self) -> "RetryableOperation":
        logger.debug(
            "Starting retryable operation",
            operation=self.operation_name,
            max_attempts=self.config.max_attempts,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_type is not None:
            logger.error(
                "Retryable operation failed",
                operation=self.operation_name,
                attempts=self._attempt,
                exception_type=exc_type.__name__,
                exception_message=str(exc_val),
            )
        return False

    def __iter__(self) -> "RetryableOperation":
        return self

    def __next__(self) -> int:
        if self._attempt >= self.config.max_attempts:
            raise StopIteration
        self._attempt += 1
        return self._attempt

    @property
    def attempt(self) -> int:
        """Current attempt number (1-indexed)."""
        return self._attempt

    def retry(self, attempt: int) -> None:
        """Record a retry and calculate delay.

        Parameters
        ----------
        attempt : int
            The current attempt number
        """
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay,
        )

        if self.config.jitter:
            delay *= 0.5 + random.random()  # nosec B311

        logger.warning(
            "Retrying operation",
            operation=self.operation_name,
            attempt=attempt,
            next_attempt=attempt + 1,
            delay_seconds=round(delay, 2),
        )

        time.sleep(delay)


__all__ = [
    "DEFAULT_RETRY_CONFIG",
    "RETRYABLE_EXCEPTIONS",
    "RetryableOperation",
    "create_retry_decorator",
    "retry_on_rate_limit",
    "retry_with_fallback",
    "with_retry",
]

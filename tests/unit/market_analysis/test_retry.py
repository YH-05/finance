"""Tests for market_analysis.utils.retry module."""

import pytest

from market_analysis.types import RetryConfig
from market_analysis.utils.retry import (
    DEFAULT_RETRY_CONFIG,
    RetryableOperation,
    create_retry_decorator,
    retry_with_fallback,
    with_retry,
)


class TestRetryConfig:
    """Tests for RetryConfig defaults."""

    def test_default_config(self) -> None:
        """Test default retry config values."""
        assert DEFAULT_RETRY_CONFIG.max_attempts == 3
        assert DEFAULT_RETRY_CONFIG.initial_delay == 1.0
        assert DEFAULT_RETRY_CONFIG.max_delay == 60.0
        assert DEFAULT_RETRY_CONFIG.exponential_base == 2.0
        assert DEFAULT_RETRY_CONFIG.jitter is True


class TestCreateRetryDecorator:
    """Tests for create_retry_decorator."""

    def test_successful_function(self) -> None:
        """Test decorator with successful function."""
        call_count = 0

        @create_retry_decorator()
        def successful_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self) -> None:
        """Test decorator retries on failure."""
        call_count = 0

        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)

        @create_retry_decorator(config)
        def failing_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 3

    def test_max_retries_exhausted(self) -> None:
        """Test decorator raises after max retries."""
        call_count = 0

        config = RetryConfig(max_attempts=2, initial_delay=0.01, jitter=False)

        @create_retry_decorator(config)
        def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            always_fails()

        assert call_count == 2


class TestWithRetry:
    """Tests for with_retry decorator."""

    def test_with_retry_success(self) -> None:
        """Test with_retry decorator with successful function."""

        @with_retry()
        def func() -> str:
            return "success"

        assert func() == "success"

    def test_with_retry_custom_config(self) -> None:
        """Test with_retry with custom config."""
        call_count = 0
        config = RetryConfig(max_attempts=2, initial_delay=0.01, jitter=False)

        @with_retry(config=config)
        def func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Fail")
            return "success"

        result = func()
        assert result == "success"
        assert call_count == 2


class TestRetryWithFallback:
    """Tests for retry_with_fallback decorator."""

    def test_returns_fallback_on_exhaustion(self) -> None:
        """Test fallback value is returned when retries exhausted."""
        config = RetryConfig(max_attempts=2, initial_delay=0.01, jitter=False)

        @retry_with_fallback(fallback_value="default", config=config)
        def always_fails() -> str:
            raise ConnectionError("Always fails")

        result = always_fails()
        assert result == "default"

    def test_returns_result_on_success(self) -> None:
        """Test actual result is returned on success."""

        @retry_with_fallback(fallback_value="default")
        def succeeds() -> str:
            return "actual"

        result = succeeds()
        assert result == "actual"


class TestRetryableOperation:
    """Tests for RetryableOperation context manager."""

    def test_iteration(self) -> None:
        """Test iteration over attempts."""
        config = RetryConfig(max_attempts=3)
        attempts = []

        with RetryableOperation(config, "test") as op:
            for attempt in op:
                attempts.append(attempt)
                if attempt == 2:
                    break

        assert attempts == [1, 2]

    def test_attempt_property(self) -> None:
        """Test attempt property."""
        with RetryableOperation() as op:
            for attempt in op:
                assert op.attempt == attempt
                break

    def test_max_attempts_stops_iteration(self) -> None:
        """Test iteration stops at max attempts."""
        config = RetryConfig(max_attempts=2)
        attempts = []

        with RetryableOperation(config) as op:
            for attempt in op:
                attempts.append(attempt)

        assert attempts == [1, 2]

    def test_retry_with_delay(self) -> None:
        """Test retry method introduces delay."""
        import time

        config = RetryConfig(
            max_attempts=2,
            initial_delay=0.05,
            jitter=False,
        )

        start = time.perf_counter()
        with RetryableOperation(config, "test") as op:
            for attempt in op:
                if attempt == 1:
                    op.retry(attempt)
                    continue
                break
        elapsed = time.perf_counter() - start

        # Should have at least one delay of ~0.05s
        assert elapsed >= 0.04

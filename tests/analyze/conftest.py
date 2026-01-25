"""Pytest configuration and fixtures for analyze package tests."""

import logging
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ============================================================================
# Technical Analysis Fixtures
# ============================================================================


@pytest.fixture
def sample_prices() -> pd.Series:
    """Create sample price data for testing.

    Returns a Series of 100 prices starting from 100.0 with
    random-like variations for realistic testing.
    """
    np.random.seed(42)  # 再現性のためシード固定
    base_price = 100.0
    returns = np.random.normal(0.0005, 0.02, 100)  # 平均0.05%、標準偏差2%
    prices = base_price * np.cumprod(1 + returns)
    return pd.Series(prices)


@pytest.fixture
def uptrend_prices() -> pd.Series:
    """Create uptrending price data.

    Returns a Series of prices with a consistent upward trend.
    """
    return pd.Series([100.0 + i * 0.5 for i in range(50)])


@pytest.fixture
def downtrend_prices() -> pd.Series:
    """Create downtrending price data.

    Returns a Series of prices with a consistent downward trend.
    """
    return pd.Series([150.0 - i * 0.5 for i in range(50)])


@pytest.fixture
def volatile_prices() -> pd.Series:
    """Create highly volatile price data.

    Returns a Series of prices with large swings.
    """
    prices = []
    current = 100.0
    for i in range(50):
        change = 5.0 if i % 2 == 0 else -5.0
        current += change
        prices.append(current)
    return pd.Series(prices)


@pytest.fixture
def constant_prices() -> pd.Series:
    """Create constant price data.

    Returns a Series of prices with no variation.
    """
    return pd.Series([100.0] * 50)


# ============================================================================
# Statistics Fixtures
# ============================================================================


@pytest.fixture
def sample_series() -> pd.Series:
    """Create a sample numeric series for testing."""
    return pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])


@pytest.fixture
def sample_series_with_nan() -> pd.Series:
    """Create a sample series with NaN values."""
    return pd.Series([1.0, 2.0, np.nan, 4.0, 5.0, np.nan, 7.0, 8.0, 9.0, 10.0])


@pytest.fixture
def empty_series() -> pd.Series:
    """Create an empty series."""
    return pd.Series(dtype=np.float64)


@pytest.fixture
def constant_series() -> pd.Series:
    """Create a series with constant values (zero variance)."""
    return pd.Series([5.0, 5.0, 5.0, 5.0, 5.0])


@pytest.fixture
def sample_returns(sample_prices: pd.Series) -> pd.Series:
    """Create sample return data from sample prices.

    Returns a Series of percentage returns.
    """
    return sample_prices.pct_change()


@pytest.fixture
def benchmark_returns() -> pd.Series:
    """Create benchmark return series for beta calculations."""
    return pd.Series(
        [0.005, 0.01, -0.005, 0.015, -0.01, 0.0075, 0.0025, -0.0025, 0.01, 0.005]
    )


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create sample DataFrame with multiple series for correlation matrix."""
    return pd.DataFrame(
        {
            "A": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "B": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            "C": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
        }
    )


@pytest.fixture
def skewed_series() -> pd.Series:
    """Create a skewed series for skewness testing."""
    # Right-skewed data (positive skewness)
    return pd.Series([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 10.0, 15.0, 20.0])


# ============================================================================
# Common Fixtures
# ============================================================================


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment variables for each test."""
    test_env_vars = [var for var in os.environ if var.startswith("TEST_")]
    for var in test_env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture logs for testing with proper level."""
    caplog.set_level(logging.DEBUG)
    return caplog

"""Pytest configuration and fixtures for analyze package tests."""

import logging
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


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


@pytest.fixture
def sample_returns(sample_prices: pd.Series) -> pd.Series:
    """Create sample return data from sample prices.

    Returns a Series of percentage returns.
    """
    return sample_prices.pct_change()


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

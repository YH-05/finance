"""Pytest configuration and fixtures for analyze package tests."""

import logging
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# =============================================================================
# Technical Analysis Fixtures
# =============================================================================


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


# =============================================================================
# Sector Analysis Fixtures
# =============================================================================


@pytest.fixture
def mock_etf_returns() -> dict[str, float | None]:
    """Create mock ETF returns for all sectors."""
    return {
        "basic-materials": 0.015,
        "communication-services": -0.008,
        "consumer-cyclical": 0.022,
        "consumer-defensive": 0.005,
        "energy": -0.012,
        "financial-services": 0.018,
        "healthcare": 0.003,
        "industrials": 0.010,
        "real-estate": -0.015,
        "technology": 0.035,
        "utilities": 0.002,
    }


@pytest.fixture
def mock_etf_returns_with_none() -> dict[str, float | None]:
    """Create mock ETF returns with some None values."""
    return {
        "basic-materials": 0.015,
        "communication-services": None,
        "consumer-cyclical": 0.022,
        "consumer-defensive": None,
        "energy": -0.012,
        "financial-services": 0.018,
        "healthcare": None,
        "industrials": 0.010,
        "real-estate": -0.015,
        "technology": 0.035,
        "utilities": 0.002,
    }


@pytest.fixture
def mock_top_companies() -> list[dict[str, Any]]:
    """Create mock top companies data for a sector."""
    return [
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "weight": 0.15},
        {"symbol": "AAPL", "name": "Apple Inc.", "weight": 0.12},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "weight": 0.11},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "weight": 0.08},
        {"symbol": "META", "name": "Meta Platforms Inc.", "weight": 0.06},
    ]


@pytest.fixture
def mock_price_dataframe() -> pd.DataFrame:
    """Create mock price DataFrame for ETF returns calculation."""
    dates = pd.date_range(start="2024-01-01", periods=30, freq="B")
    data = {
        "XLK": [100 + i * 0.5 for i in range(30)],
        "XLF": [50 + i * 0.2 for i in range(30)],
        "XLE": [80 - i * 0.1 for i in range(30)],
    }
    df = pd.DataFrame(data, index=dates)
    # Create MultiIndex columns like yfinance returns
    df.columns = pd.MultiIndex.from_product([["Close"], df.columns])
    return df


@pytest.fixture
def mock_yfinance_download():
    """Create a mock for yfinance.download function."""

    def _create_mock(return_value: pd.DataFrame | None = None):
        mock = MagicMock()
        mock.return_value = return_value
        return mock

    return _create_mock


@pytest.fixture
def sample_as_of() -> datetime:
    """Create a sample as_of datetime."""
    return datetime(2024, 1, 15, 10, 30, 0)


# =============================================================================
# Common Fixtures
# =============================================================================


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


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    """Create sample data for testing."""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]


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

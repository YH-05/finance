"""Pytest configuration and fixtures for market package.

This module provides common fixtures for testing the market package,
including sample OHLCV data, MarketDataResult, and AnalysisResult fixtures.
"""

import logging
import os
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from market.types import (
    AnalysisResult,
    DataSource,
    MarketDataResult,
)

# Check if blpapi is available
try:
    import blpapi

    HAS_BLPAPI = True
except ImportError:
    HAS_BLPAPI = False


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip Bloomberg tests if blpapi is not available.

    This hook modifies the test collection to skip all tests in the
    bloomberg directories when the blpapi module is not installed.
    """
    if HAS_BLPAPI:
        return

    skip_blpapi = pytest.mark.skip(reason="blpapi not available")
    for item in items:
        if "bloomberg" in str(item.fspath):
            item.add_marker(skip_blpapi)


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


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Create sample OHLCV data for testing.

    Returns
    -------
    pd.DataFrame
        A DataFrame with 30 days of OHLCV data indexed by date.
    """
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, 30)
    prices = base_price * np.cumprod(1 + returns)

    return pd.DataFrame(
        {
            "open": prices * (1 + np.random.uniform(-0.01, 0.01, 30)),
            "high": prices * (1 + np.random.uniform(0, 0.02, 30)),
            "low": prices * (1 - np.random.uniform(0, 0.02, 30)),
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, 30),
        },
        index=dates,
    )


@pytest.fixture
def market_data_result(sample_ohlcv_data: pd.DataFrame) -> MarketDataResult:
    """Create a MarketDataResult for testing.

    Parameters
    ----------
    sample_ohlcv_data : pd.DataFrame
        Sample OHLCV data fixture.

    Returns
    -------
    MarketDataResult
        A MarketDataResult with AAPL symbol.
    """
    return MarketDataResult(
        symbol="AAPL",
        data=sample_ohlcv_data,
        source=DataSource.YFINANCE,
        fetched_at=datetime(2024, 1, 31, 12, 0, 0),
        from_cache=False,
        metadata={"info": "test"},
    )


@pytest.fixture
def analysis_result(sample_ohlcv_data: pd.DataFrame) -> AnalysisResult:
    """Create an AnalysisResult for testing.

    Parameters
    ----------
    sample_ohlcv_data : pd.DataFrame
        Sample OHLCV data fixture.

    Returns
    -------
    AnalysisResult
        An AnalysisResult with SMA indicator and statistics.
    """
    sma_series = pd.Series(sample_ohlcv_data["close"].rolling(20).mean())
    return AnalysisResult(
        symbol="AAPL",
        data=sample_ohlcv_data,
        indicators={"sma_20": sma_series},
        statistics={"mean_return": 0.05, "std_return": 0.02},
        analyzed_at=datetime(2024, 1, 31, 12, 0, 0),
    )

"""Pytest configuration and fixtures for analyze package tests."""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest


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

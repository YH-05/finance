"""Pytest fixtures for market.bloomberg tests.

This module provides common fixtures for Bloomberg module testing.
All fixtures use mocks to avoid actual Bloomberg API connections.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


@pytest.fixture
def mock_blpapi():
    """Mock the blpapi module.

    This fixture patches the blpapi import to prevent actual Bloomberg
    API connections during testing.
    """
    with patch("market.bloomberg.fetcher.blpapi") as mock:
        # Setup default successful connection
        mock_session = MagicMock()
        mock_session.start.return_value = True
        mock_session.openService.return_value = True
        mock_session.stop.return_value = None
        mock.Session.return_value = mock_session

        yield mock


@pytest.fixture
def sample_historical_df() -> pd.DataFrame:
    """Create a sample historical data DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with date, PX_LAST, PX_VOLUME, PX_OPEN, PX_HIGH, PX_LOW columns
    """
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
            ),
            "PX_LAST": [150.0, 151.0, 152.0, 151.5, 153.0],
            "PX_VOLUME": [1000000, 1100000, 1200000, 900000, 1300000],
            "PX_OPEN": [149.0, 150.0, 151.0, 152.0, 151.0],
            "PX_HIGH": [151.0, 152.0, 153.0, 152.5, 154.0],
            "PX_LOW": [148.0, 149.0, 150.0, 150.5, 150.0],
        }
    )


@pytest.fixture
def sample_reference_df() -> pd.DataFrame:
    """Create a sample reference data DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with security, NAME, GICS_SECTOR_NAME, CRNCY columns
    """
    return pd.DataFrame(
        {
            "security": ["AAPL US Equity", "MSFT US Equity", "GOOGL US Equity"],
            "NAME": ["Apple Inc", "Microsoft Corp", "Alphabet Inc"],
            "GICS_SECTOR_NAME": [
                "Information Technology",
                "Information Technology",
                "Communication Services",
            ],
            "CRNCY": ["USD", "USD", "USD"],
        }
    )


@pytest.fixture
def sample_financial_df() -> pd.DataFrame:
    """Create a sample financial data DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with security, IS_EPS, SALES_REV_TURN columns
    """
    return pd.DataFrame(
        {
            "security": ["AAPL US Equity"],
            "IS_EPS": [6.5],
            "SALES_REV_TURN": [394328000000],
            "NET_INCOME": [99803000000],
            "EBITDA": [130541000000],
        }
    )


@pytest.fixture
def sample_news_stories() -> list:
    """Create sample news stories.

    Note: This returns dicts because NewsStory may not be importable yet.
    In actual tests, convert these to NewsStory objects.

    Returns
    -------
    list
        List of news story dictionaries
    """
    return [
        {
            "story_id": "BBG123456789",
            "headline": "Apple Reports Q4 Earnings Beat",
            "datetime": datetime(2024, 1, 15, 9, 30),
            "body": "Apple Inc. reported quarterly earnings that exceeded analyst expectations...",
            "source": "Bloomberg News",
        },
        {
            "story_id": "BBG987654321",
            "headline": "Tech Stocks Rally on Strong Earnings",
            "datetime": datetime(2024, 1, 16, 14, 0),
            "body": "Technology stocks rose sharply following strong earnings reports...",
            "source": "Bloomberg News",
        },
    ]


@pytest.fixture
def sample_index_members() -> list[str]:
    """Create sample S&P 500 index members.

    Returns
    -------
    list[str]
        List of Bloomberg security identifiers
    """
    return [
        "AAPL US Equity",
        "MSFT US Equity",
        "GOOGL US Equity",
        "AMZN US Equity",
        "NVDA US Equity",
        "META US Equity",
        "TSLA US Equity",
        "BRK/B US Equity",
        "UNH US Equity",
        "JPM US Equity",
    ]


@pytest.fixture
def temp_db_path(tmp_path) -> str:
    """Create a temporary database path.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary path fixture

    Returns
    -------
    str
        Path to temporary SQLite database
    """
    return str(tmp_path / "bloomberg_test.db")

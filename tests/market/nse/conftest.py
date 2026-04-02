"""Shared test fixtures for market.nse test suite.

NSE モジュール全体で共有されるフィクスチャを定義する。
"""

from unittest.mock import MagicMock

import pytest

from market.nse.types import NseConfig, RetryConfig


@pytest.fixture()
def nse_config() -> NseConfig:
    """Default NseConfig for tests."""
    return NseConfig()


@pytest.fixture()
def retry_config() -> RetryConfig:
    """Default RetryConfig for tests."""
    return RetryConfig()


@pytest.fixture()
def fast_retry_config() -> RetryConfig:
    """Fast RetryConfig for tests that need minimal delays."""
    return RetryConfig(max_attempts=3, initial_delay=0.01)


@pytest.fixture()
def mock_httpx_response_200() -> MagicMock:
    """Mock httpx.Response with status_code 200 returning JSON data."""
    response = MagicMock()
    response.status_code = 200
    response.text = '{"data": []}'
    response.content = b'{"data": []}'
    response.json.return_value = {"data": []}
    return response


@pytest.fixture()
def mock_httpx_response_200_html() -> MagicMock:
    """Mock httpx.Response with status_code 200 returning HTML (cookie expired)."""
    response = MagicMock()
    response.status_code = 200
    response.text = "<!DOCTYPE html><html><body>Please login</body></html>"
    response.content = b"<!DOCTYPE html><html><body>Please login</body></html>"
    response.json.side_effect = ValueError("Response is not JSON")
    return response


@pytest.fixture()
def mock_httpx_response_403() -> MagicMock:
    """Mock httpx.Response with status_code 403."""
    response = MagicMock()
    response.status_code = 403
    response.text = "Forbidden"
    return response


@pytest.fixture()
def mock_httpx_response_429() -> MagicMock:
    """Mock httpx.Response with status_code 429."""
    response = MagicMock()
    response.status_code = 429
    response.text = "Too Many Requests"
    return response


@pytest.fixture()
def mock_httpx_response_500() -> MagicMock:
    """Mock httpx.Response with status_code 500."""
    response = MagicMock()
    response.status_code = 500
    response.text = "Internal Server Error"
    return response


@pytest.fixture()
def sample_equity_stockindices_response() -> dict:
    """Sample NSE /api/equity-stockIndices response payload."""
    return {
        "name": "NIFTY 50",
        "timestamp": "02-Apr-2026 15:30:00",
        "data": [
            {
                "symbol": "NIFTY 50",
                "identifier": "NIFTY50",
                "open": 22500.00,
                "dayHigh": 22750.50,
                "dayLow": 22450.00,
                "lastPrice": 22700.25,
                "previousClose": 22450.00,
                "change": 250.25,
                "pChange": 1.11,
                "totalTradedVolume": 250000000,
                "totalTradedValue": 5625000000.00,
                "lastUpdateTime": "02-Apr-2026 15:30:00",
                "yearHigh": 24200.00,
                "yearLow": 19800.00,
                "perChange365d": 14.65,
                "perChange30d": 2.31,
            },
            {
                "symbol": "RELIANCE",
                "identifier": "RELIANCE",
                "series": "EQ",
                "open": 2450.00,
                "dayHigh": 2480.50,
                "dayLow": 2440.00,
                "lastPrice": 2470.25,
                "previousClose": 2445.00,
                "change": 25.25,
                "pChange": 1.03,
                "totalTradedVolume": 5000000,
                "totalTradedValue": 12345678900.00,
                "lastUpdateTime": "02-Apr-2026 15:30:00",
                "yearHigh": 2900.00,
                "yearLow": 2100.00,
                "perChange365d": 5.40,
                "perChange30d": 1.20,
            },
        ],
        "advance": {"declines": "24", "advances": "25", "unchanged": "1"},
        "metadata": {
            "indexName": "Nifty 50",
            "open": "22500.00",
            "high": "22750.50",
            "low": "22450.00",
            "previousClose": "22450.00",
            "last": "22700.25",
            "percChange": "1.11",
            "change": "250.25",
            "breadcrumbDt": "02-Apr-2026 15:30:00",
            "isFNOSec": True,
            "isCASec": False,
        },
    }

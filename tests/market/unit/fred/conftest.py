"""Pytest configuration and fixtures for market.fred tests."""

from collections.abc import Generator
from unittest.mock import patch

import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def mock_load_dotenv() -> Generator[None]:
    """Disable load_dotenv during tests to ensure env var mocking works."""
    with patch("market.fred.fetcher.load_dotenv"):
        yield


@pytest.fixture
def mock_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """環境変数にモック API キーを設定。

    Returns
    -------
    str
        設定したモック API キー
    """
    api_key = "test_api_key_12345"
    monkeypatch.setenv("FRED_API_KEY", api_key)
    return api_key


@pytest.fixture
def sample_series() -> pd.Series:
    """テスト用のサンプル FRED シリーズデータを作成。

    Returns
    -------
    pd.Series
        日付インデックスを持つサンプルデータ
    """
    return pd.Series(
        [100.0, 101.5, 102.3],
        index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
        name="GDP",
    )


@pytest.fixture
def sample_series_info() -> pd.Series:
    """テスト用のシリーズメタデータを作成。

    Returns
    -------
    pd.Series
        シリーズ情報
    """
    return pd.Series(
        {"id": "GDP", "title": "Gross Domestic Product", "frequency": "Quarterly"}
    )

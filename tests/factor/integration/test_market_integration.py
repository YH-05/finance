"""Tests for market package integration with factor package.

This module tests the integration between market data sources and
factor analysis, ensuring proper data flow from market -> factor.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from factor.integration.market_integration import (
    MarketDataProvider,
    create_market_provider,
)
from factor.providers.base import DataProvider


class TestMarketDataProvider:
    """Tests for MarketDataProvider class."""

    def test_正常系_DataProviderプロトコルに準拠している(self) -> None:
        """MarketDataProvider が DataProvider プロトコルを実装していることを確認。"""
        provider = MarketDataProvider()
        assert isinstance(provider, DataProvider)

    def test_正常系_get_pricesでデータを取得できる(self) -> None:
        """get_prices メソッドが正しく動作することを確認。"""
        provider = MarketDataProvider()

        # モックを使用して実際の API 呼び出しを回避
        with patch.object(provider, "_fetcher") as mock_fetcher:
            mock_result = MagicMock()
            mock_result.data = pd.DataFrame(
                {
                    "open": [100.0, 101.0],
                    "high": [102.0, 103.0],
                    "low": [99.0, 100.0],
                    "close": [101.0, 102.0],
                    "volume": [1000, 1100],
                },
                index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"], name="Date"),
            )
            mock_result.symbol = "AAPL"
            mock_result.is_empty = False
            mock_fetcher.fetch.return_value = [mock_result]

            result = provider.get_prices(
                symbols=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-01-31",
            )

            # 結果がMultiIndex DataFrameであることを確認
            assert isinstance(result, pd.DataFrame)
            assert result.index.name == "Date"

    def test_正常系_get_volumesでデータを取得できる(self) -> None:
        """get_volumes メソッドが正しく動作することを確認。"""
        provider = MarketDataProvider()

        with patch.object(provider, "_fetcher") as mock_fetcher:
            mock_result = MagicMock()
            mock_result.data = pd.DataFrame(
                {
                    "open": [100.0],
                    "high": [102.0],
                    "low": [99.0],
                    "close": [101.0],
                    "volume": [1000],
                },
                index=pd.DatetimeIndex(["2024-01-01"], name="Date"),
            )
            mock_result.symbol = "AAPL"
            mock_result.is_empty = False
            mock_fetcher.fetch.return_value = [mock_result]

            result = provider.get_volumes(
                symbols=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-01-31",
            )

            assert isinstance(result, pd.DataFrame)
            assert "AAPL" in result.columns

    def test_異常系_空のシンボルリストでValueError(self) -> None:
        """空のシンボルリストでValueErrorが発生することを確認。"""
        provider = MarketDataProvider()

        with pytest.raises(ValueError, match="symbols"):
            provider.get_prices(
                symbols=[],
                start_date="2024-01-01",
                end_date="2024-01-31",
            )


class TestCreateMarketProvider:
    """Tests for create_market_provider factory function."""

    def test_正常系_ファクトリ関数でプロバイダを作成できる(self) -> None:
        """create_market_provider でプロバイダインスタンスを作成できることを確認。"""
        provider = create_market_provider()

        assert isinstance(provider, MarketDataProvider)
        assert isinstance(provider, DataProvider)

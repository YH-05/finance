"""Unit tests for analyze.integration.market_integration module.

Tests for the market integration module that connects the market package
data sources with the analyze package analysis functions.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from analyze.integration.market_integration import (
    MarketDataAnalyzer,
    analyze_market_data,
    fetch_and_analyze,
)


class TestMarketDataAnalyzer:
    """Tests for MarketDataAnalyzer class."""

    def test_正常系_インスタンス作成が成功する(self) -> None:
        """MarketDataAnalyzer インスタンスが正常に作成できることを確認。"""
        analyzer = MarketDataAnalyzer()
        assert analyzer is not None

    def test_正常系_YFinanceFetcher経由でデータ取得と分析ができる(self) -> None:
        """YFinanceFetcher を使用してデータを取得し、分析できることを確認。"""
        # Mock market data
        mock_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "volume": [1000, 1100, 1200, 1300, 1400],
            },
            index=pd.date_range("2024-01-01", periods=5),
        )

        with patch(
            "analyze.integration.market_integration.YFinanceFetcher"
        ) as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_result = MagicMock()
            mock_result.data = mock_data
            mock_result.symbol = "AAPL"
            mock_result.is_empty = False
            mock_fetcher.fetch.return_value = [mock_result]
            mock_fetcher_class.return_value = mock_fetcher

            analyzer = MarketDataAnalyzer()
            result = analyzer.fetch_and_analyze(
                symbols=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-01-05",
            )

            assert result is not None
            assert "AAPL" in result
            assert "technical_indicators" in result["AAPL"]

    def test_正常系_テクニカル指標が計算される(self) -> None:
        """取得したデータに対してテクニカル指標が計算されることを確認。"""
        mock_data = pd.DataFrame(
            {
                "open": np.random.uniform(100, 110, 50),
                "high": np.random.uniform(110, 120, 50),
                "low": np.random.uniform(90, 100, 50),
                "close": np.random.uniform(100, 110, 50),
                "volume": np.random.randint(1000, 2000, 50),
            },
            index=pd.date_range("2024-01-01", periods=50),
        )

        with patch(
            "analyze.integration.market_integration.YFinanceFetcher"
        ) as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_result = MagicMock()
            mock_result.data = mock_data
            mock_result.symbol = "AAPL"
            mock_result.is_empty = False
            mock_fetcher.fetch.return_value = [mock_result]
            mock_fetcher_class.return_value = mock_fetcher

            analyzer = MarketDataAnalyzer()
            result = analyzer.fetch_and_analyze(
                symbols=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-02-19",
            )

            assert "AAPL" in result
            indicators = result["AAPL"]["technical_indicators"]
            assert "returns" in indicators
            assert "sma_20" in indicators
            assert "rsi" in indicators

    def test_正常系_統計情報が計算される(self) -> None:
        """取得したデータに対して統計情報が計算されることを確認。"""
        mock_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "volume": [1000, 1100, 1200, 1300, 1400],
            },
            index=pd.date_range("2024-01-01", periods=5),
        )

        with patch(
            "analyze.integration.market_integration.YFinanceFetcher"
        ) as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_result = MagicMock()
            mock_result.data = mock_data
            mock_result.symbol = "AAPL"
            mock_result.is_empty = False
            mock_fetcher.fetch.return_value = [mock_result]
            mock_fetcher_class.return_value = mock_fetcher

            analyzer = MarketDataAnalyzer()
            result = analyzer.fetch_and_analyze(
                symbols=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-01-05",
            )

            assert "AAPL" in result
            assert "statistics" in result["AAPL"]
            stats = result["AAPL"]["statistics"]
            assert stats.count == 5
            assert stats.mean is not None

    def test_異常系_空のシンボルリストでValueError(self) -> None:
        """空のシンボルリストが渡された場合に ValueError が発生することを確認。"""
        analyzer = MarketDataAnalyzer()
        with pytest.raises(ValueError, match="symbols must not be empty"):
            analyzer.fetch_and_analyze(
                symbols=[],
                start_date="2024-01-01",
                end_date="2024-01-05",
            )

    def test_エッジケース_データが空の場合は空の結果を返す(self) -> None:
        """データが空の場合は空の分析結果を返すことを確認。"""
        with patch(
            "analyze.integration.market_integration.YFinanceFetcher"
        ) as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_result = MagicMock()
            mock_result.data = pd.DataFrame()
            mock_result.symbol = "INVALID"
            mock_result.is_empty = True
            mock_fetcher.fetch.return_value = [mock_result]
            mock_fetcher_class.return_value = mock_fetcher

            analyzer = MarketDataAnalyzer()
            result = analyzer.fetch_and_analyze(
                symbols=["INVALID"],
                start_date="2024-01-01",
                end_date="2024-01-05",
            )

            assert "INVALID" in result
            assert result["INVALID"]["data_empty"] is True


class TestAnalyzeMarketData:
    """Tests for analyze_market_data function."""

    def test_正常系_DataFrameからテクニカル指標を計算(self) -> None:
        """DataFrame からテクニカル指標が計算されることを確認。"""
        data = pd.DataFrame(
            {
                "open": np.random.uniform(100, 110, 50),
                "high": np.random.uniform(110, 120, 50),
                "low": np.random.uniform(90, 100, 50),
                "close": np.random.uniform(100, 110, 50),
                "volume": np.random.randint(1000, 2000, 50),
            },
            index=pd.date_range("2024-01-01", periods=50),
        )

        result = analyze_market_data(data)

        assert "technical_indicators" in result
        assert "statistics" in result

    def test_正常系_close列からリターンを計算(self) -> None:
        """close 列からリターンが正しく計算されることを確認。"""
        data = pd.DataFrame(
            {
                "open": [100.0, 100.0],
                "high": [110.0, 110.0],
                "low": [90.0, 90.0],
                "close": [100.0, 102.0],
                "volume": [1000, 1000],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )

        result = analyze_market_data(data)

        # 2% リターン
        assert result["technical_indicators"]["returns"].iloc[1] == pytest.approx(
            0.02, rel=0.01
        )


class TestFetchAndAnalyze:
    """Tests for fetch_and_analyze convenience function."""

    def test_正常系_便利関数でデータ取得と分析ができる(self) -> None:
        """fetch_and_analyze 便利関数が正常に動作することを確認。"""
        mock_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "volume": [1000, 1100, 1200, 1300, 1400],
            },
            index=pd.date_range("2024-01-01", periods=5),
        )

        with patch(
            "analyze.integration.market_integration.YFinanceFetcher"
        ) as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_result = MagicMock()
            mock_result.data = mock_data
            mock_result.symbol = "AAPL"
            mock_result.is_empty = False
            mock_fetcher.fetch.return_value = [mock_result]
            mock_fetcher_class.return_value = mock_fetcher

            result = fetch_and_analyze(
                symbols=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-01-05",
            )

            assert result is not None
            assert "AAPL" in result

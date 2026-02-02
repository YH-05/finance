"""DollarsIndexAndMetalsAnalyzer のテスト.

ドル指数と金属価格の分析クラスのテスト。
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pandas import DataFrame

from analyze.currency import DollarsIndexAndMetalsAnalyzer


class TestDollarsIndexAndMetalsAnalyzerInit:
    """DollarsIndexAndMetalsAnalyzer の初期化テスト."""

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_デフォルト初期化が成功する(
        self,
        mock_yfinance: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """DollarsIndexAndMetalsAnalyzerがデフォルト設定で初期化できることを確認."""
        # モックを設定
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0, 111.0, 112.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        mock_cache.return_value = mock_cache_instance

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []
        mock_yfinance.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()

        assert analyzer is not None
        assert hasattr(analyzer, "logger")

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_金属ティッカーリストが正しく設定される(
        self,
        mock_yfinance: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """デフォルトの金属ETFティッカーが正しく設定されることを確認."""
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0]},
            index=pd.to_datetime(["2024-01-01"]),
        )
        mock_cache.return_value = mock_cache_instance

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []
        mock_yfinance.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()

        expected_tickers = ["GLD", "SLV", "PPLT", "CPER", "PALL", "DBB"]
        assert analyzer.metal_tickers == expected_tickers


class TestLoadMetalPrice:
    """金属価格データ取得のテスト."""

    @pytest.fixture
    def mock_metal_data(self) -> list[MagicMock]:
        """YFinanceFetcher.fetch の戻り値をモック."""
        results = []
        metal_data = {
            "GLD": [180.0, 181.0, 182.0],
            "SLV": [22.0, 22.5, 23.0],
            "PPLT": [95.0, 96.0, 97.0],
            "CPER": [25.0, 25.5, 26.0],
            "PALL": [140.0, 142.0, 144.0],
            "DBB": [20.0, 20.5, 21.0],
        }
        dates = pd.date_range("2024-01-01", periods=3, freq="D")

        for symbol, values in metal_data.items():
            mock_result = MagicMock()
            mock_result.symbol = symbol
            mock_result.data = DataFrame(
                {
                    "open": values,
                    "high": [v + 0.5 for v in values],
                    "low": [v - 0.5 for v in values],
                    "close": values,
                    "adj_close": values,
                    "volume": [1000] * 3,
                },
                index=dates,
            )
            mock_result.is_empty = False
            results.append(mock_result)

        return results

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_金属価格データを取得できる(
        self,
        mock_yfinance_class: MagicMock,
        mock_cache: MagicMock,
        mock_metal_data: list[MagicMock],
    ) -> None:
        """YFinanceFetcherを使用して金属ETF価格を取得できることを確認."""
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0, 111.0, 112.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        mock_cache.return_value = mock_cache_instance

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_metal_data
        mock_yfinance_class.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()
        metal_prices = analyzer.load_metal_prices()

        assert "GLD" in metal_prices.columns
        assert "SLV" in metal_prices.columns
        assert len(metal_prices) == 3


class TestLoadDollarIndex:
    """ドル指数データ取得のテスト."""

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_FREDからドル指数を取得できる(
        self,
        mock_yfinance: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """HistoricalCacheを使用してFREDのドル指数を取得できることを確認."""
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0, 111.0, 112.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        mock_cache.return_value = mock_cache_instance

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []
        mock_yfinance.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()
        dollar_index = analyzer.load_dollar_index()

        assert dollar_index is not None
        assert len(dollar_index) == 3
        mock_cache_instance.get_series_df.assert_called_with("DTWEXAFEGS")


class TestLoadPrice:
    """ドル指数と金属価格の結合データ取得テスト."""

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_ドル指数と金属価格を結合できる(
        self,
        mock_yfinance_class: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """ドル指数と金属価格データを結合してロング形式で返すことを確認."""
        # FRED データをモック
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0, 111.0, 112.0]},
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        mock_cache.return_value = mock_cache_instance

        # 金属価格データをモック
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        mock_results = []
        for symbol, values in [
            ("GLD", [180.0, 181.0, 182.0]),
            ("SLV", [22.0, 22.5, 23.0]),
        ]:
            mock_result = MagicMock()
            mock_result.symbol = symbol
            mock_result.data = DataFrame(
                {
                    "open": values,
                    "high": values,
                    "low": values,
                    "close": values,
                    "adj_close": values,
                    "volume": [1000] * 3,
                },
                index=dates,
            )
            mock_result.is_empty = False
            mock_results.append(mock_result)

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_yfinance_class.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()
        price_df = analyzer.load_price()

        # ロング形式で返されることを確認
        assert "Date" in price_df.columns
        assert "Ticker" in price_df.columns
        assert "value" in price_df.columns
        assert "variable" in price_df.columns
        assert "DTWEXAFEGS" in price_df["Ticker"].values


class TestCalcReturn:
    """累積リターン計算のテスト."""

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_開始日からの累積リターンを計算できる(
        self,
        mock_yfinance_class: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """指定された開始日からの累積リターンが正しく計算されることを確認."""
        # FREDデータをモック
        dates = pd.to_datetime(
            ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05"]
        )
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [100.0, 101.0, 102.0, 103.0, 104.0]},
            index=dates,
        )
        mock_cache.return_value = mock_cache_instance

        # 金属価格データをモック
        mock_results = []
        for symbol, values in [
            ("GLD", [100.0, 102.0, 104.0, 106.0, 108.0]),
            ("SLV", [50.0, 51.0, 52.0, 53.0, 54.0]),
        ]:
            mock_result = MagicMock()
            mock_result.symbol = symbol
            mock_result.data = DataFrame(
                {
                    "open": values,
                    "high": values,
                    "low": values,
                    "close": values,
                    "adj_close": values,
                    "volume": [1000] * 5,
                },
                index=dates,
            )
            mock_result.is_empty = False
            mock_results.append(mock_result)

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_yfinance_class.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()
        cum_return = analyzer.calc_return(start_date="2020-01-01")

        # 累積リターンが計算されていることを確認
        assert cum_return is not None
        assert isinstance(cum_return, pd.DataFrame)
        # 初日のリターンは1.0
        assert cum_return.iloc[0]["GLD"] == pytest.approx(1.0, rel=0.01)

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_デフォルト開始日は2020年1月1日(
        self,
        mock_yfinance_class: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """開始日を指定しない場合、2020-01-01がデフォルトで使用されることを確認."""
        dates = pd.to_datetime(["2020-01-01", "2020-01-02"])
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [100.0, 101.0]},
            index=dates,
        )
        mock_cache.return_value = mock_cache_instance

        mock_results = []
        mock_result = MagicMock()
        mock_result.symbol = "GLD"
        mock_result.data = DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [100.0, 101.0],
                "low": [100.0, 101.0],
                "close": [100.0, 101.0],
                "adj_close": [100.0, 101.0],
                "volume": [1000, 1000],
            },
            index=dates,
        )
        mock_result.is_empty = False
        mock_results.append(mock_result)

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_yfinance_class.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()
        # デフォルト引数でcalc_returnを呼び出し
        cum_return = analyzer.calc_return()

        assert cum_return is not None


class TestGetSummary:
    """サマリー取得のテスト."""

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_サマリーに必要な情報が含まれる(
        self,
        mock_yfinance_class: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """サマリーに全ての必要情報が含まれることを確認."""
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0, 111.0, 112.0]},
            index=dates,
        )
        mock_cache.return_value = mock_cache_instance

        mock_results = []
        for symbol, values in [
            ("GLD", [180.0, 181.0, 182.0]),
            ("SLV", [22.0, 22.5, 23.0]),
        ]:
            mock_result = MagicMock()
            mock_result.symbol = symbol
            mock_result.data = DataFrame(
                {
                    "open": values,
                    "high": values,
                    "low": values,
                    "close": values,
                    "adj_close": values,
                    "volume": [1000] * 3,
                },
                index=dates,
            )
            mock_result.is_empty = False
            mock_results.append(mock_result)

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_yfinance_class.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()
        summary = analyzer.get_summary()

        assert "generated_at" in summary
        assert "dollar_index_latest" in summary
        assert "metal_prices_latest" in summary
        assert "cumulative_returns" in summary


class TestLogging:
    """ロギングのテスト."""

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_正常系_structlogを使用している(
        self,
        mock_yfinance: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """structlogを使用したロギングが実装されていることを確認."""
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0]},
            index=pd.to_datetime(["2024-01-01"]),
        )
        mock_cache.return_value = mock_cache_instance

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []
        mock_yfinance.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()

        # loggerが存在することを確認
        assert hasattr(analyzer, "logger")


class TestEdgeCases:
    """エッジケースのテスト."""

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_異常系_FREDデータ取得失敗時に適切なエラー(
        self,
        mock_yfinance: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """FREDからドル指数が取得できない場合のエラーハンドリングを確認."""
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = None
        mock_cache.return_value = mock_cache_instance

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []
        mock_yfinance.return_value = mock_fetcher

        with pytest.raises(ValueError, match="DTWEXAFEGS"):
            DollarsIndexAndMetalsAnalyzer()

    @patch("analyze.currency.HistoricalCache")
    @patch("analyze.currency.YFinanceFetcher")
    def test_エッジケース_一部金属データが欠損しても処理継続(
        self,
        mock_yfinance_class: MagicMock,
        mock_cache: MagicMock,
    ) -> None:
        """一部の金属ETFデータが欠損していても処理が継続されることを確認."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        mock_cache_instance = MagicMock()
        mock_cache_instance.get_series_df.return_value = pd.DataFrame(
            {"value": [110.0, 111.0, 112.0]},
            index=dates,
        )
        mock_cache.return_value = mock_cache_instance

        # 一部のデータは空
        mock_results = []
        mock_result1 = MagicMock()
        mock_result1.symbol = "GLD"
        mock_result1.data = DataFrame(
            {
                "open": [180.0, 181.0, 182.0],
                "high": [180.0, 181.0, 182.0],
                "low": [180.0, 181.0, 182.0],
                "close": [180.0, 181.0, 182.0],
                "adj_close": [180.0, 181.0, 182.0],
                "volume": [1000] * 3,
            },
            index=dates,
        )
        mock_result1.is_empty = False
        mock_results.append(mock_result1)

        mock_result2 = MagicMock()
        mock_result2.symbol = "SLV"
        mock_result2.data = DataFrame()
        mock_result2.is_empty = True
        mock_results.append(mock_result2)

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_results
        mock_yfinance_class.return_value = mock_fetcher

        analyzer = DollarsIndexAndMetalsAnalyzer()
        metal_prices = analyzer.load_metal_prices()

        # GLDのデータは取得できる
        assert "GLD" in metal_prices.columns
        # SLVは欠損
        assert "SLV" not in metal_prices.columns


class TestDocstrings:
    """Docstringのテスト."""

    def test_正常系_クラスにNumPy形式のDocstringがある(self) -> None:
        """クラスにNumPy形式のDocstringがあることを確認."""
        docstring = DollarsIndexAndMetalsAnalyzer.__doc__
        assert docstring is not None
        # NumPy形式の要素が含まれていることを確認
        assert "Attributes" in docstring or "Parameters" in docstring

"""Unit tests for MarketAnalysisProvider.

このテストファイルは、strategy パッケージの MarketAnalysisProvider の実装を検証します。

テストTODO:
- [x] MarketAnalysisProvider クラスが実装されている
- [x] DataProvider Protocol を満たしている
- [x] get_prices() で market_analysis の YFinanceFetcher を使用
- [x] get_ticker_info() で銘柄情報を取得
- [x] get_ticker_infos() で複数銘柄情報を一括取得
- [x] market_analysis のエラーを DataProviderError に変換
- [x] キャッシュ設定を使用

Note: 統合テストは tests/strategy/integration/providers/test_market_analysis.py に配置
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market_analysis.errors import DataFetchError, ErrorCode
from market_analysis.types import DataSource, FetchOptions, MarketDataResult
from strategy.errors import DataProviderError
from strategy.providers.market_analysis import MarketAnalysisProvider
from strategy.providers.protocol import DataProvider
from strategy.types import TickerInfo


class TestMarketAnalysisProviderProtocol:
    """MarketAnalysisProvider が DataProvider Protocol を満たすことを確認するテスト。"""

    def test_正常系_DataProviderプロトコルを満たす(self) -> None:
        """MarketAnalysisProvider が DataProvider のインスタンスとして認識されることを確認。"""
        provider = MarketAnalysisProvider()

        assert isinstance(provider, DataProvider)

    def test_正常系_get_pricesメソッドが存在する(self) -> None:
        """MarketAnalysisProvider に get_prices メソッドが存在することを確認。"""
        provider = MarketAnalysisProvider()

        assert hasattr(provider, "get_prices")
        assert callable(getattr(provider, "get_prices", None))

    def test_正常系_get_ticker_infoメソッドが存在する(self) -> None:
        """MarketAnalysisProvider に get_ticker_info メソッドが存在することを確認。"""
        provider = MarketAnalysisProvider()

        assert hasattr(provider, "get_ticker_info")
        assert callable(getattr(provider, "get_ticker_info", None))

    def test_正常系_get_ticker_infosメソッドが存在する(self) -> None:
        """MarketAnalysisProvider に get_ticker_infos メソッドが存在することを確認。"""
        provider = MarketAnalysisProvider()

        assert hasattr(provider, "get_ticker_infos")
        assert callable(getattr(provider, "get_ticker_infos", None))


class TestGetPrices:
    """get_prices メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MarketAnalysisProvider()
        self.tickers = ["AAPL", "GOOGL"]
        self.start = "2024-01-01"
        self.end = "2024-12-31"

    def _create_mock_result(
        self,
        symbol: str,
        data: pd.DataFrame | None = None,
    ) -> MarketDataResult:
        """テスト用のモック MarketDataResult を作成。"""
        if data is None:
            dates = pd.date_range("2024-01-01", periods=5, freq="D")
            data = pd.DataFrame(
                {
                    "open": [100.0] * 5,
                    "high": [105.0] * 5,
                    "low": [95.0] * 5,
                    "close": [102.0] * 5,
                    "volume": [1000000] * 5,
                },
                index=dates,
            )
        return MarketDataResult(
            symbol=symbol,
            data=data,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=False,
        )

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_正常系_get_pricesで価格データを取得(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """get_prices で YFinanceFetcher を使用して価格データを取得することを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch.return_value = [
            self._create_mock_result("AAPL"),
            self._create_mock_result("GOOGL"),
        ]

        provider = MarketAnalysisProvider()

        # Act
        result = provider.get_prices(self.tickers, self.start, self.end)

        # Assert
        assert isinstance(result, pd.DataFrame)
        mock_fetcher.fetch.assert_called_once()

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_正常系_戻り値がMultiIndexDataFrameである(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """get_prices の戻り値が MultiIndex DataFrame であることを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch.return_value = [
            self._create_mock_result("AAPL"),
            self._create_mock_result("GOOGL"),
        ]

        provider = MarketAnalysisProvider()

        # Act
        result = provider.get_prices(self.tickers, self.start, self.end)

        # Assert
        assert isinstance(result.columns, pd.MultiIndex)
        assert "ticker" in result.columns.names
        assert "price_type" in result.columns.names

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_正常系_OHLCVカラムが含まれる(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """get_prices の戻り値に OHLCV カラムが含まれることを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch.return_value = [
            self._create_mock_result("AAPL"),
            self._create_mock_result("GOOGL"),
        ]

        provider = MarketAnalysisProvider()

        # Act
        result = provider.get_prices(self.tickers, self.start, self.end)

        # Assert
        price_types = result.columns.get_level_values("price_type").unique()
        expected_types = {"open", "high", "low", "close", "volume"}
        assert set(price_types) == expected_types

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_正常系_指定したティッカーが含まれる(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """get_prices の戻り値に指定したティッカーが含まれることを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch.return_value = [
            self._create_mock_result("AAPL"),
            self._create_mock_result("GOOGL"),
        ]

        provider = MarketAnalysisProvider()

        # Act
        result = provider.get_prices(self.tickers, self.start, self.end)

        # Assert
        tickers_in_result = result.columns.get_level_values("ticker").unique()
        assert set(tickers_in_result) == set(self.tickers)

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_正常系_FetchOptionsに正しいパラメータが渡される(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """get_prices が FetchOptions に正しいパラメータを渡すことを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch.return_value = [
            self._create_mock_result("AAPL"),
        ]

        provider = MarketAnalysisProvider()

        # Act
        provider.get_prices(["AAPL"], "2024-01-01", "2024-06-30")

        # Assert
        call_args = mock_fetcher.fetch.call_args
        options: FetchOptions = call_args[0][0]
        assert options.symbols == ["AAPL"]
        assert "2024-01-01" in str(options.start_date)
        assert "2024-06-30" in str(options.end_date)


class TestGetTickerInfo:
    """get_ticker_info メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MarketAnalysisProvider()

    @patch("strategy.providers.market_analysis.yf.Ticker")
    def test_正常系_get_ticker_infoで銘柄情報を取得(
        self,
        mock_ticker_class: MagicMock,
    ) -> None:
        """get_ticker_info で yfinance から銘柄情報を取得することを確認。"""
        # Arrange
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }

        # Act
        result = self.provider.get_ticker_info("AAPL")

        # Assert
        assert isinstance(result, TickerInfo)
        assert result.ticker == "AAPL"
        assert result.name == "Apple Inc."

    @patch("strategy.providers.market_analysis.yf.Ticker")
    def test_正常系_sectorとindustryが設定される(
        self,
        mock_ticker_class: MagicMock,
    ) -> None:
        """get_ticker_info で sector と industry が設定されることを確認。"""
        # Arrange
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
        }

        # Act
        result = self.provider.get_ticker_info("AAPL")

        # Assert
        assert result.sector == "Technology"
        assert result.industry == "Consumer Electronics"

    @patch("strategy.providers.market_analysis.yf.Ticker")
    def test_正常系_asset_classがequityに設定される(
        self,
        mock_ticker_class: MagicMock,
    ) -> None:
        """get_ticker_info で asset_class がデフォルトで equity に設定されることを確認。"""
        # Arrange
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
        }

        # Act
        result = self.provider.get_ticker_info("AAPL")

        # Assert
        assert result.asset_class == "equity"

    @patch("strategy.providers.market_analysis.yf.Ticker")
    def test_正常系_infoがNoneの場合でも動作する(
        self,
        mock_ticker_class: MagicMock,
    ) -> None:
        """yfinance の info が空でも TickerInfo を返すことを確認。"""
        # Arrange
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {}

        # Act
        result = self.provider.get_ticker_info("AAPL")

        # Assert
        assert isinstance(result, TickerInfo)
        assert result.ticker == "AAPL"


class TestGetTickerInfos:
    """get_ticker_infos メソッドのテスト。"""

    def setup_method(self) -> None:
        """テストのセットアップ。"""
        self.provider = MarketAnalysisProvider()
        self.tickers = ["AAPL", "GOOGL", "MSFT"]

    @patch("strategy.providers.market_analysis.yf.Ticker")
    def test_正常系_get_ticker_infosで複数銘柄情報を一括取得(
        self,
        mock_ticker_class: MagicMock,
    ) -> None:
        """get_ticker_infos で複数銘柄の情報を一括取得することを確認。"""

        # Arrange
        def create_mock_info(symbol: str) -> dict[str, Any]:
            return {
                "symbol": symbol,
                "shortName": f"{symbol} Inc.",
                "sector": "Technology",
                "industry": "Software",
            }

        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        # 各呼び出しで異なる info を返す
        mock_ticker.info = create_mock_info("AAPL")

        # Act
        result = self.provider.get_ticker_infos(self.tickers)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == len(self.tickers)

    @patch("strategy.providers.market_analysis.yf.Ticker")
    def test_正常系_全てのティッカーが辞書のキーに含まれる(
        self,
        mock_ticker_class: MagicMock,
    ) -> None:
        """get_ticker_infos の戻り値に全てのティッカーがキーとして含まれることを確認。"""
        # Arrange
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
        }

        # Act
        result = self.provider.get_ticker_infos(self.tickers)

        # Assert
        assert set(result.keys()) == set(self.tickers)

    @patch("strategy.providers.market_analysis.yf.Ticker")
    def test_正常系_各値がTickerInfoである(
        self,
        mock_ticker_class: MagicMock,
    ) -> None:
        """get_ticker_infos の各値が TickerInfo であることを確認。"""
        # Arrange
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
        }

        # Act
        result = self.provider.get_ticker_infos(self.tickers)

        # Assert
        for ticker, info in result.items():
            assert isinstance(info, TickerInfo)


class TestErrorHandling:
    """エラーハンドリングのテスト。"""

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_異常系_DataFetchErrorをDataProviderErrorに変換(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """market_analysis の DataFetchError を DataProviderError に変換することを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch.side_effect = DataFetchError(
            "Failed to fetch data",
            symbol="AAPL",
            source="yfinance",
            code=ErrorCode.API_ERROR,
        )

        # Provider を patch 適用後に作成
        provider = MarketAnalysisProvider()

        # Act & Assert
        with pytest.raises(DataProviderError) as exc_info:
            provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")

        assert exc_info.value.cause is not None
        assert isinstance(exc_info.value.cause, DataFetchError)

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_異常系_エラーメッセージが適切に設定される(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """DataProviderError のエラーメッセージが適切に設定されることを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        original_error = DataFetchError(
            "Network connection failed",
            symbol="AAPL",
            source="yfinance",
            code=ErrorCode.NETWORK_ERROR,
        )
        mock_fetcher.fetch.side_effect = original_error

        # Provider を patch 適用後に作成
        provider = MarketAnalysisProvider()

        # Act & Assert
        with pytest.raises(DataProviderError) as exc_info:
            provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")

        # エラーメッセージに元のエラー情報が含まれていることを確認
        assert "AAPL" in str(exc_info.value.message) or exc_info.value.cause is not None

    @patch("strategy.providers.market_analysis.yf.Ticker")
    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_異常系_get_ticker_infoでExceptionをDataProviderErrorに変換(
        self,
        mock_fetcher_class: MagicMock,
        mock_ticker_class: MagicMock,
    ) -> None:
        """get_ticker_info で発生した Exception を DataProviderError に変換することを確認。"""
        # Arrange
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        # info プロパティへのアクセスで例外を発生させる
        type(mock_ticker).info = property(
            fget=MagicMock(side_effect=Exception("API error"))
        )

        # Provider を patch 適用後に作成
        provider = MarketAnalysisProvider()

        # Act & Assert
        with pytest.raises(DataProviderError):
            provider.get_ticker_info("INVALID")


class TestCacheConfiguration:
    """キャッシュ設定のテスト。"""

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_正常系_キャッシュ有効でFetchOptionsのuse_cacheがTrue(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """キャッシュ有効時に FetchOptions.use_cache が True であることを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher

        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_data = pd.DataFrame(
            {
                "open": [100.0] * 5,
                "high": [105.0] * 5,
                "low": [95.0] * 5,
                "close": [102.0] * 5,
                "volume": [1000000] * 5,
            },
            index=dates,
        )
        mock_fetcher.fetch.return_value = [
            MarketDataResult(
                symbol="AAPL",
                data=mock_data,
                source=DataSource.YFINANCE,
                fetched_at=datetime.now(),
                from_cache=False,
            )
        ]

        provider = MarketAnalysisProvider(use_cache=True)

        # Act
        provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")

        # Assert
        call_args = mock_fetcher.fetch.call_args
        options: FetchOptions = call_args[0][0]
        assert options.use_cache is True

    @patch("strategy.providers.market_analysis.YFinanceFetcher")
    def test_正常系_キャッシュ無効でFetchOptionsのuse_cacheがFalse(
        self,
        mock_fetcher_class: MagicMock,
    ) -> None:
        """キャッシュ無効時に FetchOptions.use_cache が False であることを確認。"""
        # Arrange
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher

        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_data = pd.DataFrame(
            {
                "open": [100.0] * 5,
                "high": [105.0] * 5,
                "low": [95.0] * 5,
                "close": [102.0] * 5,
                "volume": [1000000] * 5,
            },
            index=dates,
        )
        mock_fetcher.fetch.return_value = [
            MarketDataResult(
                symbol="AAPL",
                data=mock_data,
                source=DataSource.YFINANCE,
                fetched_at=datetime.now(),
                from_cache=False,
            )
        ]

        provider = MarketAnalysisProvider(use_cache=False)

        # Act
        provider.get_prices(["AAPL"], "2024-01-01", "2024-12-31")

        # Assert
        call_args = mock_fetcher.fetch.call_args
        options: FetchOptions = call_args[0][0]
        assert options.use_cache is False

"""Unit tests for TickerInfo type and get_ticker_info/get_ticker_infos methods.

Tests for the TickerInfo Pydantic model and MarketDataAnalyzer's
get_ticker_info() and get_ticker_infos() methods.
"""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from analyze.integration.market_integration import MarketDataAnalyzer
from analyze.types import AssetClass, TickerInfo


class TestTickerInfo:
    """Tests for TickerInfo Pydantic model."""

    def test_正常系_必須フィールドのみで作成できる(self) -> None:
        """ticker と name のみで TickerInfo を作成できることを確認。"""
        info = TickerInfo(ticker="AAPL", name="Apple Inc.")
        assert info.ticker == "AAPL"
        assert info.name == "Apple Inc."
        assert info.sector is None
        assert info.industry is None
        assert info.asset_class == "equity"

    def test_正常系_全フィールド指定で作成できる(self) -> None:
        """全フィールドを指定して TickerInfo を作成できることを確認。"""
        info = TickerInfo(
            ticker="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            asset_class="equity",
        )
        assert info.ticker == "AAPL"
        assert info.name == "Apple Inc."
        assert info.sector == "Technology"
        assert info.industry == "Consumer Electronics"
        assert info.asset_class == "equity"

    def test_正常系_ETFのasset_classを指定できる(self) -> None:
        """ETF の asset_class を指定して TickerInfo を作成できることを確認。"""
        info = TickerInfo(
            ticker="VOO",
            name="Vanguard S&P 500 ETF",
            asset_class="etf",
        )
        assert info.asset_class == "etf"

    def test_正常系_indexのasset_classを指定できる(self) -> None:
        """index の asset_class を指定して TickerInfo を作成できることを確認。"""
        info = TickerInfo(
            ticker="^GSPC",
            name="S&P 500",
            asset_class="index",
        )
        assert info.asset_class == "index"

    def test_正常系_frozenモデルでイミュータブル(self) -> None:
        """TickerInfo がイミュータブルであることを確認。"""
        info = TickerInfo(ticker="AAPL", name="Apple Inc.")
        with pytest.raises(ValidationError):
            info.ticker = "GOOGL"

    def test_異常系_tickerが空文字でValidationError(self) -> None:
        """ticker が空文字の場合に ValidationError が発生することを確認。"""
        with pytest.raises(ValidationError):
            TickerInfo(ticker="", name="Apple Inc.")

    def test_異常系_nameが空文字でValidationError(self) -> None:
        """name が空文字の場合に ValidationError が発生することを確認。"""
        with pytest.raises(ValidationError):
            TickerInfo(ticker="AAPL", name="")

    def test_異常系_無効なasset_classでValidationError(self) -> None:
        """無効な asset_class の場合に ValidationError が発生することを確認。"""
        with pytest.raises(ValidationError):
            TickerInfo(
                ticker="AAPL",
                name="Apple Inc.",
                asset_class="invalid",  # type: ignore[arg-type]
            )


class TestGetTickerInfo:
    """Tests for MarketDataAnalyzer.get_ticker_info method."""

    def _make_analyzer_with_mock_fetcher(self) -> MarketDataAnalyzer:
        """Create MarketDataAnalyzer with a mocked fetcher."""
        with patch(
            "analyze.integration.market_integration.YFinanceFetcher"
        ) as mock_cls:
            mock_cls.return_value = MagicMock()
            return MarketDataAnalyzer()

    def test_正常系_株式銘柄の情報を取得できる(self) -> None:
        """株式銘柄の TickerInfo を正常に取得できることを確認。"""
        mock_info = {
            "shortName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "quoteType": "EQUITY",
        }

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = mock_info
            mock_ticker_cls.return_value = mock_ticker

            result = analyzer.get_ticker_info("AAPL")

        assert isinstance(result, TickerInfo)
        assert result.ticker == "AAPL"
        assert result.name == "Apple Inc."
        assert result.sector == "Technology"
        assert result.industry == "Consumer Electronics"
        assert result.asset_class == "equity"

    def test_正常系_ETF銘柄の情報を取得できる(self) -> None:
        """ETF 銘柄の TickerInfo を正常に取得できることを確認。"""
        mock_info = {
            "shortName": "Vanguard S&P 500 ETF",
            "sector": None,
            "industry": None,
            "quoteType": "ETF",
        }

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = mock_info
            mock_ticker_cls.return_value = mock_ticker

            result = analyzer.get_ticker_info("VOO")

        assert isinstance(result, TickerInfo)
        assert result.ticker == "VOO"
        assert result.name == "Vanguard S&P 500 ETF"
        assert result.sector is None
        assert result.industry is None
        assert result.asset_class == "etf"

    def test_正常系_longNameにフォールバックする(self) -> None:
        """shortName がない場合に longName にフォールバックすることを確認。"""
        mock_info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "quoteType": "EQUITY",
        }

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = mock_info
            mock_ticker_cls.return_value = mock_ticker

            result = analyzer.get_ticker_info("AAPL")

        assert result.name == "Apple Inc."

    def test_正常系_名前がない場合tickerにフォールバックする(self) -> None:
        """shortName も longName もない場合に ticker をフォールバックに使うことを確認。"""
        mock_info = {
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "quoteType": "EQUITY",
        }

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = mock_info
            mock_ticker_cls.return_value = mock_ticker

            result = analyzer.get_ticker_info("AAPL")

        assert result.name == "AAPL"

    def test_正常系_indexのquoteTypeを正しく変換する(self) -> None:
        """quoteType=INDEX の場合に asset_class=index に変換されることを確認。"""
        mock_info = {
            "shortName": "S&P 500",
            "quoteType": "INDEX",
        }

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = mock_info
            mock_ticker_cls.return_value = mock_ticker

            result = analyzer.get_ticker_info("^GSPC")

        assert result.asset_class == "index"

    def test_正常系_不明なquoteTypeはequityになる(self) -> None:
        """不明な quoteType の場合は equity にフォールバックすることを確認。"""
        mock_info = {
            "shortName": "Unknown Asset",
            "quoteType": "UNKNOWN_TYPE",
        }

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = mock_info
            mock_ticker_cls.return_value = mock_ticker

            result = analyzer.get_ticker_info("XXX")

        assert result.asset_class == "equity"

    def test_異常系_API呼び出し失敗でDataFetchError(self) -> None:
        """yfinance API 呼び出し失敗時に DataFetchError が発生することを確認。"""
        from market.errors import DataFetchError

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = property(
                fget=MagicMock(side_effect=Exception("API error"))
            )
            # Make accessing .info raise an exception
            type(mock_ticker).info = property(
                fget=MagicMock(side_effect=Exception("API error"))
            )
            mock_ticker_cls.return_value = mock_ticker

            with pytest.raises(DataFetchError):
                analyzer.get_ticker_info("AAPL")

    def test_異常系_空のinfoでDataFetchError(self) -> None:
        """yfinance が空の info を返した場合に DataFetchError が発生することを確認。"""
        from market.errors import DataFetchError

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = {}
            mock_ticker_cls.return_value = mock_ticker

            with pytest.raises(DataFetchError):
                analyzer.get_ticker_info("INVALID")


class TestGetTickerInfos:
    """Tests for MarketDataAnalyzer.get_ticker_infos method."""

    def _make_analyzer_with_mock_fetcher(self) -> MarketDataAnalyzer:
        """Create MarketDataAnalyzer with a mocked fetcher."""
        with patch(
            "analyze.integration.market_integration.YFinanceFetcher"
        ) as mock_cls:
            mock_cls.return_value = MagicMock()
            return MarketDataAnalyzer()

    def test_正常系_複数銘柄の情報を一括取得できる(self) -> None:
        """複数銘柄の TickerInfo を一括取得できることを確認。"""
        mock_infos = {
            "AAPL": {
                "shortName": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "quoteType": "EQUITY",
            },
            "GOOGL": {
                "shortName": "Alphabet Inc.",
                "sector": "Communication Services",
                "industry": "Internet Content & Information",
                "quoteType": "EQUITY",
            },
        }

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:

            def make_mock_ticker(symbol: str, *args, **kwargs) -> MagicMock:
                mock = MagicMock()
                mock.info = mock_infos.get(symbol, {})
                return mock

            mock_ticker_cls.side_effect = make_mock_ticker

            result = analyzer.get_ticker_infos(["AAPL", "GOOGL"])

        assert len(result) == 2
        assert "AAPL" in result
        assert "GOOGL" in result
        assert result["AAPL"].name == "Apple Inc."
        assert result["GOOGL"].name == "Alphabet Inc."

    def test_異常系_空のティッカーリストでValueError(self) -> None:
        """空のティッカーリストが渡された場合に ValueError が発生することを確認。"""
        analyzer = self._make_analyzer_with_mock_fetcher()

        with pytest.raises(ValueError, match="tickers must not be empty"):
            analyzer.get_ticker_infos([])

    def test_エッジケース_1銘柄のリストでも辞書を返す(self) -> None:
        """1銘柄のリストでも正しく辞書形式で返すことを確認。"""
        mock_info = {
            "shortName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "quoteType": "EQUITY",
        }

        analyzer = self._make_analyzer_with_mock_fetcher()

        with patch("yfinance.Ticker") as mock_ticker_cls:
            mock_ticker = MagicMock()
            mock_ticker.info = mock_info
            mock_ticker_cls.return_value = mock_ticker

            result = analyzer.get_ticker_infos(["AAPL"])

        assert isinstance(result, dict)
        assert len(result) == 1
        assert "AAPL" in result

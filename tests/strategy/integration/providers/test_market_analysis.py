"""Integration tests for MarketAnalysisProvider.

このテストファイルは、MarketAnalysisProvider が実際の yfinance API を
使用してデータを取得できることを確認します。

Note:
    これらのテストは実際の API 呼び出しを行うため、ネットワーク接続が必要です。
    CI 環境では skip される可能性があります。
"""

import pandas as pd
import pytest

from strategy.providers.market_analysis import MarketAnalysisProvider
from strategy.providers.protocol import DataProvider
from strategy.types import TickerInfo


@pytest.mark.integration
class TestMarketAnalysisProviderIntegration:
    """MarketAnalysisProvider の統合テスト."""

    def test_正常系_実データでDataProviderプロトコルを満たす(self) -> None:
        """実際の API を使用して DataProvider プロトコルを満たすことを確認."""
        provider = MarketAnalysisProvider(use_cache=False)
        assert isinstance(provider, DataProvider)

    def test_正常系_実データで価格データを取得(self) -> None:
        """実際の yfinance API から価格データを取得できることを確認."""
        provider = MarketAnalysisProvider(use_cache=False)

        # 短い期間で少量のデータを取得
        df = provider.get_prices(
            tickers=["AAPL"],
            start="2024-01-01",
            end="2024-01-31",
        )

        # 基本的な検証
        assert isinstance(df, pd.DataFrame)
        assert isinstance(df.columns, pd.MultiIndex)
        assert "ticker" in df.columns.names
        assert "price_type" in df.columns.names

        # ティッカーが含まれていること
        tickers = df.columns.get_level_values("ticker").unique()
        assert "AAPL" in tickers

        # OHLCV カラムが存在すること
        price_types = df.columns.get_level_values("price_type").unique()
        assert "close" in price_types

    def test_正常系_実データで複数銘柄の価格データを取得(self) -> None:
        """複数銘柄の価格データを取得できることを確認."""
        provider = MarketAnalysisProvider(use_cache=False)

        df = provider.get_prices(
            tickers=["AAPL", "GOOGL"],
            start="2024-01-01",
            end="2024-01-31",
        )

        # 両方のティッカーが含まれていること
        tickers = df.columns.get_level_values("ticker").unique()
        assert "AAPL" in tickers
        assert "GOOGL" in tickers

    def test_正常系_実データで銘柄情報を取得(self) -> None:
        """実際の yfinance API から銘柄情報を取得できることを確認."""
        provider = MarketAnalysisProvider()

        info = provider.get_ticker_info("AAPL")

        assert isinstance(info, TickerInfo)
        assert info.ticker == "AAPL"
        assert info.name is not None
        assert len(info.name) > 0

    def test_正常系_実データで複数銘柄情報を一括取得(self) -> None:
        """複数銘柄の情報を一括取得できることを確認."""
        provider = MarketAnalysisProvider()

        infos = provider.get_ticker_infos(["AAPL", "MSFT"])

        assert isinstance(infos, dict)
        assert "AAPL" in infos
        assert "MSFT" in infos
        assert isinstance(infos["AAPL"], TickerInfo)
        assert isinstance(infos["MSFT"], TickerInfo)

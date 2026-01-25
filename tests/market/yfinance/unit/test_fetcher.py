"""Unit tests for market.yfinance.fetcher module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from market.yfinance import (
    DataFetchError,
    DataSource,
    FetchOptions,
    Interval,
    RetryConfig,
    ValidationError,
    YFinanceFetcher,
)


class TestYFinanceSymbolPattern:
    """Tests for yfinance symbol pattern validation."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance."""
        return YFinanceFetcher()

    @pytest.mark.parametrize(
        "symbol",
        [
            "AAPL",
            "GOOGL",
            "MSFT",
            "BRK.B",
            "BRK-B",
            "^GSPC",
            "^DJI",
            "USDJPY=X",
            "EURUSD=X",
        ],
    )
    def test_パラメトライズ_有効なシンボルがTrueを返す(
        self, fetcher: YFinanceFetcher, symbol: str
    ) -> None:
        """有効なシンボルで validate_symbol が True を返すことを確認。"""
        assert fetcher.validate_symbol(symbol) is True

    @pytest.mark.parametrize(
        "symbol",
        [
            "",
            "   ",
        ],
    )
    def test_パラメトライズ_無効なシンボルがFalseを返す(
        self, fetcher: YFinanceFetcher, symbol: str
    ) -> None:
        """無効なシンボルで validate_symbol が False を返すことを確認。"""
        assert fetcher.validate_symbol(symbol) is False


class TestYFinanceFetcherProperties:
    """Tests for YFinanceFetcher class properties."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance without cache."""
        return YFinanceFetcher()

    def test_正常系_source_propertyがYFINANCEを返す(
        self, fetcher: YFinanceFetcher
    ) -> None:
        """source property が DataSource.YFINANCE を返すことを確認。"""
        assert fetcher.source == DataSource.YFINANCE

    def test_正常系_default_intervalがDAILYを返す(
        self, fetcher: YFinanceFetcher
    ) -> None:
        """default_interval property が Interval.DAILY を返すことを確認。"""
        assert fetcher.default_interval == Interval.DAILY


class TestYFinanceFetcherValidation:
    """Tests for YFinanceFetcher validation."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance."""
        return YFinanceFetcher()

    def test_異常系_空のシンボルリストでValidationError(
        self, fetcher: YFinanceFetcher
    ) -> None:
        """空のシンボルリストで ValidationError が発生することを確認。"""
        options = FetchOptions(symbols=[])

        with pytest.raises(ValidationError):
            fetcher.fetch(options)

    def test_異常系_無効なシンボルでValidationError(
        self, fetcher: YFinanceFetcher
    ) -> None:
        """無効なシンボルで ValidationError が発生することを確認。"""
        options = FetchOptions(symbols=["AAPL", "", "GOOGL"])

        with pytest.raises(ValidationError):
            fetcher.fetch(options)


class TestYFinanceFetcherFetch:
    """Tests for YFinanceFetcher.fetch() method."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance."""
        return YFinanceFetcher()

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create a sample OHLCV DataFrame."""
        return pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0],
                "High": [155.0, 156.0, 157.0],
                "Low": [149.0, 150.0, 151.0],
                "Close": [154.0, 155.0, 156.0],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )

    @patch("market.yfinance.fetcher.yf.Ticker")
    def test_正常系_有効なシンボルでデータ取得(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df: pd.DataFrame,
    ) -> None:
        """有効なシンボルでデータを取得できることを確認。"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_df
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(
            symbols=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].symbol == "AAPL"
        assert results[0].source == DataSource.YFINANCE
        assert results[0].from_cache is False
        assert len(results[0].data) == 3
        assert list(results[0].data.columns) == [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]

    @patch("market.yfinance.fetcher.yf.Ticker")
    def test_正常系_複数シンボルのデータ取得(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df: pd.DataFrame,
    ) -> None:
        """複数シンボルのデータを取得できることを確認。"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_df
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(symbols=["AAPL", "GOOGL", "MSFT"])

        results = fetcher.fetch(options)

        assert len(results) == 3
        assert [r.symbol for r in results] == ["AAPL", "GOOGL", "MSFT"]

    @patch("market.yfinance.fetcher.yf.Ticker")
    def test_正常系_日付指定でデータ取得(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df: pd.DataFrame,
    ) -> None:
        """日付指定（datetime オブジェクト）でデータを取得できることを確認。"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_df
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(
            symbols=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
        )

        fetcher.fetch(options)

        mock_ticker.history.assert_called_once()
        call_kwargs = mock_ticker.history.call_args.kwargs
        assert call_kwargs["start"] == "2024-01-01"
        assert call_kwargs["end"] == "2024-12-31"

    @patch("market.yfinance.fetcher.yf.Ticker")
    def test_正常系_インターバル指定でデータ取得(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df: pd.DataFrame,
    ) -> None:
        """インターバル指定でデータを取得できることを確認。"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_df
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(
            symbols=["AAPL"],
            interval=Interval.WEEKLY,
        )

        fetcher.fetch(options)

        mock_ticker.history.assert_called_once()
        call_kwargs = mock_ticker.history.call_args.kwargs
        assert call_kwargs["interval"] == "1wk"


class TestYFinanceFetcherErrors:
    """Tests for YFinanceFetcher error handling."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance."""
        return YFinanceFetcher()

    @patch("market.yfinance.fetcher.yf.Ticker")
    def test_エッジケース_空データで空結果(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """空の DataFrame が返された場合、空の結果を返すことを確認。"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        # Valid symbol (has regularMarketPrice) but no historical data for period
        mock_ticker.info = {"regularMarketPrice": 150.0}
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(symbols=["AAPL"])

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].is_empty

    @patch("market.yfinance.fetcher.yf.Ticker")
    def test_異常系_無効または上場廃止シンボルでDataFetchError(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """無効または上場廃止のシンボルで DataFetchError が発生することを確認。"""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        # Invalid symbol: no regularMarketPrice indicates delisted/invalid
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(symbols=["INVALID"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "Invalid or delisted symbol" in str(exc_info.value)

    @patch("market.yfinance.fetcher.yf.Ticker")
    def test_異常系_APIエラーでDataFetchError(
        self,
        mock_ticker_class: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """API エラーで DataFetchError が発生することを確認。"""
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("API Error")
        mock_ticker_class.return_value = mock_ticker

        options = FetchOptions(symbols=["AAPL"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "Failed to fetch data for AAPL" in str(exc_info.value)


class TestYFinanceFetcherRetry:
    """Tests for YFinanceFetcher retry functionality."""

    def test_正常系_retry_configが設定される(self) -> None:
        """RetryConfig が正しく設定されることを確認。"""
        retry_config = RetryConfig(max_attempts=5)
        fetcher = YFinanceFetcher(retry_config=retry_config)

        assert fetcher._retry_config == retry_config


class TestYFinanceFetcherIntervalMapping:
    """Tests for interval mapping."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance."""
        return YFinanceFetcher()

    @pytest.mark.parametrize(
        "interval,expected",
        [
            (Interval.DAILY, "1d"),
            (Interval.WEEKLY, "1wk"),
            (Interval.MONTHLY, "1mo"),
            (Interval.HOURLY, "1h"),
        ],
    )
    def test_パラメトライズ_インターバルマッピングが正しい(
        self, fetcher: YFinanceFetcher, interval: Interval, expected: str
    ) -> None:
        """Interval enum が正しい yfinance 形式にマッピングされることを確認。"""
        assert fetcher._map_interval(interval) == expected

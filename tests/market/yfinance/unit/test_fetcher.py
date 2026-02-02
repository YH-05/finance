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
    """Tests for YFinanceFetcher.fetch() method using yf.download."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance."""
        return YFinanceFetcher()

    @pytest.fixture
    def sample_df_single(self) -> pd.DataFrame:
        """Create a sample OHLCV DataFrame for single symbol (MultiIndex columns)."""
        # yfinance 1.0+ returns MultiIndex columns even for single symbol
        data = {
            ("Close", "AAPL"): [154.0, 155.0, 156.0],
            ("High", "AAPL"): [155.0, 156.0, 157.0],
            ("Low", "AAPL"): [149.0, 150.0, 151.0],
            ("Open", "AAPL"): [150.0, 151.0, 152.0],
            ("Volume", "AAPL"): [1000000, 1100000, 1200000],
        }
        df = pd.DataFrame(
            data,
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        return df

    @pytest.fixture
    def sample_df_multi(self) -> pd.DataFrame:
        """Create a sample OHLCV DataFrame for multiple symbols."""
        data = {
            ("Close", "AAPL"): [154.0, 155.0, 156.0],
            ("Close", "GOOGL"): [140.0, 141.0, 142.0],
            ("Close", "MSFT"): [380.0, 381.0, 382.0],
            ("High", "AAPL"): [155.0, 156.0, 157.0],
            ("High", "GOOGL"): [142.0, 143.0, 144.0],
            ("High", "MSFT"): [382.0, 383.0, 384.0],
            ("Low", "AAPL"): [149.0, 150.0, 151.0],
            ("Low", "GOOGL"): [138.0, 139.0, 140.0],
            ("Low", "MSFT"): [378.0, 379.0, 380.0],
            ("Open", "AAPL"): [150.0, 151.0, 152.0],
            ("Open", "GOOGL"): [139.0, 140.0, 141.0],
            ("Open", "MSFT"): [379.0, 380.0, 381.0],
            ("Volume", "AAPL"): [1000000, 1100000, 1200000],
            ("Volume", "GOOGL"): [500000, 550000, 600000],
            ("Volume", "MSFT"): [2000000, 2100000, 2200000],
        }
        df = pd.DataFrame(
            data,
            index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        )
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        return df

    @patch("market.yfinance.fetcher.yf.download")
    def test_正常系_有効なシンボルでデータ取得(
        self,
        mock_download: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df_single: pd.DataFrame,
    ) -> None:
        """有効なシンボルでデータを取得できることを確認。"""
        mock_download.return_value = sample_df_single

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

    @patch("market.yfinance.fetcher.yf.download")
    def test_正常系_複数シンボルのデータ取得(
        self,
        mock_download: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df_multi: pd.DataFrame,
    ) -> None:
        """複数シンボルのデータを取得できることを確認。"""
        mock_download.return_value = sample_df_multi

        options = FetchOptions(symbols=["AAPL", "GOOGL", "MSFT"])

        results = fetcher.fetch(options)

        assert len(results) == 3
        assert [r.symbol for r in results] == ["AAPL", "GOOGL", "MSFT"]
        for result in results:
            assert len(result.data) == 3
            assert list(result.data.columns) == [
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]

    @patch("market.yfinance.fetcher.yf.download")
    def test_正常系_日付指定でデータ取得(
        self,
        mock_download: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df_single: pd.DataFrame,
    ) -> None:
        """日付指定（datetime オブジェクト）でデータを取得できることを確認。"""
        mock_download.return_value = sample_df_single

        options = FetchOptions(
            symbols=["AAPL"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
        )

        fetcher.fetch(options)

        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args.kwargs
        assert call_kwargs["start"] == "2024-01-01"
        assert call_kwargs["end"] == "2024-12-31"

    @patch("market.yfinance.fetcher.yf.download")
    def test_正常系_インターバル指定でデータ取得(
        self,
        mock_download: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df_single: pd.DataFrame,
    ) -> None:
        """インターバル指定でデータを取得できることを確認。"""
        mock_download.return_value = sample_df_single

        options = FetchOptions(
            symbols=["AAPL"],
            interval=Interval.WEEKLY,
        )

        fetcher.fetch(options)

        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args.kwargs
        assert call_kwargs["interval"] == "1wk"

    @patch("market.yfinance.fetcher.yf.download")
    def test_正常系_bulk_downloadメタデータが設定される(
        self,
        mock_download: MagicMock,
        fetcher: YFinanceFetcher,
        sample_df_single: pd.DataFrame,
    ) -> None:
        """bulk_download メタデータが True で設定されることを確認。"""
        mock_download.return_value = sample_df_single

        options = FetchOptions(symbols=["AAPL"])
        results = fetcher.fetch(options)

        assert results[0].metadata.get("bulk_download") is True


class TestYFinanceFetcherErrors:
    """Tests for YFinanceFetcher error handling."""

    @pytest.fixture
    def fetcher(self) -> YFinanceFetcher:
        """Create a YFinanceFetcher instance with minimal retries."""
        return YFinanceFetcher(
            retry_config=RetryConfig(max_attempts=1, initial_delay=0.01)
        )

    @patch("market.yfinance.fetcher.yf.download")
    def test_エッジケース_空データで空結果(
        self,
        mock_download: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """空の DataFrame が返された場合、空の結果を返すことを確認。"""
        mock_download.return_value = pd.DataFrame()

        options = FetchOptions(symbols=["AAPL"])

        results = fetcher.fetch(options)

        assert len(results) == 1
        assert results[0].is_empty

    @patch("market.yfinance.fetcher.yf.download")
    def test_異常系_シンボルがMultiIndexに存在しない場合(
        self,
        mock_download: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """シンボルが MultiIndex に存在しない場合、エラー情報付きの空結果を返す。"""
        # Return data for different symbol
        data = {
            ("Close", "OTHER"): [100.0],
            ("High", "OTHER"): [101.0],
            ("Low", "OTHER"): [99.0],
            ("Open", "OTHER"): [100.0],
            ("Volume", "OTHER"): [1000],
        }
        df = pd.DataFrame(data, index=pd.to_datetime(["2024-01-01"]))
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        mock_download.return_value = df

        options = FetchOptions(symbols=["AAPL"])
        results = fetcher.fetch(options)

        # Should return result with data (using full df as fallback)
        assert len(results) == 1
        assert results[0].symbol == "AAPL"

    @patch("market.yfinance.fetcher.yf.download")
    def test_異常系_APIエラーでDataFetchError(
        self,
        mock_download: MagicMock,
        fetcher: YFinanceFetcher,
    ) -> None:
        """API エラーで DataFetchError が発生することを確認。"""
        mock_download.side_effect = Exception("API Error")

        options = FetchOptions(symbols=["AAPL"])

        with pytest.raises(DataFetchError) as exc_info:
            fetcher.fetch(options)

        assert "Failed to fetch data" in str(exc_info.value)


class TestYFinanceFetcherRetry:
    """Tests for YFinanceFetcher retry functionality."""

    def test_正常系_retry_configが設定される(self) -> None:
        """RetryConfig が正しく設定されることを確認。"""
        retry_config = RetryConfig(max_attempts=5)
        fetcher = YFinanceFetcher(retry_config=retry_config)

        assert fetcher._retry_config == retry_config

    def test_正常系_デフォルトretry_configが設定される(self) -> None:
        """デフォルトの RetryConfig が設定されることを確認。"""
        fetcher = YFinanceFetcher()

        assert fetcher._retry_config is not None
        assert fetcher._retry_config.max_attempts == 3

    @patch("market.yfinance.fetcher.yf.download")
    @patch("market.yfinance.fetcher.time.sleep")
    def test_正常系_リトライ時にセッションがローテートされる(
        self,
        mock_sleep: MagicMock,
        mock_download: MagicMock,
    ) -> None:
        """リトライ時にブラウザセッションがローテートされることを確認。"""
        fetcher = YFinanceFetcher(
            retry_config=RetryConfig(max_attempts=3, initial_delay=0.01)
        )

        # Fail first two times, succeed on third
        sample_data = pd.DataFrame(
            {
                ("Close", "AAPL"): [154.0],
                ("High", "AAPL"): [155.0],
                ("Low", "AAPL"): [149.0],
                ("Open", "AAPL"): [150.0],
                ("Volume", "AAPL"): [1000000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        sample_data.columns = pd.MultiIndex.from_tuples(sample_data.columns)
        mock_download.side_effect = [
            Exception("Rate limited"),
            Exception("Rate limited"),
            sample_data,
        ]

        options = FetchOptions(symbols=["AAPL"])
        results = fetcher.fetch(options)

        assert len(results) == 1
        assert mock_download.call_count == 3
        # Sleep should be called between retries
        assert mock_sleep.call_count == 2


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


class TestYFinanceFetcherSession:
    """Tests for curl_cffi session management."""

    def test_正常系_コンテキストマネージャーでセッションがクローズされる(self) -> None:
        """コンテキストマネージャー使用時にセッションがクローズされることを確認。"""
        with YFinanceFetcher() as fetcher:
            # Create session
            session = fetcher._get_session()
            assert session is not None

        # After context exit, session should be closed
        assert fetcher._session is None

    def test_正常系_impersonate指定が反映される(self) -> None:
        """impersonate パラメータが正しく設定されることを確認。"""
        fetcher = YFinanceFetcher(impersonate="chrome110")
        assert fetcher._impersonate == "chrome110"

    def test_正常系_impersonate未指定でランダム選択(self) -> None:
        """impersonate 未指定時にランダムなブラウザが選択されることを確認。"""
        from market.yfinance.fetcher import BROWSER_IMPERSONATE_TARGETS

        fetcher = YFinanceFetcher()
        assert fetcher._impersonate in BROWSER_IMPERSONATE_TARGETS


class TestYFinanceFetcherHttpSessionInjection:
    """Tests for http_session dependency injection in YFinanceFetcher."""

    def test_正常系_http_sessionパラメータが追加されている(self) -> None:
        """コンストラクタに http_session パラメータが存在することを確認。"""
        import inspect

        sig = inspect.signature(YFinanceFetcher.__init__)
        params = list(sig.parameters.keys())
        assert "http_session" in params

    def test_正常系_http_session未指定でCurlCffiSessionがデフォルト(self) -> None:
        """http_session 未指定時に CurlCffiSession がデフォルトで使用されることを確認。"""
        from market.yfinance.session import CurlCffiSession

        fetcher = YFinanceFetcher()
        session = fetcher._get_session()

        # Session should be an instance of CurlCffiSession (or compatible)
        assert session is not None
        assert hasattr(session, "get")
        assert hasattr(session, "close")

    def test_正常系_http_sessionを注入できる(self) -> None:
        """http_session パラメータでカスタムセッションを注入できることを確認。"""
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=MagicMock())
        mock_session.close = MagicMock()

        fetcher = YFinanceFetcher(http_session=mock_session)
        session = fetcher._get_session()

        # Should return the injected session
        assert session is mock_session

    def test_正常系_注入されたセッションのgetメソッドが呼び出される(self) -> None:
        """注入されたセッションの get メソッドが正しく呼び出されることを確認。"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.get.return_value = mock_response

        fetcher = YFinanceFetcher(http_session=mock_session)
        session = fetcher._get_session()

        # Verify we got the mock session
        assert session is mock_session
        assert session.get is mock_session.get

    @patch("market.yfinance.fetcher.yf.download")
    def test_正常系_fetchで注入されたセッションのraw_sessionが使用される(
        self,
        mock_download: MagicMock,
    ) -> None:
        """fetch メソッドで注入されたセッションの raw_session が使用されることを確認。

        yfinance は curl_cffi.requests.Session を直接要求するため、
        HttpSessionProtocol 実装の raw_session プロパティを渡す必要がある。
        """
        # Create sample data
        sample_data = pd.DataFrame(
            {
                ("Close", "AAPL"): [154.0],
                ("High", "AAPL"): [155.0],
                ("Low", "AAPL"): [149.0],
                ("Open", "AAPL"): [150.0],
                ("Volume", "AAPL"): [1000000],
            },
            index=pd.to_datetime(["2024-01-01"]),
        )
        sample_data.columns = pd.MultiIndex.from_tuples(sample_data.columns)
        mock_download.return_value = sample_data

        # Create mock for the underlying raw session
        mock_raw_session = MagicMock()

        mock_session = MagicMock()
        mock_session.get = MagicMock()
        mock_session.close = MagicMock()
        mock_session.raw_session = mock_raw_session

        fetcher = YFinanceFetcher(http_session=mock_session)
        options = FetchOptions(symbols=["AAPL"])

        fetcher.fetch(options)

        # Verify download was called with the raw_session, not the wrapper
        mock_download.assert_called_once()
        call_kwargs = mock_download.call_args.kwargs
        assert call_kwargs["session"] is mock_raw_session

    def test_正常系_closeで注入されたセッションがクローズされる(self) -> None:
        """close メソッドで注入されたセッションがクローズされることを確認。"""
        mock_session = MagicMock()
        mock_session.close = MagicMock()

        fetcher = YFinanceFetcher(http_session=mock_session)
        fetcher.close()

        mock_session.close.assert_called_once()

    def test_正常系_コンテキストマネージャーで注入されたセッションがクローズされる(
        self,
    ) -> None:
        """コンテキストマネージャー終了時に注入されたセッションがクローズされることを確認。"""
        mock_session = MagicMock()
        mock_session.close = MagicMock()

        with YFinanceFetcher(http_session=mock_session):
            pass

        mock_session.close.assert_called_once()

    def test_正常系_HttpSessionProtocol互換のオブジェクトが使用できる(self) -> None:
        """HttpSessionProtocol に準拠したオブジェクトが使用できることを確認。"""
        from market.yfinance.session import StandardRequestsSession

        # StandardRequestsSession also implements HttpSessionProtocol
        with patch("market.yfinance.session.requests.Session"):
            session = StandardRequestsSession()
            fetcher = YFinanceFetcher(http_session=session)

            # Should be able to get the session
            assert fetcher._get_session() is session

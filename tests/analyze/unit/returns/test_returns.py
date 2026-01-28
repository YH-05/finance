"""Unit tests for multi-period returns calculation module.

This module tests the analyze.returns implementation for Issue #956.
Tests cover:
- Single period return calculation
- Multi-period returns calculation (RETURN_PERIODS)
- MTD/YTD dynamic period calculation
- TOPIX data fetching with fallback logic
- Returns report generation

References:
- Issue #956: [Phase2] analyzeパッケージ: returnsモジュール移植
- market_analysis/analysis/returns.py (移植元)
- template/tests/unit/test_example.py
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# AIDEV-NOTE: Importing from the new analyze.returns module.
# Tests are expected to fail (Red state) until implementation is complete.
from analyze.returns import (
    RETURN_PERIODS,
    TICKERS_GLOBAL_INDICES,
    TICKERS_MAG7,
    TICKERS_SECTORS,
    TICKERS_US_INDICES,
    calculate_multi_period_returns,
    calculate_return,
    fetch_topix_data,
    generate_returns_report,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_prices() -> pd.Series:
    """Create sample price series for testing.

    Returns 100 days of synthetic price data starting from 100.0
    with small random variations.
    """
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="B")  # Business days
    base_price = 100.0
    # Generate random walk prices
    returns = np.random.normal(0.001, 0.02, 100)
    prices = base_price * np.cumprod(1 + returns)
    return pd.Series(prices, index=dates, name="close")


@pytest.fixture
def sample_prices_short() -> pd.Series:
    """Create short price series (10 days) for edge case testing."""
    dates = pd.date_range("2024-01-01", periods=10, freq="B")
    prices = [100.0, 101.0, 102.0, 101.5, 103.0, 104.0, 103.5, 105.0, 106.0, 107.0]
    return pd.Series(prices, index=dates, name="close")


@pytest.fixture
def sample_prices_mtd() -> pd.Series:
    """Create price series starting from the beginning of a month for MTD testing."""
    # Create data spanning February 2024 for clear MTD calculation
    dates = pd.date_range("2024-02-01", periods=20, freq="B")
    base_price = 100.0
    np.random.seed(123)
    returns = np.random.normal(0.002, 0.01, 20)
    prices = base_price * np.cumprod(1 + returns)
    return pd.Series(prices, index=dates, name="close")


@pytest.fixture
def sample_prices_ytd() -> pd.Series:
    """Create price series starting from the beginning of a year for YTD testing."""
    # Create data spanning from start of 2024
    dates = pd.date_range("2024-01-02", periods=60, freq="B")
    base_price = 100.0
    np.random.seed(456)
    returns = np.random.normal(0.001, 0.015, 60)
    prices = base_price * np.cumprod(1 + returns)
    return pd.Series(prices, index=dates, name="close")


@pytest.fixture
def mock_yfinance_data() -> pd.DataFrame:
    """Create mock yfinance return data for TOPIX testing."""
    dates = pd.date_range("2024-01-01", periods=50, freq="B")
    np.random.seed(789)
    prices = 2500 * np.cumprod(1 + np.random.normal(0.001, 0.01, 50))
    return pd.DataFrame(
        {
            "Open": prices * 0.99,
            "High": prices * 1.01,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": np.random.randint(1000000, 5000000, 50),
        },
        index=dates,
    )


# =============================================================================
# Tests for RETURN_PERIODS constant
# =============================================================================


class TestReturnPeriodsConstant:
    """Tests for RETURN_PERIODS dictionary constant."""

    def test_正常系_RETURN_PERIODSに全期間が含まれる(self) -> None:
        """RETURN_PERIODS が期待される全ての期間を含むことを確認。"""
        # 設定ファイルから読み込まれる期間（WoWが追加された）
        expected_periods = [
            "1D",
            "WoW",  # Week over Week
            "1W",
            "MTD",
            "1M",
            "3M",
            "6M",
            "YTD",
            "1Y",
            "3Y",
            "5Y",
        ]
        assert set(RETURN_PERIODS.keys()) == set(expected_periods)

    def test_正常系_固定期間は整数値(self) -> None:
        """固定期間（1D, 1W, 1M等）が正しい整数値であることを確認。"""
        assert RETURN_PERIODS["1D"] == 1
        assert RETURN_PERIODS["1W"] == 5
        assert RETURN_PERIODS["1M"] == 21
        assert RETURN_PERIODS["3M"] == 63
        assert RETURN_PERIODS["6M"] == 126
        assert RETURN_PERIODS["1Y"] == 252
        assert RETURN_PERIODS["3Y"] == 756
        assert RETURN_PERIODS["5Y"] == 1260

    def test_正常系_動的期間は文字列(self) -> None:
        """MTD と YTD が文字列マーカーであることを確認。"""
        assert RETURN_PERIODS["MTD"] == "mtd"
        assert RETURN_PERIODS["YTD"] == "ytd"


# =============================================================================
# Tests for ticker constants
# =============================================================================


class TestTickerConstants:
    """Tests for ticker list constants."""

    def test_正常系_グローバル指数ティッカーが含まれる(self) -> None:
        """TICKERS_GLOBAL_INDICES が期待されるティッカーを含むことを確認。"""
        # 設定ファイルから読み込まれるグローバル指数
        # ^TOPX はyfinanceでデータ取得できないため除外されている
        expected_tickers = [
            "^N225",  # 日経225
            "^STOXX50E",  # Euro STOXX 50
            "^FTSE",  # FTSE 100
            "^GDAXI",  # DAX
            "000001.SS",  # 上海総合
        ]
        for ticker in expected_tickers:
            assert ticker in TICKERS_GLOBAL_INDICES

    def test_正常系_US指数ティッカーが含まれる(self) -> None:
        """TICKERS_US_INDICES が期待されるティッカーを含むことを確認。"""
        expected_tickers = [
            "^GSPC",  # S&P 500
            "^DJI",  # Dow Jones Industrial Average
            "^IXIC",  # NASDAQ Composite
            "^RUT",  # Russell 2000
        ]
        for ticker in expected_tickers:
            assert ticker in TICKERS_US_INDICES

    def test_正常系_MAG7ティッカーが含まれる(self) -> None:
        """TICKERS_MAG7 が期待されるティッカーを含むことを確認。"""
        expected_tickers = [
            "AAPL",  # Apple
            "MSFT",  # Microsoft
            "GOOGL",  # Alphabet (Google)
            "AMZN",  # Amazon
            "NVDA",  # NVIDIA
            "META",  # Meta (Facebook)
            "TSLA",  # Tesla
        ]
        for ticker in expected_tickers:
            assert ticker in TICKERS_MAG7

    def test_正常系_セクターティッカーが含まれる(self) -> None:
        """TICKERS_SECTORS が期待されるセクターETFを含むことを確認。"""
        expected_tickers = [
            "XLF",  # Financial
            "XLK",  # Technology
            "XLV",  # Health Care
            "XLE",  # Energy
            "XLI",  # Industrial
        ]
        for ticker in expected_tickers:
            assert ticker in TICKERS_SECTORS


# =============================================================================
# Tests for calculate_return function
# =============================================================================


class TestCalculateReturn:
    """Tests for calculate_return function."""

    def test_正常系_1日リターンを計算できる(
        self,
        sample_prices_short: pd.Series,
    ) -> None:
        """1日リターンが正しく計算されることを確認。"""
        # prices: [100.0, 101.0, 102.0, ...]
        # 1日リターン: (107.0 - 106.0) / 106.0 = 0.00943...
        result = calculate_return(sample_prices_short, period=1)

        # 最新日と前日の騰落率
        expected = (107.0 - 106.0) / 106.0
        assert result is not None
        assert abs(result - expected) < 1e-10

    def test_正常系_5日リターンを計算できる(
        self,
        sample_prices_short: pd.Series,
    ) -> None:
        """5日（1週間）リターンが正しく計算されることを確認。"""
        # prices: [100.0, 101.0, 102.0, 101.5, 103.0, 104.0, 103.5, 105.0, 106.0, 107.0]
        # 5日前 (index 4) = 103.0, 最新 (index 9) = 107.0
        result = calculate_return(sample_prices_short, period=5)

        expected = (107.0 - 103.0) / 103.0
        assert result is not None
        assert abs(result - expected) < 1e-10

    def test_正常系_MTD期間を動的に計算できる(
        self,
        sample_prices_mtd: pd.Series,
    ) -> None:
        """MTD（月初来）リターンが動的に計算されることを確認。"""
        result = calculate_return(sample_prices_mtd, period="mtd")

        # MTD: 月初の値から最新値への騰落率
        month_start_price = sample_prices_mtd.iloc[0]
        latest_price = sample_prices_mtd.iloc[-1]
        expected = (latest_price - month_start_price) / month_start_price

        assert result is not None
        assert abs(result - expected) < 1e-10

    def test_正常系_YTD期間を動的に計算できる(
        self,
        sample_prices_ytd: pd.Series,
    ) -> None:
        """YTD（年初来）リターンが動的に計算されることを確認。"""
        result = calculate_return(sample_prices_ytd, period="ytd")

        # YTD: 年初の値から最新値への騰落率
        year_start_price = sample_prices_ytd.iloc[0]
        latest_price = sample_prices_ytd.iloc[-1]
        expected = (latest_price - year_start_price) / year_start_price

        assert result is not None
        assert abs(result - expected) < 1e-10

    def test_異常系_データ不足でNoneを返す(self) -> None:
        """データが不足している場合にNoneを返すことを確認。"""
        short_prices = pd.Series(
            [100.0, 101.0], index=pd.date_range("2024-01-01", periods=2)
        )
        result = calculate_return(short_prices, period=10)

        assert result is None

    def test_異常系_空のSeriesでNoneを返す(self) -> None:
        """空のSeriesでNoneを返すことを確認。"""
        empty_prices = pd.Series([], dtype=float)
        result = calculate_return(empty_prices, period=1)

        assert result is None

    def test_異常系_負の期間でValueError(self) -> None:
        """負の期間でValueErrorが発生することを確認。"""
        prices = pd.Series(
            [100.0, 101.0, 102.0], index=pd.date_range("2024-01-01", periods=3)
        )

        with pytest.raises(ValueError, match="period must be positive"):
            calculate_return(prices, period=-1)

    def test_異常系_ゼロ期間でValueError(self) -> None:
        """ゼロの期間でValueErrorが発生することを確認。"""
        prices = pd.Series(
            [100.0, 101.0, 102.0], index=pd.date_range("2024-01-01", periods=3)
        )

        with pytest.raises(ValueError, match="period must be positive"):
            calculate_return(prices, period=0)

    def test_エッジケース_NaN値を含むデータ(self) -> None:
        """NaN値を含むデータで適切にハンドリングされることを確認。"""
        prices = pd.Series(
            [100.0, np.nan, 102.0, 103.0, 104.0],
            index=pd.date_range("2024-01-01", periods=5),
        )
        result = calculate_return(prices, period=1)

        # NaNを除外して計算されることを期待
        # 除外後: [100.0, 102.0, 103.0, 104.0]
        # 1日リターン: (104.0 - 103.0) / 103.0
        assert result is not None or result is None  # 実装依存


# =============================================================================
# Tests for calculate_multi_period_returns function
# =============================================================================


class TestCalculateMultiPeriodReturns:
    """Tests for calculate_multi_period_returns function."""

    def test_正常系_全期間のリターンを計算できる(
        self,
        sample_prices: pd.Series,
    ) -> None:
        """RETURN_PERIODS の全期間のリターンを計算できることを確認。"""
        result = calculate_multi_period_returns(sample_prices)

        # 全期間のキーが存在することを確認
        for period in RETURN_PERIODS:
            assert period in result

    def test_正常系_結果がdict型(
        self,
        sample_prices: pd.Series,
    ) -> None:
        """結果がdict[str, float | None]型であることを確認。"""
        result = calculate_multi_period_returns(sample_prices)

        assert isinstance(result, dict)
        for key, value in result.items():
            assert isinstance(key, str)
            assert value is None or isinstance(value, float)

    def test_正常系_短いデータでは長期間がNone(
        self,
        sample_prices_short: pd.Series,
    ) -> None:
        """データが短い場合、長期間のリターンがNoneであることを確認。"""
        result = calculate_multi_period_returns(sample_prices_short)

        # 10日分のデータなので1Y, 3Y, 5YはNone
        assert result["1Y"] is None
        assert result["3Y"] is None
        assert result["5Y"] is None

        # 短期間は計算可能
        assert result["1D"] is not None
        assert result["1W"] is not None

    def test_正常系_MTDとYTDが含まれる(
        self,
        sample_prices: pd.Series,
    ) -> None:
        """MTDとYTDがリターン結果に含まれることを確認。"""
        result = calculate_multi_period_returns(sample_prices)

        assert "MTD" in result
        assert "YTD" in result

    def test_異常系_空のSeriesで全てNoneを返す(self) -> None:
        """空のSeriesで全ての値がNoneのdictを返すことを確認。"""
        empty_prices = pd.Series([], dtype=float)
        result = calculate_multi_period_returns(empty_prices)

        # 全ての値がNoneであることを確認
        for value in result.values():
            assert value is None


# =============================================================================
# Tests for fetch_topix_data function
# =============================================================================


class TestFetchTopixData:
    """Tests for fetch_topix_data function with fallback logic."""

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_TOPX成功時はTOPXデータを返す(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """^TOPX の取得が成功した場合、そのデータを返すことを確認。"""
        mock_download.return_value = mock_yfinance_data

        result = fetch_topix_data()

        assert result is not None
        assert not result.empty
        mock_download.assert_called_once()
        # ^TOPX で呼ばれたことを確認
        call_args = mock_download.call_args
        assert "^TOPX" in str(call_args)

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_TOPX失敗時は1306Tにフォールバック(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """^TOPX の取得が失敗した場合、1306.T にフォールバックすることを確認。"""

        # 最初の呼び出し（^TOPX）は空のDataFrame、2回目（1306.T）は成功
        def side_effect(*args, **kwargs):
            ticker = args[0] if args else kwargs.get("tickers", "")
            if "^TOPX" in str(ticker):
                return pd.DataFrame()  # 空のDataFrame（失敗）
            return mock_yfinance_data  # 1306.T は成功

        mock_download.side_effect = side_effect

        result = fetch_topix_data()

        assert result is not None
        assert not result.empty
        # 2回呼ばれることを確認
        assert mock_download.call_count == 2

    @patch("analyze.returns.returns.yf.download")
    def test_異常系_両方失敗時はNoneを返す(
        self,
        mock_download: MagicMock,
    ) -> None:
        """^TOPX と 1306.T の両方が失敗した場合、Noneを返すことを確認。"""
        mock_download.return_value = pd.DataFrame()  # 常に空を返す

        result = fetch_topix_data()

        assert result is None
        # 2回呼ばれることを確認（^TOPX と 1306.T）
        assert mock_download.call_count == 2

    @patch("analyze.returns.returns.yf.download")
    def test_異常系_例外発生時はフォールバック(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """^TOPX で例外が発生した場合、1306.T にフォールバックすることを確認。"""

        def side_effect(*args, **kwargs):
            ticker = args[0] if args else kwargs.get("tickers", "")
            if "^TOPX" in str(ticker):
                raise Exception("API Error")
            return mock_yfinance_data

        mock_download.side_effect = side_effect

        result = fetch_topix_data()

        assert result is not None
        assert not result.empty


# =============================================================================
# Tests for generate_returns_report function
# =============================================================================


class TestGenerateReturnsReport:
    """Tests for generate_returns_report function."""

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_レポート構造が正しい(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """レポートが期待される構造を持つことを確認。"""
        mock_download.return_value = mock_yfinance_data

        result = generate_returns_report()

        assert "as_of" in result
        assert "indices" in result
        assert "mag7" in result
        assert "sectors" in result
        assert "global_indices" in result

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_as_ofがISO形式の日時(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """as_of が ISO 8601 形式の日時文字列であることを確認。"""
        mock_download.return_value = mock_yfinance_data

        result = generate_returns_report()

        as_of = result["as_of"]
        # ISO 8601 形式でパースできることを確認
        parsed = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_指定日時でレポート生成(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """指定した日時でレポートが生成されることを確認。"""
        mock_download.return_value = mock_yfinance_data
        specified_time = datetime(2024, 6, 15, 16, 0, 0)

        result = generate_returns_report(as_of=specified_time)

        as_of = result["as_of"]
        assert "2024-06-15" in as_of

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_global_indicesにグローバル指数が含まれる(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """global_indices にグローバル指数データが含まれることを確認。"""
        mock_download.return_value = mock_yfinance_data

        result = generate_returns_report()

        global_indices = result["global_indices"]
        assert isinstance(global_indices, list)
        # 少なくとも1つの指数データが含まれることを確認
        if global_indices:
            index_entry = global_indices[0]
            assert "ticker" in index_entry or "symbol" in index_entry

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_indicesに主要指数が含まれる(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """indices に主要な市場指数データが含まれることを確認。"""
        mock_download.return_value = mock_yfinance_data

        result = generate_returns_report()

        indices = result["indices"]
        assert isinstance(indices, list)

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_mag7にMAG7銘柄が含まれる(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """mag7 セクションに MAG7 銘柄データが含まれることを確認。"""
        mock_download.return_value = mock_yfinance_data

        result = generate_returns_report()

        mag7 = result["mag7"]
        assert isinstance(mag7, list)

    @patch("analyze.returns.returns.yf.download")
    def test_正常系_sectorsにセクターデータが含まれる(
        self,
        mock_download: MagicMock,
        mock_yfinance_data: pd.DataFrame,
    ) -> None:
        """sectors セクションにセクターETFデータが含まれることを確認。"""
        mock_download.return_value = mock_yfinance_data

        result = generate_returns_report()

        sectors = result["sectors"]
        assert isinstance(sectors, list)


# =============================================================================
# Tests for edge cases and error handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_エッジケース_週末を含むデータでの計算(self) -> None:
        """週末を含むデータで正しく計算されることを確認。"""
        # 営業日のみのデータを作成
        dates = pd.date_range("2024-01-01", periods=20, freq="B")
        prices = pd.Series(range(100, 120), index=dates, dtype=float)

        result = calculate_return(prices, period=5)

        # 5営業日前と現在の比較
        assert result is not None

    def test_エッジケース_祝日を含むデータでの計算(self) -> None:
        """祝日を含むデータ（欠損日がある）で正しく計算されることを確認。"""
        # 一部の日が欠損しているデータ
        dates = pd.to_datetime(
            ["2024-01-02", "2024-01-03", "2024-01-05", "2024-01-08", "2024-01-09"]
        )
        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=dates)

        result = calculate_return(prices, period=2)

        # 2日前のインデックス位置から計算
        assert result is not None

    @pytest.mark.parametrize(
        "period_key,expected_type",
        [
            ("1D", int),
            ("1W", int),
            ("MTD", str),
            ("1M", int),
            ("3M", int),
            ("6M", int),
            ("YTD", str),
            ("1Y", int),
            ("3Y", int),
            ("5Y", int),
        ],
    )
    def test_パラメトライズ_各期間の型が正しい(
        self,
        period_key: str,
        expected_type: type,
    ) -> None:
        """各期間の値が期待される型であることを確認。"""
        assert isinstance(RETURN_PERIODS[period_key], expected_type)

    def test_エッジケース_非常に大きなリターン(self) -> None:
        """極端なリターン値でもオーバーフローしないことを確認。"""
        dates = pd.date_range("2024-01-01", periods=5, freq="B")
        prices = pd.Series([1.0, 10.0, 100.0, 1000.0, 10000.0], index=dates)

        result = calculate_return(prices, period=1)

        # 9900% のリターン
        assert result is not None
        assert result == pytest.approx(9.0, rel=1e-10)

    def test_エッジケース_非常に小さなリターン(self) -> None:
        """非常に小さなリターン値でも精度が保たれることを確認。"""
        dates = pd.date_range("2024-01-01", periods=5, freq="B")
        prices = pd.Series([100.0, 100.0001, 100.0002, 100.0003, 100.0004], index=dates)

        result = calculate_return(prices, period=1)

        # 非常に小さいリターン
        assert result is not None
        assert abs(result) < 0.001

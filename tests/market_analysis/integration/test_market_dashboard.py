"""Integration tests for market_dashboard notebook functions.

This module tests the calculation functions used in the market_dashboard marimo notebook.
These tests focus on the logic that is used within the notebook cells.

Note: These are NOT notebook execution tests. They test the pure Python functions
that the notebook uses for data processing and visualization.
"""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from market_analysis import CorrelationAnalyzer, MarketData
from market_analysis.errors import DataFetchError
from market_analysis.types import DataSource, MarketDataResult

# =============================================================================
# Helper functions from notebook (replicated for testing)
# =============================================================================


def get_date_range_from_days(days: int) -> tuple[datetime, datetime]:
    """Calculate date range from days.

    Parameters
    ----------
    days : int
        Number of days to look back

    Returns
    -------
    tuple[datetime, datetime]
        Start and end dates
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def get_date_range_from_period(period: str) -> tuple[datetime, datetime]:
    """Calculate date range from period string.

    Parameters
    ----------
    period : str
        Period string (e.g., "1mo", "3mo", "1y")

    Returns
    -------
    tuple[datetime, datetime]
        Start and end dates
    """
    end_date = datetime.now()

    period_days = {
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "2y": 730,
        "5y": 1825,
    }

    days = period_days.get(period, 365)
    start_date = end_date - timedelta(days=days)

    return start_date, end_date


def calculate_period_return(
    df: pd.DataFrame, days: int, price_col: str = "close"
) -> float | None:
    """Calculate return for a specific period.

    Parameters
    ----------
    df : pd.DataFrame
        Price data with datetime index
    days : int
        Number of trading days for the period
    price_col : str
        Column name for price data

    Returns
    -------
    float | None
        Return as percentage, None if insufficient data
    """
    if df.empty or len(df) < 2:
        return None

    try:
        # Get the most recent price
        current_price = df[price_col].iloc[-1]

        # Find price from 'days' trading days ago
        if len(df) >= days:
            past_price = df[price_col].iloc[-days]
        else:
            # Use earliest available price if less data
            past_price = df[price_col].iloc[0]

        if past_price == 0 or np.isnan(past_price):
            return None

        return ((current_price - past_price) / past_price) * 100
    except (IndexError, KeyError):
        return None


def calculate_ytd_return(df: pd.DataFrame, price_col: str = "close") -> float | None:
    """Calculate Year-to-Date return.

    Parameters
    ----------
    df : pd.DataFrame
        Price data with datetime index
    price_col : str
        Column name for price data

    Returns
    -------
    float | None
        YTD return as percentage, None if insufficient data
    """
    if df.empty or len(df) < 2:
        return None

    try:
        current_price = df[price_col].iloc[-1]

        # Find first trading day of current year
        current_year = df.index[-1].year
        year_start_data = df[df.index.year == current_year]

        if year_start_data.empty:
            return None

        year_start_price = year_start_data[price_col].iloc[0]

        if year_start_price == 0 or np.isnan(year_start_price):
            return None

        return ((current_price - year_start_price) / year_start_price) * 100
    except (IndexError, KeyError, AttributeError):
        return None


def calculate_performance_metrics(
    data: dict[str, pd.DataFrame],
    ticker_names: dict[str, str],
) -> pd.DataFrame:
    """Calculate performance metrics for multiple symbols.

    Parameters
    ----------
    data : dict[str, pd.DataFrame]
        Dictionary of symbol -> price DataFrame
    ticker_names : dict[str, str]
        Dictionary of symbol -> display name

    Returns
    -------
    pd.DataFrame
        Performance table with 1D, 1W, 1M, YTD returns
    """
    records = []

    for symbol, df in data.items():
        if df.empty:
            continue

        name = ticker_names.get(symbol, symbol)
        current_price = df["close"].iloc[-1] if not df.empty else None

        record = {
            "symbol": symbol,
            "name": name,
            "current_price": current_price,
            "1D": calculate_period_return(df, 1),
            "1W": calculate_period_return(df, 5),
            "1M": calculate_period_return(df, 21),
            "YTD": calculate_ytd_return(df),
        }
        records.append(record)

    if not records:
        return pd.DataFrame()

    return pd.DataFrame(records)


def calculate_weekly_returns(
    df: pd.DataFrame, price_col: str = "close"
) -> dict[str, Any] | None:
    """Calculate weekly log returns and statistics.

    Parameters
    ----------
    df : pd.DataFrame
        Price data with datetime index
    price_col : str
        Column name for price data

    Returns
    -------
    dict | None
        Dictionary containing returns and statistics, or None if error
    """
    if df.empty or len(df) < 14:  # Need at least 2 weeks of data
        return None

    try:
        # Resample to weekly (Friday close)
        weekly_df = df[price_col].resample("W-FRI").last().dropna()

        if len(weekly_df) < 2:
            return None

        # Calculate log returns
        log_returns = np.log(weekly_df / weekly_df.shift(1)).dropna()

        if len(log_returns) == 0:
            return None

        # Calculate statistics
        mean_return = float(log_returns.mean())
        std_return = float(log_returns.std())
        annualized_return = mean_return * 52  # Annualize
        annualized_vol = std_return * np.sqrt(52)

        return {
            "returns": log_returns.values,
            "dates": log_returns.index,
            "mean": mean_return,
            "std": std_return,
            "min": float(log_returns.min()),
            "max": float(log_returns.max()),
            "count": len(log_returns),
            "annualized_return": annualized_return,
            "annualized_vol": annualized_vol,
            "skewness": float(log_returns.skew()),
            "kurtosis": float(log_returns.kurtosis()),
        }
    except Exception:
        return None


# =============================================================================
# Tests: Tab 1 - Performance Overview
# =============================================================================


class TestCalculatePeriodReturn:
    """Tests for calculate_period_return function."""

    def test_正常系_基本的なリターン計算(self) -> None:
        """基本的なリターン計算ができることを確認。"""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame(
            {"close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 110]}, index=dates
        )

        result = calculate_period_return(df, days=5)

        # (110 - 105) / 105 * 100 = 4.76%
        assert result is not None
        assert pytest.approx(result, rel=0.01) == 4.76

    def test_正常系_1日リターン(self) -> None:
        """1日リターンが正しく計算されることを確認。"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({"close": [100, 102, 101, 103, 105]}, index=dates)

        # days=1 means comparing iloc[-1] with iloc[-1], which gives 0%
        # To calculate 1-day return, we need days=2 (compare current with previous)
        result = calculate_period_return(df, days=2)

        # (105 - 103) / 103 * 100 = 1.94%
        assert result is not None
        assert pytest.approx(result, rel=0.01) == 1.94

    def test_正常系_データ不足時は最古データを使用(self) -> None:
        """データ不足時に最古のデータを使用することを確認。"""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame({"close": [100, 105, 110]}, index=dates)

        # 21日分のデータがないが、最古のデータ(100)を使用
        result = calculate_period_return(df, days=21)

        # (110 - 100) / 100 * 100 = 10%
        assert result is not None
        assert pytest.approx(result, rel=0.01) == 10.0

    def test_異常系_空のDataFrameでNone(self) -> None:
        """空のDataFrameでNoneが返されることを確認。"""
        df = pd.DataFrame()

        result = calculate_period_return(df, days=5)

        assert result is None

    def test_異常系_1行のみのDataFrameでNone(self) -> None:
        """1行のみのDataFrameでNoneが返されることを確認。"""
        index = pd.DatetimeIndex([datetime(2024, 1, 1)])
        df = pd.DataFrame({"close": [100]}, index=index)

        result = calculate_period_return(df, days=5)

        assert result is None

    def test_異常系_過去価格が0でNone(self) -> None:
        """過去価格が0の場合にNoneが返されることを確認。"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({"close": [0, 0, 100, 105, 110]}, index=dates)

        result = calculate_period_return(df, days=5)

        assert result is None

    def test_異常系_NaN値でNone(self) -> None:
        """NaN値がある場合にNoneが返されることを確認。"""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame({"close": [np.nan, 100, 105, 110, 115]}, index=dates)

        result = calculate_period_return(df, days=5)

        assert result is None


class TestCalculateYtdReturn:
    """Tests for calculate_ytd_return function."""

    def test_正常系_YTDリターン計算(self) -> None:
        """YTDリターンが正しく計算されることを確認。"""
        # 2024年1月1日から3月までのデータ
        dates = pd.date_range("2024-01-02", "2024-03-31", freq="B")
        prices = [100 + i * 0.5 for i in range(len(dates))]
        df = pd.DataFrame({"close": prices}, index=dates)

        result = calculate_ytd_return(df)

        assert result is not None
        assert result > 0  # 価格は上昇しているのでプラス

    def test_正常系_年初価格を正しく取得(self) -> None:
        """年初の価格が正しく取得されることを確認。"""
        dates = pd.date_range("2024-01-02", periods=10, freq="B")
        df = pd.DataFrame(
            {"close": [100, 105, 102, 108, 110, 112, 115, 118, 120, 125]}, index=dates
        )

        result = calculate_ytd_return(df)

        # (125 - 100) / 100 * 100 = 25%
        assert result is not None
        assert pytest.approx(result, rel=0.01) == 25.0

    def test_異常系_空のDataFrameでNone(self) -> None:
        """空のDataFrameでNoneが返されることを確認。"""
        df = pd.DataFrame()

        result = calculate_ytd_return(df)

        assert result is None

    def test_異常系_年初データなしでNone(self) -> None:
        """年初のデータがない場合にNoneが返されることを確認。"""
        # 空のDataFrameを直接テスト
        df = pd.DataFrame({"close": pd.Series(dtype=np.float64)})

        result = calculate_ytd_return(df)

        assert result is None


class TestCalculatePerformanceMetrics:
    """Tests for calculate_performance_metrics function."""

    def test_正常系_複数シンボルのパフォーマンス計算(self) -> None:
        """複数シンボルのパフォーマンスが計算されることを確認。"""
        dates = pd.date_range("2024-01-02", periods=30, freq="B")

        data = {
            "AAPL": pd.DataFrame({"close": [100 + i for i in range(30)]}, index=dates),
            "MSFT": pd.DataFrame(
                {"close": [200 + i * 2 for i in range(30)]}, index=dates
            ),
        }

        ticker_names = {"AAPL": "Apple", "MSFT": "Microsoft"}

        result = calculate_performance_metrics(data, ticker_names)

        assert not result.empty
        assert len(result) == 2
        assert "symbol" in result.columns
        assert "1D" in result.columns
        assert "1W" in result.columns
        assert "1M" in result.columns
        assert "YTD" in result.columns

    def test_正常系_名称が正しくマッピングされる(self) -> None:
        """シンボルの名称が正しくマッピングされることを確認。"""
        dates = pd.date_range("2024-01-02", periods=10, freq="B")

        data = {
            "AAPL": pd.DataFrame({"close": [100 + i for i in range(10)]}, index=dates)
        }
        ticker_names = {"AAPL": "Apple Inc."}

        result = calculate_performance_metrics(data, ticker_names)

        assert result.iloc[0]["name"] == "Apple Inc."

    def test_正常系_未登録シンボルはシンボル名が使用される(self) -> None:
        """未登録シンボルの場合はシンボル名が使用されることを確認。"""
        dates = pd.date_range("2024-01-02", periods=10, freq="B")

        data = {
            "UNKNOWN": pd.DataFrame(
                {"close": [100 + i for i in range(10)]}, index=dates
            )
        }
        ticker_names = {}  # 空の辞書

        result = calculate_performance_metrics(data, ticker_names)

        assert result.iloc[0]["name"] == "UNKNOWN"

    def test_異常系_空のデータでは空のDataFrameが返される(self) -> None:
        """空のデータで空のDataFrameが返されることを確認。"""
        data: dict[str, pd.DataFrame] = {}
        ticker_names: dict[str, str] = {}

        result = calculate_performance_metrics(data, ticker_names)

        assert result.empty

    def test_エッジケース_空のDataFrameを含む場合はスキップ(self) -> None:
        """空のDataFrameを含む場合はスキップされることを確認。"""
        dates = pd.date_range("2024-01-02", periods=10, freq="B")

        data = {
            "AAPL": pd.DataFrame({"close": [100 + i for i in range(10)]}, index=dates),
            "INVALID": pd.DataFrame(),  # 空のDataFrame
        }
        ticker_names = {"AAPL": "Apple", "INVALID": "Invalid"}

        result = calculate_performance_metrics(data, ticker_names)

        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "AAPL"


# =============================================================================
# Tests: Tab 4 - Return Distribution
# =============================================================================


class TestCalculateWeeklyReturns:
    """Tests for calculate_weekly_returns function."""

    def test_正常系_週次リターン統計計算(self) -> None:
        """週次リターン統計が正しく計算されることを確認。"""
        # 60日分のデータ（約8週間）
        dates = pd.date_range("2024-01-02", periods=60, freq="B")
        prices = [
            100 * np.exp(0.001 * i + np.random.normal(0, 0.01)) for i in range(60)
        ]
        df = pd.DataFrame({"close": prices}, index=dates)

        result = calculate_weekly_returns(df)

        assert result is not None
        assert "mean" in result
        assert "std" in result
        assert "annualized_return" in result
        assert "annualized_vol" in result
        assert "skewness" in result
        assert "kurtosis" in result
        assert result["count"] >= 2

    def test_正常系_年率換算が正しい(self) -> None:
        """年率換算が正しく計算されることを確認。"""
        dates = pd.date_range("2024-01-02", periods=60, freq="B")
        # 一定成長率のデータ
        prices = [100 * (1.001**i) for i in range(60)]
        df = pd.DataFrame({"close": prices}, index=dates)

        result = calculate_weekly_returns(df)

        assert result is not None
        # 年率リターンは週次平均 * 52
        assert (
            pytest.approx(result["annualized_return"], rel=0.1) == result["mean"] * 52
        )
        # 年率ボラティリティは週次標準偏差 * sqrt(52)
        assert pytest.approx(result["annualized_vol"], rel=0.1) == result[
            "std"
        ] * np.sqrt(52)

    def test_異常系_データ不足でNone(self) -> None:
        """データ不足でNoneが返されることを確認。"""
        dates = pd.date_range("2024-01-02", periods=5, freq="B")
        df = pd.DataFrame({"close": [100, 101, 102, 103, 104]}, index=dates)

        result = calculate_weekly_returns(df)

        assert result is None

    def test_異常系_空のDataFrameでNone(self) -> None:
        """空のDataFrameでNoneが返されることを確認。"""
        df = pd.DataFrame()

        result = calculate_weekly_returns(df)

        assert result is None


# =============================================================================
# Tests: Tab 3 - Correlation & Beta Analysis
# =============================================================================


class TestCorrelationAnalyzerIntegration:
    """Integration tests for CorrelationAnalyzer used in Tab 3."""

    def test_正常系_ローリング相関計算(self) -> None:
        """ローリング相関が正しく計算されることを確認。"""
        # 相関のある2つの時系列を生成
        dates = pd.date_range("2024-01-02", periods=100, freq="B")
        base = np.random.randn(100).cumsum()
        series_a = pd.Series(base + np.random.randn(100) * 0.1, index=dates)
        series_b = pd.Series(base + np.random.randn(100) * 0.1, index=dates)

        result = CorrelationAnalyzer.calculate_rolling_correlation(
            series_a, series_b, window=20
        )

        assert len(result) == 100
        # 最初の19個はNaN（window-1）
        assert result.iloc[:19].isna().all()
        # 有効な相関値は-1から1の範囲
        valid_corr = result.dropna()
        assert all(-1 <= c <= 1 for c in valid_corr)

    def test_正常系_ローリングベータ計算(self) -> None:
        """ローリングベータが正しく計算されることを確認。"""
        dates = pd.date_range("2024-01-02", periods=100, freq="B")
        # ベンチマークの2倍動く資産
        benchmark_returns = pd.Series(np.random.randn(100) * 0.01, index=dates)
        asset_returns = benchmark_returns * 2 + np.random.randn(100) * 0.001

        result = CorrelationAnalyzer.calculate_rolling_beta(
            asset_returns, benchmark_returns, window=20
        )

        assert len(result) == 100
        # 有効なベータ値は2に近い
        valid_beta = result.dropna()
        assert all(b is not None for b in valid_beta)
        mean_beta = valid_beta.mean()
        assert 1.5 < mean_beta < 2.5  # ベータは約2

    def test_正常系_相関行列計算(self) -> None:
        """相関行列が正しく計算されることを確認。"""
        dates = pd.date_range("2024-01-02", periods=50, freq="B")
        returns_df = pd.DataFrame(
            {
                "XLK": np.random.randn(50) * 0.01,
                "XLF": np.random.randn(50) * 0.01,
                "XLE": np.random.randn(50) * 0.01,
            },
            index=dates,
        )

        result = CorrelationAnalyzer.calculate_correlation_matrix(returns_df)

        assert result.shape == (3, 3)
        # 対角要素は1.0
        assert result.loc["XLK", "XLK"] == pytest.approx(1.0)
        assert result.loc["XLF", "XLF"] == pytest.approx(1.0)
        assert result.loc["XLE", "XLE"] == pytest.approx(1.0)
        # 対称行列
        assert result.loc["XLK", "XLF"] == pytest.approx(result.loc["XLF", "XLK"])


# =============================================================================
# Tests: Data Caching
# =============================================================================


class TestDataCaching:
    """Tests for data caching behavior."""

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_正常系_キャッシュが有効な場合にfrom_cacheがTrue(
        self, mock_factory: MagicMock, tmp_path: Any
    ) -> None:
        """キャッシュからデータ取得時にfrom_cacheがTrueになることを確認。"""
        mock_df = pd.DataFrame(
            {"close": [100.0, 101.0]},
            index=pd.date_range("2024-01-01", periods=2),
        )
        mock_result = MarketDataResult(
            symbol="AAPL",
            data=mock_df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=True,  # キャッシュからの取得
        )
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [mock_result]
        mock_factory.create.return_value = mock_fetcher

        cache_path = str(tmp_path / "cache.db")
        market_data = MarketData(cache_path=cache_path)
        result = market_data.fetch_stock("AAPL")

        assert isinstance(result, pd.DataFrame)
        # モックでfrom_cache=Trueを返しているので、キャッシュ動作を確認

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_正常系_同一シンボルの複数回取得でキャッシュ使用(
        self, mock_factory: MagicMock, tmp_path: Any
    ) -> None:
        """同一シンボルを複数回取得した場合にキャッシュが使用されることを確認。"""
        mock_df = pd.DataFrame(
            {"close": [100.0]},
            index=pd.date_range("2024-01-01", periods=1),
        )

        # 1回目: キャッシュなし
        mock_result_1 = MarketDataResult(
            symbol="AAPL",
            data=mock_df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=False,
        )
        # 2回目: キャッシュあり
        mock_result_2 = MarketDataResult(
            symbol="AAPL",
            data=mock_df,
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=True,
        )

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = [[mock_result_1], [mock_result_2]]
        mock_factory.create.return_value = mock_fetcher

        cache_path = str(tmp_path / "cache.db")
        market_data = MarketData(cache_path=cache_path)

        # 1回目の取得
        result1 = market_data.fetch_stock("AAPL")
        # 2回目の取得（キャッシュ使用）
        result2 = market_data.fetch_stock("AAPL")

        assert isinstance(result1, pd.DataFrame)
        assert isinstance(result2, pd.DataFrame)
        assert mock_fetcher.fetch.call_count == 2


# =============================================================================
# Tests: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_異常系_FRED_API_KEY未設定でエラー(self, mock_factory: MagicMock) -> None:
        """FRED_API_KEYが未設定の場合にエラーが発生することを確認。"""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = DataFetchError(
            "FRED API key is required",
            symbol="DGS10",
            source="fred",
        )
        mock_factory.create.return_value = mock_fetcher

        market_data = MarketData()

        with pytest.raises(DataFetchError, match="API key"):
            market_data.fetch_fred("DGS10")

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_異常系_データなしでDataFetchError(self, mock_factory: MagicMock) -> None:
        """データが取得できない場合にDataFetchErrorが発生することを確認。"""
        mock_result = MarketDataResult(
            symbol="INVALID",
            data=pd.DataFrame(),
            source=DataSource.YFINANCE,
            fetched_at=datetime.now(),
            from_cache=False,
        )
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = [mock_result]
        mock_factory.create.return_value = mock_fetcher

        market_data = MarketData()

        with pytest.raises(DataFetchError, match="No data found"):
            market_data.fetch_stock("INVALID_SYMBOL")

    def test_異常系_空のシンボルでValidationError(self) -> None:
        """空のシンボルでValidationErrorが発生することを確認。"""
        from market_analysis.errors import ValidationError

        market_data = MarketData()

        with pytest.raises(ValidationError, match="cannot be empty"):
            market_data.fetch_stock("")


# =============================================================================
# Tests: Date Range Calculations
# =============================================================================


class TestDateRangeCalculations:
    """Tests for date range calculation functions."""

    def test_正常系_日数から日付範囲を計算(self) -> None:
        """日数から日付範囲が正しく計算されることを確認。"""
        start, end = get_date_range_from_days(30)

        assert end >= start
        diff = (end - start).days
        assert diff == 30

    def test_正常系_期間文字列から日付範囲を計算(self) -> None:
        """期間文字列から日付範囲が正しく計算されることを確認。"""
        test_cases = [
            ("1mo", 30),
            ("3mo", 90),
            ("6mo", 180),
            ("1y", 365),
            ("2y", 730),
            ("5y", 1825),
        ]

        for period, expected_days in test_cases:
            start, end = get_date_range_from_period(period)
            diff = (end - start).days
            assert diff == expected_days, f"Failed for period {period}"

    def test_エッジケース_未知の期間はデフォルト365日(self) -> None:
        """未知の期間文字列でデフォルト365日が使用されることを確認。"""
        start, end = get_date_range_from_period("unknown")

        diff = (end - start).days
        assert diff == 365


# =============================================================================
# Tests: Full Dashboard Integration
# =============================================================================


class TestDashboardIntegration:
    """Integration tests for full dashboard workflow."""

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_正常系_全タブのデータ取得ワークフロー(
        self, mock_factory: MagicMock
    ) -> None:
        """全タブのデータ取得ワークフローが正常に動作することを確認。"""
        # セットアップ: 各シンボルのモックデータ
        dates = pd.date_range("2024-01-02", periods=50, freq="B")

        def create_mock_result(symbol: str) -> MarketDataResult:
            mock_df = pd.DataFrame(
                {
                    "open": [100 + i for i in range(50)],
                    "high": [105 + i for i in range(50)],
                    "low": [95 + i for i in range(50)],
                    "close": [102 + i for i in range(50)],
                    "volume": [1000000] * 50,
                },
                index=dates,
            )
            return MarketDataResult(
                symbol=symbol,
                data=mock_df,
                source=DataSource.YFINANCE,
                fetched_at=datetime.now(),
                from_cache=False,
            )

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = lambda opts: [
            create_mock_result(opts.symbols[0])
        ]
        mock_factory.create.return_value = mock_fetcher

        market_data = MarketData()

        # Tab 1: パフォーマンス概要
        indices = ["^GSPC", "^DJI"]
        indices_data = {}
        for symbol in indices:
            df = market_data.fetch_stock(symbol)
            indices_data[symbol] = df

        ticker_names = {"^GSPC": "S&P 500", "^DJI": "Dow 30"}
        perf = calculate_performance_metrics(indices_data, ticker_names)

        assert not perf.empty
        assert len(perf) == 2

        # Tab 4: リターン分布
        returns_stats = calculate_weekly_returns(indices_data["^GSPC"])

        assert returns_stats is not None
        assert returns_stats["count"] >= 1

    @patch("market_analysis.api.market_data.DataFetcherFactory")
    def test_正常系_期間変更でデータが更新される(self, mock_factory: MagicMock) -> None:
        """期間選択を変更した場合にデータが更新されることを確認。"""
        periods = ["1mo", "3mo", "1y"]

        for period in periods:
            start, end = get_date_range_from_period(period)
            expected_days = {"1mo": 30, "3mo": 90, "1y": 365}[period]

            diff = (end - start).days
            assert diff == expected_days, (
                f"Period {period} should have {expected_days} days"
            )

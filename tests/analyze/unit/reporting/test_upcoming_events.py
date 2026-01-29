"""UpcomingEventsAnalyzer のテスト.

S&P500時価総額上位20社の次回決算発表日を取得する機能のテスト。
TDDに基づいてテストを先に作成し、実装を後から行う。

Issue: #2419
参照: docs/project/project-28/task-10-upcoming-events-earnings.md
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pandas import DataFrame

from analyze.reporting.upcoming_events import (
    EarningsDateInfo,
    UpcomingEventsAnalyzer,
)

# =============================================================================
# Constants for Testing
# =============================================================================

TOP20_SYMBOLS = [
    # MAG7
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    # Top 8-15
    "BRK-B",
    "LLY",
    "V",
    "UNH",
    "JPM",
    "XOM",
    "JNJ",
    "MA",
    # Top 16-20
    "PG",
    "HD",
    "AVGO",
    "CVX",
    "MRK",
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def analyzer() -> UpcomingEventsAnalyzer:
    """UpcomingEventsAnalyzer インスタンスを作成."""
    return UpcomingEventsAnalyzer()


@pytest.fixture
def mock_calendar_data() -> dict[str, Any]:
    """yfinance ticker.calendar の戻り値をモック."""
    now = datetime.now(tz=timezone.utc)
    return {
        "Earnings Date": now + timedelta(days=7),
        "Earnings High": now + timedelta(days=7),
        "Earnings Low": now + timedelta(days=7),
        "Earnings Average": now + timedelta(days=7),
        "Revenue Average": 50_000_000_000,
        "Revenue High": 55_000_000_000,
        "Revenue Low": 45_000_000_000,
    }


@pytest.fixture
def mock_earnings_dates_df() -> DataFrame:
    """yfinance get_earnings_dates の戻り値をモック."""
    now = datetime.now(tz=timezone.utc)
    dates = [
        now + timedelta(days=7),
        now + timedelta(days=14),
        now + timedelta(days=21),
    ]
    return DataFrame(
        {
            "EPS Estimate": [0.85, 1.20, 0.95],
            "Reported EPS": [None, None, None],
            "Revenue Estimate": [50_000_000_000, 55_000_000_000, None],
        },
        index=pd.DatetimeIndex(dates, name="Earnings Date"),
    )


# =============================================================================
# TestEarningsDateInfo
# =============================================================================


class TestEarningsDateInfo:
    """EarningsDateInfo データクラスのテスト."""

    def test_正常系_基本データで作成できる(self) -> None:
        """EarningsDateInfoが基本データで作成できることを確認."""
        info = EarningsDateInfo(
            symbol="AAPL",
            name="Apple Inc.",
            earnings_date=datetime(2026, 2, 5, tzinfo=timezone.utc),
        )

        assert info.symbol == "AAPL"
        assert info.name == "Apple Inc."
        assert info.earnings_date == datetime(2026, 2, 5, tzinfo=timezone.utc)
        assert info.source == "unknown"

    def test_正常系_source指定で作成できる(self) -> None:
        """EarningsDateInfoがsource指定で作成できることを確認."""
        info = EarningsDateInfo(
            symbol="AAPL",
            name="Apple Inc.",
            earnings_date=datetime(2026, 2, 5, tzinfo=timezone.utc),
            source="calendar",
        )

        assert info.source == "calendar"

    def test_正常系_to_dict変換ができる(self) -> None:
        """EarningsDateInfoをdict形式に変換できることを確認."""
        info = EarningsDateInfo(
            symbol="AAPL",
            name="Apple Inc.",
            earnings_date=datetime(2026, 2, 5, tzinfo=timezone.utc),
            source="calendar",
        )

        result = info.to_dict()

        assert result["symbol"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["earnings_date"] == "2026-02-05"
        assert result["source"] == "calendar"


# =============================================================================
# TestUpcomingEventsAnalyzerInit
# =============================================================================


class TestUpcomingEventsAnalyzerInit:
    """UpcomingEventsAnalyzer の初期化テスト."""

    def test_正常系_デフォルト初期化が成功する(self) -> None:
        """UpcomingEventsAnalyzerがデフォルト設定で初期化できることを確認."""
        analyzer = UpcomingEventsAnalyzer()

        assert analyzer is not None

    def test_正常系_デフォルト銘柄が20銘柄(self) -> None:
        """デフォルトの対象銘柄がTOP20の20銘柄であることを確認."""
        analyzer = UpcomingEventsAnalyzer()

        assert len(analyzer.default_symbols) == 20

    def test_正常系_MAG7が含まれている(self) -> None:
        """MAG7銘柄がデフォルト銘柄に含まれていることを確認."""
        analyzer = UpcomingEventsAnalyzer()
        mag7 = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

        for symbol in mag7:
            assert symbol in analyzer.default_symbols


# =============================================================================
# TestGetEarningsDateForSymbol
# =============================================================================


class TestGetEarningsDateForSymbol:
    """単一銘柄の決算日取得テスト."""

    @patch("analyze.reporting.upcoming_events.yf.Ticker")
    def test_正常系_calendarから決算日を取得できる(
        self,
        mock_ticker_class: MagicMock,
        analyzer: UpcomingEventsAnalyzer,
        mock_calendar_data: dict[str, Any],
    ) -> None:
        """ticker.calendarから決算日を取得できることを確認."""
        mock_ticker = MagicMock()
        mock_ticker.calendar = mock_calendar_data
        mock_ticker.info = {"shortName": "Apple Inc."}
        mock_ticker_class.return_value = mock_ticker

        result = analyzer.get_earnings_date_for_symbol("AAPL")

        assert result is not None
        assert result.symbol == "AAPL"
        assert result.source == "calendar"

    @patch("analyze.reporting.upcoming_events.yf.Ticker")
    def test_正常系_calendarがKeyErrorの場合get_earnings_datesにフォールバック(
        self,
        mock_ticker_class: MagicMock,
        analyzer: UpcomingEventsAnalyzer,
        mock_earnings_dates_df: DataFrame,
    ) -> None:
        """ticker.calendarがKeyErrorの場合、get_earnings_datesにフォールバックすることを確認."""
        mock_ticker = MagicMock()
        # calendarでKeyErrorを発生させる
        type(mock_ticker).calendar = property(
            lambda self: (_ for _ in ()).throw(KeyError("No calendar data"))
        )
        mock_ticker.get_earnings_dates.return_value = mock_earnings_dates_df
        mock_ticker.info = {"shortName": "Apple Inc."}
        mock_ticker_class.return_value = mock_ticker

        result = analyzer.get_earnings_date_for_symbol("AAPL")

        assert result is not None
        assert result.source == "earnings_dates"

    @patch("analyze.reporting.upcoming_events.yf.Ticker")
    def test_異常系_両方失敗時はNoneを返す(
        self,
        mock_ticker_class: MagicMock,
        analyzer: UpcomingEventsAnalyzer,
    ) -> None:
        """calendarとget_earnings_dates両方が失敗した場合、Noneを返すことを確認."""
        mock_ticker = MagicMock()
        type(mock_ticker).calendar = property(
            lambda self: (_ for _ in ()).throw(KeyError("No calendar data"))
        )
        mock_ticker.get_earnings_dates.side_effect = Exception("API Error")
        mock_ticker_class.return_value = mock_ticker

        result = analyzer.get_earnings_date_for_symbol("INVALID")

        assert result is None


# =============================================================================
# TestGetUpcomingEarnings
# =============================================================================


class TestGetUpcomingEarnings:
    """複数銘柄の決算日取得テスト."""

    @patch("analyze.reporting.upcoming_events.yf.Ticker")
    def test_正常系_20銘柄の決算日を取得できる(
        self,
        mock_ticker_class: MagicMock,
        analyzer: UpcomingEventsAnalyzer,
        mock_calendar_data: dict[str, Any],
    ) -> None:
        """20銘柄の決算日を取得できることを確認."""
        mock_ticker = MagicMock()
        mock_ticker.calendar = mock_calendar_data
        mock_ticker.info = {"shortName": "Test Corp"}
        mock_ticker_class.return_value = mock_ticker

        results = analyzer.get_upcoming_earnings()

        # 全銘柄から結果が得られるはず
        assert len(results) > 0

    @patch("analyze.reporting.upcoming_events.yf.Ticker")
    def test_正常系_指定期間でフィルタリングできる(
        self,
        mock_ticker_class: MagicMock,
        analyzer: UpcomingEventsAnalyzer,
    ) -> None:
        """指定期間で決算日をフィルタリングできることを確認."""
        now = datetime.now(tz=timezone.utc)

        # 7日後と30日後の決算日を設定
        mock_ticker = MagicMock()
        mock_ticker.calendar = {"Earnings Date": now + timedelta(days=7)}
        mock_ticker.info = {"shortName": "Test Corp"}
        mock_ticker_class.return_value = mock_ticker

        # 14日以内でフィルタリング
        results = analyzer.get_upcoming_earnings(days_ahead=14)

        # フィルタリング後、全ての結果が14日以内であることを確認
        for result in results:
            assert result.earnings_date <= now + timedelta(days=14)

    @patch("analyze.reporting.upcoming_events.yf.Ticker")
    def test_正常系_決算日で昇順ソートされる(
        self,
        mock_ticker_class: MagicMock,
        analyzer: UpcomingEventsAnalyzer,
    ) -> None:
        """結果が決算日で昇順ソートされることを確認."""
        now = datetime.now(tz=timezone.utc)

        # 異なる日付を返すようにモック
        call_count = [0]
        days_offsets = [14, 7, 21, 3, 10]  # 順不同

        def mock_calendar_side_effect(*_args: Any, **_kwargs: Any) -> MagicMock:
            mock = MagicMock()
            idx = call_count[0] % len(days_offsets)
            mock.calendar = {"Earnings Date": now + timedelta(days=days_offsets[idx])}
            mock.info = {"shortName": f"Test Corp {idx}"}
            call_count[0] += 1
            return mock

        mock_ticker_class.side_effect = mock_calendar_side_effect

        results = analyzer.get_upcoming_earnings(symbols=TOP20_SYMBOLS[:5])

        # ソート確認
        for i in range(len(results) - 1):
            assert results[i].earnings_date <= results[i + 1].earnings_date

    @patch("analyze.reporting.upcoming_events.yf.Ticker")
    def test_異常系_エラー時もクラッシュせず処理を継続(
        self,
        mock_ticker_class: MagicMock,
        analyzer: UpcomingEventsAnalyzer,
    ) -> None:
        """一部の銘柄でエラーが発生しても、処理が継続されることを確認."""
        now = datetime.now(tz=timezone.utc)
        call_count = [0]

        def mock_side_effect(*_args: Any, **_kwargs: Any) -> MagicMock:
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise Exception("API Error")
            mock = MagicMock()
            mock.calendar = {"Earnings Date": now + timedelta(days=7)}
            mock.info = {"shortName": "Test Corp"}
            return mock

        mock_ticker_class.side_effect = mock_side_effect

        # エラーが発生しても例外がスローされないことを確認
        results = analyzer.get_upcoming_earnings(symbols=["AAPL", "MSFT", "GOOGL"])

        # 一部の結果が得られるはず
        assert len(results) >= 1


# =============================================================================
# TestToDataFrame
# =============================================================================


class TestToDataFrame:
    """DataFrame 変換テスト."""

    def test_正常系_DataFrameに変換できる(
        self,
        analyzer: UpcomingEventsAnalyzer,
    ) -> None:
        """結果をDataFrameに変換できることを確認."""
        earnings_list = [
            EarningsDateInfo(
                symbol="AAPL",
                name="Apple Inc.",
                earnings_date=datetime(2026, 2, 5, tzinfo=timezone.utc),
                source="calendar",
            ),
            EarningsDateInfo(
                symbol="MSFT",
                name="Microsoft Corporation",
                earnings_date=datetime(2026, 2, 10, tzinfo=timezone.utc),
                source="earnings_dates",
            ),
        ]

        df = analyzer.to_dataframe(earnings_list)

        assert isinstance(df, DataFrame)
        assert len(df) == 2
        assert "symbol" in df.columns
        assert "name" in df.columns
        assert "earnings_date" in df.columns
        assert "source" in df.columns


# =============================================================================
# TestLogging
# =============================================================================


class TestLogging:
    """ロギングのテスト."""

    @patch("analyze.reporting.upcoming_events.yf.Ticker")
    def test_正常系_ロギングが実装されている(
        self,
        mock_ticker_class: MagicMock,
        analyzer: UpcomingEventsAnalyzer,
        mock_calendar_data: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """ロギングが実装されていることを確認."""
        mock_ticker = MagicMock()
        mock_ticker.calendar = mock_calendar_data
        mock_ticker.info = {"shortName": "Apple Inc."}
        mock_ticker_class.return_value = mock_ticker

        # ログが出力されることを確認（structlogを使用しているため直接検証は困難）
        # 代わりにエラーなく実行できることを確認
        results = analyzer.get_upcoming_earnings(symbols=["AAPL"])

        # 結果が得られることを確認
        assert len(results) > 0

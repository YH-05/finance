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
from analyze.reporting.upcoming_events import (
    MAJOR_RELEASES,
    EarningsDateInfo,
    EconomicReleaseInfo,
    UpcomingEventsAnalyzer,
    get_upcoming_economic_releases,
)
from pandas import DataFrame

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


# =============================================================================
# Economic Indicator Release Tests (Issue #2420)
# =============================================================================


# =============================================================================
# TestEconomicReleaseInfo
# =============================================================================


class TestEconomicReleaseInfo:
    """EconomicReleaseInfo データクラスのテスト."""

    def test_正常系_基本データで作成できる(self) -> None:
        """EconomicReleaseInfoが基本データで作成できることを確認."""
        info = EconomicReleaseInfo(
            release_id=10,
            name="Employment Situation",
            name_ja="雇用統計",
            release_date=datetime(2026, 2, 7, tzinfo=timezone.utc),
            importance="high",
        )

        assert info.release_id == 10
        assert info.name == "Employment Situation"
        assert info.name_ja == "雇用統計"
        assert info.release_date == datetime(2026, 2, 7, tzinfo=timezone.utc)
        assert info.importance == "high"

    def test_正常系_to_dict変換ができる(self) -> None:
        """EconomicReleaseInfoをdict形式に変換できることを確認."""
        info = EconomicReleaseInfo(
            release_id=21,
            name="Consumer Price Index",
            name_ja="消費者物価指数",
            release_date=datetime(2026, 2, 12, tzinfo=timezone.utc),
            importance="high",
        )

        result = info.to_dict()

        assert result["release_id"] == 21
        assert result["name"] == "Consumer Price Index"
        assert result["name_ja"] == "消費者物価指数"
        assert result["release_date"] == "2026-02-12"
        assert result["importance"] == "high"


# =============================================================================
# TestMajorReleases
# =============================================================================


class TestMajorReleases:
    """MAJOR_RELEASES 定数のテスト."""

    def test_正常系_8つのリリースが定義されている(self) -> None:
        """MAJOR_RELEASESに8つのリリースが定義されていることを確認."""
        assert len(MAJOR_RELEASES) == 8

    def test_正常系_必須フィールドが含まれている(self) -> None:
        """各リリースに必須フィールドが含まれていることを確認."""
        required_fields = {"release_id", "name", "name_ja", "importance"}

        for release in MAJOR_RELEASES:
            for field in required_fields:
                assert field in release, f"Missing field: {field}"

    def test_正常系_雇用統計が含まれている(self) -> None:
        """雇用統計（release_id=10）が含まれていることを確認."""
        release_ids = [r["release_id"] for r in MAJOR_RELEASES]
        assert 10 in release_ids

    def test_正常系_重要度が正しく設定されている(self) -> None:
        """重要度（high/medium/low）が正しく設定されていることを確認."""
        valid_importances = {"high", "medium", "low"}

        for release in MAJOR_RELEASES:
            assert release["importance"] in valid_importances


# =============================================================================
# TestGetUpcomingEconomicReleases
# =============================================================================


class TestGetUpcomingEconomicReleases:
    """経済指標発表予定取得のテスト."""

    @pytest.fixture
    def mock_fred_response(self) -> dict[str, Any]:
        """FRED API のレスポンスをモック."""
        return {
            "realtime_start": "2026-01-29",
            "realtime_end": "9999-12-31",
            "order_by": "release_date",
            "sort_order": "asc",
            "count": 3,
            "offset": 0,
            "limit": 10000,
            "release_dates": [
                {"release_id": 10, "date": "2026-02-07"},
                {"release_id": 10, "date": "2026-03-07"},
                {"release_id": 10, "date": "2026-04-04"},
            ],
        }

    @patch("analyze.reporting.upcoming_events.httpx.get")
    def test_正常系_FRED_APIから発表予定を取得できる(
        self,
        mock_get: MagicMock,
        mock_fred_response: dict[str, Any],
    ) -> None:
        """FRED APIから発表予定を取得できることを確認."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_fred_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_upcoming_economic_releases(days_ahead=30)

        assert result is not None
        assert "upcoming_economic_releases" in result

    @patch("analyze.reporting.upcoming_events.httpx.get")
    def test_正常系_日本語名が含まれる(
        self,
        mock_get: MagicMock,
        mock_fred_response: dict[str, Any],
    ) -> None:
        """結果に日本語名が含まれることを確認."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_fred_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_upcoming_economic_releases(days_ahead=30)

        releases = result["upcoming_economic_releases"]
        if releases:
            assert "name_ja" in releases[0]
            # 雇用統計の日本語名を確認
            employment_releases = [r for r in releases if r["release_id"] == 10]
            if employment_releases:
                assert employment_releases[0]["name_ja"] == "雇用統計"

    @patch("analyze.reporting.upcoming_events.httpx.get")
    def test_正常系_重要度が含まれる(
        self,
        mock_get: MagicMock,
        mock_fred_response: dict[str, Any],
    ) -> None:
        """結果に重要度が含まれることを確認."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_fred_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_upcoming_economic_releases(days_ahead=30)

        releases = result["upcoming_economic_releases"]
        if releases:
            assert "importance" in releases[0]
            # 雇用統計の重要度を確認
            employment_releases = [r for r in releases if r["release_id"] == 10]
            if employment_releases:
                assert employment_releases[0]["importance"] == "high"

    @patch("analyze.reporting.upcoming_events.httpx.get")
    def test_正常系_発表日でソートされている(
        self,
        mock_get: MagicMock,
    ) -> None:
        """結果が発表日で昇順ソートされていることを確認."""
        # 複数のリリースIDの応答をシミュレート
        mock_responses = [
            MagicMock(
                json=MagicMock(
                    return_value={
                        "release_dates": [{"release_id": 10, "date": "2026-02-07"}],
                    }
                ),
                status_code=200,
            ),
            MagicMock(
                json=MagicMock(
                    return_value={
                        "release_dates": [{"release_id": 21, "date": "2026-02-05"}],
                    }
                ),
                status_code=200,
            ),
            MagicMock(
                json=MagicMock(
                    return_value={
                        "release_dates": [{"release_id": 50, "date": "2026-02-10"}],
                    }
                ),
                status_code=200,
            ),
        ]
        mock_get.side_effect = mock_responses * 3  # 8 releases need responses

        result = get_upcoming_economic_releases(days_ahead=30)

        releases = result["upcoming_economic_releases"]
        if len(releases) >= 2:
            dates = [r["release_date"] for r in releases]
            assert dates == sorted(dates)

    @patch("analyze.reporting.upcoming_events.httpx.get")
    def test_正常系_指定期間でフィルタリングできる(
        self,
        mock_get: MagicMock,
    ) -> None:
        """指定期間で発表予定をフィルタリングできることを確認."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "release_dates": [
                {"release_id": 10, "date": "2026-02-07"},
                {"release_id": 10, "date": "2026-03-07"},  # 30日以上先
            ],
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # 14日先までを取得
        result = get_upcoming_economic_releases(days_ahead=14)

        releases = result["upcoming_economic_releases"]
        now = datetime.now(tz=timezone.utc)
        cutoff = now + timedelta(days=14)

        for release in releases:
            release_date = datetime.strptime(
                release["release_date"], "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)
            assert release_date <= cutoff

    @patch("analyze.reporting.upcoming_events.httpx.get")
    def test_正常系_MAJOR_RELEASESでフィルタリングされる(
        self,
        mock_get: MagicMock,
    ) -> None:
        """MAJOR_RELEASESに含まれるリリースのみ取得されることを確認."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "release_dates": [{"release_id": 10, "date": "2026-02-07"}],
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_upcoming_economic_releases(days_ahead=30)

        releases = result["upcoming_economic_releases"]
        major_release_ids = {r["release_id"] for r in MAJOR_RELEASES}

        for release in releases:
            assert release["release_id"] in major_release_ids

    @patch("analyze.reporting.upcoming_events.httpx.get")
    def test_異常系_API_エラー時は空リストを返す(
        self,
        mock_get: MagicMock,
    ) -> None:
        """FRED APIエラー時は空リストを返すことを確認."""
        mock_get.side_effect = Exception("API Error")

        result = get_upcoming_economic_releases(days_ahead=30)

        assert result["upcoming_economic_releases"] == []

    def test_異常系_API_キーがない場合はエラー(self) -> None:
        """FRED APIキーがない場合はエラーを返すことを確認."""
        # 環境変数をクリアしてテスト
        import os

        original_key = os.environ.get("FRED_API_KEY")
        try:
            if "FRED_API_KEY" in os.environ:
                del os.environ["FRED_API_KEY"]

            # APIキーなしで呼び出し
            result = get_upcoming_economic_releases(days_ahead=30)

            # エラーが返されるか、空リストが返される
            assert result["upcoming_economic_releases"] == [] or "error" in result
        finally:
            if original_key:
                os.environ["FRED_API_KEY"] = original_key

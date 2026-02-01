"""Unit tests for earnings calendar module.

This test file is for the new analyze.earnings package.
It mirrors the tests from market_analysis.analysis.earnings but uses
the new import path.

Note: These tests are in Red state until the analyze.earnings module
is implemented.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from analyze.earnings import (
    EarningsCalendar,
    EarningsData,
    get_upcoming_earnings,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_earnings_dates() -> pd.DataFrame:
    """Create mock earnings dates DataFrame as returned by yfinance."""
    now = datetime.now(tz=timezone.utc)
    dates = [
        now + timedelta(days=3),  # 3 days from now
        now + timedelta(days=10),  # 10 days from now
        now + timedelta(days=20),  # 20 days from now (outside 2 weeks)
        now - timedelta(days=5),  # 5 days ago (past)
    ]

    return pd.DataFrame(
        {
            "EPS Estimate": [0.85, 1.20, 0.95, 0.75],
            "Reported EPS": [None, None, None, 0.78],
            "Revenue Estimate": [38_500_000_000, 45_000_000_000, None, 35_000_000_000],
        },
        index=pd.DatetimeIndex(dates, name="Earnings Date"),
    )


@pytest.fixture
def mock_ticker_info() -> dict:
    """Create mock ticker info."""
    return {
        "shortName": "NVIDIA Corporation",
        "symbol": "NVDA",
        "sector": "Technology",
    }


@pytest.fixture
def earnings_calendar() -> EarningsCalendar:
    """Create EarningsCalendar instance."""
    return EarningsCalendar()


# =============================================================================
# TestEarningsData
# =============================================================================


class TestEarningsData:
    """Tests for EarningsData dataclass."""

    def test_正常系_基本データで作成できる(self) -> None:
        """EarningsDataが基本データで作成できることを確認。"""
        data = EarningsData(
            ticker="NVDA",
            name="NVIDIA Corporation",
            earnings_date=datetime(2026, 1, 28, tzinfo=timezone.utc),
        )

        assert data.ticker == "NVDA"
        assert data.name == "NVIDIA Corporation"
        assert data.earnings_date == datetime(2026, 1, 28, tzinfo=timezone.utc)
        assert data.eps_estimate is None
        assert data.revenue_estimate is None

    def test_正常系_全データで作成できる(self) -> None:
        """EarningsDataが全データで作成できることを確認。"""
        data = EarningsData(
            ticker="NVDA",
            name="NVIDIA Corporation",
            earnings_date=datetime(2026, 1, 28, tzinfo=timezone.utc),
            eps_estimate=0.85,
            revenue_estimate=38_500_000_000,
        )

        assert data.eps_estimate == 0.85
        assert data.revenue_estimate == 38_500_000_000

    def test_正常系_to_dict変換ができる(self) -> None:
        """EarningsDataをdict形式に変換できることを確認。"""
        data = EarningsData(
            ticker="NVDA",
            name="NVIDIA Corporation",
            earnings_date=datetime(2026, 1, 28, tzinfo=timezone.utc),
            eps_estimate=0.85,
            revenue_estimate=38_500_000_000,
        )

        result = data.to_dict()

        assert result["ticker"] == "NVDA"
        assert result["name"] == "NVIDIA Corporation"
        assert result["earnings_date"] == "2026-01-28"
        assert result["eps_estimate"] == 0.85
        assert result["revenue_estimate"] == 38_500_000_000


# =============================================================================
# TestEarningsCalendar
# =============================================================================


class TestEarningsCalendar:
    """Tests for EarningsCalendar class."""

    def test_正常系_デフォルトシンボルリストが存在する(
        self,
        earnings_calendar: EarningsCalendar,
    ) -> None:
        """デフォルトのシンボルリスト（Mag7 + セクター代表）が存在することを確認。"""
        symbols = earnings_calendar.default_symbols

        # Mag7 should be included
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        assert "AMZN" in symbols
        assert "NVDA" in symbols
        assert "META" in symbols
        assert "TSLA" in symbols

        # Should have more than just Mag7
        assert len(symbols) > 7

    @patch("yfinance.Ticker")
    def test_正常系_単一銘柄の決算日を取得できる(
        self,
        mock_ticker_class: MagicMock,
        earnings_calendar: EarningsCalendar,
        mock_earnings_dates: pd.DataFrame,
        mock_ticker_info: dict,
    ) -> None:
        """単一銘柄の決算日を取得できることを確認。"""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.return_value = mock_earnings_dates
        mock_ticker.info = mock_ticker_info
        mock_ticker_class.return_value = mock_ticker

        result = earnings_calendar.get_earnings_for_symbol("NVDA")

        assert result is not None
        assert result.ticker == "NVDA"
        mock_ticker.get_earnings_dates.assert_called_once()

    @patch("yfinance.Ticker")
    def test_正常系_今後2週間以内の決算をフィルタリングできる(
        self,
        mock_ticker_class: MagicMock,
        earnings_calendar: EarningsCalendar,
        mock_earnings_dates: pd.DataFrame,
        mock_ticker_info: dict,
    ) -> None:
        """今後2週間以内の決算を正しくフィルタリングできることを確認。"""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.return_value = mock_earnings_dates
        mock_ticker.info = mock_ticker_info
        mock_ticker_class.return_value = mock_ticker

        results = earnings_calendar.get_upcoming_earnings(
            symbols=["NVDA"],
            days_ahead=14,
        )

        # Should include at least 1 earnings within 14 days
        # (get_earnings_for_symbol returns the nearest future date per symbol)
        assert len(results) >= 1

        # Verify dates are within range
        now = datetime.now(tz=timezone.utc)
        for result in results:
            assert result.earnings_date > now
            assert result.earnings_date <= now + timedelta(days=14)

    @patch("yfinance.Ticker")
    def test_正常系_EPS予想と売上予想を取得できる(
        self,
        mock_ticker_class: MagicMock,
        earnings_calendar: EarningsCalendar,
        mock_earnings_dates: pd.DataFrame,
        mock_ticker_info: dict,
    ) -> None:
        """EPS予想と売上予想を取得できることを確認。"""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.return_value = mock_earnings_dates
        mock_ticker.info = mock_ticker_info
        mock_ticker_class.return_value = mock_ticker

        result = earnings_calendar.get_earnings_for_symbol("NVDA")

        assert result is not None
        assert result.eps_estimate == 0.85
        assert result.revenue_estimate == 38_500_000_000

    @patch("yfinance.Ticker")
    def test_正常系_複数銘柄の決算を取得できる(
        self,
        mock_ticker_class: MagicMock,
        earnings_calendar: EarningsCalendar,
        mock_earnings_dates: pd.DataFrame,
    ) -> None:
        """複数銘柄の決算を取得できることを確認。"""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.return_value = mock_earnings_dates
        mock_ticker.info = {"shortName": "Test Corp", "symbol": "TEST"}
        mock_ticker_class.return_value = mock_ticker

        results = earnings_calendar.get_upcoming_earnings(
            symbols=["AAPL", "MSFT", "GOOGL"],
            days_ahead=14,
        )

        # Each symbol should have results (mock returns same data for all)
        assert len(results) > 0

    @patch("yfinance.Ticker")
    def test_正常系_決算日で昇順ソートされる(
        self,
        mock_ticker_class: MagicMock,
        earnings_calendar: EarningsCalendar,
        mock_earnings_dates: pd.DataFrame,
        mock_ticker_info: dict,
    ) -> None:
        """結果が決算日で昇順ソートされることを確認。"""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.return_value = mock_earnings_dates
        mock_ticker.info = mock_ticker_info
        mock_ticker_class.return_value = mock_ticker

        results = earnings_calendar.get_upcoming_earnings(
            symbols=["NVDA"],
            days_ahead=14,
        )

        # Verify sorted order
        for i in range(len(results) - 1):
            assert results[i].earnings_date <= results[i + 1].earnings_date

    @patch("yfinance.Ticker")
    def test_異常系_APIエラー時は空リストを返す(
        self,
        mock_ticker_class: MagicMock,
        earnings_calendar: EarningsCalendar,
    ) -> None:
        """APIエラー時は空リストを返すことを確認。"""
        # Setup mock to raise exception
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.side_effect = Exception("API Error")
        mock_ticker_class.return_value = mock_ticker

        result = earnings_calendar.get_earnings_for_symbol("INVALID")

        assert result is None

    @patch("yfinance.Ticker")
    def test_異常系_決算データがない銘柄はスキップ(
        self,
        mock_ticker_class: MagicMock,
        earnings_calendar: EarningsCalendar,
    ) -> None:
        """決算データがない銘柄はスキップされることを確認。"""
        # Setup mock to return empty DataFrame
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.return_value = pd.DataFrame()
        mock_ticker.info = {"shortName": "Empty Corp"}
        mock_ticker_class.return_value = mock_ticker

        results = earnings_calendar.get_upcoming_earnings(
            symbols=["EMPTY"],
            days_ahead=14,
        )

        assert len(results) == 0

    def test_正常系_JSON出力形式に変換できる(
        self,
        earnings_calendar: EarningsCalendar,
    ) -> None:
        """結果をJSON出力形式に変換できることを確認。"""
        earnings_list = [
            EarningsData(
                ticker="NVDA",
                name="NVIDIA Corporation",
                earnings_date=datetime(2026, 1, 28, tzinfo=timezone.utc),
                eps_estimate=0.85,
                revenue_estimate=38_500_000_000,
            ),
            EarningsData(
                ticker="AAPL",
                name="Apple Inc.",
                earnings_date=datetime(2026, 1, 30, tzinfo=timezone.utc),
                eps_estimate=2.10,
                revenue_estimate=124_000_000_000,
            ),
        ]

        result = earnings_calendar.to_json_output(earnings_list)

        assert "upcoming_earnings" in result
        assert len(result["upcoming_earnings"]) == 2
        assert result["upcoming_earnings"][0]["ticker"] == "NVDA"
        assert result["upcoming_earnings"][1]["ticker"] == "AAPL"


# =============================================================================
# TestGetUpcomingEarnings (convenience function)
# =============================================================================


class TestGetUpcomingEarnings:
    """Tests for get_upcoming_earnings convenience function."""

    @patch("yfinance.Ticker")
    def test_正常系_デフォルト設定で取得できる(
        self,
        mock_ticker_class: MagicMock,
        mock_earnings_dates: pd.DataFrame,
        mock_ticker_info: dict,
    ) -> None:
        """デフォルト設定で決算情報を取得できることを確認。"""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.return_value = mock_earnings_dates
        mock_ticker.info = mock_ticker_info
        mock_ticker_class.return_value = mock_ticker

        result = get_upcoming_earnings(symbols=["NVDA"])

        assert "upcoming_earnings" in result
        assert len(result["upcoming_earnings"]) > 0

    @patch("yfinance.Ticker")
    def test_正常系_カスタム日数で取得できる(
        self,
        mock_ticker_class: MagicMock,
        mock_earnings_dates: pd.DataFrame,
        mock_ticker_info: dict,
    ) -> None:
        """カスタム日数指定で決算情報を取得できることを確認。"""
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker.get_earnings_dates.return_value = mock_earnings_dates
        mock_ticker.info = mock_ticker_info
        mock_ticker_class.return_value = mock_ticker

        result = get_upcoming_earnings(symbols=["NVDA"], days_ahead=7)

        # With 7 days, only the 3-day-ahead earnings should be included
        assert "upcoming_earnings" in result
        # Verify all results are within 7 days
        now = datetime.now(tz=timezone.utc)
        for item in result["upcoming_earnings"]:
            earnings_date = datetime.fromisoformat(item["earnings_date"])
            if earnings_date.tzinfo is None:
                earnings_date = earnings_date.replace(tzinfo=timezone.utc)
            assert (earnings_date - now).days <= 7

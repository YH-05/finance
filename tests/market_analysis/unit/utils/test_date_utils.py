"""Unit tests for market_analysis.utils.date_utils module.

This module tests the date utility functions used for weekly comment
period calculation and date formatting.
"""

from __future__ import annotations

from datetime import date

import pytest

from market_analysis.utils.date_utils import (
    calculate_weekly_comment_period,
    format_date_japanese,
    format_date_us,
    get_last_tuesday,
    get_previous_tuesday,
    get_trading_days_in_period,
    parse_date,
)


class TestGetPreviousTuesday:
    """Tests for get_previous_tuesday function."""

    def test_正常系_火曜日からは火曜日自身を返す(self) -> None:
        # 2026-01-20 is a Tuesday
        result = get_previous_tuesday(date(2026, 1, 20))
        assert result == date(2026, 1, 20)

    def test_正常系_水曜日からは前日の火曜日を返す(self) -> None:
        # 2026-01-21 is a Wednesday
        result = get_previous_tuesday(date(2026, 1, 21))
        assert result == date(2026, 1, 20)

    def test_正常系_月曜日からは先週の火曜日を返す(self) -> None:
        # 2026-01-19 is a Monday
        result = get_previous_tuesday(date(2026, 1, 19))
        assert result == date(2026, 1, 13)

    def test_正常系_日曜日からは直前の火曜日を返す(self) -> None:
        # 2026-01-18 is a Sunday
        result = get_previous_tuesday(date(2026, 1, 18))
        assert result == date(2026, 1, 13)

    def test_正常系_土曜日からは直前の火曜日を返す(self) -> None:
        # 2026-01-17 is a Saturday
        result = get_previous_tuesday(date(2026, 1, 17))
        assert result == date(2026, 1, 13)


class TestGetLastTuesday:
    """Tests for get_last_tuesday function."""

    def test_正常系_水曜日からは先週の火曜日を返す(self) -> None:
        # 2026-01-21 is Wednesday -> should return 2026-01-13
        result = get_last_tuesday(date(2026, 1, 21))
        assert result == date(2026, 1, 13)

    def test_正常系_火曜日からは先週の火曜日を返す(self) -> None:
        # 2026-01-20 is Tuesday -> should return 2026-01-13
        result = get_last_tuesday(date(2026, 1, 20))
        assert result == date(2026, 1, 13)


class TestCalculateWeeklyCommentPeriod:
    """Tests for calculate_weekly_comment_period function."""

    def test_正常系_水曜日に実行すると前週火曜から当週火曜までの期間を返す(
        self,
    ) -> None:
        # 2026-01-21 is Wednesday (report generation day)
        result = calculate_weekly_comment_period(date(2026, 1, 21))

        assert result["start"] == date(2026, 1, 13)
        assert result["end"] == date(2026, 1, 20)
        assert result["reference"] == date(2026, 1, 21)
        assert result["report_date"] == date(2026, 1, 21)

    def test_正常系_火曜日に実行すると先々週火曜から先週火曜までの期間を返す(
        self,
    ) -> None:
        # 2026-01-20 is Tuesday
        result = calculate_weekly_comment_period(date(2026, 1, 20))

        assert result["start"] == date(2026, 1, 13)
        assert result["end"] == date(2026, 1, 20)
        assert result["reference"] == date(2026, 1, 20)
        assert result["report_date"] == date(2026, 1, 21)

    def test_正常系_reference_dateがNoneの場合は今日の日付を使用(self) -> None:
        result = calculate_weekly_comment_period(None)

        # Just verify the structure is correct
        assert "start" in result
        assert "end" in result
        assert "reference" in result
        assert "report_date" in result

        # End should be 7 days after start
        assert (result["end"] - result["start"]).days == 7


class TestFormatDateJapanese:
    """Tests for format_date_japanese function."""

    def test_正常系_fullスタイルで年月日と曜日を返す(self) -> None:
        # 2026-01-21 is Wednesday
        result = format_date_japanese(date(2026, 1, 21), "full")
        assert result == "2026年1月21日(水)"

    def test_正常系_shortスタイルで月日と曜日を返す(self) -> None:
        # 2026-01-21 is Wednesday
        result = format_date_japanese(date(2026, 1, 21), "short")
        assert result == "1/21(水)"

    def test_正常系_weekdayスタイルで曜日のみを返す(self) -> None:
        # 2026-01-21 is Wednesday
        result = format_date_japanese(date(2026, 1, 21), "weekday")
        assert result == "水"

    def test_正常系_デフォルトはfullスタイル(self) -> None:
        # 2026-01-21 is Wednesday
        result = format_date_japanese(date(2026, 1, 21))
        assert result == "2026年1月21日(水)"

    def test_正常系_各曜日が正しく表示される(self) -> None:
        # Sunday through Saturday with correct 2026 dates
        weekdays = [
            (date(2026, 1, 18), "日"),  # Sunday
            (date(2026, 1, 19), "月"),  # Monday
            (date(2026, 1, 20), "火"),  # Tuesday
            (date(2026, 1, 21), "水"),  # Wednesday
            (date(2026, 1, 22), "木"),  # Thursday
            (date(2026, 1, 23), "金"),  # Friday
            (date(2026, 1, 24), "土"),  # Saturday
        ]
        for d, expected_weekday in weekdays:
            result = format_date_japanese(d, "weekday")
            assert result == expected_weekday


class TestFormatDateUs:
    """Tests for format_date_us function."""

    def test_正常系_fullスタイルで月名日年を返す(self) -> None:
        result = format_date_us(date(2026, 1, 22), "full")
        assert result == "January 22, 2026"

    def test_正常系_shortスタイルで月日を返す(self) -> None:
        result = format_date_us(date(2026, 1, 22), "short")
        assert result == "1/22"

    def test_正常系_mdyスタイルでMM_DD_YYYYを返す(self) -> None:
        result = format_date_us(date(2026, 1, 22), "mdy")
        assert result == "01/22/2026"

    def test_正常系_デフォルトはfullスタイル(self) -> None:
        result = format_date_us(date(2026, 1, 22))
        assert result == "January 22, 2026"


class TestGetTradingDaysInPeriod:
    """Tests for get_trading_days_in_period function."""

    def test_正常系_平日のみを返す(self) -> None:
        # 2026-01-18 (Sun) to 2026-01-22 (Thu)
        result = get_trading_days_in_period(date(2026, 1, 18), date(2026, 1, 22))

        # Sun(skip), Mon(1/19), Tue(1/20), Wed(1/21), Thu(1/22) = 4 trading days
        assert len(result) == 4
        assert all(d.weekday() < 5 for d in result)

    def test_正常系_月曜から金曜まで5日間(self) -> None:
        # 2026-01-19 is Monday, 1/23 is Friday
        result = get_trading_days_in_period(date(2026, 1, 19), date(2026, 1, 23))

        # Mon(1/19), Tue(1/20), Wed(1/21), Thu(1/22), Fri(1/23) = 5 days
        assert len(result) == 5
        assert all(d.weekday() < 5 for d in result)

    def test_正常系_週末のみの期間は空リスト(self) -> None:
        # 2026-01-17 is Saturday, 1/18 is Sunday
        result = get_trading_days_in_period(date(2026, 1, 17), date(2026, 1, 18))
        assert result == []

    def test_エッジケース_同じ日で平日なら1日(self) -> None:
        # 2026-01-19 is Monday
        result = get_trading_days_in_period(date(2026, 1, 19), date(2026, 1, 19))
        assert len(result) == 1
        assert result[0] == date(2026, 1, 19)


class TestParseDate:
    """Tests for parse_date function."""

    def test_正常系_YYYY_MM_DD形式をパースできる(self) -> None:
        result = parse_date("2026-01-22")
        assert result == date(2026, 1, 22)

    def test_正常系_YYYYMMDD形式をパースできる(self) -> None:
        result = parse_date("20260122")
        assert result == date(2026, 1, 22)

    def test_正常系_MM_DD_YYYY形式をパースできる(self) -> None:
        result = parse_date("01/22/2026")
        assert result == date(2026, 1, 22)

    def test_異常系_不正な形式でValueError(self) -> None:
        with pytest.raises(ValueError, match="Unable to parse date"):
            parse_date("2026/01/22")

    def test_異常系_無効な日付でValueError(self) -> None:
        with pytest.raises(ValueError):
            parse_date("not-a-date")

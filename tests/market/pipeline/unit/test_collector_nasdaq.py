"""Unit tests for market.pipeline.collector_nasdaq.NasdaqCalendarCollector.

All external dependencies (NasdaqClient, NasdaqCalendarStorage, CollectionQueue)
are replaced with MagicMocks via DI. No real HTTP calls or DB access.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from market.pipeline.collector_nasdaq import (
    QUEUE_SOURCES,
    NasdaqCalendarCollector,
    _earnings_record_to_calendar,
    _normalize_fiscal_quarter,
    _normalize_report_time,
    _parse_eps_estimate,
)
from market.pipeline.errors import CollectorError
from market.pipeline.models import EarningsCalendarRecord

# =============================================================================
# Helper to create a mock EarningsRecord (as returned by NasdaqClient)
# =============================================================================


def _mock_earnings_record(
    symbol: str = "AAPL",
    eps_estimate: str | None = "1.55",
    time: str | None = "time-after-hours",
    fiscal_quarter_ending: str | None = "Dec/2025",
) -> MagicMock:
    record = MagicMock()
    record.symbol = symbol
    record.eps_estimate = eps_estimate
    record.time = time
    record.fiscal_quarter_ending = fiscal_quarter_ending
    return record


# =============================================================================
# Private helper function tests
# =============================================================================


class TestParseEpsEstimate:
    """Tests for _parse_eps_estimate()."""

    def test_正常系_数値文字列をfloatに変換できる(self) -> None:
        assert _parse_eps_estimate("2.50") == pytest.approx(2.50)

    def test_正常系_Noneの場合はNoneを返す(self) -> None:
        assert _parse_eps_estimate(None) is None

    def test_正常系_NAの場合はNoneを返す(self) -> None:
        assert _parse_eps_estimate("N/A") is None

    def test_正常系_空文字列の場合はNoneを返す(self) -> None:
        assert _parse_eps_estimate("") is None

    def test_正常系_ダッシュの場合はNoneを返す(self) -> None:
        assert _parse_eps_estimate("—") is None

    def test_正常系_カンマ区切り数値も変換できる(self) -> None:
        assert _parse_eps_estimate("1,234.56") == pytest.approx(1234.56)

    def test_正常系_ドル記号付きも変換できる(self) -> None:
        assert _parse_eps_estimate("$2.50") == pytest.approx(2.50)

    def test_正常系_不正な文字列はNoneを返す(self) -> None:
        assert _parse_eps_estimate("abc") is None


class TestNormalizeReportTime:
    """Tests for _normalize_report_time()."""

    def test_正常系_after_hoursはafter_closeに変換(self) -> None:
        assert _normalize_report_time("time-after-hours") == "after_close"

    def test_正常系_pre_marketはbefore_openに変換(self) -> None:
        assert _normalize_report_time("time-pre-market") == "before_open"

    def test_正常系_not_suppliedはNoneに変換(self) -> None:
        assert _normalize_report_time("time-not-supplied") is None

    def test_正常系_Noneの場合はNoneを返す(self) -> None:
        assert _normalize_report_time(None) is None

    def test_正常系_不明な値はNoneを返す(self) -> None:
        assert _normalize_report_time("unknown-time") is None


class TestNormalizeFiscalQuarter:
    """Tests for _normalize_fiscal_quarter()."""

    def test_正常系_通常の値はそのまま返す(self) -> None:
        assert _normalize_fiscal_quarter("Dec/2025") == "Dec/2025"

    def test_正常系_Noneの場合はNoneを返す(self) -> None:
        assert _normalize_fiscal_quarter(None) is None

    def test_正常系_NAの場合はNoneを返す(self) -> None:
        assert _normalize_fiscal_quarter("N/A") is None

    def test_正常系_空文字列はNoneを返す(self) -> None:
        assert _normalize_fiscal_quarter("") is None


class TestEarningsRecordToCalendar:
    """Tests for _earnings_record_to_calendar()."""

    def test_正常系_有効なレコードをEarningsCalendarRecordに変換できる(
        self,
    ) -> None:
        mock_record = _mock_earnings_record("AAPL", "1.55", "time-after-hours")
        result = _earnings_record_to_calendar(mock_record, "2026-04-30", "2026-04-03T10:00:00")
        assert result is not None
        assert isinstance(result, EarningsCalendarRecord)
        assert result.symbol == "AAPL"
        assert result.report_date == "2026-04-30"
        assert result.eps_estimate == pytest.approx(1.55)
        assert result.report_time == "after_close"

    def test_正常系_シンボルなしのレコードはNoneを返す(self) -> None:
        mock_record = MagicMock()
        mock_record.symbol = None
        result = _earnings_record_to_calendar(mock_record, "2026-04-30", "2026-04-03T10:00:00")
        assert result is None

    def test_正常系_空シンボルのレコードはNoneを返す(self) -> None:
        mock_record = _mock_earnings_record(symbol="")
        result = _earnings_record_to_calendar(mock_record, "2026-04-30", "2026-04-03T10:00:00")
        assert result is None


# =============================================================================
# NasdaqCalendarCollector tests
# =============================================================================


class TestNasdaqCalendarCollectorInit:
    """Tests for NasdaqCalendarCollector initialization."""

    def test_正常系_DI経由で初期化できる(
        self,
        mock_nasdaq_client: MagicMock,
        mock_nasdaq_storage: MagicMock,
        mock_collection_queue: MagicMock,
    ) -> None:
        collector = NasdaqCalendarCollector(
            client=mock_nasdaq_client,
            storage=mock_nasdaq_storage,
            queue=mock_collection_queue,
        )
        assert collector is not None


class TestNasdaqCalendarCollectorCollectDateRange:
    """Tests for NasdaqCalendarCollector.collect_date_range()."""

    def test_正常系_空のカレンダーを処理できる(
        self,
        mock_nasdaq_client: MagicMock,
        mock_nasdaq_storage: MagicMock,
        mock_collection_queue: MagicMock,
    ) -> None:
        mock_nasdaq_client.get_earnings_calendar.return_value = []
        collector = NasdaqCalendarCollector(
            client=mock_nasdaq_client,
            storage=mock_nasdaq_storage,
            queue=mock_collection_queue,
        )
        result = collector.collect_date_range("2026-04-30", "2026-04-30")
        assert result["dates_collected"] == 1
        assert result["records_upserted"] == 0
        assert result["symbols_enqueued"] == 0
        assert result["errors"] == []

    def test_正常系_レコードをupsertしてenqueueする(
        self,
        mock_nasdaq_client: MagicMock,
        mock_nasdaq_storage: MagicMock,
        mock_collection_queue: MagicMock,
    ) -> None:
        mock_nasdaq_client.get_earnings_calendar.return_value = [
            _mock_earnings_record("AAPL"),
            _mock_earnings_record("MSFT"),
        ]
        mock_nasdaq_storage.upsert.return_value = 2
        mock_collection_queue.enqueue.return_value = len(QUEUE_SOURCES)

        collector = NasdaqCalendarCollector(
            client=mock_nasdaq_client,
            storage=mock_nasdaq_storage,
            queue=mock_collection_queue,
        )
        result = collector.collect_date_range("2026-04-30", "2026-04-30")
        assert result["records_upserted"] == 2
        mock_nasdaq_storage.upsert.assert_called_once()
        assert mock_collection_queue.enqueue.call_count == 2

    def test_正常系_複数日付を処理できる(
        self,
        mock_nasdaq_client: MagicMock,
        mock_nasdaq_storage: MagicMock,
        mock_collection_queue: MagicMock,
    ) -> None:
        mock_nasdaq_client.get_earnings_calendar.return_value = []
        collector = NasdaqCalendarCollector(
            client=mock_nasdaq_client,
            storage=mock_nasdaq_storage,
            queue=mock_collection_queue,
        )
        result = collector.collect_date_range("2026-04-28", "2026-04-30")
        assert result["dates_collected"] == 3

    def test_正常系_APIエラーはerrorsリストに記録される(
        self,
        mock_nasdaq_client: MagicMock,
        mock_nasdaq_storage: MagicMock,
        mock_collection_queue: MagicMock,
    ) -> None:
        mock_nasdaq_client.get_earnings_calendar.side_effect = Exception("API Error")
        collector = NasdaqCalendarCollector(
            client=mock_nasdaq_client,
            storage=mock_nasdaq_storage,
            queue=mock_collection_queue,
        )
        result = collector.collect_date_range("2026-04-30", "2026-04-30")
        assert result["dates_collected"] == 1
        assert len(result["errors"]) == 1

    def test_異常系_不正な日付フォーマットでCollectorError(
        self,
        mock_nasdaq_client: MagicMock,
        mock_nasdaq_storage: MagicMock,
        mock_collection_queue: MagicMock,
    ) -> None:
        collector = NasdaqCalendarCollector(
            client=mock_nasdaq_client,
            storage=mock_nasdaq_storage,
            queue=mock_collection_queue,
        )
        with pytest.raises(CollectorError):
            collector.collect_date_range("invalid-date", "2026-04-30")


class TestNasdaqCalendarCollectorCollectRecent:
    """Tests for NasdaqCalendarCollector.collect_recent()."""

    def test_正常系_指定期間の日数分処理される(
        self,
        mock_nasdaq_client: MagicMock,
        mock_nasdaq_storage: MagicMock,
        mock_collection_queue: MagicMock,
    ) -> None:
        mock_nasdaq_client.get_earnings_calendar.return_value = []
        collector = NasdaqCalendarCollector(
            client=mock_nasdaq_client,
            storage=mock_nasdaq_storage,
            queue=mock_collection_queue,
        )
        result = collector.collect_recent(days_back=3, days_forward=3)
        # 3 back + today + 3 forward = 7 days
        assert result["dates_collected"] == 7

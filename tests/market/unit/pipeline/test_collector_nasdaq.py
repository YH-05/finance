"""Unit tests for market.pipeline.collector_nasdaq.NasdaqCalendarCollector."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from market.pipeline.collector_nasdaq import NasdaqCalendarCollector

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Helpers / stubs
# ---------------------------------------------------------------------------

_QUEUE_SOURCES = ["av_earnings", "av_overview", "sec_edgar", "yfinance"]


def _make_earnings_record(symbol: str = "AAPL", date_str: str = "01/30/2026") -> MagicMock:
    """Build a minimal EarningsRecord mock."""
    rec = MagicMock()
    rec.symbol = symbol
    rec.date = date_str
    rec.eps_estimate = "2.50"
    rec.time = "time-after-hours"
    rec.fiscal_quarter_ending = "Dec/2025"
    return rec


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestNasdaqCalendarCollectorInit:
    def test_正常系_デフォルト引数で初期化できる(self, tmp_path: Path) -> None:
        """Collector should initialize without arguments (DI or default)."""
        with (
            patch("market.pipeline.collector_nasdaq.NasdaqClient") as mock_client_cls,
            patch("market.pipeline.collector_nasdaq.NasdaqCalendarStorage") as mock_storage_cls,
            patch("market.pipeline.collector_nasdaq.CollectionQueue") as mock_queue_cls,
        ):
            mock_client_cls.return_value.__enter__ = lambda s: s
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
            collector = NasdaqCalendarCollector()
        assert collector is not None

    def test_正常系_DIで依存を注入できる(self, tmp_path: Path) -> None:
        """Collector should accept injected client/storage/queue."""
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_queue = MagicMock()
        collector = NasdaqCalendarCollector(
            client=mock_client,
            storage=mock_storage,
            queue=mock_queue,
        )
        assert collector is not None


# ---------------------------------------------------------------------------
# collect_date_range
# ---------------------------------------------------------------------------


class TestCollectDateRange:
    def _make_collector(self) -> tuple[NasdaqCalendarCollector, MagicMock, MagicMock, MagicMock]:
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = 4
        mock_storage.upsert.return_value = 1
        collector = NasdaqCalendarCollector(
            client=mock_client,
            storage=mock_storage,
            queue=mock_queue,
        )
        return collector, mock_client, mock_storage, mock_queue

    def test_正常系_単一日付でclient呼び出し(self) -> None:
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = [_make_earnings_record()]

        collector.collect_date_range("2026-01-30", "2026-01-30")

        mock_client.get_earnings_calendar.assert_called_once_with("2026-01-30")

    def test_正常系_複数日付でclientを複数回呼び出し(self) -> None:
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = []

        collector.collect_date_range("2026-01-30", "2026-02-01")

        # 3 dates: 2026-01-30, 2026-01-31, 2026-02-01
        assert mock_client.get_earnings_calendar.call_count == 3

    def test_正常系_レコードが取得されたらupsertとenqueueを呼び出す(self) -> None:
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = [_make_earnings_record("AAPL")]

        collector.collect_date_range("2026-01-30", "2026-01-30")

        assert mock_storage.upsert.call_count >= 1
        assert mock_queue.enqueue.call_count >= 1

    def test_正常系_enqueueに指定ソースを渡す(self) -> None:
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = [_make_earnings_record("AAPL")]

        collector.collect_date_range("2026-01-30", "2026-01-30")

        call_args = mock_queue.enqueue.call_args
        # sources is 2nd positional arg or keyword
        passed_sources = call_args[0][2] if len(call_args[0]) > 2 else call_args[1].get("sources")
        assert set(passed_sources) == set(_QUEUE_SOURCES)

    def test_正常系_結果を返す(self) -> None:
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = [_make_earnings_record("AAPL")]

        result = collector.collect_date_range("2026-01-30", "2026-01-30")

        assert result is not None

    def test_異常系_空のレコードリストでも例外が起きない(self) -> None:
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = []

        result = collector.collect_date_range("2026-01-30", "2026-01-30")

        # No upsert or enqueue calls when empty
        assert mock_storage.upsert.call_count == 0
        assert mock_queue.enqueue.call_count == 0


# ---------------------------------------------------------------------------
# collect_recent
# ---------------------------------------------------------------------------


class TestCollectRecent:
    def _make_collector(self) -> tuple[NasdaqCalendarCollector, MagicMock, MagicMock, MagicMock]:
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_queue = MagicMock()
        mock_queue.enqueue.return_value = 4
        mock_storage.upsert.return_value = 0
        collector = NasdaqCalendarCollector(
            client=mock_client,
            storage=mock_storage,
            queue=mock_queue,
        )
        return collector, mock_client, mock_storage, mock_queue

    def test_正常系_デフォルトで14日分呼び出す(self) -> None:
        """days_back=7 + days_forward=7 = 15 days including today."""
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = []

        collector.collect_recent()

        # 7 + 1 + 7 = 15 dates
        assert mock_client.get_earnings_calendar.call_count == 15

    def test_正常系_days_back_と_days_forward_でウィンドウを制御できる(self) -> None:
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = []

        collector.collect_recent(days_back=3, days_forward=3)

        assert mock_client.get_earnings_calendar.call_count == 7  # 3+1+3

    def test_正常系_collect_date_rangeを内部的に呼び出す(self) -> None:
        """collect_recent delegates to collect_date_range."""
        collector, mock_client, mock_storage, mock_queue = self._make_collector()
        mock_client.get_earnings_calendar.return_value = []

        # Should not raise
        result = collector.collect_recent(days_back=1, days_forward=1)

        assert mock_client.get_earnings_calendar.call_count == 3

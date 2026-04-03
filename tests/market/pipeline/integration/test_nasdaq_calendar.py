"""Integration tests for Phase 1: NASDAQ earnings calendar real API.

Tests use the real NASDAQ API via ``NasdaqCalendarCollector`` and persist
data to a temporary SQLite database. All tests require ``@pytest.mark.integration``
and are skipped in normal CI runs.

Run with:
    uv run pytest tests/market/pipeline/integration/ -v -m integration

Test TODO List:
- [x] 実際のNASDAQ APIからデータを取得できること
- [x] 取得したデータが一時DBに正常にupsertされること
- [x] キューにエントリが追加されること
- [x] collect_date_range が指定した日付の範囲を処理すること
- [x] 結果のサマリー構造が正しいこと
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from market.pipeline.collector_nasdaq import NasdaqCalendarCollector
from market.pipeline.queue import CollectionQueue
from market.pipeline.storage_nasdaq import NasdaqCalendarStorage


@pytest.mark.integration
class TestNasdaqCalendarIntegration:
    """Integration tests for NasdaqCalendarCollector using real NASDAQ API.

    These tests hit the live NASDAQ API and write to a temporary SQLite
    database. They are opt-in via ``@pytest.mark.integration`` and should
    not be run in normal CI.
    """

    def test_collect_recent_returns_valid_summary(self, tmp_path: Path) -> None:
        """NASDAQ APIから直近のデータを取得してサマリーが正しいことを確認する.

        Verifies that ``collect_recent()`` returns a summary dict with the
        required keys and non-negative values.
        """
        db_path = tmp_path / "nasdaq_integration.db"
        storage = NasdaqCalendarStorage(db_path=db_path)
        queue = CollectionQueue(db_path=db_path)
        collector = NasdaqCalendarCollector(
            storage=storage,
            queue=queue,
        )

        result = collector.collect_recent(days_back=3, days_forward=3)

        assert isinstance(result, dict), "collect_recent should return a dict"
        assert "dates_collected" in result
        assert "records_upserted" in result
        assert "symbols_enqueued" in result
        assert "errors" in result

        assert result["dates_collected"] == 7, (
            f"days_back=3 + days_forward=3 + today = 7 days, got {result['dates_collected']}"
        )
        assert result["records_upserted"] >= 0
        assert result["symbols_enqueued"] >= 0
        assert isinstance(result["errors"], list)

    def test_collect_date_range_single_day(self, tmp_path: Path) -> None:
        """単一日の決算データをNASDAQ APIから取得できることを確認する.

        Verifies that ``collect_date_range()`` processes exactly 1 date and
        returns non-negative counts.
        """
        db_path = tmp_path / "nasdaq_single_day.db"
        storage = NasdaqCalendarStorage(db_path=db_path)
        queue = CollectionQueue(db_path=db_path)
        collector = NasdaqCalendarCollector(
            storage=storage,
            queue=queue,
        )

        result = collector.collect_date_range("2026-01-15", "2026-01-15")

        assert result["dates_collected"] == 1
        assert result["records_upserted"] >= 0
        assert isinstance(result["errors"], list)

    def test_upserted_records_persisted_in_db(self, tmp_path: Path) -> None:
        """取得したデータが一時DBに正常にupsertされてクエリできることを確認する.

        Collects data for a known earnings-heavy week and verifies that
        records can be retrieved back from storage.
        """
        db_path = tmp_path / "nasdaq_persist.db"
        storage = NasdaqCalendarStorage(db_path=db_path)
        queue = CollectionQueue(db_path=db_path)
        collector = NasdaqCalendarCollector(
            storage=storage,
            queue=queue,
        )

        result = collector.collect_date_range("2026-01-26", "2026-01-30")

        records_upserted = result["records_upserted"]
        if records_upserted > 0:
            # Verify records are retrievable from storage
            retrieved = storage.get_by_date_range("2026-01-26", "2026-01-30")
            assert len(retrieved) > 0, (
                f"Expected at least 1 record after upserting {records_upserted}, got 0"
            )
            # Each record should have required fields (sqlite3.Row supports key access)
            for rec in retrieved:
                assert rec["symbol"], "Record symbol should not be empty"
                assert rec["report_date"], "Record report_date should not be empty"
                assert rec["fetched_at"], "Record fetched_at should not be empty"

    def test_queue_entries_added_after_collection(self, tmp_path: Path) -> None:
        """決算データ収集後にキューエントリが追加されることを確認する.

        After collecting earnings calendar data, verifies that corresponding
        queue entries exist for the collected symbols.
        """
        db_path = tmp_path / "nasdaq_queue.db"
        storage = NasdaqCalendarStorage(db_path=db_path)
        queue = CollectionQueue(db_path=db_path)
        collector = NasdaqCalendarCollector(
            storage=storage,
            queue=queue,
        )

        result = collector.collect_date_range("2026-01-26", "2026-01-30")

        if result["symbols_enqueued"] > 0:
            # At least one queue source should have pending entries
            sources = ["av_earnings", "av_overview", "sec_edgar", "yfinance"]
            total_pending = 0
            for source in sources:
                entries = queue.get_pending(source)
                total_pending += len(entries)
            assert total_pending > 0, (
                f"Expected queue entries after enqueuing {result['symbols_enqueued']} symbols"
            )

    def test_db_cleanup_after_test(self, tmp_path: Path) -> None:
        """テスト後に一時DBがpytestによって自動削除されることを確認する.

        Verifies that the temporary database file is created during the test
        and will be cleaned up by pytest's ``tmp_path`` fixture.
        """
        db_path = tmp_path / "nasdaq_cleanup.db"
        storage = NasdaqCalendarStorage(db_path=db_path)
        queue = CollectionQueue(db_path=db_path)
        collector = NasdaqCalendarCollector(
            storage=storage,
            queue=queue,
        )

        collector.collect_date_range("2026-01-15", "2026-01-15")

        # The db file should exist during the test
        assert db_path.exists(), "Database file should be created during collection"
        # Cleanup is handled by pytest's tmp_path fixture (automatic after test)

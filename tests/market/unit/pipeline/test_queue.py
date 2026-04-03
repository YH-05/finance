"""Unit tests for market.pipeline.queue.CollectionQueue."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from market.pipeline.models import QueueEntry
from market.pipeline.queue import CollectionQueue

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def queue(tmp_path: Path) -> CollectionQueue:
    """Create a CollectionQueue backed by a temp file DB."""
    return CollectionQueue(db_path=tmp_path / "test_queue.db")


@pytest.fixture()
def mem_queue(tmp_path: Path) -> CollectionQueue:
    """Create a CollectionQueue backed by a temp file DB (named mem_queue for clarity)."""
    return CollectionQueue(db_path=tmp_path / "queue_test.db")


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


class TestCollectionQueueInit:
    def test_正常系_tmp_pathで初期化できる(self, tmp_path: Path) -> None:
        q = CollectionQueue(db_path=tmp_path / "init_test.db")
        assert q is not None

    def test_正常系_tmp_pathで別のpathで初期化できる(self, tmp_path: Path) -> None:
        q = CollectionQueue(db_path=tmp_path / "another.db")
        assert q is not None

    def test_正常系_初期化時にテーブルが作成される(self, mem_queue: CollectionQueue) -> None:
        # enqueue が成功すればテーブルは存在する
        count = mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        assert count == 1


# ---------------------------------------------------------------------------
# enqueue tests
# ---------------------------------------------------------------------------


class TestEnqueue:
    def test_正常系_単一ソースでエントリを追加できる(self, mem_queue: CollectionQueue) -> None:
        count = mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        assert count == 1

    def test_正常系_複数ソースで複数エントリを追加できる(self, mem_queue: CollectionQueue) -> None:
        count = mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq", "yfinance"])
        assert count == 2

    def test_正常系_priorityを指定できる(self, mem_queue: CollectionQueue) -> None:
        count = mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"], priority=5)
        assert count == 1

    def test_冪等性_同一エントリを2回追加しても1件のみ保存される(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        count = mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        assert count == 1
        pending = mem_queue.get_pending("nasdaq")
        assert len(pending) == 1

    def test_冪等性_同一シンボル異なるソースは別エントリとして追加される(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq", "yfinance"])
        pending_nasdaq = mem_queue.get_pending("nasdaq")
        pending_yf = mem_queue.get_pending("yfinance")
        assert len(pending_nasdaq) == 1
        assert len(pending_yf) == 1

    def test_エッジケース_空のsourcesリストでゼロを返す(self, mem_queue: CollectionQueue) -> None:
        count = mem_queue.enqueue("AAPL", "2026-04-30", [])
        assert count == 0


# ---------------------------------------------------------------------------
# get_pending tests
# ---------------------------------------------------------------------------


class TestGetPending:
    def test_正常系_pendingエントリを返す(self, mem_queue: CollectionQueue) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 1
        assert entries[0].symbol == "AAPL"
        assert entries[0].earnings_date == "2026-04-30"
        assert entries[0].source == "nasdaq"
        assert entries[0].status == "pending"

    def test_正常系_priority_DESC_created_at_ASCの順で返す(
        self, mem_queue: CollectionQueue
    ) -> None:
        # priority=0 (low) entry first
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"], priority=0)
        # priority=5 (high) entry second
        mem_queue.enqueue("MSFT", "2026-04-30", ["nasdaq"], priority=5)
        # priority=3 (medium) entry third
        mem_queue.enqueue("GOOG", "2026-04-30", ["nasdaq"], priority=3)

        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 3
        # priority DESC: MSFT(5), GOOG(3), AAPL(0)
        assert entries[0].symbol == "MSFT"
        assert entries[1].symbol == "GOOG"
        assert entries[2].symbol == "AAPL"

    def test_正常系_limitで件数を制限できる(self, mem_queue: CollectionQueue) -> None:
        for i in range(10):
            mem_queue.enqueue(f"SYM{i:02d}", "2026-04-30", ["nasdaq"])
        entries = mem_queue.get_pending("nasdaq", limit=5)
        assert len(entries) == 5

    def test_正常系_他ソースのエントリを返さない(self, mem_queue: CollectionQueue) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq", "yfinance"])
        nasdaq_entries = mem_queue.get_pending("nasdaq")
        yf_entries = mem_queue.get_pending("yfinance")
        assert all(e.source == "nasdaq" for e in nasdaq_entries)
        assert all(e.source == "yfinance" for e in yf_entries)

    def test_正常系_completedエントリを返さない(self, mem_queue: CollectionQueue) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.mark_completed("AAPL", "2026-04-30", "nasdaq")
        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 0

    def test_エッジケース_エントリがない場合は空リストを返す(
        self, mem_queue: CollectionQueue
    ) -> None:
        entries = mem_queue.get_pending("nasdaq")
        assert entries == []

    def test_正常系_QueueEntryオブジェクトのリストを返す(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        entries = mem_queue.get_pending("nasdaq")
        assert isinstance(entries[0], QueueEntry)


# ---------------------------------------------------------------------------
# mark_completed tests
# ---------------------------------------------------------------------------


class TestMarkCompleted:
    def test_正常系_pendingからcompletedに変更される(self, mem_queue: CollectionQueue) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.mark_completed("AAPL", "2026-04-30", "nasdaq")
        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 0

    def test_正常系_completed後はget_pendingに出てこない(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.enqueue("MSFT", "2026-04-30", ["nasdaq"])
        mem_queue.mark_completed("AAPL", "2026-04-30", "nasdaq")
        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 1
        assert entries[0].symbol == "MSFT"


# ---------------------------------------------------------------------------
# mark_failed tests
# ---------------------------------------------------------------------------


class TestMarkFailed:
    def test_正常系_failedステータスに変更される(self, mem_queue: CollectionQueue) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "Connection timeout")
        stats = mem_queue.get_stats()
        assert stats["nasdaq"]["failed"] == 1

    def test_正常系_failed後はget_pendingに出てこない(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "error")
        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 0


# ---------------------------------------------------------------------------
# mark_skipped tests
# ---------------------------------------------------------------------------


class TestMarkSkipped:
    def test_正常系_skippedステータスに変更される(self, mem_queue: CollectionQueue) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.mark_skipped("AAPL", "2026-04-30", "nasdaq")
        stats = mem_queue.get_stats()
        assert stats["nasdaq"]["skipped"] == 1

    def test_正常系_skipped後はget_pendingに出てこない(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.mark_skipped("AAPL", "2026-04-30", "nasdaq")
        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 0


# ---------------------------------------------------------------------------
# reset_failed tests
# ---------------------------------------------------------------------------


class TestResetFailed:
    def test_正常系_max_attempts未満のfailedエントリをpendingに戻す(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
        # attempts=1 < max_attempts=3 なのでリセットされる
        reset_count = mem_queue.reset_failed(max_attempts=3)
        assert reset_count == 1
        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 1

    def test_正常系_max_attempts以上のfailedエントリはリセットされない(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        # 3回失敗させる
        for _ in range(3):
            mem_queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
            mem_queue.reset_failed(max_attempts=3)
        # 3回目のfail後にリセット試行 (attempts=3 >= max_attempts=3)
        mem_queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
        reset_count = mem_queue.reset_failed(max_attempts=3)
        assert reset_count == 0

    def test_正常系_failedがない場合は0を返す(self, mem_queue: CollectionQueue) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        reset_count = mem_queue.reset_failed(max_attempts=3)
        assert reset_count == 0

    def test_正常系_リセット後はget_pendingに出てくる(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "error")
        mem_queue.reset_failed(max_attempts=3)
        entries = mem_queue.get_pending("nasdaq")
        assert len(entries) == 1


# ---------------------------------------------------------------------------
# get_stats tests
# ---------------------------------------------------------------------------


class TestGetStats:
    def test_正常系_source_x_status形式のdictを返す(
        self, mem_queue: CollectionQueue
    ) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq", "yfinance"])
        stats = mem_queue.get_stats()
        assert "nasdaq" in stats
        assert "yfinance" in stats
        assert stats["nasdaq"]["pending"] == 1
        assert stats["yfinance"]["pending"] == 1

    def test_正常系_混在した状態のカウントが正しい(self, mem_queue: CollectionQueue) -> None:
        mem_queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        mem_queue.enqueue("MSFT", "2026-04-30", ["nasdaq"])
        mem_queue.enqueue("GOOG", "2026-04-30", ["nasdaq"])
        mem_queue.mark_completed("AAPL", "2026-04-30", "nasdaq")
        mem_queue.mark_failed("MSFT", "2026-04-30", "nasdaq", "error")
        stats = mem_queue.get_stats()
        assert stats["nasdaq"]["pending"] == 1
        assert stats["nasdaq"]["completed"] == 1
        assert stats["nasdaq"]["failed"] == 1

    def test_エッジケース_エントリがない場合は空dictを返す(
        self, mem_queue: CollectionQueue
    ) -> None:
        stats = mem_queue.get_stats()
        assert stats == {}

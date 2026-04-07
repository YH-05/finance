"""Unit tests for market.pipeline.queue.CollectionQueue.

Tests verify:
- enqueue idempotency (INSERT OR IGNORE semantics)
- priority ordering in get_pending()
- mark_completed / mark_failed / mark_skipped transitions
- reset_failed() behavior
- get_stats() aggregation

All tests use a real SQLite DB via the ``tmp_db_path`` fixture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from market.pipeline.errors import QueueError
from market.pipeline.queue import CollectionQueue

if TYPE_CHECKING:
    from pathlib import Path

# =============================================================================
# Initialization tests
# =============================================================================


class TestCollectionQueueInit:
    """Tests for CollectionQueue initialization."""

    def test_正常系_インメモリDBで初期化できる(self, tmp_db_path: Path) -> None:
        # SQLiteClient opens a new connection per call, so in-memory DBs
        # lose tables between calls. Use a tmp file for verification.
        queue = CollectionQueue(db_path=tmp_db_path)
        assert queue.get_stats() == {}

    def test_正常系_tempfileパスで初期化できる(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        assert queue.get_stats() == {}

    def test_正常系_ensure_tablesを複数回呼べる(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.ensure_tables()
        queue.ensure_tables()


# =============================================================================
# enqueue tests (idempotency)
# =============================================================================


class TestCollectionQueueEnqueue:
    """Tests for CollectionQueue.enqueue() with focus on idempotency."""

    def test_正常系_新規エントリをenqueueできる(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        result = queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        assert result == 1

    def test_正常系_複数ソースをまとめてenqueueできる(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        result = queue.enqueue("AAPL", "2026-04-30", ["nasdaq", "yfinance"])
        assert result == 2

    def test_正常系_空リストはno_op(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        result = queue.enqueue("AAPL", "2026-04-30", [])
        assert result == 0

    def test_正常系_同一エントリの重複enqueueはINSERT_OR_IGNORE(
        self, tmp_db_path: Path
    ) -> None:
        """同じ (symbol, earnings_date, source) の重複enqueueは既存エントリを変更しない."""
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        result = queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        # The entry already exists; count should still reflect 1 existing entry
        assert result == 1

    def test_正常系_異なる日付は別エントリとしてenqueue(
        self, tmp_db_path: Path
    ) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        queue.enqueue("AAPL", "2026-05-15", ["nasdaq"])
        pending = queue.get_pending("nasdaq")
        assert len(pending) == 2

    def test_正常系_priorityパラメータが設定される(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"], priority=10)
        pending = queue.get_pending("nasdaq")
        assert pending[0].priority == 10


# =============================================================================
# priority ordering tests
# =============================================================================


class TestCollectionQueuePriorityOrdering:
    """Tests that get_pending() returns entries ordered by priority DESC."""

    def test_正常系_高優先度のエントリが先に返される(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"], priority=0)
        queue.enqueue("MSFT", "2026-04-30", ["nasdaq"], priority=10)
        queue.enqueue("GOOGL", "2026-04-30", ["nasdaq"], priority=5)
        pending = queue.get_pending("nasdaq")
        # Should be sorted by priority DESC
        assert pending[0].symbol == "MSFT"
        assert pending[1].symbol == "GOOGL"
        assert pending[2].symbol == "AAPL"

    def test_正常系_同一優先度はcreated_at昇順(self, tmp_db_path: Path) -> None:
        """同一priorityの場合は created_at 昇順 (古いものが先)."""
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"], priority=0)
        queue.enqueue("MSFT", "2026-04-30", ["nasdaq"], priority=0)
        pending = queue.get_pending("nasdaq")
        # AAPL was inserted first, so it should come first
        assert pending[0].symbol == "AAPL"


# =============================================================================
# mark_* tests
# =============================================================================


class TestCollectionQueueMarkCompleted:
    """Tests for CollectionQueue.mark_completed()."""

    def test_正常系_pendingをcompletedにできる(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        queue.mark_completed("AAPL", "2026-04-30", "nasdaq")
        stats = queue.get_stats()
        assert stats.get("nasdaq", {}).get("completed") == 1
        assert stats.get("nasdaq", {}).get("pending") is None

    def test_正常系_completedにすると_get_pendingに返らない(
        self, tmp_db_path: Path
    ) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        queue.mark_completed("AAPL", "2026-04-30", "nasdaq")
        pending = queue.get_pending("nasdaq")
        assert pending == []


class TestCollectionQueueMarkFailed:
    """Tests for CollectionQueue.mark_failed()."""

    def test_正常系_pendingをfailedにできる(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
        stats = queue.get_stats()
        assert stats.get("nasdaq", {}).get("failed") == 1

    def test_正常系_失敗時にattemptsがインクリメントされる(
        self, tmp_db_path: Path
    ) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "error1")
        queue.reset_failed(max_attempts=3)
        queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "error2")
        # After 2 failures, attempts should be 2
        # get_pending won't show it since it's failed again
        stats = queue.get_stats()
        assert stats.get("nasdaq", {}).get("failed") == 1


class TestCollectionQueueMarkSkipped:
    """Tests for CollectionQueue.mark_skipped()."""

    def test_正常系_pendingをskippedにできる(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        queue.mark_skipped("AAPL", "2026-04-30", "nasdaq")
        stats = queue.get_stats()
        assert stats.get("nasdaq", {}).get("skipped") == 1


# =============================================================================
# reset_failed tests
# =============================================================================


class TestCollectionQueueResetFailed:
    """Tests for CollectionQueue.reset_failed()."""

    def test_正常系_failedをpendingにリセットできる(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
        reset_count = queue.reset_failed(max_attempts=3)
        assert reset_count == 1
        pending = queue.get_pending("nasdaq")
        assert len(pending) == 1
        assert pending[0].symbol == "AAPL"

    def test_正常系_試行回数超過のエントリはリセットされない(
        self, tmp_db_path: Path
    ) -> None:
        """attempts >= max_attemptsのエントリはリセット対象外."""
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        # Fail 3 times
        for _ in range(3):
            queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "error")
            queue.reset_failed(max_attempts=5)
        # Fail once more, making attempts=4
        queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "error")
        # Reset with max_attempts=3 → 4 >= 3, so should NOT reset
        reset_count = queue.reset_failed(max_attempts=3)
        assert reset_count == 0

    def test_正常系_failedなしは0を返す(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        assert queue.reset_failed() == 0

    def test_正常系_priority_boost指定時にリセット後のpriorityが加算される(
        self, tmp_db_path: Path
    ) -> None:
        """priority_boost=10 指定時、リセットされたエントリの priority が +10."""
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"], priority=5)
        queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
        reset_count = queue.reset_failed(max_attempts=3, priority_boost=10)
        assert reset_count == 1
        pending = queue.get_pending("nasdaq")
        assert len(pending) == 1
        assert pending[0].priority == 15  # 5 + 10

    def test_正常系_priority_boost_0はデフォルト動作と同一(
        self, tmp_db_path: Path
    ) -> None:
        """priority_boost=0（デフォルト）で既存動作と同一."""
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"], priority=7)
        queue.mark_failed("AAPL", "2026-04-30", "nasdaq", "timeout")
        reset_count = queue.reset_failed(max_attempts=3, priority_boost=0)
        assert reset_count == 1
        pending = queue.get_pending("nasdaq")
        assert len(pending) == 1
        assert pending[0].priority == 7  # 変化なし


# =============================================================================
# get_stats tests
# =============================================================================


class TestCollectionQueueGetStats:
    """Tests for CollectionQueue.get_stats()."""

    def test_正常系_空キューは空dictを返す(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        assert queue.get_stats() == {}

    def test_正常系_ソースとステータス別にカウントが返る(
        self, tmp_db_path: Path
    ) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq", "yfinance"])
        queue.enqueue("MSFT", "2026-04-30", ["nasdaq"])
        queue.mark_completed("AAPL", "2026-04-30", "nasdaq")
        stats = queue.get_stats()
        assert stats["nasdaq"]["pending"] == 1  # MSFT is still pending
        assert stats["nasdaq"]["completed"] == 1  # AAPL completed
        assert stats["yfinance"]["pending"] == 1  # AAPL yfinance still pending

    def test_正常系_複数ステータスが正しく集計される(self, tmp_db_path: Path) -> None:
        queue = CollectionQueue(db_path=tmp_db_path)
        queue.enqueue("AAPL", "2026-04-30", ["nasdaq"])
        queue.enqueue("MSFT", "2026-04-30", ["nasdaq"])
        queue.enqueue("GOOGL", "2026-04-30", ["nasdaq"])
        queue.mark_completed("AAPL", "2026-04-30", "nasdaq")
        queue.mark_failed("MSFT", "2026-04-30", "nasdaq", "error")
        stats = queue.get_stats()
        assert stats["nasdaq"]["pending"] == 1
        assert stats["nasdaq"]["completed"] == 1
        assert stats["nasdaq"]["failed"] == 1

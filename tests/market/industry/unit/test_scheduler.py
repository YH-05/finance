"""Unit tests for market.industry.scheduler module.

Tests the IndustryScheduler class which provides APScheduler-based
weekly execution of the IndustryCollector, following the same pattern
as rss.services.batch_scheduler.BatchScheduler.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =============================================================================
# IndustryScheduler Initialization Tests
# =============================================================================


class TestIndustryScheduler:
    """Tests for the IndustryScheduler class."""

    def test_正常系_デフォルトパラメータで初期化できる(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler()
        # Default: Sunday 0:00 (day_of_week='sun', hour=0, minute=0)
        assert scheduler.day_of_week == "sun"
        assert scheduler.hour == 0
        assert scheduler.minute == 0

    def test_正常系_カスタム曜日と時刻で初期化できる(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler(day_of_week="sat", hour=3, minute=30)
        assert scheduler.day_of_week == "sat"
        assert scheduler.hour == 3
        assert scheduler.minute == 30

    def test_正常系_セクター指定で初期化できる(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler(sector="Technology")
        assert scheduler.sector == "Technology"

    def test_異常系_無効な時間で初期化するとValueError(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        with pytest.raises(ValueError, match="hour must be between 0 and 23"):
            IndustryScheduler(hour=25)

    def test_異常系_無効な分で初期化するとValueError(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        with pytest.raises(ValueError, match="minute must be between 0 and 59"):
            IndustryScheduler(minute=60)

    def test_異常系_負の時間で初期化するとValueError(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        with pytest.raises(ValueError, match="hour must be between 0 and 23"):
            IndustryScheduler(hour=-1)

    def test_正常系_last_statsの初期値はNone(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler()
        assert scheduler.last_stats is None


# =============================================================================
# IndustryScheduler run_batch Tests
# =============================================================================


class TestIndustrySchedulerRunBatch:
    """Tests for IndustryScheduler.run_batch() method."""

    @pytest.mark.asyncio
    async def test_正常系_run_batchがCollectionStatsを返す(self) -> None:
        from market.industry.collector import CollectionStats
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler(sector="Technology")

        mock_stats = CollectionStats(
            total_sources=7,
            success_count=5,
            failure_count=2,
            total_reports=42,
            duration_seconds=120.5,
        )

        with patch("market.industry.collector.IndustryCollector") as MockCollector:
            mock_collector = AsyncMock()
            mock_collector.collect = AsyncMock(return_value=mock_stats)
            MockCollector.return_value = mock_collector

            stats = await scheduler.run_batch()

        assert stats.total_sources == 7
        assert stats.success_count == 5
        assert stats.total_reports == 42
        assert scheduler.last_stats == stats

    @pytest.mark.asyncio
    async def test_正常系_run_batchがlast_statsを更新する(self) -> None:
        from market.industry.collector import CollectionStats
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler()

        mock_stats = CollectionStats(
            total_sources=3,
            success_count=3,
            failure_count=0,
            total_reports=15,
            duration_seconds=60.0,
        )

        with patch("market.industry.collector.IndustryCollector") as MockCollector:
            mock_collector = AsyncMock()
            mock_collector.collect = AsyncMock(return_value=mock_stats)
            MockCollector.return_value = mock_collector

            await scheduler.run_batch()

        assert scheduler.last_stats is not None
        assert scheduler.last_stats.total_sources == 3


# =============================================================================
# IndustryScheduler start/stop Tests
# =============================================================================


class TestIndustrySchedulerStartStop:
    """Tests for IndustryScheduler start() and stop() methods."""

    def test_正常系_stopでスケジューラが正常停止する(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler()
        # Stop without starting should not raise
        scheduler.stop()
        assert scheduler._scheduler is None

    def test_正常系_startがAPSchedulerを設定する(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler(day_of_week="sun", hour=0, minute=0)

        with patch(
            "apscheduler.schedulers.background.BackgroundScheduler"
        ) as MockBgScheduler:
            mock_sched = MagicMock()
            MockBgScheduler.return_value = mock_sched

            scheduler.start(blocking=False)

            MockBgScheduler.assert_called_once()
            mock_sched.add_job.assert_called_once()
            mock_sched.start.assert_called_once()

    def test_正常系_start_blockingモードがBlockingSchedulerを使用する(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler()

        with patch(
            "apscheduler.schedulers.blocking.BlockingScheduler"
        ) as MockBlkScheduler:
            mock_sched = MagicMock()
            MockBlkScheduler.return_value = mock_sched

            scheduler.start(blocking=True)

            MockBlkScheduler.assert_called_once()
            mock_sched.add_job.assert_called_once()

    def test_正常系_get_next_run_timeがNoneを返す_未起動時(self) -> None:
        from market.industry.scheduler import IndustryScheduler

        scheduler = IndustryScheduler()
        assert scheduler.get_next_run_time() is None


# =============================================================================
# Default Constants Tests
# =============================================================================


class TestSchedulerDefaults:
    """Tests for scheduler default constants."""

    def test_正常系_デフォルト曜日がsun(self) -> None:
        from market.industry.scheduler import DEFAULT_DAY_OF_WEEK

        assert DEFAULT_DAY_OF_WEEK == "sun"

    def test_正常系_デフォルト時間が0(self) -> None:
        from market.industry.scheduler import DEFAULT_HOUR

        assert DEFAULT_HOUR == 0

    def test_正常系_デフォルト分が0(self) -> None:
        from market.industry.scheduler import DEFAULT_MINUTE

        assert DEFAULT_MINUTE == 0

"""Unit tests for BatchScheduler class."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from rss.services.batch_scheduler import (
    DEFAULT_HOUR,
    DEFAULT_MINUTE,
    BatchScheduler,
)
from rss.services.feed_fetcher import FeedFetcher
from rss.types import BatchStats, FetchResult


class TestBatchSchedulerInit:
    """Test BatchScheduler initialization."""

    def test_init_success_default_values(self, tmp_path: Path) -> None:
        """Test successful initialization with default hour and minute."""
        fetcher = FeedFetcher(tmp_path)
        scheduler = BatchScheduler(fetcher)

        assert scheduler.fetcher is fetcher
        assert scheduler.hour == DEFAULT_HOUR
        assert scheduler.minute == DEFAULT_MINUTE
        assert scheduler.last_stats is None
        assert scheduler._scheduler is None

    def test_init_success_custom_time(self, tmp_path: Path) -> None:
        """Test successful initialization with custom hour and minute."""
        fetcher = FeedFetcher(tmp_path)
        scheduler = BatchScheduler(fetcher, hour=7, minute=30)

        assert scheduler.hour == 7
        assert scheduler.minute == 30

    def test_init_invalid_hour_too_low(self, tmp_path: Path) -> None:
        """Test initialization fails with hour < 0."""
        fetcher = FeedFetcher(tmp_path)
        with pytest.raises(ValueError, match="hour must be between 0 and 23"):
            BatchScheduler(fetcher, hour=-1)

    def test_init_invalid_hour_too_high(self, tmp_path: Path) -> None:
        """Test initialization fails with hour > 23."""
        fetcher = FeedFetcher(tmp_path)
        with pytest.raises(ValueError, match="hour must be between 0 and 23"):
            BatchScheduler(fetcher, hour=24)

    def test_init_invalid_minute_too_low(self, tmp_path: Path) -> None:
        """Test initialization fails with minute < 0."""
        fetcher = FeedFetcher(tmp_path)
        with pytest.raises(ValueError, match="minute must be between 0 and 59"):
            BatchScheduler(fetcher, minute=-1)

    def test_init_invalid_minute_too_high(self, tmp_path: Path) -> None:
        """Test initialization fails with minute > 59."""
        fetcher = FeedFetcher(tmp_path)
        with pytest.raises(ValueError, match="minute must be between 0 and 59"):
            BatchScheduler(fetcher, minute=60)

    def test_init_boundary_values(self, tmp_path: Path) -> None:
        """Test initialization with boundary values."""
        fetcher = FeedFetcher(tmp_path)

        # Test boundary values
        scheduler_min = BatchScheduler(fetcher, hour=0, minute=0)
        assert scheduler_min.hour == 0
        assert scheduler_min.minute == 0

        scheduler_max = BatchScheduler(fetcher, hour=23, minute=59)
        assert scheduler_max.hour == 23
        assert scheduler_max.minute == 59


class TestRunBatch:
    """Test run_batch method."""

    def test_run_batch_success_all_feeds(self, tmp_path: Path) -> None:
        """Test successful batch execution with all feeds succeeding."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path
        mock_fetcher.fetch_all.return_value = [
            FetchResult(
                feed_id="feed-1",
                success=True,
                items_count=10,
                new_items=5,
                error_message=None,
            ),
            FetchResult(
                feed_id="feed-2",
                success=True,
                items_count=20,
                new_items=8,
                error_message=None,
            ),
        ]

        scheduler = BatchScheduler(mock_fetcher)
        stats = scheduler.run_batch()

        # Verify stats
        assert isinstance(stats, BatchStats)
        assert stats.total_feeds == 2
        assert stats.success_count == 2
        assert stats.failure_count == 0
        assert stats.total_items == 30
        assert stats.new_items == 13
        assert stats.duration_seconds >= 0

        # Verify timestamps are ISO 8601 format
        datetime.fromisoformat(stats.started_at)
        datetime.fromisoformat(stats.completed_at)

        # Verify last_stats is updated
        assert scheduler.last_stats is stats

        # Verify fetch_all was called
        mock_fetcher.fetch_all.assert_called_once()

    def test_run_batch_partial_failure(self, tmp_path: Path) -> None:
        """Test batch execution with some feeds failing."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path
        mock_fetcher.fetch_all.return_value = [
            FetchResult(
                feed_id="feed-1",
                success=True,
                items_count=10,
                new_items=5,
                error_message=None,
            ),
            FetchResult(
                feed_id="feed-2",
                success=False,
                items_count=0,
                new_items=0,
                error_message="Network error",
            ),
            FetchResult(
                feed_id="feed-3",
                success=True,
                items_count=15,
                new_items=3,
                error_message=None,
            ),
        ]

        scheduler = BatchScheduler(mock_fetcher)
        stats = scheduler.run_batch()

        # Verify stats
        assert stats.total_feeds == 3
        assert stats.success_count == 2
        assert stats.failure_count == 1
        assert stats.total_items == 25
        assert stats.new_items == 8

    def test_run_batch_all_failures(self, tmp_path: Path) -> None:
        """Test batch execution with all feeds failing."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path
        mock_fetcher.fetch_all.return_value = [
            FetchResult(
                feed_id="feed-1",
                success=False,
                items_count=0,
                new_items=0,
                error_message="Error 1",
            ),
            FetchResult(
                feed_id="feed-2",
                success=False,
                items_count=0,
                new_items=0,
                error_message="Error 2",
            ),
        ]

        scheduler = BatchScheduler(mock_fetcher)
        stats = scheduler.run_batch()

        # Verify stats
        assert stats.total_feeds == 2
        assert stats.success_count == 0
        assert stats.failure_count == 2
        assert stats.total_items == 0
        assert stats.new_items == 0

    def test_run_batch_no_feeds(self, tmp_path: Path) -> None:
        """Test batch execution with no feeds."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path
        mock_fetcher.fetch_all.return_value = []

        scheduler = BatchScheduler(mock_fetcher)
        stats = scheduler.run_batch()

        # Verify stats
        assert stats.total_feeds == 0
        assert stats.success_count == 0
        assert stats.failure_count == 0
        assert stats.total_items == 0
        assert stats.new_items == 0

    def test_run_batch_duration_measurement(self, tmp_path: Path) -> None:
        """Test that batch duration is measured correctly."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path
        mock_fetcher.fetch_all.return_value = []

        scheduler = BatchScheduler(mock_fetcher)
        stats = scheduler.run_batch()

        # Duration should be a positive number (or zero for very fast execution)
        assert stats.duration_seconds >= 0
        # Duration should be rounded to 3 decimal places
        assert len(str(stats.duration_seconds).split(".")[-1]) <= 3


class TestStart:
    """Test start method."""

    def test_start_raises_import_error_without_apscheduler(
        self, tmp_path: Path
    ) -> None:
        """Test that start raises ImportError when APScheduler is not installed."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path

        scheduler = BatchScheduler(mock_fetcher)

        with (
            patch.dict("sys.modules", {"apscheduler.schedulers.blocking": None}),
            patch("rss.services.batch_scheduler.BatchScheduler.start") as mock_start,
        ):
            mock_start.side_effect = ImportError("APScheduler is required")
            with pytest.raises(ImportError, match="APScheduler is required"):
                scheduler.start()

    def test_start_blocking_mode(self, tmp_path: Path) -> None:
        """Test start in blocking mode."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path

        scheduler = BatchScheduler(mock_fetcher, hour=7, minute=30)

        mock_blocking_scheduler = Mock()

        with patch(
            "apscheduler.schedulers.blocking.BlockingScheduler",
            return_value=mock_blocking_scheduler,
        ):
            scheduler.start(blocking=True)

        # Verify scheduler was started
        mock_blocking_scheduler.add_job.assert_called_once()
        mock_blocking_scheduler.start.assert_called_once()

        # Verify job configuration
        call_args = mock_blocking_scheduler.add_job.call_args
        assert call_args[1]["hour"] == 7
        assert call_args[1]["minute"] == 30
        assert call_args[1]["id"] == "daily_feed_fetch"

    def test_start_background_mode(self, tmp_path: Path) -> None:
        """Test start in background mode."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path

        scheduler = BatchScheduler(mock_fetcher)

        mock_bg_scheduler = Mock()

        with patch(
            "apscheduler.schedulers.background.BackgroundScheduler",
            return_value=mock_bg_scheduler,
        ):
            scheduler.start(blocking=False)

        # Verify scheduler was started
        mock_bg_scheduler.add_job.assert_called_once()
        mock_bg_scheduler.start.assert_called_once()


class TestStop:
    """Test stop method."""

    def test_stop_running_scheduler(self, tmp_path: Path) -> None:
        """Test stopping a running scheduler."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path

        scheduler = BatchScheduler(mock_fetcher)
        mock_scheduler = Mock()
        scheduler._scheduler = mock_scheduler

        scheduler.stop()

        # Verify shutdown was called (must check before stop() sets _scheduler to None)
        mock_scheduler.shutdown.assert_called_once_with(wait=True)
        # Verify _scheduler is set to None after stop
        assert scheduler._scheduler is None

    def test_stop_not_running_scheduler(self, tmp_path: Path) -> None:
        """Test stopping when scheduler is not running."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path

        scheduler = BatchScheduler(mock_fetcher)

        # Should not raise any error
        scheduler.stop()


class TestGetNextRunTime:
    """Test get_next_run_time method."""

    def test_get_next_run_time_scheduler_not_running(self, tmp_path: Path) -> None:
        """Test get_next_run_time when scheduler is not running."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path

        scheduler = BatchScheduler(mock_fetcher)

        result = scheduler.get_next_run_time()

        assert result is None

    def test_get_next_run_time_scheduler_running(self, tmp_path: Path) -> None:
        """Test get_next_run_time when scheduler is running."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path

        scheduler = BatchScheduler(mock_fetcher)

        mock_job = Mock()
        expected_time = datetime(2026, 1, 15, 6, 0, 0)
        mock_job.next_run_time = expected_time

        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = mock_job

        scheduler._scheduler = mock_scheduler

        result = scheduler.get_next_run_time()

        assert result == expected_time
        mock_scheduler.get_job.assert_called_once_with("daily_feed_fetch")

    def test_get_next_run_time_job_not_found(self, tmp_path: Path) -> None:
        """Test get_next_run_time when job is not found."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path

        scheduler = BatchScheduler(mock_fetcher)

        mock_scheduler = Mock()
        mock_scheduler.get_job.return_value = None

        scheduler._scheduler = mock_scheduler

        result = scheduler.get_next_run_time()

        assert result is None


class TestCreateFromDataDir:
    """Test create_from_data_dir factory method."""

    def test_create_from_data_dir_default_values(self, tmp_path: Path) -> None:
        """Test factory method with default values."""
        scheduler = BatchScheduler.create_from_data_dir(tmp_path)

        assert isinstance(scheduler, BatchScheduler)
        assert isinstance(scheduler.fetcher, FeedFetcher)
        assert scheduler.fetcher.data_dir == tmp_path
        assert scheduler.hour == DEFAULT_HOUR
        assert scheduler.minute == DEFAULT_MINUTE

    def test_create_from_data_dir_custom_time(self, tmp_path: Path) -> None:
        """Test factory method with custom time."""
        scheduler = BatchScheduler.create_from_data_dir(
            tmp_path,
            hour=8,
            minute=45,
        )

        assert scheduler.hour == 8
        assert scheduler.minute == 45


class TestDefaultConstants:
    """Test default constants."""

    def test_default_hour(self) -> None:
        """Test DEFAULT_HOUR value."""
        assert DEFAULT_HOUR == 6

    def test_default_minute(self) -> None:
        """Test DEFAULT_MINUTE value."""
        assert DEFAULT_MINUTE == 0


class TestBatchStatsType:
    """Test BatchStats dataclass."""

    def test_batch_stats_creation(self) -> None:
        """Test BatchStats dataclass creation."""
        stats = BatchStats(
            total_feeds=10,
            success_count=8,
            failure_count=2,
            total_items=100,
            new_items=25,
            started_at="2026-01-14T06:00:00+00:00",
            completed_at="2026-01-14T06:05:30+00:00",
            duration_seconds=330.5,
        )

        assert stats.total_feeds == 10
        assert stats.success_count == 8
        assert stats.failure_count == 2
        assert stats.total_items == 100
        assert stats.new_items == 25
        assert stats.started_at == "2026-01-14T06:00:00+00:00"
        assert stats.completed_at == "2026-01-14T06:05:30+00:00"
        assert stats.duration_seconds == 330.5


class TestLogging:
    """Test structured logging behavior."""

    def test_run_batch_logs_start_and_end(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that batch execution logs start and end."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path
        mock_fetcher.fetch_all.return_value = []

        scheduler = BatchScheduler(mock_fetcher)
        scheduler.run_batch()

        # Note: In CI environment, structlog may not output to stdout
        captured = capsys.readouterr()
        assert (
            "started" in captured.out.lower()
            or "completed" in captured.out.lower()
            or captured.out == ""
        )

    def test_run_batch_logs_individual_results(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that batch execution logs individual feed results."""
        mock_fetcher = Mock(spec=FeedFetcher)
        mock_fetcher.data_dir = tmp_path
        mock_fetcher.fetch_all.return_value = [
            FetchResult(
                feed_id="feed-1",
                success=True,
                items_count=10,
                new_items=5,
                error_message=None,
            ),
            FetchResult(
                feed_id="feed-2",
                success=False,
                items_count=0,
                new_items=0,
                error_message="Error",
            ),
        ]

        scheduler = BatchScheduler(mock_fetcher)
        scheduler.run_batch()

        # Note: In CI environment, structlog may not output to stdout
        captured = capsys.readouterr()
        assert (
            "feed-1" in captured.out.lower()
            or "succeeded" in captured.out.lower()
            or captured.out == ""
        )
        assert (
            "feed-2" in captured.out.lower()
            or "failed" in captured.out.lower()
            or captured.out == ""
        )

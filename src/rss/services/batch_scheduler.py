"""Batch scheduler service for daily feed fetching.

This module provides the BatchScheduler class that uses APScheduler
to execute scheduled feed fetching operations.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ..types import BatchStats, FetchResult

if TYPE_CHECKING:
    from pathlib import Path

    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.blocking import BlockingScheduler

    from .feed_fetcher import FeedFetcher


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="batch_scheduler")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()

DEFAULT_HOUR = 6
DEFAULT_MINUTE = 0


class BatchScheduler:
    """Scheduler for daily batch feed fetching.

    This class provides scheduled batch execution of feed fetching
    using APScheduler with cron-based scheduling.

    Parameters
    ----------
    fetcher : FeedFetcher
        Feed fetcher instance for executing fetches
    hour : int, default=6
        Hour to run daily batch (0-23)
    minute : int, default=0
        Minute to run daily batch (0-59)

    Attributes
    ----------
    fetcher : FeedFetcher
        Feed fetcher instance
    hour : int
        Scheduled hour
    minute : int
        Scheduled minute
    last_stats : BatchStats | None
        Statistics from the last batch execution

    Examples
    --------
    >>> from pathlib import Path
    >>> from rss.services.feed_fetcher import FeedFetcher
    >>> fetcher = FeedFetcher(Path("data/raw/rss"))
    >>> scheduler = BatchScheduler(fetcher, hour=6, minute=0)
    >>> scheduler.start()  # Runs daily at 6:00 AM
    """

    def __init__(
        self,
        fetcher: FeedFetcher,
        hour: int = DEFAULT_HOUR,
        minute: int = DEFAULT_MINUTE,
    ) -> None:
        """Initialize BatchScheduler.

        Parameters
        ----------
        fetcher : FeedFetcher
            Feed fetcher instance for executing fetches
        hour : int, default=6
            Hour to run daily batch (0-23)
        minute : int, default=0
            Minute to run daily batch (0-59)

        Raises
        ------
        ValueError
            If hour or minute is out of valid range
        """
        if not (0 <= hour <= 23):
            logger.error(
                "Invalid hour value",
                hour=hour,
                valid_range="0-23",
            )
            raise ValueError(f"hour must be between 0 and 23, got {hour}")

        if not (0 <= minute <= 59):
            logger.error(
                "Invalid minute value",
                minute=minute,
                valid_range="0-59",
            )
            raise ValueError(f"minute must be between 0 and 59, got {minute}")

        self.fetcher = fetcher
        self.hour = hour
        self.minute = minute
        self.last_stats: BatchStats | None = None
        self._scheduler: BackgroundScheduler | BlockingScheduler | None = None

        logger.debug(
            "BatchScheduler initialized",
            scheduled_time=f"{hour:02d}:{minute:02d}",
            data_dir=str(fetcher.data_dir),
        )

    def run_batch(self) -> BatchStats:
        """Execute batch fetch for all enabled feeds.

        This method fetches all enabled feeds and collects statistics.
        Errors in individual feeds do not stop the batch processing.

        Returns
        -------
        BatchStats
            Statistics from the batch execution including success/failure
            counts and total items fetched

        Examples
        --------
        >>> scheduler = BatchScheduler(fetcher)
        >>> stats = scheduler.run_batch()
        >>> print(f"Success: {stats.success_count}/{stats.total_feeds}")
        """
        started_at = datetime.now(UTC)
        start_time = time.perf_counter()

        logger.info(
            "Batch execution started",
            scheduled_time=f"{self.hour:02d}:{self.minute:02d}",
            started_at=started_at.isoformat(),
        )

        # Fetch all feeds
        results: list[FetchResult] = self.fetcher.fetch_all()

        # Calculate statistics
        end_time = time.perf_counter()
        completed_at = datetime.now(UTC)
        duration_seconds = end_time - start_time

        success_count = sum(1 for r in results if r.success)
        failure_count = len(results) - success_count
        total_items = sum(r.items_count for r in results)
        new_items = sum(r.new_items for r in results)

        # Log individual results
        for result in results:
            if result.success:
                logger.info(
                    "Feed fetch succeeded",
                    feed_id=result.feed_id,
                    items_count=result.items_count,
                    new_items=result.new_items,
                )
            else:
                logger.error(
                    "Feed fetch failed",
                    feed_id=result.feed_id,
                    error_message=result.error_message,
                )

        # Create statistics
        stats = BatchStats(
            total_feeds=len(results),
            success_count=success_count,
            failure_count=failure_count,
            total_items=total_items,
            new_items=new_items,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration_seconds=round(duration_seconds, 3),
        )

        self.last_stats = stats

        logger.info(
            "Batch execution completed",
            total_feeds=stats.total_feeds,
            success_count=stats.success_count,
            failure_count=stats.failure_count,
            total_items=stats.total_items,
            new_items=stats.new_items,
            duration_seconds=stats.duration_seconds,
        )

        return stats

    def start(self, *, blocking: bool = True) -> None:
        """Start the scheduler.

        Parameters
        ----------
        blocking : bool, default=True
            If True, uses BlockingScheduler (blocks the main thread).
            If False, uses BackgroundScheduler (runs in background thread).

        Raises
        ------
        ImportError
            If APScheduler is not installed

        Examples
        --------
        >>> scheduler = BatchScheduler(fetcher, hour=6)
        >>> scheduler.start(blocking=True)  # Blocks until stopped

        >>> # Non-blocking mode
        >>> scheduler.start(blocking=False)
        >>> # ... do other work ...
        >>> scheduler.stop()
        """
        try:
            if blocking:
                from apscheduler.schedulers.blocking import BlockingScheduler

                self._scheduler = BlockingScheduler()
            else:
                from apscheduler.schedulers.background import BackgroundScheduler

                self._scheduler = BackgroundScheduler()
        except ImportError as e:
            logger.error(
                "APScheduler not installed",
                error=str(e),
                install_hint="Install with: uv add apscheduler",
            )
            raise ImportError(
                "APScheduler is required for scheduling. "
                "Install with: uv add 'finance[scheduler]'"
            ) from e

        self._scheduler.add_job(
            self.run_batch,
            "cron",
            hour=self.hour,
            minute=self.minute,
            id="daily_feed_fetch",
            name="Daily Feed Fetch",
        )

        logger.info(
            "Scheduler started",
            mode="blocking" if blocking else "background",
            scheduled_time=f"{self.hour:02d}:{self.minute:02d}",
        )

        self._scheduler.start()

    def stop(self) -> None:
        """Stop the scheduler.

        This method gracefully shuts down the scheduler if it's running.
        """
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")
            self._scheduler = None

    def get_next_run_time(self) -> datetime | None:
        """Get the next scheduled run time.

        Returns
        -------
        datetime | None
            Next scheduled run time, or None if scheduler is not running

        Examples
        --------
        >>> scheduler.start(blocking=False)
        >>> next_run = scheduler.get_next_run_time()
        >>> print(f"Next run: {next_run}")
        """
        if self._scheduler is None:
            return None

        job = self._scheduler.get_job("daily_feed_fetch")
        if job is None:
            return None

        return job.next_run_time

    @classmethod
    def create_from_data_dir(
        cls,
        data_dir: Path,
        *,
        hour: int = DEFAULT_HOUR,
        minute: int = DEFAULT_MINUTE,
    ) -> BatchScheduler:
        """Create a BatchScheduler from a data directory.

        This is a convenience factory method that creates both the
        FeedFetcher and BatchScheduler instances.

        Parameters
        ----------
        data_dir : Path
            Root directory for RSS feed data
        hour : int, default=6
            Hour to run daily batch (0-23)
        minute : int, default=0
            Minute to run daily batch (0-59)

        Returns
        -------
        BatchScheduler
            Configured batch scheduler instance

        Examples
        --------
        >>> scheduler = BatchScheduler.create_from_data_dir(
        ...     Path("data/raw/rss"),
        ...     hour=7,
        ...     minute=30
        ... )
        >>> scheduler.start()
        """
        from .feed_fetcher import FeedFetcher

        fetcher = FeedFetcher(data_dir)
        return cls(fetcher, hour=hour, minute=minute)

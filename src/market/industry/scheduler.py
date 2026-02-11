"""APScheduler-based weekly scheduler for industry report collection.

This module provides the ``IndustryScheduler`` class that uses APScheduler
to execute the ``IndustryCollector`` on a weekly cron schedule (default:
Sunday midnight).

The implementation follows the same pattern as
``rss.services.batch_scheduler.BatchScheduler``.

Features
--------
- Weekly cron-based scheduling (configurable day/time)
- Blocking and background scheduler modes
- Execution statistics tracking (``last_stats``)
- Graceful start/stop lifecycle

Examples
--------
>>> from market.industry.scheduler import IndustryScheduler
>>> scheduler = IndustryScheduler(sector="Technology")
>>> scheduler.start(blocking=True)  # Blocks until stopped

>>> # Background mode
>>> scheduler = IndustryScheduler(day_of_week="sat", hour=3)
>>> scheduler.start(blocking=False)
>>> # ... do other work ...
>>> scheduler.stop()

See Also
--------
market.industry.collector : IndustryCollector (collection orchestrator).
rss.services.batch_scheduler : BatchScheduler (reference implementation).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from datetime import datetime

    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.schedulers.blocking import BlockingScheduler

    from market.industry.collector import CollectionStats

logger = get_logger(__name__)

# =============================================================================
# Default Configuration
# =============================================================================

DEFAULT_DAY_OF_WEEK: str = "sun"
"""Default day of week for scheduled execution (Sunday)."""

DEFAULT_HOUR: int = 0
"""Default hour for scheduled execution (midnight)."""

DEFAULT_MINUTE: int = 0
"""Default minute for scheduled execution."""


# =============================================================================
# IndustryScheduler
# =============================================================================


class IndustryScheduler:
    """Weekly scheduler for industry report collection using APScheduler.

    Wraps the ``IndustryCollector`` with APScheduler cron-based scheduling
    to enable automated weekly collection of industry reports.

    Parameters
    ----------
    sector : str
        Target sector for collection. Defaults to ``"all"``.
    source : str | None
        Specific source to collect from. Defaults to ``None`` (all sources).
    day_of_week : str
        Day of week for cron schedule (e.g. ``"sun"``, ``"mon"``).
        Defaults to ``"sun"``.
    hour : int
        Hour for cron schedule (0-23). Defaults to 0.
    minute : int
        Minute for cron schedule (0-59). Defaults to 0.

    Attributes
    ----------
    last_stats : CollectionStats | None
        Statistics from the last collection run.

    Raises
    ------
    ValueError
        If hour or minute is out of valid range.

    Examples
    --------
    >>> scheduler = IndustryScheduler(sector="Technology")
    >>> scheduler.start(blocking=True)  # Weekly on Sunday at midnight

    >>> scheduler = IndustryScheduler(day_of_week="sat", hour=3, minute=30)
    >>> scheduler.start(blocking=False)
    """

    def __init__(
        self,
        sector: str = "all",
        source: str | None = None,
        day_of_week: str = DEFAULT_DAY_OF_WEEK,
        hour: int = DEFAULT_HOUR,
        minute: int = DEFAULT_MINUTE,
    ) -> None:
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

        self.sector: str = sector
        self.source: str | None = source
        self.day_of_week: str = day_of_week
        self.hour: int = hour
        self.minute: int = minute
        self.last_stats: CollectionStats | None = None
        self._scheduler: BackgroundScheduler | BlockingScheduler | None = None

        logger.debug(
            "IndustryScheduler initialized",
            sector=sector,
            source=source,
            schedule=f"{day_of_week} {hour:02d}:{minute:02d}",
        )

    async def run_batch(self) -> CollectionStats:
        """Execute a single collection batch.

        Creates an ``IndustryCollector`` with the configured settings
        and runs the collection. Updates ``last_stats`` with the results.

        Returns
        -------
        CollectionStats
            Statistics from the collection run.
        """
        from market.industry.collector import IndustryCollector

        logger.info(
            "Batch execution started",
            sector=self.sector,
            source=self.source,
        )

        collector = IndustryCollector(
            sector=self.sector,
            source=self.source,
        )

        stats = await collector.collect()
        self.last_stats = stats

        logger.info(
            "Batch execution completed",
            total_sources=stats.total_sources,
            success_count=stats.success_count,
            failure_count=stats.failure_count,
            total_reports=stats.total_reports,
            duration_seconds=stats.duration_seconds,
        )

        return stats

    def _run_batch_sync(self) -> None:
        """Synchronous wrapper for ``run_batch()``.

        Used as the APScheduler job function since APScheduler does not
        natively support async functions.
        """
        try:
            asyncio.run(self.run_batch())
        except Exception as e:
            logger.error(
                "Batch execution failed",
                error=str(e),
                exc_info=True,
            )

    def start(self, *, blocking: bool = True) -> None:
        """Start the scheduler.

        Parameters
        ----------
        blocking : bool, default=True
            If ``True``, uses ``BlockingScheduler`` (blocks the main thread).
            If ``False``, uses ``BackgroundScheduler`` (runs in background).

        Raises
        ------
        ImportError
            If APScheduler is not installed.

        Examples
        --------
        >>> scheduler = IndustryScheduler()
        >>> scheduler.start(blocking=True)  # Blocks until stopped

        >>> scheduler.start(blocking=False)
        >>> # ... do other work ...
        >>> scheduler.stop()
        """
        if blocking:
            from apscheduler.schedulers.blocking import BlockingScheduler

            self._scheduler = BlockingScheduler()
        else:
            from apscheduler.schedulers.background import BackgroundScheduler

            self._scheduler = BackgroundScheduler()

        self._scheduler.add_job(
            self._run_batch_sync,
            "cron",
            day_of_week=self.day_of_week,
            hour=self.hour,
            minute=self.minute,
            id="weekly_industry_collection",
            name="Weekly Industry Report Collection",
        )

        logger.info(
            "Scheduler started",
            mode="blocking" if blocking else "background",
            schedule=f"{self.day_of_week} {self.hour:02d}:{self.minute:02d}",
            sector=self.sector,
        )

        self._scheduler.start()

    def stop(self) -> None:
        """Stop the scheduler.

        Gracefully shuts down the scheduler if it is running.
        Safe to call multiple times.
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
            Next scheduled run time, or ``None`` if scheduler is not running.
        """
        if self._scheduler is None:
            return None

        job = self._scheduler.get_job("weekly_industry_collection")
        if job is None:
            return None

        return job.next_run_time


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    "DEFAULT_DAY_OF_WEEK",
    "DEFAULT_HOUR",
    "DEFAULT_MINUTE",
    "IndustryScheduler",
]

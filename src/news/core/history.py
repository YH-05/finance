"""Collection history models and management for the news package.

This module provides data models for tracking collection run history,
including per-source statistics, sink results, and aggregated metrics.

Classes
-------
SourceStats
    Statistics for a single data source during collection.
SinkResult
    Result of a sink operation (file write, GitHub post, etc.).
CollectionRun
    Record of a single collection execution.
CollectionHistory
    Manager for collection run history with persistence.

Examples
--------
>>> stats = SourceStats(success_count=50, error_count=2, article_count=480)
>>> stats.success_rate
0.9615384615384616

>>> from datetime import datetime, timezone
>>> run = CollectionRun(
...     started_at=datetime.now(timezone.utc),
...     completed_at=datetime.now(timezone.utc),
...     sources={"rss": stats},
...     sinks={"file": SinkResult(success=True)},
... )
>>> run.total_article_count
480
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from ..utils.logging_config import get_logger

logger = get_logger(__name__, module="history")


class SourceStats(BaseModel):
    """Statistics for a single data source during collection.

    Tracks success/error counts and article counts for a source.

    Attributes
    ----------
    success_count : int
        Number of successful fetch operations (default: 0).
    error_count : int
        Number of failed fetch operations (default: 0).
    article_count : int
        Total number of articles fetched (default: 0).

    Examples
    --------
    >>> stats = SourceStats(success_count=50, error_count=2, article_count=480)
    >>> stats.total_count
    52
    >>> stats.success_rate
    0.9615384615384616
    """

    success_count: int = Field(default=0, description="Number of successful fetches")
    error_count: int = Field(default=0, description="Number of failed fetches")
    article_count: int = Field(default=0, description="Total articles fetched")

    @field_validator("success_count", mode="before")
    @classmethod
    def validate_success_count(cls, v: int) -> int:
        """Validate that success_count is non-negative."""
        if v < 0:
            raise ValueError("success_count must be non-negative")
        return v

    @field_validator("error_count", mode="before")
    @classmethod
    def validate_error_count(cls, v: int) -> int:
        """Validate that error_count is non-negative."""
        if v < 0:
            raise ValueError("error_count must be non-negative")
        return v

    @field_validator("article_count", mode="before")
    @classmethod
    def validate_article_count(cls, v: int) -> int:
        """Validate that article_count is non-negative."""
        if v < 0:
            raise ValueError("article_count must be non-negative")
        return v

    @property
    def total_count(self) -> int:
        """Return the total number of fetch operations.

        Returns
        -------
        int
            Sum of success_count and error_count.
        """
        return self.success_count + self.error_count

    @property
    def success_rate(self) -> float:
        """Return the success rate as a ratio.

        Returns
        -------
        float
            Success rate between 0.0 and 1.0.
            Returns 1.0 if total_count is 0.
        """
        if self.total_count == 0:
            return 1.0
        return self.success_count / self.total_count


class SinkResult(BaseModel):
    """Result of a sink operation.

    Represents the outcome of writing to a sink (file, GitHub, etc.).

    Attributes
    ----------
    success : bool
        Whether the sink operation succeeded.
    error_message : str | None
        Error message if the operation failed.
    metadata : dict[str, Any]
        Additional metadata (e.g., issues_created, file_path).

    Examples
    --------
    >>> result = SinkResult(success=True, metadata={"issues_created": 10})
    >>> result.success
    True
    >>> result.metadata["issues_created"]
    10
    """

    success: bool = Field(..., description="Whether the operation succeeded")
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class CollectionRun(BaseModel):
    """Record of a single collection execution.

    Tracks timing, source statistics, and sink results for one run.

    Attributes
    ----------
    run_id : str
        Unique identifier for the run (auto-generated UUID if not provided).
    started_at : datetime
        When the collection started.
    completed_at : datetime
        When the collection completed.
    sources : dict[str, SourceStats]
        Statistics per source name.
    sinks : dict[str, SinkResult]
        Results per sink name.

    Examples
    --------
    >>> from datetime import datetime, timezone, timedelta
    >>> started = datetime(2026, 1, 28, 12, 0, 0, tzinfo=timezone.utc)
    >>> completed = started + timedelta(minutes=5)
    >>> run = CollectionRun(
    ...     started_at=started,
    ...     completed_at=completed,
    ...     sources={"rss": SourceStats(article_count=100)},
    ...     sinks={"file": SinkResult(success=True)},
    ... )
    >>> run.duration_seconds
    300.0
    """

    run_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique run identifier"
    )
    started_at: datetime = Field(..., description="Collection start time")
    completed_at: datetime = Field(..., description="Collection end time")
    sources: dict[str, SourceStats] = Field(
        default_factory=dict, description="Per-source statistics"
    )
    sinks: dict[str, SinkResult] = Field(
        default_factory=dict, description="Per-sink results"
    )

    @property
    def duration(self) -> timedelta:
        """Return the duration of the collection run.

        Returns
        -------
        timedelta
            Time elapsed between started_at and completed_at.
        """
        return self.completed_at - self.started_at

    @property
    def duration_seconds(self) -> float:
        """Return the duration in seconds.

        Returns
        -------
        float
            Duration in seconds.
        """
        return self.duration.total_seconds()

    @property
    def total_article_count(self) -> int:
        """Return the total number of articles across all sources.

        Returns
        -------
        int
            Sum of article_count from all sources.
        """
        return sum(stats.article_count for stats in self.sources.values())

    @property
    def total_error_count(self) -> int:
        """Return the total number of errors across all sources.

        Returns
        -------
        int
            Sum of error_count from all sources.
        """
        return sum(stats.error_count for stats in self.sources.values())

    @property
    def is_successful(self) -> bool:
        """Return whether all sinks completed successfully.

        Returns
        -------
        bool
            True if all sinks succeeded, or if there are no sinks.
        """
        if not self.sinks:
            return True
        return all(sink.success for sink in self.sinks.values())


class CollectionHistory(BaseModel):
    """Manager for collection run history with persistence.

    Stores multiple collection runs and provides statistics and queries.

    Attributes
    ----------
    runs : list[CollectionRun]
        List of collection runs (newest first after sorting).
    max_runs : int | None
        Maximum number of runs to keep (None for unlimited).

    Examples
    --------
    >>> history = CollectionHistory(max_runs=100)
    >>> history.add_run(run)
    >>> len(history)
    1
    >>> stats = history.get_statistics()
    >>> stats["total_runs"]
    1
    """

    runs: list[CollectionRun] = Field(
        default_factory=list, description="List of collection runs"
    )
    max_runs: int | None = Field(
        default=None, description="Maximum runs to keep (None for unlimited)"
    )

    def __len__(self) -> int:
        """Return the number of runs in the history."""
        return len(self.runs)

    def add_run(self, run: CollectionRun) -> None:
        """Add a collection run to the history.

        Parameters
        ----------
        run : CollectionRun
            The run to add.

        Notes
        -----
        If max_runs is set and exceeded, the oldest runs are removed.
        """
        self.runs.append(run)
        logger.debug(
            "Collection run added",
            run_id=run.run_id,
            article_count=run.total_article_count,
            is_successful=run.is_successful,
        )

        # Enforce max_runs limit by removing oldest runs
        if self.max_runs is not None and len(self.runs) > self.max_runs:
            # Sort by started_at to ensure we remove oldest
            self.runs.sort(key=lambda r: r.started_at, reverse=True)
            self.runs = self.runs[: self.max_runs]
            logger.debug(
                "Old runs removed to enforce max_runs",
                max_runs=self.max_runs,
                remaining_runs=len(self.runs),
            )

    def get_latest_runs(self, n: int) -> list[CollectionRun]:
        """Get the N most recent runs.

        Parameters
        ----------
        n : int
            Maximum number of runs to return.

        Returns
        -------
        list[CollectionRun]
            Up to N most recent runs, sorted by started_at descending.
        """
        sorted_runs = sorted(self.runs, key=lambda r: r.started_at, reverse=True)
        return sorted_runs[:n]

    def get_run_by_id(self, run_id: str) -> CollectionRun | None:
        """Get a run by its ID.

        Parameters
        ----------
        run_id : str
            The run ID to search for.

        Returns
        -------
        CollectionRun | None
            The matching run, or None if not found.
        """
        for run in self.runs:
            if run.run_id == run_id:
                return run
        return None

    def get_statistics(self) -> dict[str, Any]:
        """Calculate aggregate statistics across all runs.

        Returns
        -------
        dict[str, Any]
            Statistics including:
            - total_runs: Total number of runs
            - successful_runs: Number of fully successful runs
            - failed_runs: Number of runs with at least one sink failure
            - total_articles: Total articles across all runs
            - total_errors: Total errors across all runs
            - average_duration_seconds: Average run duration
            - success_rate: Ratio of successful runs
        """
        if not self.runs:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "total_articles": 0,
                "total_errors": 0,
                "average_duration_seconds": 0.0,
                "success_rate": 1.0,
            }

        successful_runs = sum(1 for run in self.runs if run.is_successful)
        failed_runs = len(self.runs) - successful_runs
        total_articles = sum(run.total_article_count for run in self.runs)
        total_errors = sum(run.total_error_count for run in self.runs)
        total_duration = sum(run.duration_seconds for run in self.runs)
        average_duration = total_duration / len(self.runs)
        success_rate = successful_runs / len(self.runs)

        return {
            "total_runs": len(self.runs),
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "total_articles": total_articles,
            "total_errors": total_errors,
            "average_duration_seconds": average_duration,
            "success_rate": success_rate,
        }

    def get_statistics_by_source(self) -> dict[str, dict[str, int]]:
        """Calculate per-source aggregate statistics.

        Returns
        -------
        dict[str, dict[str, int]]
            Per-source statistics including:
            - total_success: Total successful fetches
            - total_errors: Total failed fetches
            - total_articles: Total articles fetched
        """
        source_stats: dict[str, dict[str, int]] = {}

        for run in self.runs:
            for source_name, stats in run.sources.items():
                if source_name not in source_stats:
                    source_stats[source_name] = {
                        "total_success": 0,
                        "total_errors": 0,
                        "total_articles": 0,
                    }
                source_stats[source_name]["total_success"] += stats.success_count
                source_stats[source_name]["total_errors"] += stats.error_count
                source_stats[source_name]["total_articles"] += stats.article_count

        return source_stats

    def save(self, path: str | Path) -> None:
        """Save the history to a JSON file.

        Parameters
        ----------
        path : str | Path
            File path to save to. Parent directories are created if needed.
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        json_data = self.model_dump_json(indent=2)
        file_path.write_text(json_data, encoding="utf-8")

        logger.info(
            "Collection history saved",
            path=str(file_path),
            run_count=len(self.runs),
        )

    @classmethod
    def load(cls, path: str | Path) -> "CollectionHistory":
        """Load history from a JSON file.

        Parameters
        ----------
        path : str | Path
            File path to load from.

        Returns
        -------
        CollectionHistory
            Loaded history, or empty history if file doesn't exist.

        Raises
        ------
        ValueError
            If the file contains invalid JSON.
        """
        file_path = Path(path)

        if not file_path.exists():
            logger.debug(
                "History file not found, returning empty history",
                path=str(file_path),
            )
            return cls()

        try:
            json_data = file_path.read_text(encoding="utf-8")
            history = cls.model_validate_json(json_data)
            logger.info(
                "Collection history loaded",
                path=str(file_path),
                run_count=len(history.runs),
            )
            return history
        except Exception as e:
            logger.error(
                "Failed to load history file",
                path=str(file_path),
                error=str(e),
            )
            raise ValueError(f"Invalid JSON in history file: {e}") from e


__all__ = [
    "CollectionHistory",
    "CollectionRun",
    "SinkResult",
    "SourceStats",
]

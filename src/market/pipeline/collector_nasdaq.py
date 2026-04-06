"""NASDAQ earnings calendar data collector.

This module provides the ``NasdaqCalendarCollector`` class that coordinates
data fetching from ``NasdaqClient``, mapping of ``EarningsRecord`` API responses
to ``EarningsCalendarRecord`` dataclass records, and persistence via
``NasdaqCalendarStorage`` and ``CollectionQueue``.

Key components
--------------
- ``QUEUE_SOURCES`` -- List of downstream sources to enqueue after calendar collection.
- ``NasdaqCalendarCollector`` -- DI-based orchestrator (client + storage + queue).

Supported collection methods
-----------------------------
- ``collect_date_range(start, end)`` -- Collect all dates in the given range.
- ``collect_recent(days_back=7, days_forward=7)`` -- Collect a rolling window.

Examples
--------
>>> collector = NasdaqCalendarCollector()
>>> result = collector.collect_recent(days_back=7, days_forward=7)
>>> result["dates_collected"]
15

See Also
--------
market.nasdaq.client : NasdaqClient providing ``get_earnings_calendar()``.
market.pipeline.storage_nasdaq : NasdaqCalendarStorage for persistence.
market.pipeline.queue : CollectionQueue for downstream task management.
market.alphavantage.collector : Reference DI pattern.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from market.nasdaq.client import NasdaqClient
from market.pipeline.errors import CollectorError
from market.pipeline.models import EarningsCalendarRecord
from market.pipeline.queue import CollectionQueue
from market.pipeline.storage_nasdaq import NasdaqCalendarStorage
from utils_core.logging import get_logger

# Maximum priority value for earnings happening today.
_MAX_PRIORITY: int = 30

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Downstream sources to enqueue for each earnings symbol found in the calendar.
QUEUE_SOURCES: list[str] = ["av_earnings", "av_overview", "sec_edgar", "yfinance"]

# Mapping from NASDAQ API time strings to normalized report_time values.
_TIME_MAP: dict[str, str] = {
    "time-after-hours": "after_close",
    "time-pre-market": "before_open",
    "time-not-supplied": None,  # type: ignore[dict-item]
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_eps_estimate(value: str | None) -> float | None:
    """Convert a raw EPS string like ``"2.50"`` or ``"N/A"`` to float."""
    if value is None or value.strip() in ("N/A", "", "—"):
        return None
    try:
        return float(value.replace(",", "").replace("$", ""))
    except ValueError:
        return None


def _normalize_report_time(time_str: str | None) -> str | None:
    """Map NASDAQ API timing strings to normalized values."""
    if time_str is None:
        return None
    return _TIME_MAP.get(time_str)


def _compute_priority(report_date: str) -> int:
    """Compute queue priority based on proximity to today.

    Closer earnings dates get higher priority (max ``_MAX_PRIORITY``).
    Both future and past dates use absolute distance so that recent
    actual results are also prioritised.

    Parameters
    ----------
    report_date : str
        ISO 8601 date string (e.g. ``"2026-04-10"``).

    Returns
    -------
    int
        Priority value in ``[0, _MAX_PRIORITY]``.

    Examples
    --------
    >>> _compute_priority(date.today().isoformat())
    30
    """
    try:
        target = date.fromisoformat(report_date)
    except ValueError:
        return 0
    days_away = abs((target - date.today()).days)
    return max(0, _MAX_PRIORITY - days_away)


def _normalize_fiscal_quarter(fq: str | None) -> str | None:
    """Normalize fiscal quarter strings like ``"Dec/2025"`` → ``"2025-12-31"``."""
    if fq is None or fq.strip() in ("N/A", ""):
        return None
    return fq


def _earnings_record_to_calendar(
    record: Any,
    report_date: str,
    fetched_at: str,
) -> EarningsCalendarRecord | None:
    """Convert a ``NasdaqClient`` ``EarningsRecord`` to ``EarningsCalendarRecord``.

    Returns ``None`` if the record has no symbol.
    """
    symbol: str | None = getattr(record, "symbol", None)
    if not symbol:
        return None

    return EarningsCalendarRecord(
        symbol=symbol,
        report_date=report_date,
        eps_estimate=_parse_eps_estimate(getattr(record, "eps_estimate", None)),
        report_time=_normalize_report_time(getattr(record, "time", None)),
        fiscal_quarter_ending=_normalize_fiscal_quarter(
            getattr(record, "fiscal_quarter_ending", None)
        ),
        fetched_at=fetched_at,
    )


# ---------------------------------------------------------------------------
# NasdaqCalendarCollector
# ---------------------------------------------------------------------------


class NasdaqCalendarCollector:
    """Orchestrator for NASDAQ earnings calendar data collection.

    Fetches earnings calendar data from the NASDAQ API via ``NasdaqClient``,
    converts each ``EarningsRecord`` to an ``EarningsCalendarRecord``, persists
    records via ``NasdaqCalendarStorage``, and enqueues downstream collection
    tasks via ``CollectionQueue``.

    Parameters
    ----------
    client : NasdaqClient | None
        NASDAQ API client. When ``None``, a default ``NasdaqClient()`` is created.
    storage : NasdaqCalendarStorage | None
        Storage layer for earnings calendar records. When ``None``, a default
        ``NasdaqCalendarStorage()`` is created.
    queue : CollectionQueue | None
        Queue for downstream collection tasks. When ``None``, a default
        ``CollectionQueue()`` is created.

    Examples
    --------
    >>> collector = NasdaqCalendarCollector()
    >>> result = collector.collect_recent(days_back=7, days_forward=7)
    >>> result["dates_collected"]
    15
    """

    def __init__(
        self,
        client: NasdaqClient | None = None,
        storage: NasdaqCalendarStorage | None = None,
        queue: CollectionQueue | None = None,
    ) -> None:
        """Initialize the collector with optional DI parameters."""
        self._client = client or NasdaqClient()
        self._storage = storage or NasdaqCalendarStorage()
        self._queue = queue or CollectionQueue()
        logger.debug(
            "NasdaqCalendarCollector initialized",
            client_type=type(self._client).__name__,
            storage_type=type(self._storage).__name__,
            queue_type=type(self._queue).__name__,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect_date_range(self, start: str, end: str) -> dict[str, Any]:
        """Collect earnings calendar data for all dates in [start, end].

        Iterates over each calendar day from ``start`` to ``end`` (inclusive),
        fetches earnings records from ``NasdaqClient.get_earnings_calendar()``,
        upserts them via ``NasdaqCalendarStorage.upsert()``, and enqueues
        downstream tasks via ``CollectionQueue.enqueue()``.

        Parameters
        ----------
        start : str
            Start date in ISO 8601 format (e.g. ``"2026-01-30"``).
        end : str
            End date in ISO 8601 format (e.g. ``"2026-02-15"``).

        Returns
        -------
        dict[str, Any]
            Summary dict with keys:
            - ``"dates_collected"``: number of calendar days processed
            - ``"records_upserted"``: total records persisted
            - ``"symbols_enqueued"``: total symbols enqueued
            - ``"errors"``: list of error strings for failed dates

        Raises
        ------
        CollectorError
            If date parsing fails (invalid ISO 8601 format).

        Examples
        --------
        >>> collector = NasdaqCalendarCollector(client=mock, storage=mock, queue=mock)
        >>> result = collector.collect_date_range("2026-01-30", "2026-01-30")
        >>> result["dates_collected"]
        1
        """
        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except ValueError as exc:
            raise CollectorError(
                f"Invalid date format: {exc}",
                context={"start": start, "end": end},
            ) from exc

        dates_collected = 0
        records_upserted = 0
        symbols_enqueued = 0
        errors: list[str] = []

        current = start_date
        while current <= end_date:
            date_str = current.isoformat()
            fetched_at = datetime.now(UTC).isoformat()

            try:
                raw_records = self._client.get_earnings_calendar(date_str)
                logger.debug(
                    "NASDAQ calendar fetched",
                    date=date_str,
                    count=len(raw_records),
                )
            except Exception as exc:
                msg = f"Failed to fetch calendar for {date_str}: {exc}"
                logger.warning(msg, date=date_str, error=str(exc))
                errors.append(msg)
                current += timedelta(days=1)
                dates_collected += 1
                continue

            calendar_records: list[EarningsCalendarRecord] = []
            for raw in raw_records:
                converted = _earnings_record_to_calendar(raw, date_str, fetched_at)
                if converted is not None:
                    calendar_records.append(converted)

            if calendar_records:
                upserted = self._storage.upsert(calendar_records)
                records_upserted += upserted

                for record in calendar_records:
                    priority = _compute_priority(record.report_date)
                    enqueued = self._queue.enqueue(
                        record.symbol,
                        record.report_date,
                        QUEUE_SOURCES,
                        priority=priority,
                    )
                    symbols_enqueued += enqueued

            dates_collected += 1
            current += timedelta(days=1)

        logger.info(
            "NASDAQ calendar collection completed",
            start=start,
            end=end,
            dates_collected=dates_collected,
            records_upserted=records_upserted,
            symbols_enqueued=symbols_enqueued,
            error_count=len(errors),
        )

        return {
            "dates_collected": dates_collected,
            "records_upserted": records_upserted,
            "symbols_enqueued": symbols_enqueued,
            "errors": errors,
        }

    def collect_recent(
        self,
        days_back: int = 7,
        days_forward: int = 7,
    ) -> dict[str, Any]:
        """Collect earnings calendar for a rolling window around today.

        Computes ``start = today - days_back`` and
        ``end = today + days_forward``, then delegates to
        ``collect_date_range()``.

        Parameters
        ----------
        days_back : int
            Number of past calendar days to include. Default ``7``.
        days_forward : int
            Number of future calendar days to include. Default ``7``.

        Returns
        -------
        dict[str, Any]
            Summary from ``collect_date_range()``.

        Examples
        --------
        >>> collector = NasdaqCalendarCollector(client=mock, storage=mock, queue=mock)
        >>> result = collector.collect_recent(days_back=3, days_forward=3)
        >>> result["dates_collected"]
        7
        """
        today = date.today()
        start = (today - timedelta(days=days_back)).isoformat()
        end = (today + timedelta(days=days_forward)).isoformat()

        logger.info(
            "Collecting recent NASDAQ calendar",
            days_back=days_back,
            days_forward=days_forward,
            start=start,
            end=end,
        )

        return self.collect_date_range(start, end)


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "QUEUE_SOURCES",
    "NasdaqCalendarCollector",
]

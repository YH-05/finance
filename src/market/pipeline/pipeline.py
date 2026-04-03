"""EarningsPipeline: 4-phase earnings data collection orchestrator.

This module provides the ``EarningsPipeline`` class that coordinates the
multi-phase market data collection pipeline:

- Phase 1: NASDAQ earnings calendar fetch (``NasdaqCalendarCollector``)
- Phase 2: Alpha Vantage earnings + overview collection from queue
  (``AlphaVantageCollector`` via ``CollectionQueue``)
- Phase 3: SEC EDGAR financial statement collection (``SecEdgarCollector``)
- Phase 4: Yahoo Finance daily price collection (``YFinanceCollector``)

Key design choices
------------------
- All collectors use default initialization (DI-friendly, but defaults work
  out of the box).
- ``av_daily_budget`` is split evenly between ``av_earnings`` and
  ``av_overview`` queues in Phase 2 (``budget // 2`` each).
- ``skip_phases`` allows selective phase execution for debugging/re-runs.
- Each phase records ``PhaseResult``; all results aggregate into
  ``PipelineResult``.
- structlog is used for per-phase start/end logging.

Examples
--------
>>> pipeline = EarningsPipeline()
>>> result = pipeline.run(days_back=7, days_forward=7)
>>> result.phase1 is not None
True

See Also
--------
market.pipeline.models : ``PhaseResult`` / ``PipelineResult``
market.pipeline.queue : ``CollectionQueue.get_pending()``
market.pipeline.collector_nasdaq : ``NasdaqCalendarCollector``
market.pipeline.collector_sec : ``SecEdgarCollector``
market.pipeline.collector_yfinance : ``YFinanceCollector``
market.alphavantage.collector : ``AlphaVantageCollector``
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from market.pipeline.constants import AV_DEFAULT_DAILY_BUDGET
from market.pipeline.errors import PipelineError
from market.pipeline.models import PhaseResult, PipelineResult
from market.pipeline.queue import CollectionQueue
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# EarningsPipeline
# ---------------------------------------------------------------------------


class EarningsPipeline:
    """4-phase earnings data collection orchestrator.

    Coordinates the complete earnings data pipeline:

    - **Phase 1**: Fetch NASDAQ earnings calendar for the configured window.
    - **Phase 2**: Collect Alpha Vantage earnings + company overview from
      the ``nc_collection_queue`` (respects ``av_daily_budget``).
    - **Phase 3**: Collect SEC EDGAR financial statements for queued symbols.
    - **Phase 4**: Collect Yahoo Finance daily prices for queued symbols.

    All collectors are default-initialized at construction time. Pass custom
    instances via the ``*_collector`` / ``queue`` parameters for testing.

    Parameters
    ----------
    av_daily_budget : int
        Total Alpha Vantage API calls allowed per day. Phase 2 splits this
        evenly: ``budget // 2`` calls each for ``av_earnings`` and
        ``av_overview``. Default: 25 (Alpha Vantage free-tier limit).
    queue : CollectionQueue | None
        Shared collection queue. When ``None``, a default queue is created.

    Examples
    --------
    >>> pipeline = EarningsPipeline(av_daily_budget=25)
    >>> result = pipeline.run(days_back=7, days_forward=7)
    >>> result.phase1 is not None
    True
    >>> result = pipeline.run(skip_phases=[2, 3])
    >>> result.phase2 is None
    True
    >>> result.phase3 is None
    True
    """

    def __init__(
        self,
        av_daily_budget: int = AV_DEFAULT_DAILY_BUDGET,
        *,
        queue: CollectionQueue | None = None,
    ) -> None:
        self._av_daily_budget = av_daily_budget
        self._queue = queue or CollectionQueue()
        logger.info(
            "EarningsPipeline initialized",
            av_daily_budget=av_daily_budget,
        )

    # ------------------------------------------------------------------
    # Public API: run()
    # ------------------------------------------------------------------

    def run(
        self,
        *,
        days_back: int = 7,
        days_forward: int = 7,
        skip_phases: list[int] | None = None,
    ) -> PipelineResult:
        """Execute the full earnings pipeline.

        Phases are executed in order (1 → 2 → 3 → 4). Each phase may be
        skipped by including its number in ``skip_phases``.

        Parameters
        ----------
        days_back : int
            Number of days before today to include in the earnings calendar
            window. Default: 7.
        days_forward : int
            Number of days after today to include in the earnings calendar
            window. Default: 7.
        skip_phases : list[int] | None
            Phase numbers to skip (e.g. ``[2, 3]`` to skip AV and SEC phases).
            ``None`` means no phases are skipped.

        Returns
        -------
        PipelineResult
            Aggregated result containing per-phase ``PhaseResult`` objects.
            Phases that were skipped have ``None`` in the corresponding field.

        Examples
        --------
        >>> pipeline = EarningsPipeline()
        >>> result = pipeline.run(days_back=3, days_forward=3)
        >>> result.total_duration_sec >= 0.0
        True
        """
        skip = set(skip_phases or [])
        pipeline_start = time.monotonic()

        logger.info(
            "EarningsPipeline.run started",
            days_back=days_back,
            days_forward=days_forward,
            skip_phases=list(skip),
        )

        phase1: PhaseResult | None = None
        phase2: PhaseResult | None = None
        phase3: PhaseResult | None = None
        phase4: PhaseResult | None = None

        if 1 not in skip:
            phase1 = self.run_phase1(days_back=days_back, days_forward=days_forward)
        else:
            logger.info("Phase 1 skipped")

        if 2 not in skip:
            phase2 = self.run_phase2()
        else:
            logger.info("Phase 2 skipped")

        if 3 not in skip:
            phase3 = self.run_phase3()
        else:
            logger.info("Phase 3 skipped")

        if 4 not in skip:
            phase4 = self.run_phase4()
        else:
            logger.info("Phase 4 skipped")

        total_duration = time.monotonic() - pipeline_start

        result = PipelineResult(
            phase1=phase1,
            phase2=phase2,
            phase3=phase3,
            phase4=phase4,
            total_duration_sec=total_duration,
        )

        logger.info(
            "EarningsPipeline.run completed",
            total_duration_sec=round(total_duration, 3),
            phase1_success=phase1.success_count if phase1 else None,
            phase2_success=phase2.success_count if phase2 else None,
            phase3_success=phase3.success_count if phase3 else None,
            phase4_success=phase4.success_count if phase4 else None,
        )

        return result

    # ------------------------------------------------------------------
    # Phase 1: NASDAQ earnings calendar
    # ------------------------------------------------------------------

    def run_phase1(
        self,
        *,
        days_back: int = 7,
        days_forward: int = 7,
    ) -> PhaseResult:
        """Phase 1: Fetch NASDAQ earnings calendar and populate the queue.

        Uses ``NasdaqCalendarCollector.collect_recent()`` to fetch the
        earnings calendar for the given window, persist records, and enqueue
        downstream collection tasks.

        Parameters
        ----------
        days_back : int
            Days before today to fetch. Default: 7.
        days_forward : int
            Days after today to fetch. Default: 7.

        Returns
        -------
        PhaseResult
            Phase 1 execution summary.
        """
        phase_start = time.monotonic()
        logger.info(
            "Phase 1 started: NASDAQ earnings calendar fetch",
            days_back=days_back,
            days_forward=days_forward,
        )

        errors: list[str] = []
        success_count = 0
        fail_count = 0
        skip_count = 0

        try:
            from market.pipeline.collector_nasdaq import NasdaqCalendarCollector

            # Pass the shared queue so newly enqueued entries are visible in Phase 2-4
            collector = NasdaqCalendarCollector(queue=self._queue)
            result: dict[str, Any] = collector.collect_recent(
                days_back=days_back,
                days_forward=days_forward,
            )

            success_count = int(result.get("records_upserted", 0))
            fail_count = int(result.get("records_failed", 0))
            skip_count = int(result.get("records_skipped", 0))

        except Exception as exc:
            logger.error("Phase 1 failed", exc_info=True)
            errors.append(str(exc))
            fail_count += 1

        duration = time.monotonic() - phase_start
        logger.info(
            "Phase 1 completed",
            success_count=success_count,
            fail_count=fail_count,
            skip_count=skip_count,
            duration_sec=round(duration, 3),
        )

        return PhaseResult(
            phase=1,
            success_count=success_count,
            fail_count=fail_count,
            skip_count=skip_count,
            duration_sec=duration,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Phase 2: Alpha Vantage queue processing
    # ------------------------------------------------------------------

    def run_phase2(self) -> PhaseResult:
        """Phase 2: Collect Alpha Vantage data from the queue.

        Pulls up to ``av_daily_budget // 2`` pending entries for each of
        ``av_earnings`` and ``av_overview`` from ``CollectionQueue``, then
        delegates to ``AlphaVantageCollector`` (one call per symbol).

        Returns
        -------
        PhaseResult
            Phase 2 execution summary.
        """
        phase_start = time.monotonic()
        logger.info(
            "Phase 2 started: Alpha Vantage queue processing",
            av_daily_budget=self._av_daily_budget,
        )

        errors: list[str] = []
        success_count = 0
        fail_count = 0
        skip_count = 0

        per_source_limit = max(1, self._av_daily_budget // 2)

        try:
            from market.alphavantage.collector import AlphaVantageCollector

            av_collector = AlphaVantageCollector()

            # Fetch pending entries for both sources
            earnings_entries = self._queue.get_pending(
                "av_earnings", limit=per_source_limit
            )
            overview_entries = self._queue.get_pending(
                "av_overview", limit=per_source_limit
            )

            logger.info(
                "Phase 2 queue entries fetched",
                av_earnings_count=len(earnings_entries),
                av_overview_count=len(overview_entries),
                per_source_limit=per_source_limit,
            )

            # Process av_earnings
            for entry in earnings_entries:
                try:
                    collect_result = av_collector.collect_earnings(entry.symbol)
                    if collect_result.success:
                        self._queue.mark_completed(
                            entry.symbol, entry.earnings_date, entry.source
                        )
                        success_count += 1
                    else:
                        error_msg = collect_result.error_message or "unknown error"
                        self._queue.mark_failed(
                            entry.symbol, entry.earnings_date, entry.source, error_msg
                        )
                        fail_count += 1
                        errors.append(
                            f"av_earnings/{entry.symbol}: {error_msg}"
                        )
                except Exception as exc:
                    error_msg = str(exc)
                    logger.error(
                        "Phase 2 av_earnings failed",
                        symbol=entry.symbol,
                        exc_info=True,
                    )
                    try:
                        self._queue.mark_failed(
                            entry.symbol, entry.earnings_date, entry.source, error_msg
                        )
                    except Exception:
                        pass
                    fail_count += 1
                    errors.append(f"av_earnings/{entry.symbol}: {error_msg}")

            # Process av_overview
            for entry in overview_entries:
                try:
                    collect_result = av_collector.collect_company_overview(entry.symbol)
                    if collect_result.success:
                        self._queue.mark_completed(
                            entry.symbol, entry.earnings_date, entry.source
                        )
                        success_count += 1
                    else:
                        error_msg = collect_result.error_message or "unknown error"
                        self._queue.mark_failed(
                            entry.symbol, entry.earnings_date, entry.source, error_msg
                        )
                        fail_count += 1
                        errors.append(
                            f"av_overview/{entry.symbol}: {error_msg}"
                        )
                except Exception as exc:
                    error_msg = str(exc)
                    logger.error(
                        "Phase 2 av_overview failed",
                        symbol=entry.symbol,
                        exc_info=True,
                    )
                    try:
                        self._queue.mark_failed(
                            entry.symbol, entry.earnings_date, entry.source, error_msg
                        )
                    except Exception:
                        pass
                    fail_count += 1
                    errors.append(f"av_overview/{entry.symbol}: {error_msg}")

        except Exception as exc:
            logger.error("Phase 2 initialization failed", exc_info=True)
            errors.append(str(exc))
            fail_count += 1

        duration = time.monotonic() - phase_start
        logger.info(
            "Phase 2 completed",
            success_count=success_count,
            fail_count=fail_count,
            skip_count=skip_count,
            duration_sec=round(duration, 3),
        )

        return PhaseResult(
            phase=2,
            success_count=success_count,
            fail_count=fail_count,
            skip_count=skip_count,
            duration_sec=duration,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Phase 3: SEC EDGAR financial statements
    # ------------------------------------------------------------------

    def run_phase3(self) -> PhaseResult:
        """Phase 3: Collect SEC EDGAR financial statements from the queue.

        Pulls all pending ``sec_edgar`` entries from ``CollectionQueue``
        and delegates to ``SecEdgarCollector``.

        Returns
        -------
        PhaseResult
            Phase 3 execution summary.
        """
        phase_start = time.monotonic()
        logger.info("Phase 3 started: SEC EDGAR financial statement collection")

        errors: list[str] = []
        success_count = 0
        fail_count = 0
        skip_count = 0

        try:
            from market.pipeline.collector_sec import SecEdgarCollector

            sec_collector = SecEdgarCollector()
            entries = self._queue.get_pending("sec_edgar")

            logger.info(
                "Phase 3 queue entries fetched",
                sec_edgar_count=len(entries),
            )

            for entry in entries:
                try:
                    result: dict[str, Any] = sec_collector.collect_symbol(entry.symbol)
                    records_upserted = int(result.get("records_upserted", 0))
                    if result.get("status") == "success" or records_upserted >= 0:
                        self._queue.mark_completed(
                            entry.symbol, entry.earnings_date, entry.source
                        )
                        success_count += 1
                    else:
                        error_msg = result.get("error", "unknown error")
                        self._queue.mark_failed(
                            entry.symbol, entry.earnings_date, entry.source,
                            str(error_msg),
                        )
                        fail_count += 1
                        errors.append(f"sec_edgar/{entry.symbol}: {error_msg}")
                except Exception as exc:
                    error_msg = str(exc)
                    logger.error(
                        "Phase 3 failed for symbol",
                        symbol=entry.symbol,
                        exc_info=True,
                    )
                    try:
                        self._queue.mark_failed(
                            entry.symbol, entry.earnings_date, entry.source, error_msg
                        )
                    except Exception:
                        pass
                    fail_count += 1
                    errors.append(f"sec_edgar/{entry.symbol}: {error_msg}")

        except Exception as exc:
            logger.error("Phase 3 initialization failed", exc_info=True)
            errors.append(str(exc))
            fail_count += 1

        duration = time.monotonic() - phase_start
        logger.info(
            "Phase 3 completed",
            success_count=success_count,
            fail_count=fail_count,
            skip_count=skip_count,
            duration_sec=round(duration, 3),
        )

        return PhaseResult(
            phase=3,
            success_count=success_count,
            fail_count=fail_count,
            skip_count=skip_count,
            duration_sec=duration,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Phase 4: Yahoo Finance daily prices
    # ------------------------------------------------------------------

    def run_phase4(self) -> PhaseResult:
        """Phase 4: Collect Yahoo Finance daily prices from the queue.

        Pulls all pending ``yfinance`` entries from ``CollectionQueue``
        and delegates to ``YFinanceCollector``.

        Returns
        -------
        PhaseResult
            Phase 4 execution summary.
        """
        phase_start = time.monotonic()
        logger.info("Phase 4 started: Yahoo Finance daily price collection")

        errors: list[str] = []
        success_count = 0
        fail_count = 0
        skip_count = 0

        try:
            from market.pipeline.collector_yfinance import YFinanceCollector

            yf_collector = YFinanceCollector()
            entries = self._queue.get_pending("yfinance")

            logger.info(
                "Phase 4 queue entries fetched",
                yfinance_count=len(entries),
            )

            for entry in entries:
                try:
                    result: dict[str, Any] = yf_collector.collect_daily(entry.symbol)
                    if result.get("status") == "success" or "symbol" in result:
                        self._queue.mark_completed(
                            entry.symbol, entry.earnings_date, entry.source
                        )
                        success_count += 1
                    else:
                        error_msg = result.get("error", "unknown error")
                        self._queue.mark_failed(
                            entry.symbol, entry.earnings_date, entry.source,
                            str(error_msg),
                        )
                        fail_count += 1
                        errors.append(f"yfinance/{entry.symbol}: {error_msg}")
                except Exception as exc:
                    error_msg = str(exc)
                    logger.error(
                        "Phase 4 failed for symbol",
                        symbol=entry.symbol,
                        exc_info=True,
                    )
                    try:
                        self._queue.mark_failed(
                            entry.symbol, entry.earnings_date, entry.source, error_msg
                        )
                    except Exception:
                        pass
                    fail_count += 1
                    errors.append(f"yfinance/{entry.symbol}: {error_msg}")

        except Exception as exc:
            logger.error("Phase 4 initialization failed", exc_info=True)
            errors.append(str(exc))
            fail_count += 1

        duration = time.monotonic() - phase_start
        logger.info(
            "Phase 4 completed",
            success_count=success_count,
            fail_count=fail_count,
            skip_count=skip_count,
            duration_sec=round(duration, 3),
        )

        return PhaseResult(
            phase=4,
            success_count=success_count,
            fail_count=fail_count,
            skip_count=skip_count,
            duration_sec=duration,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Status / utility
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return queue statistics for all sources.

        Returns
        -------
        dict[str, Any]
            Queue stats from ``CollectionQueue.get_stats()`` plus pipeline
            configuration metadata. Never raises; returns an error key on
            failure.

        Examples
        --------
        >>> pipeline = EarningsPipeline()
        >>> status = pipeline.get_status()
        >>> "queue_stats" in status
        True
        >>> "av_daily_budget" in status
        True
        """
        try:
            stats = self._queue.get_stats()
        except Exception as exc:
            logger.error("get_status failed", exc_info=True)
            return {
                "error": str(exc),
                "av_daily_budget": self._av_daily_budget,
                "queue_stats": {},
            }

        return {
            "av_daily_budget": self._av_daily_budget,
            "queue_stats": stats,
        }


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = ["EarningsPipeline"]

"""Storage record and result models for the pipeline package.

This module defines frozen dataclass types for pipeline data records and
phase/pipeline result aggregates.

Record types (correspond to SQLite tables in ``constants.py``)
--------------------------------------------------------------
- ``EarningsCalendarRecord`` -- ``nc_earnings_calendar``
- ``QueueEntry`` -- ``nc_collection_queue``
- ``FinancialStatementRecord`` -- ``se_financial_statements``
- ``YFDailyPriceRecord`` -- ``yf_daily_prices``

Result types (pipeline execution outputs)
-----------------------------------------
- ``PhaseResult`` -- per-phase execution summary
- ``PipelineResult`` -- full pipeline run summary (aggregates all phases)

All dataclasses use ``frozen=True`` to ensure immutability. Required fields
(without defaults) are listed first, followed by Optional fields with
``None`` defaults, following the pattern established in
``market.alphavantage.models``.

See Also
--------
market.pipeline.constants : Table name constants used by these models.
market.alphavantage.models : Reference implementation pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# =============================================================================
# NASDAQ Earnings Calendar
# =============================================================================


@dataclass(frozen=True)
class EarningsCalendarRecord:
    """Earnings calendar record for ``nc_earnings_calendar``.

    Parameters
    ----------
    symbol : str
        Ticker symbol in NASDAQ format (e.g. ``"AAPL"``).
    report_date : str
        Expected earnings report date in ISO 8601 format (e.g. ``"2026-04-30"``).
    eps_estimate : float | None
        Consensus EPS estimate. ``None`` when not yet available.
    report_time : str | None
        Report timing relative to market: ``"before_open"``, ``"after_close"``,
        or ``"during_trading"``. ``None`` when not specified.
    fiscal_quarter_ending : str | None
        Fiscal quarter end date (e.g. ``"2026-03-31"``). ``None`` when unavailable.
    fetched_at : str
        ISO 8601 timestamp of when the record was fetched.

    Examples
    --------
    >>> record = EarningsCalendarRecord(
    ...     symbol="AAPL",
    ...     report_date="2026-04-30",
    ...     fetched_at="2026-04-03T10:00:00",
    ... )
    >>> record.symbol
    'AAPL'
    """

    # --- Required key fields ---
    symbol: str
    report_date: str

    # --- Optional data fields ---
    eps_estimate: float | None = None
    report_time: str | None = None
    fiscal_quarter_ending: str | None = None

    # --- Metadata ---
    fetched_at: str = ""


# =============================================================================
# Collection Queue
# =============================================================================


@dataclass(frozen=True)
class QueueEntry:
    """Collection task queue entry for ``nc_collection_queue``.

    Each row represents one ``(symbol, earnings_date, source)`` combination.
    The composite primary key is ``(symbol, earnings_date, source)``.

    Parameters
    ----------
    symbol : str
        Ticker symbol in NASDAQ format (e.g. ``"AAPL"``).
    earnings_date : str
        Expected earnings date in ISO 8601 format (e.g. ``"2026-04-30"``).
    source : str
        Data source identifier (e.g. ``"nasdaq"``, ``"yfinance"``).
    status : str
        Current status: ``"pending"``, ``"completed"``, ``"failed"``,
        or ``"skipped"``.
    priority : int
        Collection priority. Higher values are processed first.
        Default is ``0``.
    attempts : int
        Number of collection attempts made so far. Starts at ``0``.
    created_at : str
        ISO 8601 timestamp of when the entry was added to the queue.
    updated_at : str | None
        ISO 8601 timestamp of the last status update. ``None`` when never updated.
    error_message : str | None
        Error description when ``status == "failed"``. ``None`` otherwise.

    Examples
    --------
    >>> entry = QueueEntry(
    ...     symbol="AAPL",
    ...     earnings_date="2026-04-30",
    ...     source="nasdaq",
    ...     status="pending",
    ...     priority=0,
    ...     attempts=0,
    ...     created_at="2026-04-03T09:00:00",
    ... )
    >>> entry.status
    'pending'
    """

    # --- Required key fields ---
    symbol: str
    earnings_date: str
    source: str
    status: str
    priority: int
    attempts: int
    created_at: str

    # --- Optional fields ---
    updated_at: str | None = None
    error_message: str | None = None


# =============================================================================
# SEC EDGAR Financial Statements
# =============================================================================


@dataclass(frozen=True)
class FinancialStatementRecord:
    """Financial statement record for ``se_financial_statements``.

    Parameters
    ----------
    symbol : str
        Ticker symbol in SEC EDGAR format (e.g. ``"AAPL"``).
    fiscal_date_ending : str
        Fiscal period end date in ISO 8601 format.
    statement_type : str
        Statement type: ``"income"``, ``"balance_sheet"``, or ``"cash_flow"``.
    report_type : str
        Period type: ``"annual"`` or ``"quarterly"``.
    revenue : float | None
        Total revenue / net sales. ``None`` when not applicable.
    net_income : float | None
        Net income. ``None`` when not applicable.
    total_assets : float | None
        Total assets. ``None`` when not applicable.
    total_liabilities : float | None
        Total liabilities. ``None`` when not applicable.
    operating_cashflow : float | None
        Operating cash flow. ``None`` when not applicable.
    fetched_at : str
        ISO 8601 timestamp of when the record was fetched.

    Examples
    --------
    >>> record = FinancialStatementRecord(
    ...     symbol="AAPL",
    ...     fiscal_date_ending="2025-09-30",
    ...     statement_type="income",
    ...     report_type="annual",
    ...     fetched_at="2026-04-03T10:00:00",
    ... )
    >>> record.statement_type
    'income'
    """

    # --- Required key fields ---
    symbol: str
    fiscal_date_ending: str
    statement_type: str
    report_type: str

    # --- Optional financial data fields ---
    revenue: float | None = None
    net_income: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    operating_cashflow: float | None = None

    # --- Metadata ---
    fetched_at: str = ""


# =============================================================================
# Yahoo Finance Daily Prices
# =============================================================================


@dataclass(frozen=True)
class YFDailyPriceRecord:
    """Yahoo Finance daily OHLCV price record for ``yf_daily_prices``.

    Parameters
    ----------
    symbol : str
        Ticker symbol in yfinance format (e.g. ``"BRK-B"``).
    date : str
        Trading date in ISO 8601 format (e.g. ``"2026-04-03"``).
    open : float
        Opening price.
    high : float
        Highest price during the session.
    low : float
        Lowest price during the session.
    close : float
        Closing price.
    adjusted_close : float | None
        Split/dividend-adjusted closing price.
        ``None`` when adjustment data is unavailable.
    volume : int
        Trading volume (number of shares).
    fetched_at : str
        ISO 8601 timestamp of when the data was fetched.

    Examples
    --------
    >>> record = YFDailyPriceRecord(
    ...     symbol="AAPL",
    ...     date="2026-04-03",
    ...     open=170.0,
    ...     high=175.0,
    ...     low=169.0,
    ...     close=173.0,
    ...     adjusted_close=173.0,
    ...     volume=50_000_000,
    ...     fetched_at="2026-04-03T20:00:00",
    ... )
    >>> record.symbol
    'AAPL'
    """

    # --- Required key fields ---
    symbol: str
    date: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float | None
    volume: int

    # --- Metadata ---
    fetched_at: str = ""


# =============================================================================
# Phase / Pipeline Result Types
# =============================================================================


@dataclass(frozen=True)
class PhaseResult:
    """Execution summary for a single pipeline phase.

    Parameters
    ----------
    phase : int
        Phase number (1-based, e.g. 1 for calendar fetch, 2 for queue build).
    success_count : int
        Number of records successfully processed in this phase.
    fail_count : int
        Number of records that failed processing in this phase.
    skip_count : int
        Number of records skipped (e.g. already up-to-date) in this phase.
    duration_sec : float
        Wall-clock execution time for this phase in seconds.
    errors : list[str]
        List of error messages collected during this phase.
        Empty list when no errors occurred.

    Examples
    --------
    >>> result = PhaseResult(
    ...     phase=1,
    ...     success_count=100,
    ...     fail_count=2,
    ...     skip_count=5,
    ...     duration_sec=12.3,
    ...     errors=["AAPL: rate limit", "MSFT: timeout"],
    ... )
    >>> result.success_count
    100
    """

    phase: int
    success_count: int
    fail_count: int
    skip_count: int
    duration_sec: float
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineResult:
    """Full pipeline run summary aggregating all phase results.

    Parameters
    ----------
    phase1 : PhaseResult | None
        Result of phase 1 (earnings calendar fetch). ``None`` when not run.
    phase2 : PhaseResult | None
        Result of phase 2 (queue build). ``None`` when not run.
    phase3 : PhaseResult | None
        Result of phase 3 (financial statement collection). ``None`` when not run.
    phase4 : PhaseResult | None
        Result of phase 4 (price collection). ``None`` when not run.
    total_duration_sec : float
        Total wall-clock execution time for the complete pipeline run.

    Examples
    --------
    >>> from market.pipeline.models import PhaseResult, PipelineResult
    >>> p1 = PhaseResult(phase=1, success_count=50, fail_count=0, skip_count=0,
    ...                  duration_sec=5.0)
    >>> result = PipelineResult(
    ...     phase1=p1,
    ...     phase2=None,
    ...     phase3=None,
    ...     phase4=None,
    ...     total_duration_sec=5.0,
    ... )
    >>> result.phase1.success_count
    50
    """

    phase1: PhaseResult | None
    phase2: PhaseResult | None
    phase3: PhaseResult | None
    phase4: PhaseResult | None
    total_duration_sec: float


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    "EarningsCalendarRecord",
    "FinancialStatementRecord",
    "PhaseResult",
    "PipelineResult",
    "QueueEntry",
    "YFDailyPriceRecord",
]

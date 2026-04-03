"""Pytest configuration and shared fixtures for market.pipeline test suite.

This module provides reusable fixtures for testing the pipeline package
modules including storage, queue, and collector components.

Fixtures
--------
tmp_db_path : Path
    Temporary SQLite database path backed by a real tempfile (cleaned up
    automatically after the test).
mock_collection_queue : MagicMock
    MagicMock simulating a CollectionQueue instance.
mock_nasdaq_storage : MagicMock
    MagicMock simulating a NasdaqCalendarStorage instance.
mock_sec_storage : MagicMock
    MagicMock simulating a SecEdgarStorage instance.
mock_yfinance_storage : MagicMock
    MagicMock simulating a YFinanceStorage instance.
mock_nasdaq_client : MagicMock
    MagicMock simulating a NasdaqClient instance.
mock_av_collector : MagicMock
    MagicMock simulating an AlphaVantageCollector instance.
mock_yfinance_fetcher : MagicMock
    MagicMock simulating a YFinanceFetcher instance.

See Also
--------
tests.market.nasdaq.conftest : Reference fixture pattern for the nasdaq module.
market.pipeline.models : Data model types used in fixtures.
"""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from market.pipeline.models import (
    EarningsCalendarRecord,
    FinancialStatementRecord,
    QueueEntry,
    YFDailyPriceRecord,
)

if TYPE_CHECKING:
    from pathlib import Path

# =============================================================================
# Database fixtures
# =============================================================================


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary SQLite database path backed by a real file.

    Uses pytest's ``tmp_path`` fixture to create a unique temporary directory
    per test. The database file is automatically cleaned up after the test.

    Parameters
    ----------
    tmp_path : Path
        pytest-provided temporary directory (unique per test).

    Returns
    -------
    Path
        Path to a temporary SQLite database file (does not need to exist yet;
        SQLiteClient creates it on first use).
    """
    return tmp_path / "test_pipeline.db"


# =============================================================================
# Storage mock fixtures
# =============================================================================


@pytest.fixture
def mock_nasdaq_storage() -> MagicMock:
    """Create a MagicMock simulating a NasdaqCalendarStorage instance.

    The mock provides default return values for all storage methods:
    - ``upsert()`` returns 0 (no records upserted by default)
    - ``get_by_date_range()`` returns an empty list
    - ``get_latest_fetched_date()`` returns None
    - ``get_table_names()`` returns ['nc_earnings_calendar']
    - ``ensure_tables()`` returns None

    Returns
    -------
    MagicMock
        A MagicMock mimicking NasdaqCalendarStorage.
    """
    storage = MagicMock()
    storage.upsert.return_value = 0
    storage.get_by_date_range.return_value = []
    storage.get_latest_fetched_date.return_value = None
    storage.get_table_names.return_value = ["nc_earnings_calendar"]
    storage.ensure_tables.return_value = None
    return storage


@pytest.fixture
def mock_sec_storage() -> MagicMock:
    """Create a MagicMock simulating a SecEdgarStorage instance.

    The mock provides default return values for all storage methods:
    - ``upsert()`` returns 0
    - ``get_by_symbol()`` returns an empty list
    - ``get_symbols_with_data()`` returns an empty list
    - ``get_latest_filing_date()`` returns None
    - ``get_table_names()`` returns ['se_financial_statements']
    - ``ensure_tables()`` returns None

    Returns
    -------
    MagicMock
        A MagicMock mimicking SecEdgarStorage.
    """
    storage = MagicMock()
    storage.upsert.return_value = 0
    storage.get_by_symbol.return_value = []
    storage.get_symbols_with_data.return_value = []
    storage.get_latest_filing_date.return_value = None
    storage.get_table_names.return_value = ["se_financial_statements"]
    storage.ensure_tables.return_value = None
    return storage


@pytest.fixture
def mock_yfinance_storage() -> MagicMock:
    """Create a MagicMock simulating a YFinanceStorage instance.

    The mock provides default return values for all storage methods:
    - ``upsert()`` returns 0
    - ``get_latest_date()`` returns None (no prior data)
    - ``get_by_symbol_date_range()`` returns an empty list
    - ``get_table_names()`` returns ['yf_daily_prices']
    - ``ensure_tables()`` returns None

    Returns
    -------
    MagicMock
        A MagicMock mimicking YFinanceStorage.
    """
    storage = MagicMock()
    storage.upsert.return_value = 0
    storage.get_latest_date.return_value = None
    storage.get_by_symbol_date_range.return_value = []
    storage.get_table_names.return_value = ["yf_daily_prices"]
    storage.ensure_tables.return_value = None
    return storage


# =============================================================================
# Queue mock fixture
# =============================================================================


@pytest.fixture
def mock_collection_queue() -> MagicMock:
    """Create a MagicMock simulating a CollectionQueue instance.

    The mock provides default return values for all queue methods:
    - ``enqueue()`` returns 0 (no new entries by default)
    - ``get_pending()`` returns an empty list
    - ``get_stats()`` returns an empty dict
    - ``mark_completed()``, ``mark_failed()``, ``mark_skipped()`` return None
    - ``reset_failed()`` returns 0
    - ``ensure_tables()`` returns None

    Returns
    -------
    MagicMock
        A MagicMock mimicking CollectionQueue.
    """
    queue = MagicMock()
    queue.enqueue.return_value = 0
    queue.get_pending.return_value = []
    queue.get_stats.return_value = {}
    queue.mark_completed.return_value = None
    queue.mark_failed.return_value = None
    queue.mark_skipped.return_value = None
    queue.reset_failed.return_value = 0
    queue.ensure_tables.return_value = None
    return queue


# =============================================================================
# Client / fetcher mock fixtures
# =============================================================================


@pytest.fixture
def mock_nasdaq_client() -> MagicMock:
    """Create a MagicMock simulating a NasdaqClient instance.

    The mock's ``get_earnings_calendar()`` method returns an empty list
    by default (no earnings records).

    Returns
    -------
    MagicMock
        A MagicMock mimicking NasdaqClient.
    """
    client = MagicMock()
    client.get_earnings_calendar.return_value = []
    return client


@pytest.fixture
def mock_av_collector() -> MagicMock:
    """Create a MagicMock simulating an AlphaVantageCollector instance.

    The mock's ``collect_earnings()`` and ``collect_company_overview()``
    methods return a successful result by default.

    Returns
    -------
    MagicMock
        A MagicMock mimicking AlphaVantageCollector.
    """
    collector = MagicMock()
    result = MagicMock()
    result.success = True
    result.error_message = None
    collector.collect_earnings.return_value = result
    collector.collect_company_overview.return_value = result
    return collector


@pytest.fixture
def mock_yfinance_fetcher() -> MagicMock:
    """Create a MagicMock simulating a YFinanceFetcher instance.

    The mock's ``fetch()`` method returns an empty list by default
    (no market data results).

    Returns
    -------
    MagicMock
        A MagicMock mimicking YFinanceFetcher.
    """
    fetcher = MagicMock()
    fetcher.fetch.return_value = []
    return fetcher


# =============================================================================
# Sample data fixtures
# =============================================================================


@pytest.fixture
def sample_earnings_record() -> EarningsCalendarRecord:
    """Create a sample EarningsCalendarRecord for testing.

    Returns
    -------
    EarningsCalendarRecord
        A sample record for AAPL with all fields populated.
    """
    return EarningsCalendarRecord(
        symbol="AAPL",
        report_date="2026-04-30",
        eps_estimate=1.55,
        report_time="after_close",
        fiscal_quarter_ending="2026-03-31",
        fetched_at="2026-04-03T10:00:00+00:00",
    )


@pytest.fixture
def sample_financial_record() -> FinancialStatementRecord:
    """Create a sample FinancialStatementRecord for testing.

    Returns
    -------
    FinancialStatementRecord
        A sample income statement record for AAPL.
    """
    return FinancialStatementRecord(
        symbol="AAPL",
        fiscal_date_ending="2025-09-30",
        statement_type="income",
        report_type="annual",
        revenue=391_035_000_000.0,
        net_income=93_736_000_000.0,
        total_assets=None,
        total_liabilities=None,
        operating_cashflow=None,
        fetched_at="2026-04-03T10:00:00+00:00",
    )


@pytest.fixture
def sample_yf_price_record() -> YFDailyPriceRecord:
    """Create a sample YFDailyPriceRecord for testing.

    Returns
    -------
    YFDailyPriceRecord
        A sample daily price record for AAPL.
    """
    return YFDailyPriceRecord(
        symbol="AAPL",
        date="2026-04-03",
        open=170.0,
        high=175.0,
        low=169.0,
        close=173.0,
        adjusted_close=173.0,
        volume=50_000_000,
        fetched_at="2026-04-03T20:00:00+00:00",
    )


@pytest.fixture
def sample_queue_entry() -> QueueEntry:
    """Create a sample QueueEntry for testing.

    Returns
    -------
    QueueEntry
        A sample pending queue entry for AAPL with nasdaq source.
    """
    return QueueEntry(
        symbol="AAPL",
        earnings_date="2026-04-30",
        source="nasdaq",
        status="pending",
        priority=0,
        attempts=0,
        created_at="2026-04-03T09:00:00+00:00",
        updated_at=None,
        error_message=None,
    )

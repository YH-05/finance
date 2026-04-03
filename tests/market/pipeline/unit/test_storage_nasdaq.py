"""Unit tests for market.pipeline.storage_nasdaq.NasdaqCalendarStorage.

Tests use a real SQLite DB via the ``tmp_db_path`` fixture from conftest.py.
No external dependencies are required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market.pipeline.errors import StorageError
from market.pipeline.models import EarningsCalendarRecord
from market.pipeline.storage_nasdaq import NasdaqCalendarStorage

# =============================================================================
# Helper factories
# =============================================================================


def _make_record(
    symbol: str = "AAPL",
    report_date: str = "2026-04-30",
    eps_estimate: float | None = 1.55,
    report_time: str | None = "after_close",
    fiscal_quarter_ending: str | None = "2026-03-31",
    fetched_at: str = "2026-04-03T10:00:00+00:00",
) -> EarningsCalendarRecord:
    return EarningsCalendarRecord(
        symbol=symbol,
        report_date=report_date,
        eps_estimate=eps_estimate,
        report_time=report_time,
        fiscal_quarter_ending=fiscal_quarter_ending,
        fetched_at=fetched_at,
    )


# =============================================================================
# Initialization tests
# =============================================================================


class TestNasdaqCalendarStorageInit:
    """Tests for NasdaqCalendarStorage initialization."""

    def test_正常系_インメモリDBで初期化できる(self) -> None:
        storage = NasdaqCalendarStorage(db_path=Path(":memory:"))
        assert "nc_earnings_calendar" in storage.get_table_names()

    def test_正常系_tempfileパスで初期化できる(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        assert "nc_earnings_calendar" in storage.get_table_names()

    def test_正常系_ensure_tablesを複数回呼べる(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        # Should not raise
        storage.ensure_tables()
        storage.ensure_tables()


# =============================================================================
# upsert tests
# =============================================================================


class TestNasdaqCalendarStorageUpsert:
    """Tests for NasdaqCalendarStorage.upsert()."""

    def test_正常系_レコードをupsertできる(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        record = _make_record()
        result = storage.upsert([record])
        assert result == 1

    def test_正常系_複数レコードをupsertできる(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        records = [
            _make_record("AAPL", "2026-04-30"),
            _make_record("MSFT", "2026-04-30"),
            _make_record("GOOGL", "2026-05-01"),
        ]
        result = storage.upsert(records)
        assert result == 3

    def test_正常系_空リストはno_op(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        result = storage.upsert([])
        assert result == 0

    def test_正常系_同一レコードの重複upsertは置換される(
        self, tmp_db_path: Path
    ) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        record1 = _make_record("AAPL", "2026-04-30", eps_estimate=1.55)
        storage.upsert([record1])
        # Update with new eps_estimate
        record2 = _make_record("AAPL", "2026-04-30", eps_estimate=1.70)
        storage.upsert([record2])
        # Retrieve to verify update
        rows = storage.get_by_date_range("2026-04-30", "2026-04-30")
        assert len(rows) == 1
        assert rows[0]["eps_estimate"] == pytest.approx(1.70)

    def test_正常系_Noneフィールドを含むレコードをupsertできる(
        self, tmp_db_path: Path
    ) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        record = _make_record(
            eps_estimate=None, report_time=None, fiscal_quarter_ending=None
        )
        result = storage.upsert([record])
        assert result == 1


# =============================================================================
# get_by_date_range tests
# =============================================================================


class TestNasdaqCalendarStorageGetByDateRange:
    """Tests for NasdaqCalendarStorage.get_by_date_range()."""

    def test_正常系_日付範囲内のレコードを取得できる(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record("AAPL", "2026-04-28"),
                _make_record("MSFT", "2026-04-30"),
                _make_record("GOOGL", "2026-05-02"),
            ]
        )
        rows = storage.get_by_date_range("2026-04-28", "2026-04-30")
        assert len(rows) == 2
        symbols = {row["symbol"] for row in rows}
        assert symbols == {"AAPL", "MSFT"}

    def test_正常系_範囲外のレコードは含まれない(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        storage.upsert([_make_record("AAPL", "2026-04-28")])
        rows = storage.get_by_date_range("2026-05-01", "2026-05-31")
        assert rows == []

    def test_正常系_空テーブルは空リストを返す(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        rows = storage.get_by_date_range("2026-04-01", "2026-04-30")
        assert rows == []


# =============================================================================
# get_latest_fetched_date tests
# =============================================================================


class TestNasdaqCalendarStorageGetLatestFetchedDate:
    """Tests for NasdaqCalendarStorage.get_latest_fetched_date()."""

    def test_正常系_データがある場合は最新fetched_atを返す(
        self, tmp_db_path: Path
    ) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record(fetched_at="2026-04-01T10:00:00+00:00"),
                _make_record("MSFT", fetched_at="2026-04-03T15:00:00+00:00"),
            ]
        )
        latest = storage.get_latest_fetched_date()
        assert latest == "2026-04-03T15:00:00+00:00"

    def test_正常系_テーブルが空の場合はNoneを返す(self, tmp_db_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_db_path)
        assert storage.get_latest_fetched_date() is None

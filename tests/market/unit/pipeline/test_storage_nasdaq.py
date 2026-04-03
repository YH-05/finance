"""Unit tests for market.pipeline.storage_nasdaq.NasdaqCalendarStorage."""

from __future__ import annotations

from pathlib import Path

import pytest

from market.pipeline.models import EarningsCalendarRecord
from market.pipeline.storage_nasdaq import NasdaqCalendarStorage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def storage(tmp_path: Path) -> NasdaqCalendarStorage:
    """Create a NasdaqCalendarStorage backed by a temp file DB."""
    return NasdaqCalendarStorage(db_path=tmp_path / "nasdaq_test.db")


@pytest.fixture()
def sample_record() -> EarningsCalendarRecord:
    return EarningsCalendarRecord(
        symbol="AAPL",
        report_date="2026-04-30",
        eps_estimate=1.5,
        report_time="after_close",
        fiscal_quarter_ending="2026-03-31",
        fetched_at="2026-04-03T10:00:00",
    )


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


class TestNasdaqCalendarStorageInit:
    def test_正常系_tmp_pathで初期化できる(self, tmp_path: Path) -> None:
        storage = NasdaqCalendarStorage(db_path=tmp_path / "test.db")
        assert storage is not None

    def test_正常系_memoryパスで初期化できる(self) -> None:
        storage = NasdaqCalendarStorage(db_path=Path(":memory:"))
        assert storage is not None

    def test_正常系_初期化時にテーブルが作成される(
        self, storage: NasdaqCalendarStorage
    ) -> None:
        tables = storage.get_table_names()
        assert "nc_earnings_calendar" in tables

    def test_正常系_db_pathNoneでデフォルトパスが使われる(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        env_path = str(tmp_path / "env_override.db")
        monkeypatch.setenv("PIPELINE_NASDAQ_DB_PATH", env_path)
        storage = NasdaqCalendarStorage()
        assert storage is not None


# ---------------------------------------------------------------------------
# ensure_tables tests
# ---------------------------------------------------------------------------


class TestEnsureTables:
    def test_正常系_複数回呼び出しても安全(
        self, storage: NasdaqCalendarStorage
    ) -> None:
        storage.ensure_tables()
        storage.ensure_tables()
        tables = storage.get_table_names()
        assert "nc_earnings_calendar" in tables


# ---------------------------------------------------------------------------
# upsert tests
# ---------------------------------------------------------------------------


class TestUpsert:
    def test_正常系_レコードを挿入できる(
        self, storage: NasdaqCalendarStorage, sample_record: EarningsCalendarRecord
    ) -> None:
        count = storage.upsert([sample_record])
        assert count == 1

    def test_正常系_同一レコードを2回挿入しても1件のみ保存される(
        self, storage: NasdaqCalendarStorage, sample_record: EarningsCalendarRecord
    ) -> None:
        storage.upsert([sample_record])
        storage.upsert([sample_record])
        rows = storage.get_by_date_range("2026-04-30", "2026-04-30")
        assert len(rows) == 1

    def test_正常系_空リストで0件返す(self, storage: NasdaqCalendarStorage) -> None:
        count = storage.upsert([])
        assert count == 0

    def test_正常系_複数レコードを一括挿入できる(
        self, storage: NasdaqCalendarStorage
    ) -> None:
        records = [
            EarningsCalendarRecord(
                symbol="AAPL",
                report_date="2026-04-30",
                fetched_at="2026-04-03T10:00:00",
            ),
            EarningsCalendarRecord(
                symbol="MSFT",
                report_date="2026-05-01",
                fetched_at="2026-04-03T10:00:00",
            ),
        ]
        count = storage.upsert(records)
        assert count == 2

    def test_正常系_upsertが既存レコードを上書きする(
        self, storage: NasdaqCalendarStorage
    ) -> None:
        original = EarningsCalendarRecord(
            symbol="AAPL",
            report_date="2026-04-30",
            eps_estimate=1.0,
            fetched_at="2026-04-03T10:00:00",
        )
        updated = EarningsCalendarRecord(
            symbol="AAPL",
            report_date="2026-04-30",
            eps_estimate=2.0,
            fetched_at="2026-04-03T11:00:00",
        )
        storage.upsert([original])
        storage.upsert([updated])
        rows = storage.get_by_date_range("2026-04-30", "2026-04-30")
        assert len(rows) == 1
        assert rows[0]["eps_estimate"] == 2.0


# ---------------------------------------------------------------------------
# get_by_date_range tests
# ---------------------------------------------------------------------------


class TestGetByDateRange:
    def test_正常系_日付範囲でレコードを取得できる(
        self, storage: NasdaqCalendarStorage
    ) -> None:
        records = [
            EarningsCalendarRecord(
                symbol="AAPL",
                report_date="2026-04-29",
                fetched_at="2026-04-03T10:00:00",
            ),
            EarningsCalendarRecord(
                symbol="MSFT",
                report_date="2026-04-30",
                fetched_at="2026-04-03T10:00:00",
            ),
            EarningsCalendarRecord(
                symbol="GOOG",
                report_date="2026-05-02",
                fetched_at="2026-04-03T10:00:00",
            ),
        ]
        storage.upsert(records)
        rows = storage.get_by_date_range("2026-04-29", "2026-04-30")
        assert len(rows) == 2

    def test_正常系_データなしで空リストを返す(
        self, storage: NasdaqCalendarStorage
    ) -> None:
        rows = storage.get_by_date_range("2026-04-29", "2026-04-30")
        assert rows == []

    def test_正常系_startとendが同じ日付で単一レコードを取得(
        self, storage: NasdaqCalendarStorage, sample_record: EarningsCalendarRecord
    ) -> None:
        storage.upsert([sample_record])
        rows = storage.get_by_date_range("2026-04-30", "2026-04-30")
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# get_latest_fetched_date tests
# ---------------------------------------------------------------------------


class TestGetLatestFetchedDate:
    def test_正常系_レコードがある場合に最新fetched_atを返す(
        self, storage: NasdaqCalendarStorage
    ) -> None:
        records = [
            EarningsCalendarRecord(
                symbol="AAPL",
                report_date="2026-04-30",
                fetched_at="2026-04-01T10:00:00",
            ),
            EarningsCalendarRecord(
                symbol="MSFT",
                report_date="2026-05-01",
                fetched_at="2026-04-03T10:00:00",
            ),
        ]
        storage.upsert(records)
        latest = storage.get_latest_fetched_date()
        assert latest == "2026-04-03T10:00:00"

    def test_正常系_レコードがない場合にNoneを返す(
        self, storage: NasdaqCalendarStorage
    ) -> None:
        latest = storage.get_latest_fetched_date()
        assert latest is None


# ---------------------------------------------------------------------------
# StorageError wrapping tests
# ---------------------------------------------------------------------------


class TestStorageError:
    def test_異常系_無効なdb_pathで初期化時にStorageErrorが発生する(self) -> None:
        from market.pipeline.errors import StorageError

        with pytest.raises(StorageError):
            # Attempt to create in a non-existent path that cannot be created
            NasdaqCalendarStorage(
                db_path=Path("/nonexistent_root/nested/very/deep/test.db")
            )

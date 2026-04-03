"""Unit tests for market.pipeline.storage_yfinance.YFinanceStorage."""

from __future__ import annotations

from pathlib import Path

import pytest

from market.pipeline.models import YFDailyPriceRecord
from market.pipeline.storage_yfinance import YFinanceStorage

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def storage(tmp_path: Path) -> YFinanceStorage:
    """Create a YFinanceStorage backed by a temp file DB."""
    return YFinanceStorage(db_path=tmp_path / "yfinance_test.db")


@pytest.fixture()
def sample_record() -> YFDailyPriceRecord:
    return YFDailyPriceRecord(
        symbol="AAPL",
        date="2026-04-03",
        open=170.0,
        high=175.0,
        low=169.0,
        close=173.0,
        adjusted_close=173.0,
        volume=50_000_000,
        fetched_at="2026-04-03T20:00:00",
    )


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


class TestYFinanceStorageInit:
    def test_正常系_tmp_pathで初期化できる(self, tmp_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_path / "test.db")
        assert storage is not None

    def test_正常系_memoryパスで初期化できる(self) -> None:
        storage = YFinanceStorage(db_path=Path(":memory:"))
        assert storage is not None

    def test_正常系_初期化時にテーブルが作成される(
        self, storage: YFinanceStorage
    ) -> None:
        tables = storage.get_table_names()
        assert "yf_daily_prices" in tables

    def test_正常系_db_pathNoneでデフォルトパスが使われる(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        env_path = str(tmp_path / "env_override.db")
        monkeypatch.setenv("PIPELINE_YFINANCE_DB_PATH", env_path)
        storage = YFinanceStorage()
        assert storage is not None


# ---------------------------------------------------------------------------
# ensure_tables tests
# ---------------------------------------------------------------------------


class TestEnsureTables:
    def test_正常系_複数回呼び出しても安全(self, storage: YFinanceStorage) -> None:
        storage.ensure_tables()
        storage.ensure_tables()
        tables = storage.get_table_names()
        assert "yf_daily_prices" in tables


# ---------------------------------------------------------------------------
# upsert tests
# ---------------------------------------------------------------------------


class TestUpsert:
    def test_正常系_レコードを挿入できる(
        self, storage: YFinanceStorage, sample_record: YFDailyPriceRecord
    ) -> None:
        count = storage.upsert([sample_record])
        assert count == 1

    def test_正常系_同一レコードを2回挿入しても1件のみ保存される(
        self, storage: YFinanceStorage, sample_record: YFDailyPriceRecord
    ) -> None:
        storage.upsert([sample_record])
        storage.upsert([sample_record])
        rows = storage.get_by_symbol_date_range("AAPL", "2026-04-03", "2026-04-03")
        assert len(rows) == 1

    def test_正常系_空リストで0件返す(self, storage: YFinanceStorage) -> None:
        count = storage.upsert([])
        assert count == 0

    def test_正常系_複数レコードを一括挿入できる(
        self, storage: YFinanceStorage
    ) -> None:
        records = [
            YFDailyPriceRecord(
                symbol="AAPL",
                date="2026-04-01",
                open=170.0,
                high=175.0,
                low=169.0,
                close=173.0,
                adjusted_close=173.0,
                volume=50_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
            YFDailyPriceRecord(
                symbol="AAPL",
                date="2026-04-02",
                open=171.0,
                high=176.0,
                low=170.0,
                close=174.0,
                adjusted_close=174.0,
                volume=45_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
        ]
        count = storage.upsert(records)
        assert count == 2

    def test_正常系_adjusted_closeがNoneでも挿入できる(
        self, storage: YFinanceStorage
    ) -> None:
        record = YFDailyPriceRecord(
            symbol="AAPL",
            date="2026-04-03",
            open=170.0,
            high=175.0,
            low=169.0,
            close=173.0,
            adjusted_close=None,
            volume=50_000_000,
            fetched_at="2026-04-03T20:00:00",
        )
        count = storage.upsert([record])
        assert count == 1


# ---------------------------------------------------------------------------
# get_latest_date tests
# ---------------------------------------------------------------------------


class TestGetLatestDate:
    def test_正常系_データがある場合に最新日付を返す(
        self, storage: YFinanceStorage
    ) -> None:
        records = [
            YFDailyPriceRecord(
                symbol="AAPL",
                date="2026-04-01",
                open=170.0,
                high=175.0,
                low=169.0,
                close=173.0,
                adjusted_close=173.0,
                volume=50_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
            YFDailyPriceRecord(
                symbol="AAPL",
                date="2026-04-03",
                open=171.0,
                high=176.0,
                low=170.0,
                close=174.0,
                adjusted_close=174.0,
                volume=45_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
        ]
        storage.upsert(records)
        latest = storage.get_latest_date("AAPL")
        assert latest == "2026-04-03"

    def test_正常系_データなしでNoneを返す(self, storage: YFinanceStorage) -> None:
        latest = storage.get_latest_date("AAPL")
        assert latest is None

    def test_正常系_他の銘柄のデータには影響されない(
        self, storage: YFinanceStorage
    ) -> None:
        records = [
            YFDailyPriceRecord(
                symbol="MSFT",
                date="2026-04-05",
                open=300.0,
                high=305.0,
                low=299.0,
                close=302.0,
                adjusted_close=302.0,
                volume=20_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
        ]
        storage.upsert(records)
        latest = storage.get_latest_date("AAPL")
        assert latest is None


# ---------------------------------------------------------------------------
# get_by_symbol_date_range tests
# ---------------------------------------------------------------------------


class TestGetBySymbolDateRange:
    def test_正常系_銘柄と日付範囲でレコードを取得できる(
        self, storage: YFinanceStorage
    ) -> None:
        records = [
            YFDailyPriceRecord(
                symbol="AAPL",
                date="2026-03-31",
                open=168.0,
                high=172.0,
                low=167.0,
                close=170.0,
                adjusted_close=170.0,
                volume=48_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
            YFDailyPriceRecord(
                symbol="AAPL",
                date="2026-04-01",
                open=170.0,
                high=175.0,
                low=169.0,
                close=173.0,
                adjusted_close=173.0,
                volume=50_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
            YFDailyPriceRecord(
                symbol="AAPL",
                date="2026-04-03",
                open=171.0,
                high=176.0,
                low=170.0,
                close=174.0,
                adjusted_close=174.0,
                volume=45_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
        ]
        storage.upsert(records)
        rows = storage.get_by_symbol_date_range("AAPL", "2026-04-01", "2026-04-03")
        assert len(rows) == 2

    def test_正常系_データなしで空リストを返す(self, storage: YFinanceStorage) -> None:
        rows = storage.get_by_symbol_date_range("AAPL", "2026-04-01", "2026-04-03")
        assert rows == []

    def test_正常系_他の銘柄のデータは返されない(
        self, storage: YFinanceStorage
    ) -> None:
        records = [
            YFDailyPriceRecord(
                symbol="AAPL",
                date="2026-04-01",
                open=170.0,
                high=175.0,
                low=169.0,
                close=173.0,
                adjusted_close=173.0,
                volume=50_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
            YFDailyPriceRecord(
                symbol="MSFT",
                date="2026-04-01",
                open=300.0,
                high=305.0,
                low=299.0,
                close=302.0,
                adjusted_close=302.0,
                volume=20_000_000,
                fetched_at="2026-04-03T20:00:00",
            ),
        ]
        storage.upsert(records)
        rows = storage.get_by_symbol_date_range("AAPL", "2026-04-01", "2026-04-01")
        assert len(rows) == 1
        assert dict(rows[0])["symbol"] == "AAPL"


# ---------------------------------------------------------------------------
# StorageError wrapping tests
# ---------------------------------------------------------------------------


class TestStorageError:
    def test_異常系_無効なdb_pathでStorageErrorが発生する(self) -> None:
        from market.pipeline.errors import StorageError

        with pytest.raises(StorageError):
            YFinanceStorage(db_path=Path("/nonexistent_root/nested/very/deep/test.db"))

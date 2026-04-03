"""Unit tests for market.pipeline.storage_sec.SecEdgarStorage."""

from __future__ import annotations

from pathlib import Path

import pytest

from market.pipeline.models import FinancialStatementRecord
from market.pipeline.storage_sec import SecEdgarStorage

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def storage(tmp_path: Path) -> SecEdgarStorage:
    """Create a SecEdgarStorage backed by a temp file DB."""
    return SecEdgarStorage(db_path=tmp_path / "sec_test.db")


@pytest.fixture()
def income_record() -> FinancialStatementRecord:
    return FinancialStatementRecord(
        symbol="AAPL",
        fiscal_date_ending="2025-09-30",
        statement_type="income",
        report_type="annual",
        revenue=391_035_000_000.0,
        net_income=93_736_000_000.0,
        fetched_at="2026-04-03T10:00:00",
    )


@pytest.fixture()
def balance_record() -> FinancialStatementRecord:
    return FinancialStatementRecord(
        symbol="AAPL",
        fiscal_date_ending="2025-09-30",
        statement_type="balance_sheet",
        report_type="annual",
        total_assets=352_583_000_000.0,
        total_liabilities=308_030_000_000.0,
        fetched_at="2026-04-03T10:00:00",
    )


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


class TestSecEdgarStorageInit:
    def test_正常系_tmp_pathで初期化できる(self, tmp_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_path / "test.db")
        assert storage is not None

    def test_正常系_memoryパスで初期化できる(self) -> None:
        storage = SecEdgarStorage(db_path=Path(":memory:"))
        assert storage is not None

    def test_正常系_初期化時にテーブルが作成される(
        self, storage: SecEdgarStorage
    ) -> None:
        tables = storage.get_table_names()
        assert "se_financial_statements" in tables

    def test_正常系_db_pathNoneでデフォルトパスが使われる(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        env_path = str(tmp_path / "env_override.db")
        monkeypatch.setenv("PIPELINE_SEC_EDGAR_DB_PATH", env_path)
        storage = SecEdgarStorage()
        assert storage is not None


# ---------------------------------------------------------------------------
# ensure_tables tests
# ---------------------------------------------------------------------------


class TestEnsureTables:
    def test_正常系_複数回呼び出しても安全(self, storage: SecEdgarStorage) -> None:
        storage.ensure_tables()
        storage.ensure_tables()
        tables = storage.get_table_names()
        assert "se_financial_statements" in tables


# ---------------------------------------------------------------------------
# upsert tests
# ---------------------------------------------------------------------------


class TestUpsert:
    def test_正常系_レコードを挿入できる(
        self, storage: SecEdgarStorage, income_record: FinancialStatementRecord
    ) -> None:
        count = storage.upsert([income_record])
        assert count == 1

    def test_正常系_PRIMARY_KEYで重複時にREPLACEされる(
        self, storage: SecEdgarStorage, income_record: FinancialStatementRecord
    ) -> None:
        storage.upsert([income_record])
        updated = FinancialStatementRecord(
            symbol="AAPL",
            fiscal_date_ending="2025-09-30",
            statement_type="income",
            report_type="annual",
            revenue=999_000_000_000.0,
            fetched_at="2026-04-04T10:00:00",
        )
        storage.upsert([updated])
        rows = storage.get_by_symbol("AAPL")
        assert len(rows) == 1
        assert rows[0]["revenue"] == 999_000_000_000.0

    def test_正常系_空リストで0件返す(self, storage: SecEdgarStorage) -> None:
        count = storage.upsert([])
        assert count == 0

    def test_正常系_異なるstatement_typeは別レコードとして保存される(
        self,
        storage: SecEdgarStorage,
        income_record: FinancialStatementRecord,
        balance_record: FinancialStatementRecord,
    ) -> None:
        storage.upsert([income_record, balance_record])
        rows = storage.get_by_symbol("AAPL")
        assert len(rows) == 2


# ---------------------------------------------------------------------------
# get_symbols_with_data tests
# ---------------------------------------------------------------------------


class TestGetSymbolsWithData:
    def test_正常系_データがある銘柄リストを返す(
        self, storage: SecEdgarStorage
    ) -> None:
        records = [
            FinancialStatementRecord(
                symbol="AAPL",
                fiscal_date_ending="2025-09-30",
                statement_type="income",
                report_type="annual",
                fetched_at="2026-04-03T10:00:00",
            ),
            FinancialStatementRecord(
                symbol="MSFT",
                fiscal_date_ending="2025-06-30",
                statement_type="income",
                report_type="annual",
                fetched_at="2026-04-03T10:00:00",
            ),
        ]
        storage.upsert(records)
        symbols = storage.get_symbols_with_data()
        assert set(symbols) == {"AAPL", "MSFT"}

    def test_正常系_データなしで空リストを返す(self, storage: SecEdgarStorage) -> None:
        symbols = storage.get_symbols_with_data()
        assert symbols == []


# ---------------------------------------------------------------------------
# get_by_symbol tests
# ---------------------------------------------------------------------------


class TestGetBySymbol:
    def test_正常系_銘柄でレコードを取得できる(
        self,
        storage: SecEdgarStorage,
        income_record: FinancialStatementRecord,
        balance_record: FinancialStatementRecord,
    ) -> None:
        storage.upsert([income_record, balance_record])
        rows = storage.get_by_symbol("AAPL")
        assert len(rows) == 2

    def test_正常系_存在しない銘柄で空リストを返す(
        self, storage: SecEdgarStorage
    ) -> None:
        rows = storage.get_by_symbol("UNKOWN")
        assert rows == []

    def test_正常系_他の銘柄のデータは返されない(
        self, storage: SecEdgarStorage
    ) -> None:
        records = [
            FinancialStatementRecord(
                symbol="AAPL",
                fiscal_date_ending="2025-09-30",
                statement_type="income",
                report_type="annual",
                fetched_at="2026-04-03T10:00:00",
            ),
            FinancialStatementRecord(
                symbol="MSFT",
                fiscal_date_ending="2025-06-30",
                statement_type="income",
                report_type="annual",
                fetched_at="2026-04-03T10:00:00",
            ),
        ]
        storage.upsert(records)
        rows = storage.get_by_symbol("AAPL")
        assert all(dict(r)["symbol"] == "AAPL" for r in rows)


# ---------------------------------------------------------------------------
# get_latest_filing_date tests
# ---------------------------------------------------------------------------


class TestGetLatestFilingDate:
    def test_正常系_annual_filingの最新日付を返す(
        self, storage: SecEdgarStorage
    ) -> None:
        records = [
            FinancialStatementRecord(
                symbol="AAPL",
                fiscal_date_ending="2024-09-30",
                statement_type="income",
                report_type="annual",
                fetched_at="2026-04-03T10:00:00",
            ),
            FinancialStatementRecord(
                symbol="AAPL",
                fiscal_date_ending="2025-09-30",
                statement_type="income",
                report_type="annual",
                fetched_at="2026-04-03T10:00:00",
            ),
        ]
        storage.upsert(records)
        latest = storage.get_latest_filing_date("AAPL", "annual")
        assert latest == "2025-09-30"

    def test_正常系_データなしでNoneを返す(self, storage: SecEdgarStorage) -> None:
        latest = storage.get_latest_filing_date("AAPL", "annual")
        assert latest is None

    def test_正常系_report_typeで絞り込まれる(self, storage: SecEdgarStorage) -> None:
        records = [
            FinancialStatementRecord(
                symbol="AAPL",
                fiscal_date_ending="2025-09-30",
                statement_type="income",
                report_type="annual",
                fetched_at="2026-04-03T10:00:00",
            ),
            FinancialStatementRecord(
                symbol="AAPL",
                fiscal_date_ending="2025-12-31",
                statement_type="income",
                report_type="quarterly",
                fetched_at="2026-04-03T10:00:00",
            ),
        ]
        storage.upsert(records)
        latest_annual = storage.get_latest_filing_date("AAPL", "annual")
        assert latest_annual == "2025-09-30"
        latest_quarterly = storage.get_latest_filing_date("AAPL", "quarterly")
        assert latest_quarterly == "2025-12-31"


# ---------------------------------------------------------------------------
# StorageError wrapping tests
# ---------------------------------------------------------------------------


class TestStorageError:
    def test_異常系_無効なdb_pathでStorageErrorが発生する(self) -> None:
        from market.pipeline.errors import StorageError

        with pytest.raises(StorageError):
            SecEdgarStorage(db_path=Path("/nonexistent_root/nested/very/deep/test.db"))

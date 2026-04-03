"""Unit tests for market.pipeline.storage_sec.SecEdgarStorage.

Tests verify PRIMARY KEY idempotency (INSERT OR REPLACE semantics),
correct data retrieval, and None-handling for optional fields.
Tests use a real SQLite DB via the ``tmp_db_path`` fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market.pipeline.models import FinancialStatementRecord
from market.pipeline.storage_sec import SecEdgarStorage

# =============================================================================
# Helper factories
# =============================================================================


def _make_record(
    symbol: str = "AAPL",
    fiscal_date_ending: str = "2025-09-30",
    statement_type: str = "income",
    report_type: str = "annual",
    revenue: float | None = 391_035_000_000.0,
    net_income: float | None = 93_736_000_000.0,
    total_assets: float | None = None,
    total_liabilities: float | None = None,
    operating_cashflow: float | None = None,
    fetched_at: str = "2026-04-03T10:00:00+00:00",
) -> FinancialStatementRecord:
    return FinancialStatementRecord(
        symbol=symbol,
        fiscal_date_ending=fiscal_date_ending,
        statement_type=statement_type,
        report_type=report_type,
        revenue=revenue,
        net_income=net_income,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        operating_cashflow=operating_cashflow,
        fetched_at=fetched_at,
    )


# =============================================================================
# Initialization tests
# =============================================================================


class TestSecEdgarStorageInit:
    """Tests for SecEdgarStorage initialization."""

    def test_正常系_インメモリDBで初期化できる(self) -> None:
        storage = SecEdgarStorage(db_path=Path(":memory:"))
        assert "se_financial_statements" in storage.get_table_names()

    def test_正常系_tempfileパスで初期化できる(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        assert "se_financial_statements" in storage.get_table_names()

    def test_正常系_ensure_tablesを複数回呼べる(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        storage.ensure_tables()
        storage.ensure_tables()


# =============================================================================
# upsert tests (PRIMARY KEY idempotency & REPLACE behavior)
# =============================================================================


class TestSecEdgarStorageUpsert:
    """Tests for SecEdgarStorage.upsert() with focus on PK idempotency."""

    def test_正常系_レコードをupsertできる(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        record = _make_record()
        result = storage.upsert([record])
        assert result == 1

    def test_正常系_複数レコードをupsertできる(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        records = [
            _make_record("AAPL", "2025-09-30", "income", "annual"),
            _make_record("AAPL", "2025-06-30", "income", "quarterly"),
            _make_record("MSFT", "2025-06-30", "balance_sheet", "annual"),
        ]
        result = storage.upsert(records)
        assert result == 3

    def test_正常系_空リストはno_op(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        result = storage.upsert([])
        assert result == 0

    def test_正常系_同一PKの重複upsertはREPLACEされる(self, tmp_db_path: Path) -> None:
        """PRIMARY KEY (symbol, fiscal_date_ending, statement_type, report_type) の
        重複レコードは INSERT OR REPLACE で更新されることを確認する。
        """
        storage = SecEdgarStorage(db_path=tmp_db_path)
        record1 = _make_record(revenue=391_035_000_000.0)
        storage.upsert([record1])
        # Same PK, different revenue
        record2 = _make_record(revenue=400_000_000_000.0)
        storage.upsert([record2])
        rows = storage.get_by_symbol("AAPL")
        # Should still be just 1 row (not duplicated)
        assert len(rows) == 1
        assert rows[0]["revenue"] == pytest.approx(400_000_000_000.0)

    def test_正常系_異なるstatement_typeは別レコードとして保存(
        self, tmp_db_path: Path
    ) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        records = [
            _make_record("AAPL", "2025-09-30", "income", "annual"),
            _make_record("AAPL", "2025-09-30", "balance_sheet", "annual"),
            _make_record("AAPL", "2025-09-30", "cash_flow", "annual"),
        ]
        storage.upsert(records)
        rows = storage.get_by_symbol("AAPL")
        assert len(rows) == 3

    def test_正常系_Noneフィールドを含むレコードをupsertできる(
        self, tmp_db_path: Path
    ) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        record = _make_record(revenue=None, net_income=None)
        result = storage.upsert([record])
        assert result == 1


# =============================================================================
# get_by_symbol tests
# =============================================================================


class TestSecEdgarStorageGetBySymbol:
    """Tests for SecEdgarStorage.get_by_symbol()."""

    def test_正常系_シンボルのレコードを取得できる(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record("AAPL", "2025-09-30"),
                _make_record("MSFT", "2025-06-30"),
            ]
        )
        rows = storage.get_by_symbol("AAPL")
        assert len(rows) == 1
        assert rows[0]["symbol"] == "AAPL"

    def test_正常系_データのないシンボルは空リストを返す(
        self, tmp_db_path: Path
    ) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        rows = storage.get_by_symbol("NVDA")
        assert rows == []


# =============================================================================
# get_symbols_with_data tests
# =============================================================================


class TestSecEdgarStorageGetSymbolsWithData:
    """Tests for SecEdgarStorage.get_symbols_with_data()."""

    def test_正常系_データのあるシンボル一覧を取得できる(
        self, tmp_db_path: Path
    ) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record("AAPL"),
                _make_record("MSFT", "2025-06-30"),
            ]
        )
        symbols = storage.get_symbols_with_data()
        assert set(symbols) == {"AAPL", "MSFT"}

    def test_正常系_空テーブルは空リストを返す(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        assert storage.get_symbols_with_data() == []


# =============================================================================
# get_latest_filing_date tests
# =============================================================================


class TestSecEdgarStorageGetLatestFilingDate:
    """Tests for SecEdgarStorage.get_latest_filing_date()."""

    def test_正常系_最新のfiscal_date_endingを返す(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record("AAPL", "2024-09-30", report_type="annual"),
                _make_record("AAPL", "2025-09-30", report_type="annual"),
            ]
        )
        latest = storage.get_latest_filing_date("AAPL", "annual")
        assert latest == "2025-09-30"

    def test_正常系_データのないシンボルはNoneを返す(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        assert storage.get_latest_filing_date("NVDA", "annual") is None

    def test_正常系_filing_typeでフィルタされる(self, tmp_db_path: Path) -> None:
        storage = SecEdgarStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record("AAPL", "2025-09-30", report_type="annual"),
                _make_record("AAPL", "2025-06-30", report_type="quarterly"),
            ]
        )
        annual = storage.get_latest_filing_date("AAPL", "annual")
        quarterly = storage.get_latest_filing_date("AAPL", "quarterly")
        assert annual == "2025-09-30"
        assert quarterly == "2025-06-30"

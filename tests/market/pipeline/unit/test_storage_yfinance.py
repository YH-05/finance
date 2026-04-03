"""Unit tests for market.pipeline.storage_yfinance.YFinanceStorage.

Tests verify upsert idempotency, get_latest_date() None-case (no prior data),
and date range queries. Tests use a real SQLite DB via ``tmp_db_path``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market.pipeline.models import YFDailyPriceRecord
from market.pipeline.storage_yfinance import YFinanceStorage

# =============================================================================
# Helper factories
# =============================================================================


def _make_record(
    symbol: str = "AAPL",
    date: str = "2026-04-03",
    open: float = 170.0,
    high: float = 175.0,
    low: float = 169.0,
    close: float = 173.0,
    adjusted_close: float | None = 173.0,
    volume: int = 50_000_000,
    fetched_at: str = "2026-04-03T20:00:00+00:00",
) -> YFDailyPriceRecord:
    return YFDailyPriceRecord(
        symbol=symbol,
        date=date,
        open=open,
        high=high,
        low=low,
        close=close,
        adjusted_close=adjusted_close,
        volume=volume,
        fetched_at=fetched_at,
    )


# =============================================================================
# Initialization tests
# =============================================================================


class TestYFinanceStorageInit:
    """Tests for YFinanceStorage initialization."""

    def test_正常系_インメモリDBで初期化できる(self) -> None:
        storage = YFinanceStorage(db_path=Path(":memory:"))
        assert "yf_daily_prices" in storage.get_table_names()

    def test_正常系_tempfileパスで初期化できる(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        assert "yf_daily_prices" in storage.get_table_names()

    def test_正常系_ensure_tablesを複数回呼べる(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        storage.ensure_tables()
        storage.ensure_tables()


# =============================================================================
# upsert tests
# =============================================================================


class TestYFinanceStorageUpsert:
    """Tests for YFinanceStorage.upsert()."""

    def test_正常系_レコードをupsertできる(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        record = _make_record()
        result = storage.upsert([record])
        assert result == 1

    def test_正常系_複数レコードをupsertできる(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        records = [
            _make_record("AAPL", "2026-04-01"),
            _make_record("AAPL", "2026-04-02"),
            _make_record("MSFT", "2026-04-01"),
        ]
        result = storage.upsert(records)
        assert result == 3

    def test_正常系_空リストはno_op(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        result = storage.upsert([])
        assert result == 0

    def test_正常系_同一PKの重複upsertはREPLACEされる(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        record1 = _make_record(close=173.0)
        storage.upsert([record1])
        record2 = _make_record(close=175.0)
        storage.upsert([record2])
        rows = storage.get_by_symbol_date_range("AAPL", "2026-04-03", "2026-04-03")
        assert len(rows) == 1
        assert rows[0]["close"] == pytest.approx(175.0)

    def test_正常系_adjusted_close_Noneのレコードをupsertできる(
        self, tmp_db_path: Path
    ) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        record = _make_record(adjusted_close=None)
        result = storage.upsert([record])
        assert result == 1


# =============================================================================
# get_latest_date tests (critical: None-case for incremental collection)
# =============================================================================


class TestYFinanceStorageGetLatestDate:
    """Tests for YFinanceStorage.get_latest_date()."""

    def test_正常系_データがない場合はNoneを返す(self, tmp_db_path: Path) -> None:
        """インクリメンタル収集の初回実行時にNoneが返ることを確認する."""
        storage = YFinanceStorage(db_path=tmp_db_path)
        assert storage.get_latest_date("AAPL") is None

    def test_正常系_空テーブルは全シンボルでNoneを返す(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        for symbol in ["AAPL", "MSFT", "GOOGL", "NVDA"]:
            assert storage.get_latest_date(symbol) is None

    def test_正常系_データがある場合は最新日付を返す(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record("AAPL", "2026-04-01"),
                _make_record("AAPL", "2026-04-03"),
                _make_record("AAPL", "2026-04-02"),
            ]
        )
        latest = storage.get_latest_date("AAPL")
        assert latest == "2026-04-03"

    def test_正常系_他のシンボルのデータは影響しない(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        storage.upsert([_make_record("MSFT", "2026-04-10")])
        assert storage.get_latest_date("AAPL") is None

    def test_正常系_シンボル別に最新日付が返る(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record("AAPL", "2026-04-03"),
                _make_record("MSFT", "2026-04-10"),
            ]
        )
        assert storage.get_latest_date("AAPL") == "2026-04-03"
        assert storage.get_latest_date("MSFT") == "2026-04-10"


# =============================================================================
# get_by_symbol_date_range tests
# =============================================================================


class TestYFinanceStorageGetBySymbolDateRange:
    """Tests for YFinanceStorage.get_by_symbol_date_range()."""

    def test_正常系_日付範囲内のレコードを取得できる(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        storage.upsert(
            [
                _make_record("AAPL", "2026-04-01"),
                _make_record("AAPL", "2026-04-03"),
                _make_record("AAPL", "2026-04-05"),
            ]
        )
        rows = storage.get_by_symbol_date_range("AAPL", "2026-04-01", "2026-04-03")
        assert len(rows) == 2
        dates = [row["date"] for row in rows]
        assert "2026-04-01" in dates
        assert "2026-04-03" in dates

    def test_正常系_範囲外のレコードは含まれない(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        storage.upsert([_make_record("AAPL", "2026-04-01")])
        rows = storage.get_by_symbol_date_range("AAPL", "2026-05-01", "2026-05-31")
        assert rows == []

    def test_正常系_空テーブルは空リストを返す(self, tmp_db_path: Path) -> None:
        storage = YFinanceStorage(db_path=tmp_db_path)
        rows = storage.get_by_symbol_date_range("AAPL", "2026-01-01", "2026-12-31")
        assert rows == []

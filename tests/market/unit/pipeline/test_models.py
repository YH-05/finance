"""Unit tests for market.pipeline.models."""

import dataclasses

import pytest

from market.pipeline.models import (
    EarningsCalendarRecord,
    FinancialStatementRecord,
    PhaseResult,
    PipelineResult,
    QueueEntry,
    YFDailyPriceRecord,
)


class TestEarningsCalendarRecord:
    def test_正常系_必須フィールドのみで生成できる(self) -> None:
        record = EarningsCalendarRecord(
            symbol="AAPL",
            report_date="2026-04-30",
            fetched_at="2026-04-03T10:00:00",
        )
        assert record.symbol == "AAPL"
        assert record.report_date == "2026-04-30"
        assert record.eps_estimate is None
        assert record.report_time is None
        assert record.fiscal_quarter_ending is None

    def test_正常系_全フィールドで生成できる(self) -> None:
        record = EarningsCalendarRecord(
            symbol="AAPL",
            report_date="2026-04-30",
            eps_estimate=1.5,
            report_time="after_close",
            fiscal_quarter_ending="2026-03-31",
            fetched_at="2026-04-03T10:00:00",
        )
        assert record.eps_estimate == 1.5
        assert record.report_time == "after_close"

    def test_正常系_frozenでイミュータブルである(self) -> None:
        record = EarningsCalendarRecord(
            symbol="AAPL",
            report_date="2026-04-30",
            fetched_at="2026-04-03T10:00:00",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.symbol = "MSFT"  # type: ignore[misc]

    def test_正常系_frozen_dataclassである(self) -> None:
        assert dataclasses.is_dataclass(EarningsCalendarRecord)


class TestQueueEntry:
    def test_正常系_必須フィールドで生成できる(self) -> None:
        entry = QueueEntry(
            symbol="AAPL",
            earnings_date="2026-04-30",
            source="nasdaq",
            status="pending",
            priority=0,
            attempts=0,
            created_at="2026-04-03T09:00:00",
        )
        assert entry.symbol == "AAPL"
        assert entry.earnings_date == "2026-04-30"
        assert entry.source == "nasdaq"
        assert entry.status == "pending"
        assert entry.priority == 0
        assert entry.attempts == 0
        assert entry.error_message is None
        assert entry.updated_at is None

    def test_正常系_frozenでイミュータブルである(self) -> None:
        entry = QueueEntry(
            symbol="AAPL",
            earnings_date="2026-04-30",
            source="nasdaq",
            status="pending",
            priority=0,
            attempts=0,
            created_at="2026-04-03T09:00:00",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            entry.status = "completed"  # type: ignore[misc]


class TestFinancialStatementRecord:
    def test_正常系_必須フィールドで生成できる(self) -> None:
        record = FinancialStatementRecord(
            symbol="AAPL",
            fiscal_date_ending="2025-09-30",
            statement_type="income",
            report_type="annual",
            fetched_at="2026-04-03T10:00:00",
        )
        assert record.statement_type == "income"
        assert record.report_type == "annual"
        assert record.revenue is None
        assert record.net_income is None

    def test_正常系_frozenでイミュータブルである(self) -> None:
        record = FinancialStatementRecord(
            symbol="AAPL",
            fiscal_date_ending="2025-09-30",
            statement_type="income",
            report_type="annual",
            fetched_at="2026-04-03T10:00:00",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.revenue = 100.0  # type: ignore[misc]


class TestYFDailyPriceRecord:
    def test_正常系_全フィールドで生成できる(self) -> None:
        record = YFDailyPriceRecord(
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
        assert record.symbol == "AAPL"
        assert record.close == 173.0
        assert record.volume == 50_000_000

    def test_正常系_adjusted_closeがNoneでも生成できる(self) -> None:
        record = YFDailyPriceRecord(
            symbol="AAPL",
            date="2026-04-03",
            open=170.0,
            high=175.0,
            low=169.0,
            close=173.0,
            adjusted_close=None,
            volume=50_000_000,
        )
        assert record.adjusted_close is None

    def test_正常系_frozenでイミュータブルである(self) -> None:
        record = YFDailyPriceRecord(
            symbol="AAPL",
            date="2026-04-03",
            open=170.0,
            high=175.0,
            low=169.0,
            close=173.0,
            adjusted_close=173.0,
            volume=50_000_000,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.close = 200.0  # type: ignore[misc]


class TestPhaseResult:
    def test_正常系_全フィールドで生成できる(self) -> None:
        result = PhaseResult(
            phase=1,
            success_count=100,
            fail_count=2,
            skip_count=5,
            duration_sec=12.3,
            errors=["AAPL: rate limit"],
        )
        assert result.phase == 1
        assert result.success_count == 100
        assert result.errors == ["AAPL: rate limit"]

    def test_正常系_errorsのデフォルトが空リストである(self) -> None:
        result = PhaseResult(
            phase=1,
            success_count=0,
            fail_count=0,
            skip_count=0,
            duration_sec=0.0,
        )
        assert result.errors == []

    def test_正常系_frozenでイミュータブルである(self) -> None:
        result = PhaseResult(
            phase=1,
            success_count=0,
            fail_count=0,
            skip_count=0,
            duration_sec=0.0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.success_count = 999  # type: ignore[misc]


class TestPipelineResult:
    def test_正常系_全フェーズがNoneで生成できる(self) -> None:
        result = PipelineResult(
            phase1=None,
            phase2=None,
            phase3=None,
            phase4=None,
            total_duration_sec=0.0,
        )
        assert result.phase1 is None
        assert result.total_duration_sec == 0.0

    def test_正常系_PhaseResultを含めて生成できる(self) -> None:
        p1 = PhaseResult(
            phase=1, success_count=50, fail_count=0, skip_count=0, duration_sec=5.0
        )
        result = PipelineResult(
            phase1=p1,
            phase2=None,
            phase3=None,
            phase4=None,
            total_duration_sec=5.0,
        )
        assert result.phase1 is p1
        assert result.phase1 is not None
        assert result.phase1.success_count == 50

    def test_正常系_frozenでイミュータブルである(self) -> None:
        result = PipelineResult(
            phase1=None,
            phase2=None,
            phase3=None,
            phase4=None,
            total_duration_sec=0.0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.total_duration_sec = 99.9  # type: ignore[misc]

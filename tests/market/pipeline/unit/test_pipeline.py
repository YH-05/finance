"""Unit tests for market.pipeline.pipeline.EarningsPipeline.

All collectors (NasdaqCalendarCollector, AlphaVantageCollector,
SecEdgarCollector, YFinanceCollector) are replaced with MagicMocks.
The CollectionQueue is also injected as a MagicMock.

Note: Collectors are imported lazily inside each run_phase*() method body.
We patch them in their source modules (e.g. market.pipeline.collector_nasdaq)
so that the lazy `from ... import` picks up the mock.

Tests verify:
- Pipeline initialization
- Correct phase execution and result aggregation
- skip_phases behavior
- get_status() output
- Per-phase error handling
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from market.pipeline.models import PhaseResult, PipelineResult
from market.pipeline.pipeline import EarningsPipeline

# =============================================================================
# Helper
# =============================================================================


def _make_phase_result(
    phase: int,
    success_count: int = 5,
    fail_count: int = 0,
    skip_count: int = 0,
    duration_sec: float = 0.1,
    errors: list[str] | None = None,
) -> PhaseResult:
    return PhaseResult(
        phase=phase,
        success_count=success_count,
        fail_count=fail_count,
        skip_count=skip_count,
        duration_sec=duration_sec,
        errors=errors or [],
    )


# =============================================================================
# Initialization tests
# =============================================================================


class TestEarningsPipelineInit:
    """Tests for EarningsPipeline initialization."""

    def test_正常系_デフォルト値で初期化できる(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        assert pipeline is not None

    def test_正常系_カスタムav_daily_budgetで初期化できる(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(av_daily_budget=10, queue=mock_collection_queue)
        status = pipeline.get_status()
        assert status["av_daily_budget"] == 10


# =============================================================================
# Phase 1 tests (NASDAQ calendar collection)
# =============================================================================


class TestEarningsPipelinePhase1:
    """Tests for EarningsPipeline.run_phase1().

    NasdaqCalendarCollector is lazily imported inside run_phase1().
    Patch it in its source module so the lazy import resolves to the mock.
    """

    def test_正常系_Phase1が正常に実行される(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        mock_collector = MagicMock()
        mock_collector.collect_recent.return_value = {
            "dates_collected": 15,
            "records_upserted": 50,
            "symbols_enqueued": 200,
            "errors": [],
        }

        with patch(
            "market.pipeline.collector_nasdaq.NasdaqCalendarCollector",
        ) as MockCollector:
            MockCollector.return_value = mock_collector
            result = pipeline.run_phase1(days_back=7, days_forward=7)

        assert isinstance(result, PhaseResult)
        assert result.phase == 1
        assert result.success_count == 50
        assert result.errors == []

    def test_正常系_Phase1でエラーが発生した場合はPhaseResultに記録(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(queue=mock_collection_queue)

        with patch(
            "market.pipeline.collector_nasdaq.NasdaqCalendarCollector",
            side_effect=Exception("Import error"),
        ):
            result = pipeline.run_phase1()

        assert result.phase == 1
        assert len(result.errors) > 0


# =============================================================================
# Phase 2 tests (Alpha Vantage queue processing)
# =============================================================================


class TestEarningsPipelinePhase2:
    """Tests for EarningsPipeline.run_phase2().

    AlphaVantageCollector is lazily imported inside run_phase2().
    Patch it in the alphavantage collector module.
    """

    def test_正常系_キューが空の場合はPhase2は何も処理しない(
        self, mock_collection_queue: MagicMock
    ) -> None:
        mock_collection_queue.get_pending.return_value = []
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        mock_av = MagicMock()

        with patch(
            "market.alphavantage.collector.AlphaVantageCollector",
        ) as MockCollector:
            MockCollector.return_value = mock_av
            result = pipeline.run_phase2()

        assert result.phase == 2
        assert result.success_count == 0
        assert result.errors == []

    def test_正常系_av_earningsエントリが正常に処理される(
        self, mock_collection_queue: MagicMock
    ) -> None:
        mock_entry = MagicMock()
        mock_entry.symbol = "AAPL"
        mock_entry.earnings_date = "2026-04-30"
        mock_entry.source = "av_earnings"

        def get_pending_side_effect(source: str, **kwargs: object) -> list:
            if source == "av_earnings":
                return [mock_entry]
            return []

        mock_collection_queue.get_pending.side_effect = get_pending_side_effect

        mock_av_result = MagicMock()
        mock_av_result.success = True
        mock_av_result.error_message = None
        mock_av_collector = MagicMock()
        mock_av_collector.collect_earnings.return_value = mock_av_result

        pipeline = EarningsPipeline(queue=mock_collection_queue)

        with patch(
            "market.alphavantage.collector.AlphaVantageCollector",
        ) as MockCollector:
            MockCollector.return_value = mock_av_collector
            result = pipeline.run_phase2()

        assert result.success_count == 1
        mock_collection_queue.mark_completed.assert_called_once_with(
            "AAPL", "2026-04-30", "av_earnings"
        )


# =============================================================================
# Phase 3 tests (SEC EDGAR)
# =============================================================================


class TestEarningsPipelinePhase3:
    """Tests for EarningsPipeline.run_phase3().

    SecEdgarCollector is lazily imported inside run_phase3().
    Patch it in its source module.
    """

    def test_正常系_キューが空の場合はPhase3は何も処理しない(
        self, mock_collection_queue: MagicMock
    ) -> None:
        mock_collection_queue.get_pending.return_value = []
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        mock_sec = MagicMock()

        with patch(
            "market.pipeline.collector_sec.SecEdgarCollector",
        ) as MockCollector:
            MockCollector.return_value = mock_sec
            result = pipeline.run_phase3()

        assert result.phase == 3
        assert result.success_count == 0

    def test_正常系_sec_edgarエントリが正常に処理される(
        self, mock_collection_queue: MagicMock
    ) -> None:
        mock_entry = MagicMock()
        mock_entry.symbol = "AAPL"
        mock_entry.earnings_date = "2026-04-30"
        mock_entry.source = "sec_edgar"
        mock_collection_queue.get_pending.return_value = [mock_entry]

        mock_sec_collector = MagicMock()
        mock_sec_collector.collect_symbol.return_value = {
            "symbol": "AAPL",
            "records_upserted": 6,
            "errors": [],
        }

        pipeline = EarningsPipeline(queue=mock_collection_queue)

        with patch(
            "market.pipeline.collector_sec.SecEdgarCollector",
        ) as MockCollector:
            MockCollector.return_value = mock_sec_collector
            result = pipeline.run_phase3()

        assert result.success_count == 1
        mock_collection_queue.mark_completed.assert_called_once_with(
            "AAPL", "2026-04-30", "sec_edgar"
        )


# =============================================================================
# Phase 4 tests (Yahoo Finance)
# =============================================================================


class TestEarningsPipelinePhase4:
    """Tests for EarningsPipeline.run_phase4().

    YFinanceCollector is lazily imported inside run_phase4().
    Patch it in its source module.
    """

    def test_正常系_キューが空の場合はPhase4は何も処理しない(
        self, mock_collection_queue: MagicMock
    ) -> None:
        mock_collection_queue.get_pending.return_value = []
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        mock_yf = MagicMock()

        with patch(
            "market.pipeline.collector_yfinance.YFinanceCollector",
        ) as MockCollector:
            MockCollector.return_value = mock_yf
            result = pipeline.run_phase4()

        assert result.phase == 4
        assert result.success_count == 0

    def test_正常系_yfinanceエントリが正常に処理される(
        self, mock_collection_queue: MagicMock
    ) -> None:
        mock_entry = MagicMock()
        mock_entry.symbol = "AAPL"
        mock_entry.earnings_date = "2026-04-30"
        mock_entry.source = "yfinance"
        mock_collection_queue.get_pending.return_value = [mock_entry]

        mock_yf_collector = MagicMock()
        mock_yf_collector.collect_daily.return_value = {
            "symbol": "AAPL",
            "records_upserted": 30,
            "start_date": "2026-01-01",
            "errors": [],
        }

        pipeline = EarningsPipeline(queue=mock_collection_queue)

        with patch(
            "market.pipeline.collector_yfinance.YFinanceCollector",
        ) as MockCollector:
            MockCollector.return_value = mock_yf_collector
            result = pipeline.run_phase4()

        assert result.success_count == 1
        mock_collection_queue.mark_completed.assert_called_once_with(
            "AAPL", "2026-04-30", "yfinance"
        )


# =============================================================================
# run() orchestration tests
# =============================================================================


class TestEarningsPipelineRun:
    """Tests for EarningsPipeline.run() full pipeline orchestration."""

    def _mock_all_phases(
        self, pipeline: EarningsPipeline
    ) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
        """Patch all 4 phase methods and return them."""
        p1 = MagicMock(return_value=_make_phase_result(1))
        p2 = MagicMock(return_value=_make_phase_result(2))
        p3 = MagicMock(return_value=_make_phase_result(3))
        p4 = MagicMock(return_value=_make_phase_result(4))
        pipeline.run_phase1 = p1
        pipeline.run_phase2 = p2
        pipeline.run_phase3 = p3
        pipeline.run_phase4 = p4
        return p1, p2, p3, p4

    def test_正常系_全フェーズが実行される(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        p1, p2, p3, p4 = self._mock_all_phases(pipeline)
        result = pipeline.run()
        assert isinstance(result, PipelineResult)
        p1.assert_called_once()
        p2.assert_called_once()
        p3.assert_called_once()
        p4.assert_called_once()

    def test_正常系_skip_phasesで特定フェーズをスキップできる(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        p1, p2, p3, p4 = self._mock_all_phases(pipeline)
        result = pipeline.run(skip_phases=[2, 3])
        p1.assert_called_once()
        p2.assert_not_called()
        p3.assert_not_called()
        p4.assert_called_once()
        assert result.phase2 is None
        assert result.phase3 is None

    def test_正常系_全フェーズをスキップできる(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        p1, p2, p3, p4 = self._mock_all_phases(pipeline)
        result = pipeline.run(skip_phases=[1, 2, 3, 4])
        p1.assert_not_called()
        p2.assert_not_called()
        p3.assert_not_called()
        p4.assert_not_called()
        assert result.phase1 is None
        assert result.phase4 is None

    def test_正常系_total_duration_secが0以上(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        self._mock_all_phases(pipeline)
        result = pipeline.run()
        assert result.total_duration_sec >= 0.0

    def test_正常系_days_back_days_forwardがPhase1に渡される(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        p1, _p2, _p3, _p4 = self._mock_all_phases(pipeline)
        pipeline.run(days_back=3, days_forward=5)
        p1.assert_called_once_with(days_back=3, days_forward=5)


# =============================================================================
# get_status tests
# =============================================================================


class TestEarningsPipelineGetStatus:
    """Tests for EarningsPipeline.get_status()."""

    def test_正常系_statusにqueue_statsが含まれる(
        self, mock_collection_queue: MagicMock
    ) -> None:
        mock_collection_queue.get_stats.return_value = {"nasdaq": {"pending": 5}}
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        status = pipeline.get_status()
        assert "queue_stats" in status
        assert status["queue_stats"] == {"nasdaq": {"pending": 5}}

    def test_正常系_statusにav_daily_budgetが含まれる(
        self, mock_collection_queue: MagicMock
    ) -> None:
        pipeline = EarningsPipeline(av_daily_budget=25, queue=mock_collection_queue)
        status = pipeline.get_status()
        assert status["av_daily_budget"] == 25

    def test_正常系_get_statsエラー時もstatusを返す(
        self, mock_collection_queue: MagicMock
    ) -> None:
        mock_collection_queue.get_stats.side_effect = Exception("DB error")
        pipeline = EarningsPipeline(queue=mock_collection_queue)
        status = pipeline.get_status()
        assert "error" in status
        assert status["queue_stats"] == {}

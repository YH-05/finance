"""Unit tests for EarningsPipeline (pipeline.py).

Tests focus on orchestration logic: phase skipping, budget splitting,
queue delegation, and error resilience. All external collectors and the
real CollectionQueue are replaced with mocks.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from market.pipeline.models import PhaseResult, PipelineResult
from market.pipeline.pipeline import EarningsPipeline
from market.pipeline.queue import CollectionQueue

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def in_memory_queue(tmp_path: pytest.TempPathFactory) -> CollectionQueue:
    """Return a fresh CollectionQueue backed by a temporary file."""
    return CollectionQueue(db_path=tmp_path / "test_pipeline.db")  # type: ignore[operator]


@pytest.fixture()
def pipeline(in_memory_queue: CollectionQueue) -> EarningsPipeline:
    """Return an EarningsPipeline backed by an in-memory queue."""
    return EarningsPipeline(av_daily_budget=25, queue=in_memory_queue)


# ---------------------------------------------------------------------------
# Phase skip logic
# ---------------------------------------------------------------------------


class TestRunSkipPhases:
    def test_正常系_skip_phases_2_3でPhase2とPhase3がNone(
        self, pipeline: EarningsPipeline
    ) -> None:
        with (
            patch(
                "market.pipeline.pipeline.EarningsPipeline.run_phase1",
                return_value=PhaseResult(
                    phase=1,
                    success_count=5,
                    fail_count=0,
                    skip_count=0,
                    duration_sec=0.1,
                ),
            ),
            patch(
                "market.pipeline.pipeline.EarningsPipeline.run_phase4",
                return_value=PhaseResult(
                    phase=4,
                    success_count=3,
                    fail_count=0,
                    skip_count=0,
                    duration_sec=0.1,
                ),
            ),
        ):
            result = pipeline.run(skip_phases=[2, 3])

        assert result.phase1 is not None
        assert result.phase2 is None
        assert result.phase3 is None
        assert result.phase4 is not None

    def test_正常系_skip_phases_全Phase指定でPipelineResultの全フィールドがNone(
        self, pipeline: EarningsPipeline
    ) -> None:
        result = pipeline.run(skip_phases=[1, 2, 3, 4])

        assert result.phase1 is None
        assert result.phase2 is None
        assert result.phase3 is None
        assert result.phase4 is None

    def test_正常系_skip_phases_Noneで全Phase実行試みる(
        self, pipeline: EarningsPipeline
    ) -> None:
        """All phases should be attempted when skip_phases=None."""
        mock_phase = PhaseResult(
            phase=1, success_count=0, fail_count=0, skip_count=0, duration_sec=0.0
        )
        with (
            patch(
                "market.pipeline.pipeline.EarningsPipeline.run_phase1",
                return_value=mock_phase,
            ) as m1,
            patch(
                "market.pipeline.pipeline.EarningsPipeline.run_phase2",
                return_value=mock_phase,
            ) as m2,
            patch(
                "market.pipeline.pipeline.EarningsPipeline.run_phase3",
                return_value=mock_phase,
            ) as m3,
            patch(
                "market.pipeline.pipeline.EarningsPipeline.run_phase4",
                return_value=mock_phase,
            ) as m4,
        ):
            pipeline.run(skip_phases=None)

        m1.assert_called_once()
        m2.assert_called_once()
        m3.assert_called_once()
        m4.assert_called_once()

    def test_正常系_PipelineResult型が返される(
        self, pipeline: EarningsPipeline
    ) -> None:
        result = pipeline.run(skip_phases=[1, 2, 3, 4])
        assert isinstance(result, PipelineResult)

    def test_正常系_total_duration_secが非負(self, pipeline: EarningsPipeline) -> None:
        result = pipeline.run(skip_phases=[1, 2, 3, 4])
        assert result.total_duration_sec >= 0.0


# ---------------------------------------------------------------------------
# Phase 2: budget splitting
# ---------------------------------------------------------------------------


class TestRunPhase2Budget:
    def test_正常系_av_daily_budget_25で各ソースに12件ずつ取得(
        self, in_memory_queue: CollectionQueue
    ) -> None:
        """budget // 2 = 12 entries per source should be requested."""
        pipeline = EarningsPipeline(av_daily_budget=25, queue=in_memory_queue)

        captured_limits: list[tuple[str, int]] = []

        def fake_get_pending(source: str, limit: int = 100) -> list:
            captured_limits.append((source, limit))
            return []

        mock_av = MagicMock()
        with (
            patch.object(in_memory_queue, "get_pending", side_effect=fake_get_pending),
            patch(
                "market.alphavantage.collector.AlphaVantageCollector",
                return_value=mock_av,
            ),
        ):
            pipeline.run_phase2()

        # Should have called get_pending("av_earnings", 12) and ("av_overview", 12)
        assert ("av_earnings", 12) in captured_limits
        assert ("av_overview", 12) in captured_limits

    def test_正常系_av_daily_budget_1で各ソースに1件ずつ取得(
        self, in_memory_queue: CollectionQueue
    ) -> None:
        """budget=1 → max(1, 1//2)=1 per source."""
        pipeline = EarningsPipeline(av_daily_budget=1, queue=in_memory_queue)

        captured_limits: list[tuple[str, int]] = []

        def fake_get_pending(source: str, limit: int = 100) -> list:
            captured_limits.append((source, limit))
            return []

        with patch.object(in_memory_queue, "get_pending", side_effect=fake_get_pending):
            pipeline.run_phase2()

        # Each source gets at least 1
        earnings_limits = [lim for src, lim in captured_limits if src == "av_earnings"]
        overview_limits = [lim for src, lim in captured_limits if src == "av_overview"]
        assert all(lim >= 1 for lim in earnings_limits)
        assert all(lim >= 1 for lim in overview_limits)


# ---------------------------------------------------------------------------
# Phase results
# ---------------------------------------------------------------------------


class TestRunPhaseResults:
    def test_正常系_run_phase1がPhaseResult_phase_1を返す(
        self, in_memory_queue: CollectionQueue
    ) -> None:
        pipeline = EarningsPipeline(queue=in_memory_queue)

        mock_collector = MagicMock()
        mock_collector.collect_recent.return_value = {
            "records_upserted": 10,
            "records_failed": 0,
            "records_skipped": 2,
        }

        with patch(
            "market.pipeline.collector_nasdaq.NasdaqCalendarCollector",
            return_value=mock_collector,
        ):
            result = pipeline.run_phase1(days_back=7, days_forward=7)

        assert isinstance(result, PhaseResult)
        assert result.phase == 1
        assert result.success_count == 10
        assert result.skip_count == 2
        assert result.fail_count == 0

    def test_正常系_run_phase2がPhaseResult_phase_2を返す(
        self, in_memory_queue: CollectionQueue
    ) -> None:
        pipeline = EarningsPipeline(queue=in_memory_queue)
        # Lazy import: patch at the module level where it will be imported
        with patch(
            "market.alphavantage.collector.AlphaVantageCollector",
        ):
            result = pipeline.run_phase2()

        assert isinstance(result, PhaseResult)
        assert result.phase == 2

    def test_正常系_run_phase3がPhaseResult_phase_3を返す(
        self, in_memory_queue: CollectionQueue
    ) -> None:
        pipeline = EarningsPipeline(queue=in_memory_queue)
        with patch(
            "market.pipeline.collector_sec.SecEdgarCollector",
        ):
            result = pipeline.run_phase3()

        assert isinstance(result, PhaseResult)
        assert result.phase == 3

    def test_正常系_run_phase4がPhaseResult_phase_4を返す(
        self, in_memory_queue: CollectionQueue
    ) -> None:
        pipeline = EarningsPipeline(queue=in_memory_queue)
        with patch(
            "market.pipeline.collector_yfinance.YFinanceCollector",
        ):
            result = pipeline.run_phase4()

        assert isinstance(result, PhaseResult)
        assert result.phase == 4


# ---------------------------------------------------------------------------
# Error resilience
# ---------------------------------------------------------------------------


class TestRunPhaseErrorResilience:
    def test_正常系_Phase1コレクター例外でもPhaseResultが返される(
        self, pipeline: EarningsPipeline
    ) -> None:
        # Patch the lazy import inside run_phase1 by making the import raise
        mock_module = MagicMock()
        mock_module.NasdaqCalendarCollector.side_effect = RuntimeError("API down")
        with patch.dict(
            "sys.modules", {"market.pipeline.collector_nasdaq": mock_module}
        ):
            result = pipeline.run_phase1()

        assert isinstance(result, PhaseResult)
        assert result.phase == 1
        assert result.fail_count >= 1
        assert len(result.errors) >= 1

    def test_正常系_Phase2コレクター例外でもPhaseResultが返される(
        self, pipeline: EarningsPipeline
    ) -> None:
        mock_module = MagicMock()
        mock_module.AlphaVantageCollector.side_effect = RuntimeError("AV down")
        with patch.dict("sys.modules", {"market.alphavantage.collector": mock_module}):
            result = pipeline.run_phase2()

        assert isinstance(result, PhaseResult)
        assert result.phase == 2
        assert len(result.errors) >= 1


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    def test_正常系_空のDBでもクラッシュしない(
        self, pipeline: EarningsPipeline
    ) -> None:
        status = pipeline.get_status()
        assert "queue_stats" in status
        assert "av_daily_budget" in status

    def test_正常系_av_daily_budgetが設定値と一致する(
        self, in_memory_queue: CollectionQueue
    ) -> None:
        pipeline = EarningsPipeline(av_daily_budget=10, queue=in_memory_queue)
        status = pipeline.get_status()
        assert status["av_daily_budget"] == 10

    def test_正常系_queue_statsがdictを返す(self, pipeline: EarningsPipeline) -> None:
        status = pipeline.get_status()
        assert isinstance(status["queue_stats"], dict)

    def test_正常系_get_stats例外でもエラーキーが返される(
        self, in_memory_queue: CollectionQueue
    ) -> None:
        pipeline = EarningsPipeline(queue=in_memory_queue)
        with patch.object(
            in_memory_queue,
            "get_stats",
            side_effect=RuntimeError("DB error"),
        ):
            status = pipeline.get_status()

        assert "error" in status


# ---------------------------------------------------------------------------
# Import contract
# ---------------------------------------------------------------------------


class TestImportContract:
    def test_正常系_EarningsPipelineがpipeline_pyからインポートできる(
        self,
    ) -> None:
        from market.pipeline.pipeline import EarningsPipeline as EP

        assert EP is EarningsPipeline

    def test_正常系_market_pipelineパッケージからEarningsPipelineがインポートできる(
        self,
    ) -> None:
        from market.pipeline import EarningsPipeline as EP

        assert EP is EarningsPipeline

    def test_正常系_market_pipelineからPhaseResultがインポートできる(
        self,
    ) -> None:
        from market.pipeline import PhaseResult as PR

        assert PR is PhaseResult

    def test_正常系_market_pipelineからPipelineResultがインポートできる(
        self,
    ) -> None:
        from market.pipeline import PipelineResult as PR

        assert PR is PipelineResult

    def test_正常系_market_pipelineからPipelineErrorがインポートできる(
        self,
    ) -> None:
        from market.pipeline import PipelineError
        from market.pipeline.errors import PipelineError as PE

        assert PipelineError is PE

    def test_正常系_market_pipelineからCollectionQueueがインポートできる(
        self,
    ) -> None:
        from market.pipeline import CollectionQueue as CQ

        assert CQ is CollectionQueue

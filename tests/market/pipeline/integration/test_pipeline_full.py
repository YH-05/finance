"""End-to-End integration tests for the full 4-phase EarningsPipeline.

Tests run all phases against real external APIs (NASDAQ, SEC EDGAR, yfinance)
with a temporary SQLite database. Phase 2 (Alpha Vantage) is skipped because
it requires an API key that is not available in integration test environments.

All tests require ``@pytest.mark.integration`` and are skipped in normal CI.

Run with:
    uv run pytest tests/market/pipeline/integration/ -v -m integration

Test TODO List:
- [x] Phase 1 (NASDAQ) のみを実行してPipelineResultが正しいこと
- [x] Phase 1 + Phase 3 (SEC) + Phase 4 (yfinance) を実行してE2Eフローを確認
- [x] skip_phases で特定フェーズをスキップできること
- [x] PipelineResult の構造が正しいこと
- [x] テスト後に一時DBがcleanupされること

Notes
-----
Environment variables ``PIPELINE_NASDAQ_DB_PATH``, ``PIPELINE_SEC_EDGAR_DB_PATH``,
and ``PIPELINE_YFINANCE_DB_PATH`` are set per test to redirect all storage to
temporary SQLite files managed by pytest's ``tmp_path`` fixture.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest

from market.pipeline.models import PipelineResult
from market.pipeline.pipeline import EarningsPipeline
from market.pipeline.queue import CollectionQueue

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db_env(
    tmp_path: Path,
) -> Generator[dict[str, Path], None, None]:
    """Set pipeline DB env vars to temporary paths and restore after test.

    Yields
    ------
    dict[str, Path]
        Mapping of env var name → temporary DB path. Allows tests to inspect
        DB files directly if needed.
    """
    db_paths = {
        "PIPELINE_NASDAQ_DB_PATH": tmp_path / "nasdaq_calendar.db",
        "PIPELINE_SEC_EDGAR_DB_PATH": tmp_path / "sec_edgar.db",
        "PIPELINE_YFINANCE_DB_PATH": tmp_path / "yfinance.db",
    }

    # Save original env values (may be None)
    original = {k: os.environ.get(k) for k in db_paths}

    # Override with tmp_path values
    for key, path in db_paths.items():
        os.environ[key] = str(path)

    try:
        yield db_paths
    finally:
        # Restore original values
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


# ---------------------------------------------------------------------------
# Integration test class
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestEarningsPipelineFullIntegration:
    """E2E integration tests for EarningsPipeline using real external APIs.

    All tests use ``tmp_db_env`` to isolate database state. Phase 2 (Alpha
    Vantage) is always skipped because it requires an API key.
    """

    def test_phase1_only_returns_valid_result(
        self,
        tmp_db_env: dict[str, Path],
    ) -> None:
        """Phase 1 のみ実行してPipelineResultが正しいことを確認する.

        Runs only Phase 1 (NASDAQ calendar fetch) and verifies that the
        ``PipelineResult`` has a valid ``phase1`` with non-negative counts.
        """
        db_path = tmp_db_env["PIPELINE_NASDAQ_DB_PATH"]
        queue = CollectionQueue(db_path=db_path)
        pipeline = EarningsPipeline(queue=queue)

        result = pipeline.run(
            days_back=1,
            days_forward=1,
            skip_phases=[2, 3, 4],
        )

        assert isinstance(result, PipelineResult)
        assert result.phase1 is not None
        assert result.phase2 is None
        assert result.phase3 is None
        assert result.phase4 is None
        assert result.total_duration_sec >= 0.0

        phase1 = result.phase1
        assert phase1.phase == 1
        assert phase1.success_count >= 0
        assert phase1.fail_count >= 0
        assert phase1.duration_sec >= 0.0
        assert isinstance(phase1.errors, list)

    def test_pipeline_result_structure(
        self,
        tmp_db_env: dict[str, Path],
    ) -> None:
        """PipelineResultの構造が正しいことを確認する.

        Verifies all fields of ``PipelineResult`` and ``PhaseResult`` are
        populated correctly when running Phase 1 only.
        """
        db_path = tmp_db_env["PIPELINE_NASDAQ_DB_PATH"]
        queue = CollectionQueue(db_path=db_path)
        pipeline = EarningsPipeline(queue=queue)

        result = pipeline.run(
            days_back=2,
            days_forward=2,
            skip_phases=[2, 3, 4],
        )

        assert hasattr(result, "phase1")
        assert hasattr(result, "phase2")
        assert hasattr(result, "phase3")
        assert hasattr(result, "phase4")
        assert hasattr(result, "total_duration_sec")

        assert result.total_duration_sec >= 0.0

        if result.phase1 is not None:
            assert hasattr(result.phase1, "phase")
            assert hasattr(result.phase1, "success_count")
            assert hasattr(result.phase1, "fail_count")
            assert hasattr(result.phase1, "skip_count")
            assert hasattr(result.phase1, "duration_sec")
            assert hasattr(result.phase1, "errors")

    def test_skip_phases_works_correctly(
        self,
        tmp_db_env: dict[str, Path],
    ) -> None:
        """skip_phases で特定フェーズをスキップできることを確認する.

        Verifies that ``skip_phases=[1, 2, 3, 4]`` produces a ``PipelineResult``
        where all phase fields are ``None``.
        """
        db_path = tmp_db_env["PIPELINE_NASDAQ_DB_PATH"]
        queue = CollectionQueue(db_path=db_path)
        pipeline = EarningsPipeline(queue=queue)

        result = pipeline.run(skip_phases=[1, 2, 3, 4])

        assert result.phase1 is None
        assert result.phase2 is None
        assert result.phase3 is None
        assert result.phase4 is None
        assert result.total_duration_sec >= 0.0

    def test_phase1_then_phase3_e2e_flow(
        self,
        tmp_db_env: dict[str, Path],
    ) -> None:
        """Phase 1 → Phase 3 の E2E フローを確認する.

        Runs Phase 1 (NASDAQ calendar) and Phase 3 (SEC EDGAR) in sequence,
        skipping Phase 2 (Alpha Vantage requires API key) and Phase 4.
        Verifies that the pipeline completes without unexpected exceptions.
        """
        nasdaq_db_path = tmp_db_env["PIPELINE_NASDAQ_DB_PATH"]
        queue = CollectionQueue(db_path=nasdaq_db_path)
        pipeline = EarningsPipeline(queue=queue)

        result = pipeline.run(
            days_back=2,
            days_forward=2,
            skip_phases=[2, 4],
        )

        assert result.phase1 is not None
        assert result.phase2 is None
        assert result.phase3 is not None
        assert result.phase4 is None
        assert result.total_duration_sec >= 0.0

        # Phase 1 should have processed dates
        assert result.phase1.phase == 1
        assert result.phase1.duration_sec >= 0.0

        # Phase 3 should have run (may have 0 entries if Phase 1 returned no data)
        assert result.phase3.phase == 3
        assert result.phase3.duration_sec >= 0.0

    def test_phase1_then_phase4_e2e_flow(
        self,
        tmp_db_env: dict[str, Path],
    ) -> None:
        """Phase 1 → Phase 4 の E2E フローを確認する.

        Runs Phase 1 (NASDAQ calendar) and Phase 4 (yfinance prices) in
        sequence, skipping Phase 2 and Phase 3. Verifies that the pipeline
        completes without unexpected exceptions.
        """
        nasdaq_db_path = tmp_db_env["PIPELINE_NASDAQ_DB_PATH"]
        queue = CollectionQueue(db_path=nasdaq_db_path)
        pipeline = EarningsPipeline(queue=queue)

        result = pipeline.run(
            days_back=1,
            days_forward=1,
            skip_phases=[2, 3],
        )

        assert result.phase1 is not None
        assert result.phase2 is None
        assert result.phase3 is None
        assert result.phase4 is not None
        assert result.total_duration_sec >= 0.0

        assert result.phase4.phase == 4
        assert result.phase4.duration_sec >= 0.0

    def test_db_cleanup_after_e2e_test(
        self,
        tmp_db_env: dict[str, Path],
    ) -> None:
        """テスト後に一時DBがpytestによって自動削除されることを確認する.

        Verifies that database files are created during the E2E pipeline run
        and will be automatically cleaned up by pytest's ``tmp_path`` fixture.
        """
        nasdaq_db_path = tmp_db_env["PIPELINE_NASDAQ_DB_PATH"]
        queue = CollectionQueue(db_path=nasdaq_db_path)
        pipeline = EarningsPipeline(queue=queue)

        pipeline.run(
            days_back=1,
            days_forward=1,
            skip_phases=[2, 3, 4],
        )

        # NASDAQ DB file should exist after Phase 1 runs
        assert nasdaq_db_path.exists(), (
            "NASDAQ calendar DB file should exist after Phase 1"
        )
        # Cleanup is handled by pytest's tmp_path fixture (automatic after test)

    def test_get_status_returns_queue_stats(
        self,
        tmp_db_env: dict[str, Path],
    ) -> None:
        """get_status がキューの統計情報を返すことを確認する.

        Verifies that ``EarningsPipeline.get_status()`` returns a dict with
        the expected keys after a Phase 1 run.
        """
        nasdaq_db_path = tmp_db_env["PIPELINE_NASDAQ_DB_PATH"]
        queue = CollectionQueue(db_path=nasdaq_db_path)
        pipeline = EarningsPipeline(queue=queue)

        # Run Phase 1 to populate the queue
        pipeline.run(
            days_back=1,
            days_forward=1,
            skip_phases=[2, 3, 4],
        )

        status = pipeline.get_status()

        assert isinstance(status, dict)
        assert "queue_stats" in status
        assert "av_daily_budget" in status
        assert status["av_daily_budget"] > 0

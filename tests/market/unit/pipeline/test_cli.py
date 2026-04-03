"""Unit tests for the pipeline CLI (cli.py).

Tests cover argument parsing, option handling, dry-run, status, and
error paths. All pipeline execution is mocked.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from market.pipeline.cli import _build_parser, _resolve_skip_phases, main
from market.pipeline.models import PhaseResult, PipelineResult


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


class TestBuildParser:
    def test_正常系_デフォルト値が正しく設定される(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.days_back == 7
        assert args.days_forward == 7
        assert args.av_budget == 25
        assert args.phase is None
        assert args.skip_phases is None
        assert args.status is False
        assert args.reset_failed is False
        assert args.dry_run is False

    def test_正常系_days_back_と_days_forwardが設定できる(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--days-back", "3", "--days-forward", "14"])
        assert args.days_back == 3
        assert args.days_forward == 14

    def test_正常系_phaseオプションが設定できる(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--phase", "2"])
        assert args.phase == 2

    def test_正常系_skip_phasesで複数Phase指定できる(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--skip-phases", "2", "3"])
        assert args.skip_phases == [2, 3]

    def test_正常系_statusフラグが有効になる(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--status"])
        assert args.status is True

    def test_正常系_reset_failedフラグが有効になる(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--reset-failed"])
        assert args.reset_failed is True

    def test_正常系_dry_runフラグが有効になる(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_正常系_av_budgetオプションが設定できる(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["--av-budget", "10"])
        assert args.av_budget == 10


# ---------------------------------------------------------------------------
# _resolve_skip_phases helper
# ---------------------------------------------------------------------------


class TestResolveSkipPhases:
    def test_正常系_phase_1指定で2_3_4がスキップリストになる(self) -> None:
        result = _resolve_skip_phases(phase=1, skip_phases=None)
        assert sorted(result) == [2, 3, 4]  # type: ignore[arg-type]

    def test_正常系_phase_3指定で1_2_4がスキップリストになる(self) -> None:
        result = _resolve_skip_phases(phase=3, skip_phases=None)
        assert sorted(result) == [1, 2, 4]  # type: ignore[arg-type]

    def test_正常系_phase_Noneかつskip_phases_Noneでそのまま返す(self) -> None:
        result = _resolve_skip_phases(phase=None, skip_phases=None)
        assert result is None

    def test_正常系_skip_phases指定でそのまま返す(self) -> None:
        result = _resolve_skip_phases(phase=None, skip_phases=[2, 3])
        assert result == [2, 3]

    def test_異常系_phase_とskip_phases_同時指定でSystemExit(self) -> None:
        with pytest.raises(SystemExit):
            _resolve_skip_phases(phase=1, skip_phases=[2])


# ---------------------------------------------------------------------------
# main() function
# ---------------------------------------------------------------------------


def _make_pipeline_result(
    phase1_ok: int = 5,
    total_duration: float = 1.23,
) -> PipelineResult:
    """Helper to build a PipelineResult for mocking."""
    p1 = PhaseResult(
        phase=1,
        success_count=phase1_ok,
        fail_count=0,
        skip_count=0,
        duration_sec=0.5,
    )
    return PipelineResult(
        phase1=p1,
        phase2=None,
        phase3=None,
        phase4=None,
        total_duration_sec=total_duration,
    )


class TestMainStatus:
    def test_正常系_statusモードで0が返る(self, capsys: pytest.CaptureFixture) -> None:
        mock_pipeline = MagicMock()
        mock_pipeline.get_status.return_value = {
            "av_daily_budget": 25,
            "queue_stats": {},
        }
        with patch("market.pipeline.cli.EarningsPipeline", return_value=mock_pipeline):
            exit_code = main(["--status"])

        assert exit_code == 0

    def test_正常系_statusモードでJSON出力が表示される(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        mock_pipeline = MagicMock()
        mock_pipeline.get_status.return_value = {
            "av_daily_budget": 25,
            "queue_stats": {"nasdaq": {"pending": 3}},
        }
        with patch("market.pipeline.cli.EarningsPipeline", return_value=mock_pipeline):
            main(["--status"])

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["av_daily_budget"] == 25

    def test_異常系_status_例外で1が返る(self, capsys: pytest.CaptureFixture) -> None:
        with patch(
            "market.pipeline.cli.EarningsPipeline",
            side_effect=RuntimeError("DB error"),
        ):
            exit_code = main(["--status"])

        assert exit_code == 1


class TestMainResetFailed:
    def test_正常系_reset_failedモードで0が返る(
        self, capsys: pytest.CaptureFixture, tmp_path: Path
    ) -> None:
        from market.pipeline.queue import CollectionQueue

        q = CollectionQueue(db_path=tmp_path / "test.db")
        with patch("market.pipeline.cli.CollectionQueue", return_value=q):
            exit_code = main(["--reset-failed"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Reset" in captured.out

    def test_異常系_reset_failed_例外で1が返る(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        with patch(
            "market.pipeline.cli.CollectionQueue",
            side_effect=RuntimeError("Queue error"),
        ):
            exit_code = main(["--reset-failed"])

        assert exit_code == 1


class TestMainDryRun:
    def test_正常系_dry_runで0が返る(self, capsys: pytest.CaptureFixture) -> None:
        exit_code = main(["--dry-run"])
        assert exit_code == 0

    def test_正常系_dry_runでphase情報が表示される(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        main(["--dry-run"])
        captured = capsys.readouterr()
        assert "phases" in captured.out

    def test_正常系_dry_run_skip_phases_2_3でphase_1_4が表示される(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        main(["--dry-run", "--skip-phases", "2", "3"])
        captured = capsys.readouterr()
        # phases 1 and 4 should appear
        assert "1" in captured.out
        assert "4" in captured.out


class TestMainNormalRun:
    def test_正常系_通常実行で0が返る(self, capsys: pytest.CaptureFixture) -> None:
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = _make_pipeline_result()
        with patch("market.pipeline.cli.EarningsPipeline", return_value=mock_pipeline):
            exit_code = main([])

        assert exit_code == 0

    def test_正常系_phase_1指定でrun呼び出し時にskip_phases_2_3_4が渡される(
        self,
    ) -> None:
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = _make_pipeline_result()
        with patch("market.pipeline.cli.EarningsPipeline", return_value=mock_pipeline):
            main(["--phase", "1"])

        call_kwargs = mock_pipeline.run.call_args[1]
        assert sorted(call_kwargs["skip_phases"]) == [2, 3, 4]

    def test_正常系_days_back_days_forwardがrunに渡される(self) -> None:
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = _make_pipeline_result()
        with patch("market.pipeline.cli.EarningsPipeline", return_value=mock_pipeline):
            main(["--days-back", "3", "--days-forward", "14"])

        call_kwargs = mock_pipeline.run.call_args[1]
        assert call_kwargs["days_back"] == 3
        assert call_kwargs["days_forward"] == 14

    def test_正常系_av_budgetがEarningsPipelineに渡される(self) -> None:
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = _make_pipeline_result()
        with patch(
            "market.pipeline.cli.EarningsPipeline", return_value=mock_pipeline
        ) as MockPipeline:
            main(["--av-budget", "10"])

        MockPipeline.assert_called_once_with(av_daily_budget=10)

    def test_異常系_run例外で1が返る(self, capsys: pytest.CaptureFixture) -> None:
        mock_pipeline = MagicMock()
        mock_pipeline.run.side_effect = RuntimeError("Pipeline crash")
        with patch("market.pipeline.cli.EarningsPipeline", return_value=mock_pipeline):
            exit_code = main([])

        assert exit_code == 1

    def test_正常系_help表示でSystemExit_0(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

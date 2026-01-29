"""Unit tests for the finance news workflow CLI script.

Tests for the CLI interface and main entry point of the finance news
workflow script that orchestrates the news collection pipeline.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from news.models import WorkflowResult


class TestCreateParser:
    """Tests for CLI argument parser creation."""

    def test_正常系_パーサーが作成される(self) -> None:
        from news.scripts.finance_news_workflow import create_parser

        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_正常系_デフォルト引数でパースできる(self) -> None:
        from news.scripts.finance_news_workflow import create_parser

        parser = create_parser()
        args = parser.parse_args([])
        assert args.config is None
        assert args.dry_run is False
        assert args.status is None
        assert args.max_articles is None

    def test_正常系_config引数を指定できる(self) -> None:
        from news.scripts.finance_news_workflow import create_parser

        parser = create_parser()
        args = parser.parse_args(["--config", "path/to/config.yaml"])
        assert args.config == "path/to/config.yaml"

    def test_正常系_dry_run引数を指定できる(self) -> None:
        from news.scripts.finance_news_workflow import create_parser

        parser = create_parser()
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_正常系_status引数を指定できる(self) -> None:
        from news.scripts.finance_news_workflow import create_parser

        parser = create_parser()
        args = parser.parse_args(["--status", "index,stock"])
        assert args.status == "index,stock"

    def test_正常系_max_articles引数を指定できる(self) -> None:
        from news.scripts.finance_news_workflow import create_parser

        parser = create_parser()
        args = parser.parse_args(["--max-articles", "10"])
        assert args.max_articles == 10

    def test_正常系_全引数を同時に指定できる(self) -> None:
        from news.scripts.finance_news_workflow import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "--config",
                "config.yaml",
                "--dry-run",
                "--status",
                "index,stock",
                "--max-articles",
                "20",
            ]
        )
        assert args.config == "config.yaml"
        assert args.dry_run is True
        assert args.status == "index,stock"
        assert args.max_articles == 20

    def test_異常系_max_articlesに非数値で拒否される(self) -> None:
        from news.scripts.finance_news_workflow import create_parser

        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--max-articles", "abc"])


class TestParseStatuses:
    """Tests for status parsing function."""

    def test_正常系_カンマ区切りでリストに変換される(self) -> None:
        from news.scripts.finance_news_workflow import parse_statuses

        result = parse_statuses("index,stock")
        assert result == ["index", "stock"]

    def test_正常系_単一のステータスでリストになる(self) -> None:
        from news.scripts.finance_news_workflow import parse_statuses

        result = parse_statuses("index")
        assert result == ["index"]

    def test_正常系_Noneの場合はNoneを返す(self) -> None:
        from news.scripts.finance_news_workflow import parse_statuses

        result = parse_statuses(None)
        assert result is None

    def test_正常系_空白がトリムされる(self) -> None:
        from news.scripts.finance_news_workflow import parse_statuses

        result = parse_statuses("index, stock , ai")
        assert result == ["index", "stock", "ai"]


class TestMain:
    """Tests for main entry point."""

    @pytest.fixture
    def mock_config_path(self, tmp_path: Path) -> Path:
        """Create a temporary config file for testing."""
        config_content = """
version: "1.0"
status_mapping:
  tech: ai
github_status_ids:
  ai: "6fbb43d0"
rss:
  presets_file: "data/config/rss-presets.json"
extraction:
  concurrency: 5
  timeout_seconds: 30
  min_body_length: 200
  max_retries: 3
summarization:
  concurrency: 3
  timeout_seconds: 60
  max_retries: 3
  prompt_template: "test"
github:
  project_number: 15
  project_id: "PVT_test"
  status_field_id: "PVTSSF_test"
  published_date_field_id: "PVTF_test"
  repository: "YH-05/finance"
filtering:
  max_age_hours: 168
output:
  result_dir: "data/exports/news-workflow"
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)
        return config_file

    @pytest.fixture
    def mock_workflow_result(self) -> WorkflowResult:
        """Create a mock WorkflowResult."""
        from news.models import WorkflowResult

        return WorkflowResult(
            total_collected=10,
            total_extracted=8,
            total_summarized=7,
            total_published=5,
            total_duplicates=2,
            extraction_failures=[],
            summarization_failures=[],
            publication_failures=[],
            started_at=datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            elapsed_seconds=300.0,
            published_articles=[],
        )

    def test_正常系_ワークフローが正常に完了すると終了コード0(
        self,
        mock_config_path: Path,
        mock_workflow_result: MagicMock,
    ) -> None:
        from news.scripts.finance_news_workflow import main

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run.return_value = mock_workflow_result

        with (
            patch(
                "news.scripts.finance_news_workflow.load_config",
            ) as mock_load_config,
            patch(
                "news.scripts.finance_news_workflow.NewsWorkflowOrchestrator",
                return_value=mock_orchestrator,
            ),
        ):
            mock_load_config.return_value = MagicMock()
            result = main(["--config", str(mock_config_path)])

        assert result == 0

    def test_正常系_dry_runモードでワークフローを実行できる(
        self,
        mock_config_path: Path,
        mock_workflow_result: MagicMock,
    ) -> None:
        from news.scripts.finance_news_workflow import main

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run.return_value = mock_workflow_result

        with (
            patch(
                "news.scripts.finance_news_workflow.load_config",
            ) as mock_load_config,
            patch(
                "news.scripts.finance_news_workflow.NewsWorkflowOrchestrator",
                return_value=mock_orchestrator,
            ),
        ):
            mock_load_config.return_value = MagicMock()
            result = main(["--config", str(mock_config_path), "--dry-run"])

        assert result == 0
        mock_orchestrator.run.assert_called_once()
        _, kwargs = mock_orchestrator.run.call_args
        assert kwargs.get("dry_run") is True

    def test_正常系_status引数が渡される(
        self,
        mock_config_path: Path,
        mock_workflow_result: MagicMock,
    ) -> None:
        from news.scripts.finance_news_workflow import main

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run.return_value = mock_workflow_result

        with (
            patch(
                "news.scripts.finance_news_workflow.load_config",
            ) as mock_load_config,
            patch(
                "news.scripts.finance_news_workflow.NewsWorkflowOrchestrator",
                return_value=mock_orchestrator,
            ),
        ):
            mock_load_config.return_value = MagicMock()
            result = main(
                ["--config", str(mock_config_path), "--status", "index,stock"]
            )

        assert result == 0
        mock_orchestrator.run.assert_called_once()
        _, kwargs = mock_orchestrator.run.call_args
        assert kwargs.get("statuses") == ["index", "stock"]

    def test_正常系_max_articles引数が渡される(
        self,
        mock_config_path: Path,
        mock_workflow_result: MagicMock,
    ) -> None:
        from news.scripts.finance_news_workflow import main

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run.return_value = mock_workflow_result

        with (
            patch(
                "news.scripts.finance_news_workflow.load_config",
            ) as mock_load_config,
            patch(
                "news.scripts.finance_news_workflow.NewsWorkflowOrchestrator",
                return_value=mock_orchestrator,
            ),
        ):
            mock_load_config.return_value = MagicMock()
            result = main(["--config", str(mock_config_path), "--max-articles", "10"])

        assert result == 0
        mock_orchestrator.run.assert_called_once()
        _, kwargs = mock_orchestrator.run.call_args
        assert kwargs.get("max_articles") == 10

    def test_異常系_設定ファイルが見つからないと終了コード1(self) -> None:
        from news.scripts.finance_news_workflow import main

        result = main(["--config", "/nonexistent/config.yaml"])
        assert result == 1

    def test_異常系_ワークフロー例外発生時に終了コード1(
        self,
        mock_config_path: Path,
    ) -> None:
        from news.scripts.finance_news_workflow import main

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run.side_effect = RuntimeError("Test error")

        with (
            patch(
                "news.scripts.finance_news_workflow.load_config",
            ) as mock_load_config,
            patch(
                "news.scripts.finance_news_workflow.NewsWorkflowOrchestrator",
                return_value=mock_orchestrator,
            ),
        ):
            mock_load_config.return_value = MagicMock()
            result = main(["--config", str(mock_config_path)])

        assert result == 1


class TestPrintResultSummary:
    """Tests for result summary printing."""

    def test_正常系_結果サマリーがフォーマットされる(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from news.models import WorkflowResult
        from news.scripts.finance_news_workflow import print_result_summary

        result = WorkflowResult(
            total_collected=10,
            total_extracted=8,
            total_summarized=7,
            total_published=5,
            total_duplicates=2,
            extraction_failures=[],
            summarization_failures=[],
            publication_failures=[],
            started_at=datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            elapsed_seconds=300.0,
            published_articles=[],
        )

        print_result_summary(result)

        captured = capsys.readouterr()
        assert "Workflow Result" in captured.out
        assert "Collected: 10" in captured.out
        assert "Extracted: 8" in captured.out
        assert "Summarized: 7" in captured.out
        assert "Published: 5" in captured.out
        assert "Duplicates: 2" in captured.out
        assert "Elapsed: 300.0s" in captured.out

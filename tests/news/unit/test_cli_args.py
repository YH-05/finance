"""Unit tests for CLI argument parsing in finance_news_workflow.

Tests --format and --export-only CLI options added in Issue #3402.

Issue: #3402 - Orchestrator統合・CLIオプション追加
"""

import pytest

from news.scripts.finance_news_workflow import create_parser


class TestCLIFormatOption:
    """Tests for --format CLI option."""

    def test_正常系_formatデフォルトはper_category(self) -> None:
        """Default --format should be per-category.

        Given:
            - No --format argument
        When:
            - Parser parses arguments
        Then:
            - args.format == "per-category"
        """
        parser = create_parser()
        args = parser.parse_args([])
        assert args.format == "per-category"

    def test_正常系_format_per_categoryが指定できる(self) -> None:
        """--format per-category should be accepted.

        Given:
            - --format per-category
        When:
            - Parser parses arguments
        Then:
            - args.format == "per-category"
        """
        parser = create_parser()
        args = parser.parse_args(["--format", "per-category"])
        assert args.format == "per-category"

    def test_正常系_format_per_articleが指定できる(self) -> None:
        """--format per-article should be accepted (legacy mode).

        Given:
            - --format per-article
        When:
            - Parser parses arguments
        Then:
            - args.format == "per-article"
        """
        parser = create_parser()
        args = parser.parse_args(["--format", "per-article"])
        assert args.format == "per-article"

    def test_異常系_無効なformat値でエラー(self) -> None:
        """Invalid --format value should raise SystemExit.

        Given:
            - --format invalid-value
        When:
            - Parser parses arguments
        Then:
            - SystemExit is raised
        """
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--format", "invalid-value"])


class TestCLIExportOnlyOption:
    """Tests for --export-only CLI option."""

    def test_正常系_export_onlyデフォルトはFalse(self) -> None:
        """Default --export-only should be False.

        Given:
            - No --export-only argument
        When:
            - Parser parses arguments
        Then:
            - args.export_only == False
        """
        parser = create_parser()
        args = parser.parse_args([])
        assert args.export_only is False

    def test_正常系_export_onlyフラグが設定できる(self) -> None:
        """--export-only flag should set export_only to True.

        Given:
            - --export-only flag
        When:
            - Parser parses arguments
        Then:
            - args.export_only == True
        """
        parser = create_parser()
        args = parser.parse_args(["--export-only"])
        assert args.export_only is True


class TestCLIOptionsCombination:
    """Tests for combining --format and --export-only with other options."""

    def test_正常系_formatとdry_runの組み合わせ(self) -> None:
        """--format and --dry-run can be combined.

        Given:
            - --format per-category --dry-run
        When:
            - Parser parses arguments
        Then:
            - Both options are correctly parsed
        """
        parser = create_parser()
        args = parser.parse_args(["--format", "per-category", "--dry-run"])
        assert args.format == "per-category"
        assert args.dry_run is True

    def test_正常系_export_onlyとdry_runの組み合わせ(self) -> None:
        """--export-only and --dry-run can be combined.

        Given:
            - --export-only --dry-run
        When:
            - Parser parses arguments
        Then:
            - Both options are correctly parsed
        """
        parser = create_parser()
        args = parser.parse_args(["--export-only", "--dry-run"])
        assert args.export_only is True
        assert args.dry_run is True

    def test_正常系_format_per_articleとexport_onlyの組み合わせ(self) -> None:
        """--format per-article and --export-only can be combined.

        Given:
            - --format per-article --export-only
        When:
            - Parser parses arguments
        Then:
            - Both options are correctly parsed
        """
        parser = create_parser()
        args = parser.parse_args(["--format", "per-article", "--export-only"])
        assert args.format == "per-article"
        assert args.export_only is True

    def test_正常系_全オプション同時指定(self) -> None:
        """All options can be specified together.

        Given:
            - --format per-category --export-only --dry-run --status index --max-articles 5
        When:
            - Parser parses arguments
        Then:
            - All options are correctly parsed
        """
        parser = create_parser()
        args = parser.parse_args(
            [
                "--format",
                "per-category",
                "--export-only",
                "--dry-run",
                "--status",
                "index",
                "--max-articles",
                "5",
                "--verbose",
            ]
        )
        assert args.format == "per-category"
        assert args.export_only is True
        assert args.dry_run is True
        assert args.status == "index"
        assert args.max_articles == 5
        assert args.verbose is True

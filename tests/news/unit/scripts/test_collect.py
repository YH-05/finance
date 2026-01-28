"""Unit tests for the news collection script.

Tests for the CLI interface, pipeline factory, and execution logic
of the auto-execution workflow script.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from news.config.models import (
    FileSinkConfig,
    NewsConfig,
    SinksConfig,
    SourcesConfig,
    YFinanceSearchSourceConfig,
    YFinanceTickerSourceConfig,
)
from news.scripts.collect import (
    CollectResult,
    build_pipeline_from_config,
    create_parser,
    execute_collection,
    main,
)


class TestCreateParser:
    """Tests for CLI argument parser creation."""

    def test_正常系_パーサーが作成される(self) -> None:
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_正常系_デフォルト引数でパースできる(self) -> None:
        parser = create_parser()
        args = parser.parse_args([])
        assert args.config is None
        assert args.source is None
        assert args.dry_run is False
        assert args.log_level == "INFO"
        assert args.log_format == "console"
        assert args.log_file is None

    def test_正常系_config引数を指定できる(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["--config", "path/to/config.yaml"])
        assert args.config == "path/to/config.yaml"

    def test_正常系_source引数を指定できる(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["--source", "yfinance_ticker"])
        assert args.source == "yfinance_ticker"

    def test_正常系_dry_run引数を指定できる(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_正常系_log_level引数を指定できる(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_正常系_log_format引数を指定できる(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["--log-format", "json"])
        assert args.log_format == "json"

    def test_正常系_log_file引数を指定できる(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["--log-file", "/var/log/news.log"])
        assert args.log_file == "/var/log/news.log"

    def test_正常系_全引数を同時に指定できる(self) -> None:
        parser = create_parser()
        args = parser.parse_args(
            [
                "--config",
                "config.yaml",
                "--source",
                "yfinance_ticker",
                "--dry-run",
                "--log-level",
                "DEBUG",
                "--log-format",
                "json",
                "--log-file",
                "/tmp/test.log",
            ]
        )
        assert args.config == "config.yaml"
        assert args.source == "yfinance_ticker"
        assert args.dry_run is True
        assert args.log_level == "DEBUG"
        assert args.log_format == "json"
        assert args.log_file == "/tmp/test.log"

    def test_異常系_無効なlog_levelで拒否される(self) -> None:
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--log-level", "INVALID"])

    def test_異常系_無効なlog_formatで拒否される(self) -> None:
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--log-format", "invalid"])


def _create_mock_source(name: str) -> MagicMock:
    """Create a mock source with the given name."""
    mock = MagicMock()
    mock.source_name = name
    return mock


class TestBuildPipelineFromConfig:
    """Tests for pipeline factory construction from config."""

    def test_正常系_デフォルト設定でパイプラインを構築できる(self) -> None:
        config = NewsConfig()
        pipeline = build_pipeline_from_config(config)
        assert pipeline is not None
        # No sources configured means empty pipeline
        assert len(pipeline.sources) == 0
        assert len(pipeline.sinks) == 0

    def test_正常系_yfinance_ticker_ソースが追加される(self) -> None:
        config = NewsConfig(
            sources=SourcesConfig(
                yfinance_ticker=YFinanceTickerSourceConfig(
                    enabled=True,
                    symbols_file="src/analyze/config/symbols.yaml",
                    categories=["indices"],
                ),
            ),
        )
        mock_index = _create_mock_source("yfinance_ticker_index")
        with (
            patch(
                "news.scripts.collect.ConfigLoader.get_ticker_symbols",
                return_value=["^GSPC", "^DJI"],
            ),
            patch(
                "news.sources.yfinance.IndexNewsSource",
                return_value=mock_index,
            ),
        ):
            pipeline = build_pipeline_from_config(config)
        assert len(pipeline.sources) >= 1

    def test_正常系_index_とstock_ソースが両方追加される(self) -> None:
        config = NewsConfig(
            sources=SourcesConfig(
                yfinance_ticker=YFinanceTickerSourceConfig(
                    enabled=True,
                    symbols_file="symbols.yaml",
                    categories=["indices", "mag7"],
                ),
            ),
        )
        mock_index = _create_mock_source("yfinance_ticker_index")
        mock_stock = _create_mock_source("yfinance_ticker_stock")
        with (
            patch(
                "news.scripts.collect.ConfigLoader.get_ticker_symbols",
                return_value=["^GSPC", "^DJI", "AAPL", "MSFT"],
            ),
            patch(
                "news.sources.yfinance.IndexNewsSource",
                return_value=mock_index,
            ),
            patch(
                "news.sources.yfinance.StockNewsSource",
                return_value=mock_stock,
            ),
        ):
            pipeline = build_pipeline_from_config(config)
        assert len(pipeline.sources) == 2

    def test_正常系_無効化されたソースは追加されない(self) -> None:
        config = NewsConfig(
            sources=SourcesConfig(
                yfinance_ticker=YFinanceTickerSourceConfig(
                    enabled=False,
                    symbols_file="symbols.yaml",
                ),
            ),
        )
        pipeline = build_pipeline_from_config(config)
        assert len(pipeline.sources) == 0

    def test_正常系_file_sinkが追加される(self, temp_dir: Path) -> None:
        config = NewsConfig(
            sinks=SinksConfig(
                file=FileSinkConfig(
                    enabled=True,
                    output_dir=str(temp_dir),
                ),
            ),
        )
        pipeline = build_pipeline_from_config(config)
        assert len(pipeline.sinks) >= 1

    def test_正常系_無効化されたsinkは追加されない(self) -> None:
        config = NewsConfig(
            sinks=SinksConfig(
                file=FileSinkConfig(
                    enabled=False,
                    output_dir="/tmp/test",
                ),
            ),
        )
        pipeline = build_pipeline_from_config(config)
        assert len(pipeline.sinks) == 0

    def test_正常系_source_filterで特定ソースのみ追加される(self) -> None:
        config = NewsConfig(
            sources=SourcesConfig(
                yfinance_ticker=YFinanceTickerSourceConfig(
                    enabled=True,
                    symbols_file="symbols.yaml",
                    categories=["indices"],
                ),
                yfinance_search=YFinanceSearchSourceConfig(
                    enabled=True,
                    keywords_file="keywords.yaml",
                ),
            ),
        )
        mock_index = _create_mock_source("yfinance_ticker_index")
        with (
            patch(
                "news.scripts.collect.ConfigLoader.get_ticker_symbols",
                return_value=["^GSPC"],
            ),
            patch(
                "news.sources.yfinance.IndexNewsSource",
                return_value=mock_index,
            ),
        ):
            pipeline = build_pipeline_from_config(
                config, source_filter="yfinance_ticker"
            )
        # Only yfinance_ticker should be added
        source_names = [s.source_name for s in pipeline.sources]
        assert any("ticker" in name for name in source_names)
        # yfinance_search should NOT be present
        assert not any("search" in name for name in source_names)

    def test_正常系_symbols_file未存在でも安全にスキップされる(self) -> None:
        config = NewsConfig(
            sources=SourcesConfig(
                yfinance_ticker=YFinanceTickerSourceConfig(
                    enabled=True,
                    symbols_file="nonexistent.yaml",
                ),
            ),
        )
        with patch(
            "news.scripts.collect.ConfigLoader.get_ticker_symbols",
            side_effect=FileNotFoundError("File not found"),
        ):
            pipeline = build_pipeline_from_config(config)
        assert len(pipeline.sources) == 0


class TestCollectResult:
    """Tests for CollectResult model."""

    def test_正常系_成功結果を作成できる(self) -> None:
        result = CollectResult(
            success=True,
            articles_fetched=10,
            articles_processed=10,
            articles_output=10,
            sources_used=["yfinance_ticker"],
            sinks_used=["json_file"],
            dry_run=False,
        )
        assert result.success is True
        assert result.articles_fetched == 10

    def test_正常系_dry_run結果を作成できる(self) -> None:
        result = CollectResult(
            success=True,
            articles_fetched=0,
            articles_processed=0,
            articles_output=0,
            sources_used=["yfinance_ticker"],
            sinks_used=["json_file"],
            dry_run=True,
        )
        assert result.dry_run is True
        assert result.articles_output == 0

    def test_正常系_エラー結果を作成できる(self) -> None:
        result = CollectResult(
            success=False,
            articles_fetched=0,
            articles_processed=0,
            articles_output=0,
            sources_used=[],
            sinks_used=[],
            dry_run=False,
            error_message="Config file not found",
        )
        assert result.success is False
        assert result.error_message == "Config file not found"

    def test_正常系_duration_secondsが設定される(self) -> None:
        result = CollectResult(
            success=True,
            articles_fetched=0,
            articles_processed=0,
            articles_output=0,
            sources_used=[],
            sinks_used=[],
            dry_run=False,
            duration_seconds=1.234,
        )
        assert result.duration_seconds == 1.234

    def test_正常系_デフォルト値が正しい(self) -> None:
        result = CollectResult(success=True)
        assert result.articles_fetched == 0
        assert result.articles_processed == 0
        assert result.articles_output == 0
        assert result.sources_used == []
        assert result.sinks_used == []
        assert result.dry_run is False
        assert result.duration_seconds is None
        assert result.error_message is None


class TestExecuteCollection:
    """Tests for execute_collection function."""

    def test_正常系_dry_runモードで収集をスキップする(self) -> None:
        config = NewsConfig()
        result = execute_collection(
            config=config,
            dry_run=True,
            source_filter=None,
        )
        assert result.success is True
        assert result.dry_run is True
        assert result.articles_fetched == 0

    def test_正常系_設定なしでも成功を返す(self) -> None:
        config = NewsConfig()
        result = execute_collection(
            config=config,
            dry_run=False,
            source_filter=None,
        )
        # Empty pipeline should succeed with 0 articles
        assert result.success is True
        assert result.articles_fetched == 0

    def test_正常系_source_filterを渡せる(self) -> None:
        config = NewsConfig()
        result = execute_collection(
            config=config,
            dry_run=False,
            source_filter="yfinance_ticker",
        )
        assert result.success is True

    def test_正常系_duration_secondsが設定される(self) -> None:
        config = NewsConfig()
        result = execute_collection(
            config=config,
            dry_run=True,
            source_filter=None,
        )
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0

    def test_正常系_例外発生時にエラー結果を返す(self) -> None:
        config = NewsConfig()
        with patch(
            "news.scripts.collect.build_pipeline_from_config",
            side_effect=RuntimeError("Test error"),
        ):
            result = execute_collection(
                config=config,
                dry_run=False,
                source_filter=None,
            )
        assert result.success is False
        assert result.error_message == "Test error"


class TestMain:
    """Tests for main entry point."""

    def test_正常系_引数なしで実行できる(self) -> None:
        with patch(
            "news.scripts.collect.execute_collection",
            return_value=CollectResult(
                success=True,
                articles_fetched=0,
                articles_processed=0,
                articles_output=0,
                sources_used=[],
                sinks_used=[],
                dry_run=False,
            ),
        ):
            result = main(["--dry-run"])
        assert result == 0

    def test_正常系_config引数で実行できる(self, tmp_path: Path) -> None:
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("settings:\n  max_articles_per_source: 5\n")
        with patch(
            "news.scripts.collect.execute_collection",
            return_value=CollectResult(
                success=True,
                articles_fetched=5,
                articles_processed=5,
                articles_output=5,
                sources_used=["yfinance_ticker"],
                sinks_used=["json_file"],
                dry_run=False,
            ),
        ):
            result = main(["--config", str(config_file)])
        assert result == 0

    def test_異常系_存在しないconfig_fileで失敗する(self) -> None:
        result = main(["--config", "/nonexistent/config.yaml"])
        assert result == 1

    def test_異常系_実行エラーで失敗コードを返す(self) -> None:
        with patch(
            "news.scripts.collect.execute_collection",
            return_value=CollectResult(
                success=False,
                articles_fetched=0,
                articles_processed=0,
                articles_output=0,
                sources_used=[],
                sinks_used=[],
                dry_run=False,
                error_message="Collection failed",
            ),
        ):
            result = main([])
        assert result == 1

    def test_正常系_source引数を渡せる(self) -> None:
        with patch(
            "news.scripts.collect.execute_collection",
            return_value=CollectResult(
                success=True,
                articles_fetched=0,
                articles_processed=0,
                articles_output=0,
                sources_used=[],
                sinks_used=[],
                dry_run=False,
            ),
        ) as mock_exec:
            result = main(["--source", "yfinance_ticker"])
        assert result == 0
        _, kwargs = mock_exec.call_args
        assert kwargs["source_filter"] == "yfinance_ticker"

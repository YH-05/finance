"""Automated news collection script for cron-based execution.

This module provides a CLI interface for collecting news from configured
sources and writing to configured sinks. It supports configuration file
specification, source filtering, dry-run mode, and logging configuration.

Usage
-----
Run all configured sources:

    python -m news.scripts.collect

Collect from a specific source:

    python -m news.scripts.collect --source yfinance_ticker

Dry-run mode (validate config without collecting):

    python -m news.scripts.collect --dry-run

Use a specific config file:

    python -m news.scripts.collect --config data/config/news_sources.yaml

Configure logging:

    python -m news.scripts.collect --log-level DEBUG --log-format json

cron Example
------------
::

    # Run daily at 08:00
    0 8 * * * cd /path/to/finance && python -m news.scripts.collect \\
        >> /var/log/news-collect.log 2>&1
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from utils_core.logging import get_logger, setup_logging

from ..config.models import ConfigLoader
from ..processors.pipeline import Pipeline, PipelineConfig
from ..sinks.file import FileSink

if TYPE_CHECKING:
    from ..config.models import NewsConfig
    from ..processors.pipeline import PipelineResult

logger = get_logger(__name__, module="scripts.collect")

# Valid source names that can be used with --source
VALID_SOURCES = frozenset(
    {
        "yfinance_ticker",
        "yfinance_search",
    }
)

# Valid log levels
VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

# Valid log formats
VALID_LOG_FORMATS = ("console", "json", "plain")


class CollectResult(BaseModel):
    """Result of a news collection execution.

    Attributes
    ----------
    success : bool
        Whether the collection completed successfully.
    articles_fetched : int
        Total number of articles fetched from all sources.
    articles_processed : int
        Total number of articles that passed through processors.
    articles_output : int
        Total number of articles written to sinks.
    sources_used : list[str]
        Names of the sources that were used.
    sinks_used : list[str]
        Names of the sinks that were used.
    dry_run : bool
        Whether this was a dry-run execution.
    duration_seconds : float | None
        Execution duration in seconds.
    error_message : str | None
        Error message if the collection failed.

    Examples
    --------
    >>> result = CollectResult(
    ...     success=True,
    ...     articles_fetched=50,
    ...     articles_processed=50,
    ...     articles_output=50,
    ...     sources_used=["yfinance_ticker"],
    ...     sinks_used=["json_file"],
    ...     dry_run=False,
    ... )
    >>> result.success
    True
    """

    success: bool = Field(..., description="Whether collection completed successfully")
    articles_fetched: int = Field(
        default=0, description="Total articles fetched from sources"
    )
    articles_processed: int = Field(
        default=0, description="Total articles processed by processors"
    )
    articles_output: int = Field(
        default=0, description="Total articles written to sinks"
    )
    sources_used: list[str] = Field(
        default_factory=list, description="Source names used"
    )
    sinks_used: list[str] = Field(default_factory=list, description="Sink names used")
    dry_run: bool = Field(default=False, description="Whether this was a dry-run")
    duration_seconds: float | None = Field(
        default=None, description="Execution duration in seconds"
    )
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the collect script.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser with all supported options.

    Examples
    --------
    >>> parser = create_parser()
    >>> args = parser.parse_args(["--dry-run", "--source", "yfinance_ticker"])
    >>> args.dry_run
    True
    >>> args.source
    'yfinance_ticker'
    """
    parser = argparse.ArgumentParser(
        prog="news-collect",
        description="Collect news from configured sources and write to sinks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s                              Collect from all configured sources
  %(prog)s --source yfinance_ticker     Collect from specific source only
  %(prog)s --dry-run                    Validate config without collecting
  %(prog)s --config config.yaml         Use specific config file
  %(prog)s --log-level DEBUG            Enable debug logging
""",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML/JSON configuration file (default: data/config/news_sources.yaml)",
    )

    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Collect from a specific source only (e.g., yfinance_ticker, yfinance_search)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate configuration and show what would be collected without actually collecting",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=VALID_LOG_LEVELS,
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-format",
        type=str,
        default="console",
        choices=VALID_LOG_FORMATS,
        help="Log output format (default: console)",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (default: stdout only)",
    )

    return parser


def build_pipeline_from_config(
    config: NewsConfig,
    source_filter: str | None = None,
) -> Pipeline:
    """Build a Pipeline instance from a NewsConfig.

    Creates sources and sinks based on the configuration, optionally
    filtering to a single source.

    Parameters
    ----------
    config : NewsConfig
        The news configuration to build the pipeline from.
    source_filter : str | None, optional
        If specified, only add this source to the pipeline.
        Must be one of: "yfinance_ticker", "yfinance_search".

    Returns
    -------
    Pipeline
        Configured Pipeline instance ready for execution.

    Examples
    --------
    >>> config = NewsConfig()
    >>> pipeline = build_pipeline_from_config(config)
    >>> len(pipeline.sources)
    0

    >>> config = NewsConfig(
    ...     sinks=SinksConfig(file=FileSinkConfig(output_dir="data/news")),
    ... )
    >>> pipeline = build_pipeline_from_config(config)
    >>> len(pipeline.sinks)
    1
    """
    pipeline_config = PipelineConfig(
        continue_on_error=True,
        batch_size=50,
    )
    pipeline = Pipeline(config=pipeline_config)

    logger.info(
        "Building pipeline from config",
        source_filter=source_filter,
    )

    # Add sources
    _add_sources(pipeline, config, source_filter)

    # Add sinks
    _add_sinks(pipeline, config)

    logger.info(
        "Pipeline built",
        source_count=len(pipeline.sources),
        sink_count=len(pipeline.sinks),
    )

    return pipeline


def _add_sources(
    pipeline: Pipeline,
    config: NewsConfig,
    source_filter: str | None,
) -> None:
    """Add configured sources to the pipeline.

    Parameters
    ----------
    pipeline : Pipeline
        The pipeline to add sources to.
    config : NewsConfig
        Configuration containing source settings.
    source_filter : str | None
        Optional filter to add only a specific source.
    """
    # Add yfinance_ticker source
    if (
        config.sources.yfinance_ticker
        and config.sources.yfinance_ticker.enabled
        and (source_filter is None or source_filter == "yfinance_ticker")
    ):
        _add_ticker_sources(pipeline, config)

    # Add yfinance_search source
    if (
        config.sources.yfinance_search
        and config.sources.yfinance_search.enabled
        and (source_filter is None or source_filter == "yfinance_search")
    ):
        _add_search_sources(pipeline, config)


def _add_ticker_sources(
    pipeline: Pipeline,
    config: NewsConfig,
) -> None:
    """Add yfinance ticker-based sources to the pipeline.

    Parameters
    ----------
    pipeline : Pipeline
        The pipeline to add sources to.
    config : NewsConfig
        Configuration containing source settings.
    """
    ticker_config = config.sources.yfinance_ticker
    if ticker_config is None:
        return

    from ..sources.yfinance import IndexNewsSource, StockNewsSource

    loader = ConfigLoader()

    try:
        symbols = loader.get_ticker_symbols(
            ticker_config.symbols_file,
            categories=ticker_config.categories if ticker_config.categories else None,
        )
        logger.info(
            "Loaded ticker symbols",
            symbol_count=len(symbols),
            categories=ticker_config.categories,
        )

        # Add index source for index symbols (starts with ^)
        index_symbols = [s for s in symbols if s.startswith("^")]
        if index_symbols:
            pipeline.add_source(
                IndexNewsSource(symbols_file=ticker_config.symbols_file)
            )
            logger.debug(
                "Added IndexNewsSource",
                symbol_count=len(index_symbols),
            )

        # Add stock source for non-index symbols
        stock_symbols = [s for s in symbols if not s.startswith("^")]
        if stock_symbols:
            pipeline.add_source(
                StockNewsSource(symbols_file=ticker_config.symbols_file)
            )
            logger.debug(
                "Added StockNewsSource",
                symbol_count=len(stock_symbols),
            )

    except FileNotFoundError:
        logger.warning(
            "Symbols file not found, skipping ticker sources",
            symbols_file=ticker_config.symbols_file,
        )
    except Exception as e:
        logger.error(
            "Failed to load ticker symbols",
            error=str(e),
            error_type=type(e).__name__,
        )


def _add_search_sources(
    pipeline: Pipeline,
    config: NewsConfig,
) -> None:
    """Add yfinance search-based sources to the pipeline.

    Parameters
    ----------
    pipeline : Pipeline
        The pipeline to add sources to.
    config : NewsConfig
        Configuration containing source settings.
    """
    search_config = config.sources.yfinance_search
    if search_config is None:
        return

    from ..sources.yfinance import SearchNewsSource

    loader = ConfigLoader()

    try:
        keywords_data = loader.load_symbols(search_config.keywords_file)
        keywords: list[str] = []
        for category_keywords in keywords_data.values():
            if isinstance(category_keywords, list):
                for item in category_keywords:
                    if isinstance(item, dict) and "query" in item:
                        keywords.append(item["query"])
                    elif isinstance(item, str):
                        keywords.append(item)

        if keywords:
            pipeline.add_source(SearchNewsSource(keywords=keywords))
            logger.debug(
                "Added SearchNewsSource",
                keyword_count=len(keywords),
            )
        else:
            logger.warning(
                "No keywords found in config, skipping search source",
                keywords_file=search_config.keywords_file,
            )
    except FileNotFoundError:
        logger.warning(
            "Keywords file not found, skipping search source",
            keywords_file=search_config.keywords_file,
        )
    except Exception as e:
        logger.error(
            "Failed to add search source",
            error=str(e),
            error_type=type(e).__name__,
        )


def _add_sinks(
    pipeline: Pipeline,
    config: NewsConfig,
) -> None:
    """Add configured sinks to the pipeline.

    Parameters
    ----------
    pipeline : Pipeline
        The pipeline to add sinks to.
    config : NewsConfig
        Configuration containing sink settings.
    """
    # Add file sink
    if config.sinks.file and config.sinks.file.enabled:
        file_config = config.sinks.file
        sink = FileSink(
            output_dir=Path(file_config.output_dir),
            filename_pattern=file_config.filename_pattern,
        )
        pipeline.add_sink(sink)
        logger.debug(
            "Added FileSink",
            output_dir=file_config.output_dir,
        )

    # GitHub sink is not added here - it requires authenticated context
    # and is typically used in interactive mode via agents
    if config.sinks.github and config.sinks.github.enabled:
        logger.info(
            "GitHub sink configured but not added to automated pipeline "
            "(requires interactive context)",
            project_number=config.sinks.github.project_number,
        )


def execute_collection(
    config: NewsConfig,
    dry_run: bool = False,
    source_filter: str | None = None,
) -> CollectResult:
    """Execute the news collection workflow.

    Parameters
    ----------
    config : NewsConfig
        The news configuration to use.
    dry_run : bool, optional
        If True, validate config and show what would be collected
        without actually collecting. Default is False.
    source_filter : str | None, optional
        If specified, collect from this source only.

    Returns
    -------
    CollectResult
        Result of the collection operation.

    Examples
    --------
    >>> config = NewsConfig()
    >>> result = execute_collection(config, dry_run=True)
    >>> result.success
    True
    >>> result.dry_run
    True
    """
    start_time = time.monotonic()

    logger.info(
        "Starting news collection",
        dry_run=dry_run,
        source_filter=source_filter,
    )

    try:
        pipeline = build_pipeline_from_config(config, source_filter=source_filter)

        source_names = [s.source_name for s in pipeline.sources]
        sink_names = [s.sink_name for s in pipeline.sinks]

        if dry_run:
            elapsed = time.monotonic() - start_time
            logger.info(
                "Dry-run mode: pipeline built successfully",
                source_count=len(pipeline.sources),
                source_names=source_names,
                sink_count=len(pipeline.sinks),
                sink_names=sink_names,
            )
            return CollectResult(
                success=True,
                articles_fetched=0,
                articles_processed=0,
                articles_output=0,
                sources_used=source_names,
                sinks_used=sink_names,
                dry_run=True,
                duration_seconds=round(elapsed, 3),
            )

        # Execute the pipeline
        pipeline_result: PipelineResult = pipeline.run(
            identifiers=_get_identifiers(config, source_filter),
            count=config.settings.max_articles_per_source,
        )

        elapsed = time.monotonic() - start_time

        logger.info(
            "Collection completed",
            success=pipeline_result.success,
            articles_fetched=pipeline_result.articles_fetched,
            articles_processed=pipeline_result.articles_processed,
            articles_output=pipeline_result.articles_output,
            error_count=len(pipeline_result.errors),
            duration_seconds=round(elapsed, 3),
        )

        return CollectResult(
            success=pipeline_result.success,
            articles_fetched=pipeline_result.articles_fetched,
            articles_processed=pipeline_result.articles_processed,
            articles_output=pipeline_result.articles_output,
            sources_used=source_names,
            sinks_used=sink_names,
            dry_run=False,
            duration_seconds=round(elapsed, 3),
        )

    except Exception as e:
        elapsed = time.monotonic() - start_time
        logger.error(
            "Collection failed with exception",
            error=str(e),
            error_type=type(e).__name__,
            duration_seconds=round(elapsed, 3),
            exc_info=True,
        )
        return CollectResult(
            success=False,
            sources_used=[],
            sinks_used=[],
            dry_run=dry_run,
            duration_seconds=round(elapsed, 3),
            error_message=str(e),
        )


def _get_identifiers(
    config: NewsConfig,
    source_filter: str | None,
) -> list[str]:
    """Get identifiers (tickers/keywords) from config for pipeline execution.

    Parameters
    ----------
    config : NewsConfig
        The news configuration.
    source_filter : str | None
        Optional source filter.

    Returns
    -------
    list[str]
        List of identifiers to fetch from sources.
    """
    identifiers: list[str] = []
    loader = ConfigLoader()

    # Get ticker symbols
    if (
        config.sources.yfinance_ticker
        and config.sources.yfinance_ticker.enabled
        and (source_filter is None or source_filter == "yfinance_ticker")
    ):
        ticker_config = config.sources.yfinance_ticker
        try:
            symbols = loader.get_ticker_symbols(
                ticker_config.symbols_file,
                categories=(
                    ticker_config.categories if ticker_config.categories else None
                ),
            )
            identifiers.extend(symbols)
        except FileNotFoundError:
            logger.warning(
                "Symbols file not found",
                symbols_file=ticker_config.symbols_file,
            )
        except Exception as e:
            logger.error(
                "Failed to load identifiers",
                error=str(e),
            )

    # Get search keywords
    if (
        config.sources.yfinance_search
        and config.sources.yfinance_search.enabled
        and (source_filter is None or source_filter == "yfinance_search")
    ):
        search_config = config.sources.yfinance_search
        try:
            keywords_data = loader.load_symbols(search_config.keywords_file)
            for category_keywords in keywords_data.values():
                if isinstance(category_keywords, list):
                    for item in category_keywords:
                        if isinstance(item, dict) and "query" in item:
                            identifiers.append(item["query"])
                        elif isinstance(item, str):
                            identifiers.append(item)
        except FileNotFoundError:
            logger.warning(
                "Keywords file not found",
                keywords_file=search_config.keywords_file,
            )
        except Exception as e:
            logger.error(
                "Failed to load search keywords",
                error=str(e),
            )

    logger.debug(
        "Identifiers loaded",
        count=len(identifiers),
        source_filter=source_filter,
    )

    return identifiers


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the news collection script.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command line arguments. If None, uses sys.argv[1:].

    Returns
    -------
    int
        Exit code: 0 for success, 1 for failure.

    Examples
    --------
    >>> exit_code = main(["--dry-run"])
    >>> exit_code
    0

    >>> exit_code = main(["--config", "config.yaml", "--source", "yfinance_ticker"])
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging
    setup_logging(
        level=args.log_level,
        format=args.log_format,
        log_file=args.log_file,
        force=True,
    )

    logger.info(
        "News collection script started",
        config=args.config,
        source=args.source,
        dry_run=args.dry_run,
        log_level=args.log_level,
        log_format=args.log_format,
    )

    # Load configuration
    try:
        loader = ConfigLoader()
        if args.config:
            config = loader.load(args.config)
        else:
            config = loader.load_from_default()
    except FileNotFoundError as e:
        logger.error(
            "Configuration file not found",
            error=str(e),
            config_path=args.config,
        )
        return 1
    except Exception as e:
        logger.error(
            "Failed to load configuration",
            error=str(e),
            error_type=type(e).__name__,
        )
        return 1

    # Execute collection
    result = execute_collection(
        config=config,
        dry_run=args.dry_run,
        source_filter=args.source,
    )

    # Log result summary
    if result.success:
        logger.info(
            "Collection script completed successfully",
            articles_fetched=result.articles_fetched,
            articles_processed=result.articles_processed,
            articles_output=result.articles_output,
            sources_used=result.sources_used,
            sinks_used=result.sinks_used,
            dry_run=result.dry_run,
            duration_seconds=result.duration_seconds,
        )
        return 0
    else:
        logger.error(
            "Collection script failed",
            error_message=result.error_message,
            duration_seconds=result.duration_seconds,
        )
        return 1


# Export all public symbols
__all__ = [
    "CollectResult",
    "build_pipeline_from_config",
    "create_parser",
    "execute_collection",
    "main",
]

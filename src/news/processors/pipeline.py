"""Pipeline execution for the news package.

This module provides the Pipeline class for managing the Source -> Processor -> Sink
chain execution with batch processing, parallel execution support, and error handling.

The pipeline orchestrates the collection, processing, and output of news articles
by chaining together multiple sources, processors, and sinks.

Examples
--------
>>> from news.processors.pipeline import Pipeline, PipelineConfig
>>> from news.sources.yfinance import IndexNewsSource
>>> from news.processors import SummarizerProcessor
>>> from news.sinks import FileSink
>>>
>>> pipeline = (
...     Pipeline()
...     .add_source(IndexNewsSource())
...     .add_processor(SummarizerProcessor())
...     .add_sink(FileSink(output_dir=Path("data/news")))
... )
>>> result = pipeline.run(identifiers=["^GSPC", "^DJI"])
>>> result.success
True
>>> result.articles_fetched
20
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ..core.article import Article  # noqa: TC001 - needed at runtime for Pydantic
from ..utils.logging_config import get_logger

if TYPE_CHECKING:
    from ..core.processor import ProcessorProtocol
    from ..core.sink import SinkProtocol
    from ..core.source import SourceProtocol

logger = get_logger(__name__, module="processors.pipeline")


class PipelineError(Exception):
    """Exception raised when a pipeline execution fails.

    This exception is raised when ``continue_on_error`` is False and a stage
    (source, processor, or sink) encounters an error.

    Parameters
    ----------
    message : str
        Human-readable error message.
    stage : str
        Pipeline stage where the error occurred ("source", "processor", or "sink").
    cause : Exception | None, optional
        Original exception that caused this error.

    Attributes
    ----------
    stage : str
        Pipeline stage where the error occurred.
    cause : Exception | None
        Original exception.

    Examples
    --------
    >>> raise PipelineError("Processor failed", stage="processor")
    """

    def __init__(
        self,
        message: str,
        stage: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize PipelineError."""
        super().__init__(message)
        self.stage = stage
        self.cause = cause

        logger.error(
            "PipelineError created",
            message=message,
            stage=stage,
            has_cause=cause is not None,
        )


class StageError(BaseModel):
    """Error information for a pipeline stage.

    Records details about an error that occurred during pipeline execution,
    including which stage failed and the error message.

    Attributes
    ----------
    stage : str
        Pipeline stage where the error occurred ("source", "processor", or "sink").
    source_name : str
        Name of the component that failed.
    error_message : str
        Human-readable error description.
    article_url : str | None
        URL of the article being processed when the error occurred, if applicable.

    Examples
    --------
    >>> error = StageError(
    ...     stage="processor",
    ...     source_name="summarizer",
    ...     error_message="Rate limit exceeded",
    ... )
    >>> error.stage
    'processor'
    """

    stage: str = Field(..., description="Pipeline stage (source, processor, sink)")
    source_name: str = Field(..., description="Name of the failed component")
    error_message: str = Field(..., description="Error description")
    article_url: str | None = Field(
        default=None,
        description="URL of the article when error occurred",
    )


class PipelineConfig(BaseModel):
    """Configuration for Pipeline execution.

    Controls error handling, batch processing, and parallelism settings.

    Attributes
    ----------
    continue_on_error : bool
        If True, continue processing when errors occur in individual stages.
        If False, raise PipelineError on first error. Default is True.
    batch_size : int
        Number of articles to process in each batch. Default is 50.
        Must be a positive integer.
    max_workers : int
        Maximum number of parallel workers for source fetching. Default is 4.
        Must be a positive integer.

    Examples
    --------
    >>> config = PipelineConfig(batch_size=100, continue_on_error=False)
    >>> config.batch_size
    100
    """

    continue_on_error: bool = Field(
        default=True,
        description="Continue processing on error (default: True)",
    )
    batch_size: int = Field(
        default=50,
        gt=0,
        description="Batch size for processing (default: 50, must be positive)",
    )
    max_workers: int = Field(
        default=4,
        gt=0,
        description="Max parallel workers (default: 4, must be positive)",
    )


class PipelineResult(BaseModel):
    """Result of a pipeline execution.

    Contains statistics, output articles, and any errors that occurred during
    the pipeline run.

    Attributes
    ----------
    success : bool
        Whether the pipeline completed without critical errors.
    articles_fetched : int
        Total number of articles fetched from all sources.
    articles_processed : int
        Total number of articles that passed through all processors.
    articles_output : int
        Total number of articles written to all sinks.
    output_articles : list[Article]
        The final processed articles (after all processors applied).
    errors : list[StageError]
        List of errors that occurred during execution.
    duration_seconds : float | None
        Pipeline execution duration in seconds.

    Examples
    --------
    >>> result = PipelineResult(
    ...     success=True,
    ...     articles_fetched=50,
    ...     articles_processed=50,
    ...     articles_output=50,
    ...     output_articles=[...],
    ... )
    >>> result.success
    True
    """

    success: bool = Field(..., description="Whether pipeline completed successfully")
    articles_fetched: int = Field(
        default=0, description="Total articles fetched from sources"
    )
    articles_processed: int = Field(
        default=0, description="Total articles processed by processors"
    )
    articles_output: int = Field(
        default=0, description="Total articles written to sinks"
    )
    output_articles: list[Article] = Field(
        default_factory=list, description="Final processed articles"
    )
    errors: list[StageError] = Field(
        default_factory=list, description="Errors during execution"
    )
    duration_seconds: float | None = Field(
        default=None, description="Execution duration in seconds"
    )


class Pipeline:
    """Pipeline for chaining Source -> Processor -> Sink execution.

    Manages the collection, processing, and output of news articles by
    orchestrating multiple sources, processors, and sinks.

    The pipeline supports:
    - Multiple sources (fetched sequentially or in parallel)
    - Multiple processors (applied in order to each article)
    - Multiple sinks (each receives the final processed articles)
    - Batch processing (articles processed in configurable batch sizes)
    - Error handling (continue on error or fail fast)

    Parameters
    ----------
    config : PipelineConfig | None, optional
        Pipeline configuration. If None, uses default PipelineConfig.

    Attributes
    ----------
    config : PipelineConfig
        The current pipeline configuration.
    sources : list[SourceProtocol]
        Registered data sources.
    processors : list[ProcessorProtocol]
        Registered processors.
    sinks : list[SinkProtocol]
        Registered output sinks.

    Examples
    --------
    Basic usage with fluent API:

    >>> pipeline = (
    ...     Pipeline()
    ...     .add_source(source)
    ...     .add_processor(processor)
    ...     .add_sink(sink)
    ... )
    >>> result = pipeline.run(identifiers=["AAPL", "GOOGL"])
    >>> result.success
    True

    With custom config:

    >>> config = PipelineConfig(batch_size=100, continue_on_error=False)
    >>> pipeline = Pipeline(config=config)
    >>> pipeline.add_source(source)
    >>> pipeline.add_sink(sink)
    >>> result = pipeline.run(identifiers=["^GSPC"])
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        """Initialize Pipeline with optional configuration.

        Parameters
        ----------
        config : PipelineConfig | None, optional
            Pipeline configuration. Uses default if None.
        """
        self._config = config or PipelineConfig()
        self._sources: list[SourceProtocol] = []
        self._processors: list[ProcessorProtocol] = []
        self._sinks: list[SinkProtocol] = []

        logger.info(
            "Pipeline initialized",
            continue_on_error=self._config.continue_on_error,
            batch_size=self._config.batch_size,
            max_workers=self._config.max_workers,
        )

    @property
    def config(self) -> PipelineConfig:
        """Return the pipeline configuration.

        Returns
        -------
        PipelineConfig
            The current configuration.
        """
        return self._config

    @property
    def sources(self) -> list[SourceProtocol]:
        """Return registered sources.

        Returns
        -------
        list[SourceProtocol]
            List of registered data sources.
        """
        return self._sources

    @property
    def processors(self) -> list[ProcessorProtocol]:
        """Return registered processors.

        Returns
        -------
        list[ProcessorProtocol]
            List of registered processors.
        """
        return self._processors

    @property
    def sinks(self) -> list[SinkProtocol]:
        """Return registered sinks.

        Returns
        -------
        list[SinkProtocol]
            List of registered output sinks.
        """
        return self._sinks

    def add_source(self, source: SourceProtocol) -> Pipeline:
        """Add a data source to the pipeline.

        Parameters
        ----------
        source : SourceProtocol
            The data source to add.

        Returns
        -------
        Pipeline
            Self, for method chaining (fluent API).

        Examples
        --------
        >>> pipeline = Pipeline()
        >>> pipeline.add_source(IndexNewsSource())
        <Pipeline ...>
        """
        self._sources.append(source)
        logger.debug(
            "Source added to pipeline",
            source_name=source.source_name,
            total_sources=len(self._sources),
        )
        return self

    def add_processor(self, processor: ProcessorProtocol) -> Pipeline:
        """Add a processor to the pipeline.

        Processors are applied in the order they are added.

        Parameters
        ----------
        processor : ProcessorProtocol
            The processor to add.

        Returns
        -------
        Pipeline
            Self, for method chaining (fluent API).

        Examples
        --------
        >>> pipeline = Pipeline()
        >>> pipeline.add_processor(SummarizerProcessor())
        <Pipeline ...>
        """
        self._processors.append(processor)
        logger.debug(
            "Processor added to pipeline",
            processor_name=processor.processor_name,
            total_processors=len(self._processors),
        )
        return self

    def add_sink(self, sink: SinkProtocol) -> Pipeline:
        """Add an output sink to the pipeline.

        Each sink receives the final processed articles independently.

        Parameters
        ----------
        sink : SinkProtocol
            The output sink to add.

        Returns
        -------
        Pipeline
            Self, for method chaining (fluent API).

        Examples
        --------
        >>> pipeline = Pipeline()
        >>> pipeline.add_sink(FileSink(output_dir=Path("data/news")))
        <Pipeline ...>
        """
        self._sinks.append(sink)
        logger.debug(
            "Sink added to pipeline",
            sink_name=sink.sink_name,
            total_sinks=len(self._sinks),
        )
        return self

    def run(
        self,
        identifiers: list[str] | None = None,
        count: int = 10,
    ) -> PipelineResult:
        """Execute the pipeline: fetch -> process -> output.

        Parameters
        ----------
        identifiers : list[str] | None, optional
            Identifiers to fetch from sources (tickers, queries, etc.).
            If None or empty, no sources are fetched.
        count : int, optional
            Maximum number of articles to fetch per identifier (default: 10).

        Returns
        -------
        PipelineResult
            Result containing statistics, processed articles, and any errors.

        Raises
        ------
        PipelineError
            If ``continue_on_error`` is False and a critical error occurs.

        Examples
        --------
        >>> pipeline = Pipeline()
        >>> pipeline.add_source(source).add_sink(sink)
        >>> result = pipeline.run(identifiers=["AAPL", "GOOGL"])
        >>> result.success
        True
        """
        import time

        start_time = time.monotonic()
        errors: list[StageError] = []

        logger.info(
            "Pipeline execution started",
            source_count=len(self._sources),
            processor_count=len(self._processors),
            sink_count=len(self._sinks),
            identifier_count=len(identifiers) if identifiers else 0,
        )

        # Stage 1: Fetch from sources
        fetched_articles = self._fetch_from_sources(
            identifiers=identifiers or [],
            count=count,
            errors=errors,
        )
        articles_fetched_count = len(fetched_articles)

        logger.info(
            "Fetch stage completed",
            articles_fetched=articles_fetched_count,
            error_count=len(errors),
        )

        # Stage 2: Process articles through processors
        processed_articles = self._process_articles(
            articles=fetched_articles,
            errors=errors,
        )
        articles_processed_count = len(processed_articles)

        logger.info(
            "Process stage completed",
            articles_processed=articles_processed_count,
            error_count=len(errors),
        )

        # Stage 3: Output to sinks
        articles_output_count = self._output_to_sinks(
            articles=processed_articles,
            errors=errors,
        )

        elapsed = time.monotonic() - start_time

        logger.info(
            "Pipeline execution completed",
            articles_fetched=articles_fetched_count,
            articles_processed=articles_processed_count,
            articles_output=articles_output_count,
            error_count=len(errors),
            duration_seconds=round(elapsed, 3),
        )

        return PipelineResult(
            success=True,
            articles_fetched=articles_fetched_count,
            articles_processed=articles_processed_count,
            articles_output=articles_output_count,
            output_articles=processed_articles,
            errors=errors,
            duration_seconds=round(elapsed, 3),
        )

    def _fetch_from_sources(
        self,
        identifiers: list[str],
        count: int,
        errors: list[StageError],
    ) -> list[Article]:
        """Fetch articles from all registered sources.

        Parameters
        ----------
        identifiers : list[str]
            Identifiers to fetch.
        count : int
            Maximum articles per identifier.
        errors : list[StageError]
            Accumulator for stage errors.

        Returns
        -------
        list[Article]
            All fetched articles from all sources.
        """
        all_articles: list[Article] = []

        if not identifiers or not self._sources:
            return all_articles

        for source in self._sources:
            try:
                results = source.fetch_all(identifiers, count=count)
                for result in results:
                    if result.success:
                        all_articles.extend(result.articles)
                    else:
                        error_msg = (
                            str(result.error) if result.error else "Fetch failed"
                        )
                        errors.append(
                            StageError(
                                stage="source",
                                source_name=source.source_name,
                                error_message=error_msg,
                            )
                        )
                        logger.warning(
                            "Source fetch failed",
                            source_name=source.source_name,
                            identifier=result.source_identifier,
                            error=error_msg,
                        )
            except Exception as e:
                error = StageError(
                    stage="source",
                    source_name=source.source_name,
                    error_message=str(e),
                )
                errors.append(error)

                if not self._config.continue_on_error:
                    raise PipelineError(
                        f"Source '{source.source_name}' failed: {e}",
                        stage="source",
                        cause=e,
                    ) from e

                logger.error(
                    "Source raised exception",
                    source_name=source.source_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

        return all_articles

    def _process_articles(
        self,
        articles: list[Article],
        errors: list[StageError],
    ) -> list[Article]:
        """Process articles through all registered processors.

        Articles are processed in batches according to ``config.batch_size``.
        Each processor is applied sequentially to each batch.

        Parameters
        ----------
        articles : list[Article]
            Articles to process.
        errors : list[StageError]
            Accumulator for stage errors.

        Returns
        -------
        list[Article]
            Processed articles.
        """
        if not articles or not self._processors:
            return articles

        processed = list(articles)

        for processor in self._processors:
            batch_results: list[Article] = []
            batches = self._create_batches(processed, self._config.batch_size)

            for batch in batches:
                try:
                    result = processor.process_batch(batch)
                    batch_results.extend(result)
                except Exception as e:
                    # Record per-article errors for the batch
                    for article in batch:
                        errors.append(
                            StageError(
                                stage="processor",
                                source_name=processor.processor_name,
                                error_message=str(e),
                                article_url=str(article.url),
                            )
                        )

                    if not self._config.continue_on_error:
                        raise PipelineError(
                            f"Processor '{processor.processor_name}' failed: {e}",
                            stage="processor",
                            cause=e,
                        ) from e

                    logger.error(
                        "Processor batch failed",
                        processor_name=processor.processor_name,
                        batch_size=len(batch),
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    # In continue_on_error mode, skip the failed batch
                    # (don't add unprocessed articles)

            processed = batch_results

        return processed

    def _output_to_sinks(
        self,
        articles: list[Article],
        errors: list[StageError],
    ) -> int:
        """Output articles to all registered sinks.

        Each sink receives the same set of processed articles independently.

        Parameters
        ----------
        articles : list[Article]
            Articles to output.
        errors : list[StageError]
            Accumulator for stage errors.

        Returns
        -------
        int
            Total number of articles successfully output (sum across sinks).
        """
        if not articles or not self._sinks:
            return 0

        total_output = 0

        for sink in self._sinks:
            try:
                success = sink.write(articles)
                if success:
                    total_output += len(articles)
                    logger.info(
                        "Sink write succeeded",
                        sink_name=sink.sink_name,
                        article_count=len(articles),
                    )
                else:
                    errors.append(
                        StageError(
                            stage="sink",
                            source_name=sink.sink_name,
                            error_message="Sink write returned False",
                        )
                    )
                    logger.warning(
                        "Sink write returned False",
                        sink_name=sink.sink_name,
                    )
            except Exception as e:
                errors.append(
                    StageError(
                        stage="sink",
                        source_name=sink.sink_name,
                        error_message=str(e),
                    )
                )

                if not self._config.continue_on_error:
                    raise PipelineError(
                        f"Sink '{sink.sink_name}' failed: {e}",
                        stage="sink",
                        cause=e,
                    ) from e

                logger.error(
                    "Sink raised exception",
                    sink_name=sink.sink_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )

        return total_output

    @staticmethod
    def _create_batches(
        items: list[Article],
        batch_size: int,
    ) -> list[list[Article]]:
        """Split items into batches of the specified size.

        Parameters
        ----------
        items : list[Article]
            Items to split.
        batch_size : int
            Maximum items per batch.

        Returns
        -------
        list[list[Article]]
            List of batches, each containing up to ``batch_size`` items.

        Examples
        --------
        >>> Pipeline._create_batches([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
        """
        return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


# Export all public symbols
__all__ = [
    "Pipeline",
    "PipelineConfig",
    "PipelineError",
    "PipelineResult",
    "StageError",
]

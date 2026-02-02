"""Main collector module for news aggregation.

This module provides the Collector class that orchestrates news collection
from multiple sources and outputs to multiple sinks.

Examples
--------
>>> from news.collector import Collector
>>> collector = Collector()
>>> source = YFinanceTickerSource()
>>> sink = JsonFileSink(path="output.json")
>>> collector.register_source(source)
>>> collector.register_sink(sink)
>>> result = collector.collect()
>>> result.success
True
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from utils_core.logging import get_logger

from .core.result import FetchResult
from .core.sink import SinkProtocol
from .core.source import SourceProtocol

logger = get_logger(__name__, module="collector")


class CollectorConfig(BaseModel):
    """Configuration for the Collector.

    Parameters
    ----------
    max_articles_per_source : int
        Maximum number of articles to fetch per source (default: 10).
    continue_on_source_error : bool
        Whether to continue if a source fails (default: True).
    continue_on_sink_error : bool
        Whether to continue if a sink fails (default: True).

    Examples
    --------
    >>> config = CollectorConfig()
    >>> config.max_articles_per_source
    10
    """

    max_articles_per_source: int = Field(
        default=10,
        ge=1,
        description="Maximum number of articles to fetch per source",
    )
    continue_on_source_error: bool = Field(
        default=True,
        description="Whether to continue if a source fails",
    )
    continue_on_sink_error: bool = Field(
        default=True,
        description="Whether to continue if a sink fails",
    )


@dataclass
class CollectionResult:
    """Result of a collection operation.

    Attributes
    ----------
    success : bool
        Whether the collection was overall successful.
    total_articles : int
        Total number of articles collected.
    sources_processed : int
        Number of sources that were processed.
    sinks_written : int
        Number of sinks that received data.
    source_errors : dict[str, str]
        Mapping of source names to error messages.
    sink_errors : dict[str, str]
        Mapping of sink names to error messages.
    no_sinks_warning : bool
        Whether collection completed without any sinks.
    collected_at : datetime
        Timestamp when the collection occurred.

    Examples
    --------
    >>> result = CollectionResult(
    ...     success=True,
    ...     total_articles=5,
    ...     sources_processed=2,
    ...     sinks_written=1,
    ... )
    >>> result.success
    True
    """

    success: bool
    total_articles: int = 0
    sources_processed: int = 0
    sinks_written: int = 0
    source_errors: dict[str, str] = field(default_factory=dict)
    sink_errors: dict[str, str] = field(default_factory=dict)
    no_sinks_warning: bool = False
    collected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


class Collector:
    """Main orchestrator for news collection.

    This class manages news sources and sinks, coordinating the collection
    process from multiple sources and output to multiple destinations.

    Parameters
    ----------
    config : CollectorConfig | None, optional
        Configuration for the collector. If None, uses default settings.

    Attributes
    ----------
    sources : dict[str, SourceProtocol]
        Registered news sources.
    sinks : dict[str, SinkProtocol]
        Registered output sinks.

    Examples
    --------
    >>> collector = Collector()
    >>> collector.register_source(my_source)
    >>> collector.register_sink(my_sink)
    >>> result = collector.collect()
    >>> print(f"Collected {result.total_articles} articles")
    """

    def __init__(self, config: CollectorConfig | None = None) -> None:
        """Initialize the Collector with optional configuration."""
        self._config = config or CollectorConfig()
        self._sources: dict[str, SourceProtocol] = {}
        self._sinks: dict[str, SinkProtocol] = {}
        logger.info("Collector initialized")

    @property
    def sources(self) -> dict[str, SourceProtocol]:
        """Return registered sources."""
        return self._sources

    @property
    def sinks(self) -> dict[str, SinkProtocol]:
        """Return registered sinks."""
        return self._sinks

    def register_source(self, source: SourceProtocol) -> None:
        """Register a news source.

        Parameters
        ----------
        source : SourceProtocol
            The source to register.

        Raises
        ------
        ValueError
            If a source with the same name is already registered.

        Examples
        --------
        >>> collector = Collector()
        >>> source = MySource()
        >>> collector.register_source(source)
        """
        name = source.source_name
        if name in self._sources:
            msg = f"Source '{name}' is already registered"
            logger.error(msg)
            raise ValueError(msg)
        self._sources[name] = source
        logger.info("Source registered", source_name=name)

    def register_sink(self, sink: SinkProtocol) -> None:
        """Register an output sink.

        Parameters
        ----------
        sink : SinkProtocol
            The sink to register.

        Raises
        ------
        ValueError
            If a sink with the same name is already registered.

        Examples
        --------
        >>> collector = Collector()
        >>> sink = MySink()
        >>> collector.register_sink(sink)
        """
        name = sink.sink_name
        if name in self._sinks:
            msg = f"Sink '{name}' is already registered"
            logger.error(msg)
            raise ValueError(msg)
        self._sinks[name] = sink
        logger.info("Sink registered", sink_name=name)

    def collect(self) -> CollectionResult:
        """Collect news from all sources and write to all sinks.

        Returns
        -------
        CollectionResult
            Result of the collection operation including statistics
            and any errors encountered.

        Notes
        -----
        - If one source fails, other sources are still processed.
        - If one sink fails, other sinks are still written to.
        - Success is determined by whether any articles were collected
          or if there were no sources to collect from.

        Examples
        --------
        >>> collector = Collector()
        >>> collector.register_source(source)
        >>> collector.register_sink(sink)
        >>> result = collector.collect()
        >>> if result.success:
        ...     print(f"Collected {result.total_articles} articles")
        """
        logger.info(
            "Starting collection",
            sources=list(self._sources.keys()),
            sinks=list(self._sinks.keys()),
        )

        # Collect from all sources
        all_results, source_errors, sources_processed = self._collect_from_sources()

        # Aggregate articles
        all_articles = self._aggregate_articles(all_results)
        total_articles = len(all_articles)

        logger.info(
            "Collection phase completed",
            total_articles=total_articles,
            sources_processed=sources_processed,
            source_errors=len(source_errors),
        )

        # Write to all sinks
        no_sinks_warning = len(self._sinks) == 0
        if no_sinks_warning:
            logger.warning("No sinks registered, articles collected but not written")

        sink_errors, sinks_written = self._write_to_sinks(all_articles)

        # Determine success
        success = self._determine_success(total_articles, source_errors)

        result = CollectionResult(
            success=success,
            total_articles=total_articles,
            sources_processed=sources_processed,
            sinks_written=sinks_written,
            source_errors=source_errors,
            sink_errors=sink_errors,
            no_sinks_warning=no_sinks_warning,
        )

        logger.info(
            "Collection completed",
            success=result.success,
            total_articles=result.total_articles,
            sources_processed=result.sources_processed,
            sinks_written=result.sinks_written,
        )

        return result

    def _collect_from_sources(
        self,
    ) -> tuple[list[FetchResult], dict[str, str], int]:
        """Collect articles from all registered sources.

        Returns
        -------
        tuple[list[FetchResult], dict[str, str], int]
            Tuple of (successful results, errors, sources processed count).
        """
        all_results: list[FetchResult] = []
        source_errors: dict[str, str] = {}
        sources_processed = 0

        for name, source in self._sources.items():
            logger.debug("Fetching from source", source_name=name)
            try:
                result = source.fetch("", self._config.max_articles_per_source)
                sources_processed += 1
                if result.success:
                    all_results.append(result)
                    logger.info(
                        "Source fetch completed",
                        source_name=name,
                        articles=result.article_count,
                    )
                else:
                    error_msg = str(result.error) if result.error else "Unknown error"
                    source_errors[name] = error_msg
                    logger.warning(
                        "Source fetch failed",
                        source_name=name,
                        error=error_msg,
                    )
            except Exception as e:
                source_errors[name] = str(e)
                logger.error(
                    "Source fetch exception",
                    source_name=name,
                    error=str(e),
                    exc_info=True,
                )
                if not self._config.continue_on_source_error:
                    break

        return all_results, source_errors, sources_processed

    def _aggregate_articles(
        self,
        results: list[FetchResult],
    ) -> list:
        """Aggregate articles from multiple fetch results.

        Parameters
        ----------
        results : list[FetchResult]
            List of fetch results to aggregate.

        Returns
        -------
        list
            Combined list of articles from all results.
        """
        all_articles = []
        for result in results:
            all_articles.extend(result.articles)
        return all_articles

    def _write_to_sinks(
        self,
        articles: list,
    ) -> tuple[dict[str, str], int]:
        """Write articles to all registered sinks.

        Parameters
        ----------
        articles : list
            Articles to write.

        Returns
        -------
        tuple[dict[str, str], int]
            Tuple of (errors, sinks written count).
        """
        sink_errors: dict[str, str] = {}
        sinks_written = 0

        for name, sink in self._sinks.items():
            logger.debug("Writing to sink", sink_name=name)
            try:
                success = sink.write(articles)
                if success:
                    sinks_written += 1
                    logger.info(
                        "Sink write completed",
                        sink_name=name,
                        articles=len(articles),
                    )
                else:
                    sink_errors[name] = "Write operation returned False"
                    logger.warning("Sink write failed", sink_name=name)
            except Exception as e:
                sink_errors[name] = str(e)
                logger.error(
                    "Sink write exception",
                    sink_name=name,
                    error=str(e),
                    exc_info=True,
                )
                if not self._config.continue_on_sink_error:
                    break

        return sink_errors, sinks_written

    def _determine_success(
        self,
        total_articles: int,
        source_errors: dict[str, str],
    ) -> bool:
        """Determine if the collection was successful.

        Success is determined by:
        - We collected some articles, OR
        - There were no sources (empty collection is valid), OR
        - Not all sources failed

        Parameters
        ----------
        total_articles : int
            Number of articles collected.
        source_errors : dict[str, str]
            Mapping of source names to error messages.

        Returns
        -------
        bool
            True if collection was successful.
        """
        if len(self._sources) == 0:
            return True
        if total_articles > 0:
            return True
        return len(source_errors) != len(self._sources)

    def collect_from_source(self, source_name: str) -> FetchResult:
        """Collect news from a specific source.

        Parameters
        ----------
        source_name : str
            Name of the source to collect from.

        Returns
        -------
        FetchResult
            Result of fetching from the specified source.

        Raises
        ------
        KeyError
            If the source is not found.

        Examples
        --------
        >>> collector = Collector()
        >>> collector.register_source(source)
        >>> result = collector.collect_from_source("my_source")
        >>> result.success
        True
        """
        if source_name not in self._sources:
            msg = f"Source '{source_name}' not found"
            logger.error(msg, available_sources=list(self._sources.keys()))
            raise KeyError(msg)

        source = self._sources[source_name]
        logger.info("Collecting from specific source", source_name=source_name)

        result = source.fetch("", self._config.max_articles_per_source)
        logger.info(
            "Collection from source completed",
            source_name=source_name,
            success=result.success,
            articles=result.article_count,
        )

        return result


# Export all public symbols
__all__ = [
    "CollectionResult",
    "Collector",
    "CollectorConfig",
]

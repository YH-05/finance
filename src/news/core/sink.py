"""Output destination protocol for the news package.

This module defines the SinkProtocol, an abstract interface for writing
news to various destinations (file, GitHub Issue, report, etc.).

Examples
--------
>>> class JsonFileSink:
...     @property
...     def sink_name(self) -> str:
...         return "json_file"
...
...     @property
...     def sink_type(self) -> SinkType:
...         return SinkType.FILE
...
...     def write(
...         self,
...         articles: list[Article],
...         metadata: dict | None = None,
...     ) -> bool:
...         # Implementation here
...         ...
...
...     def write_batch(self, results: list[FetchResult]) -> bool:
...         # Implementation here
...         ...
"""

from enum import Enum
from typing import Protocol, runtime_checkable

from ..utils.logging_config import get_logger
from .article import Article
from .result import FetchResult

logger = get_logger(__name__, module="sink")


class SinkType(str, Enum):
    """Sink type enumeration for news output destinations.

    Represents the type of output destination for news articles.

    Attributes
    ----------
    FILE : str
        File-based output (JSON, Parquet, Markdown, etc.).
    GITHUB : str
        GitHub-based output (Issue, Project, etc.).
    REPORT : str
        Report-based output (weekly report data, etc.).
    """

    FILE = "file"
    GITHUB = "github"
    REPORT = "report"


@runtime_checkable
class SinkProtocol(Protocol):
    """Protocol for news output destinations.

    This protocol defines the interface that all news output destinations must
    implement. It provides a unified way to write news to different destinations
    (file, GitHub Issue, report, etc.).

    Attributes
    ----------
    sink_name : str
        Human-readable name of the sink (e.g., "json_file").
    sink_type : SinkType
        Type of the sink from the SinkType enum.

    Methods
    -------
    write(articles, metadata=None)
        Write articles to the destination.
    write_batch(results)
        Write multiple fetch results to the destination.

    Notes
    -----
    - This is a `Protocol` class, so implementations don't need to
      explicitly inherit from it.
    - The `@runtime_checkable` decorator enables `isinstance()` checks.
    - Implementations should handle errors gracefully and return
      `False` on failure rather than raising exceptions.

    Examples
    --------
    Creating a custom sink:

    >>> class MySink:
    ...     @property
    ...     def sink_name(self) -> str:
    ...         return "my_sink"
    ...
    ...     @property
    ...     def sink_type(self) -> SinkType:
    ...         return SinkType.FILE
    ...
    ...     def write(
    ...         self,
    ...         articles: list[Article],
    ...         metadata: dict | None = None,
    ...     ) -> bool:
    ...         # Write articles to destination
    ...         ...
    ...
    ...     def write_batch(self, results: list[FetchResult]) -> bool:
    ...         for result in results:
    ...             if not self.write(result.articles):
    ...                 return False
    ...         return True

    Checking if an object implements the protocol:

    >>> isinstance(MySink(), SinkProtocol)
    True
    """

    @property
    def sink_name(self) -> str:
        """Name of the output destination.

        Returns
        -------
        str
            Human-readable name identifying this sink.
            Examples: "json_file", "github_issue", "weekly_report".

        Notes
        -----
        This name is used for logging and identifying the sink
        in output operations.
        """
        ...

    @property
    def sink_type(self) -> SinkType:
        """Type of the output destination.

        Returns
        -------
        SinkType
            The SinkType enum value for this sink.

        Notes
        -----
        This type is used to categorize the output destination
        (file, GitHub, report, etc.).
        """
        ...

    def write(
        self,
        articles: list[Article],
        metadata: dict | None = None,
    ) -> bool:
        """Write articles to the destination.

        Parameters
        ----------
        articles : list[Article]
            List of articles to write.
        metadata : dict | None, optional
            Additional metadata to include in the output (default: None).
            Examples: {"source": "test", "timestamp": "2026-01-28"}.

        Returns
        -------
        bool
            True if the write operation succeeded, False otherwise.

        Notes
        -----
        - Implementations should handle errors gracefully and return
          `False` rather than raising exceptions.
        - Empty `articles` list should be handled gracefully (return True).
        - The `metadata` parameter is optional and may be ignored by
          implementations that don't support it.

        Examples
        --------
        >>> sink = JsonFileSink(path="output.json")
        >>> success = sink.write(articles, metadata={"version": "1.0"})
        >>> success
        True
        """
        ...

    def write_batch(self, results: list[FetchResult]) -> bool:
        """Write multiple fetch results to the destination.

        Parameters
        ----------
        results : list[FetchResult]
            List of FetchResult objects to write.
            Each FetchResult contains articles and metadata about the fetch.

        Returns
        -------
        bool
            True if all write operations succeeded, False otherwise.

        Notes
        -----
        - If `results` is empty, should return True.
        - Each FetchResult is processed independently; a failure for one
          result may or may not affect others depending on implementation.
        - Implementations may choose to process results in parallel
          or sequentially.

        Examples
        --------
        >>> sink = JsonFileSink(path="output.json")
        >>> results = [
        ...     FetchResult(articles=[...], success=True, ticker="AAPL"),
        ...     FetchResult(articles=[...], success=True, ticker="GOOGL"),
        ... ]
        >>> success = sink.write_batch(results)
        >>> success
        True
        """
        ...


# Export all public symbols
__all__ = [
    "SinkProtocol",
    "SinkType",
]

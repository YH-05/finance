"""File output sink for the news package.

This module provides the FileSink class for writing news articles to JSON files.
It supports both overwrite and append modes, with automatic deduplication.

Examples
--------
>>> from pathlib import Path
>>> from news.sinks.file import FileSink, WriteMode
>>> sink = FileSink(output_dir=Path("data/news"))
>>> sink.write(articles)  # Writes to data/news/news_YYYYMMDD.json
True

>>> sink = FileSink(
...     output_dir=Path("data/news"),
...     write_mode=WriteMode.APPEND,
... )
>>> sink.write(articles)  # Appends to existing file
True
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path  # noqa: TC003 - used at runtime for Path operations
from typing import TYPE_CHECKING, Any

from utils_core.logging import get_logger

from ..core.sink import SinkType

if TYPE_CHECKING:
    from ..core.article import Article
    from ..core.result import FetchResult

logger = get_logger(__name__, module="sinks.file")


class WriteMode(str, Enum):
    """Write mode for file output.

    Attributes
    ----------
    OVERWRITE : str
        Overwrite existing file with new content.
    APPEND : str
        Append new articles to existing file (with deduplication).
    """

    OVERWRITE = "overwrite"
    APPEND = "append"


class FileSink:
    """File-based output sink for news articles.

    Writes news articles to JSON files with configurable output path,
    filename pattern, and write mode.

    Parameters
    ----------
    output_dir : Path
        Directory path for output files.
    write_mode : WriteMode, optional
        Write mode (OVERWRITE or APPEND). Default is OVERWRITE.
    filename_pattern : str, optional
        Pattern for output filenames. Default is "news_{date}.json".
        The {date} placeholder is replaced with YYYYMMDD format.

    Attributes
    ----------
    output_dir : Path
        Directory path for output files.
    write_mode : WriteMode
        Current write mode.
    filename_pattern : str
        Pattern for output filenames.

    Examples
    --------
    >>> sink = FileSink(output_dir=Path("data/news"))
    >>> sink.sink_name
    'json_file'
    >>> sink.sink_type
    <SinkType.FILE: 'file'>

    Notes
    -----
    - The output directory is created automatically if it doesn't exist.
    - In APPEND mode, duplicate articles (same URL) are skipped.
    - The JSON output format follows the project.md specification.
    """

    def __init__(
        self,
        output_dir: Path,
        write_mode: WriteMode = WriteMode.OVERWRITE,
        filename_pattern: str = "news_{date}.json",
    ) -> None:
        """Initialize FileSink with output configuration.

        Parameters
        ----------
        output_dir : Path
            Directory path for output files.
        write_mode : WriteMode, optional
            Write mode. Default is OVERWRITE.
        filename_pattern : str, optional
            Pattern for output filenames. Default is "news_{date}.json".
        """
        self._output_dir = output_dir
        self._write_mode = write_mode
        self._filename_pattern = filename_pattern

        logger.info(
            "FileSink initialized",
            output_dir=str(output_dir),
            write_mode=write_mode.value,
            filename_pattern=filename_pattern,
        )

    @property
    def output_dir(self) -> Path:
        """Return the output directory path.

        Returns
        -------
        Path
            Directory path for output files.
        """
        return self._output_dir

    @property
    def write_mode(self) -> WriteMode:
        """Return the current write mode.

        Returns
        -------
        WriteMode
            Current write mode (OVERWRITE or APPEND).
        """
        return self._write_mode

    @property
    def filename_pattern(self) -> str:
        """Return the filename pattern.

        Returns
        -------
        str
            Pattern for output filenames.
        """
        return self._filename_pattern

    @property
    def sink_name(self) -> str:
        """Return the sink name.

        Returns
        -------
        str
            The name "json_file".
        """
        return "json_file"

    @property
    def sink_type(self) -> SinkType:
        """Return the sink type.

        Returns
        -------
        SinkType
            SinkType.FILE.
        """
        return SinkType.FILE

    def write(
        self,
        articles: list[Article],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Write articles to a JSON file.

        Parameters
        ----------
        articles : list[Article]
            List of articles to write.
        metadata : dict[str, Any] | None, optional
            Additional metadata to include in the output. Default is None.

        Returns
        -------
        bool
            True if the write operation succeeded, False otherwise.

        Notes
        -----
        - Empty articles list is handled gracefully (returns True).
        - Directory is created if it doesn't exist.
        - In APPEND mode, duplicate URLs are skipped.
        """
        if not articles:
            logger.debug("No articles to write, returning True")
            return True

        try:
            output_path = self._get_output_path()
            self._ensure_directory_exists()

            if self._write_mode == WriteMode.APPEND and output_path.exists():
                return self._append_to_file(output_path, articles, metadata)
            else:
                return self._write_new_file(output_path, articles, metadata)

        except PermissionError as e:
            logger.error(
                "Permission denied when writing file",
                error=str(e),
                output_dir=str(self._output_dir),
            )
            return False
        except OSError as e:
            logger.error(
                "OS error when writing file",
                error=str(e),
                output_dir=str(self._output_dir),
            )
            return False
        except Exception as e:
            logger.error(
                "Unexpected error when writing file",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def write_batch(self, results: list[FetchResult]) -> bool:
        """Write multiple fetch results to a JSON file.

        Parameters
        ----------
        results : list[FetchResult]
            List of FetchResult objects to write.

        Returns
        -------
        bool
            True if all write operations succeeded, False otherwise.

        Notes
        -----
        - Only successful FetchResults (success=True) are included.
        - All articles from all results are written to a single file.
        """
        if not results:
            logger.debug("No results to write, returning True")
            return True

        # Collect all articles from successful results
        all_articles: list[Article] = []
        for result in results:
            if result.success:
                all_articles.extend(result.articles)
            else:
                logger.debug(
                    "Skipping failed FetchResult",
                    source_identifier=result.source_identifier,
                )

        return self.write(all_articles)

    def _get_output_path(self) -> Path:
        """Generate the output file path based on the pattern.

        Returns
        -------
        Path
            The full path to the output file.
        """
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        filename = self._filename_pattern.replace("{date}", today)
        return self._output_dir / filename

    def _ensure_directory_exists(self) -> None:
        """Create the output directory if it doesn't exist."""
        if not self._output_dir.exists():
            self._output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                "Created output directory",
                output_dir=str(self._output_dir),
            )

    def _write_new_file(
        self,
        output_path: Path,
        articles: list[Article],
        metadata: dict[str, Any] | None,
    ) -> bool:
        """Write articles to a new JSON file.

        Parameters
        ----------
        output_path : Path
            Path to the output file.
        articles : list[Article]
            List of articles to write.
        metadata : dict[str, Any] | None
            Additional metadata to include.

        Returns
        -------
        bool
            True if successful.
        """
        data = self._create_output_data(articles, metadata)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(
            "Written articles to file",
            output_path=str(output_path),
            article_count=len(articles),
        )
        return True

    def _append_to_file(
        self,
        output_path: Path,
        articles: list[Article],
        metadata: dict[str, Any] | None,
    ) -> bool:
        """Append articles to an existing JSON file.

        Parameters
        ----------
        output_path : Path
            Path to the output file.
        articles : list[Article]
            List of articles to append.
        metadata : dict[str, Any] | None
            Additional metadata to include.

        Returns
        -------
        bool
            True if successful.
        """
        # Read existing data
        with output_path.open(encoding="utf-8") as f:
            existing_data = json.load(f)

        # Get existing URLs for deduplication
        existing_urls: set[str] = set()
        for article_data in existing_data.get("articles", []):
            if "url" in article_data:
                existing_urls.add(article_data["url"])

        # Filter out duplicate articles
        new_articles = [
            article for article in articles if str(article.url) not in existing_urls
        ]

        if not new_articles:
            logger.debug(
                "No new articles to append (all duplicates)",
                total_articles=len(articles),
            )
            return True

        # Convert new articles to dict
        new_articles_data = [self._article_to_dict(article) for article in new_articles]

        # Merge articles
        existing_data["articles"].extend(new_articles_data)

        # Update metadata
        existing_sources = set(existing_data["meta"].get("sources", []))
        for article in new_articles:
            existing_sources.add(article.source.value)
        existing_data["meta"]["sources"] = sorted(existing_sources)
        existing_data["meta"]["article_count"] = len(existing_data["articles"])
        existing_data["meta"]["fetched_at"] = datetime.now(timezone.utc).isoformat()

        # Add custom metadata
        if metadata:
            for key, value in metadata.items():
                existing_data["meta"][key] = value

        # Write back
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(
            "Appended articles to file",
            output_path=str(output_path),
            new_article_count=len(new_articles),
            total_article_count=len(existing_data["articles"]),
        )
        return True

    def _create_output_data(
        self,
        articles: list[Article],
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Create the JSON output data structure.

        Parameters
        ----------
        articles : list[Article]
            List of articles.
        metadata : dict[str, Any] | None
            Additional metadata.

        Returns
        -------
        dict[str, Any]
            The JSON-serializable output data.
        """
        # Collect unique sources
        sources = sorted({article.source.value for article in articles})

        # Build meta section
        meta: dict[str, Any] = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "sources": sources,
            "article_count": len(articles),
            "version": "1.0",
        }

        # Add custom metadata
        if metadata:
            meta.update(metadata)

        # Convert articles to dict
        articles_data = [self._article_to_dict(article) for article in articles]

        return {
            "meta": meta,
            "articles": articles_data,
        }

    def _article_to_dict(self, article: Article) -> dict[str, Any]:
        """Convert an Article to a JSON-serializable dictionary.

        Parameters
        ----------
        article : Article
            The article to convert.

        Returns
        -------
        dict[str, Any]
            The article as a dictionary.
        """
        return {
            "url": str(article.url),
            "title": article.title,
            "published_at": article.published_at.isoformat(),
            "source": article.source.value,
            "summary": article.summary,
            "content_type": article.content_type.value,
            "provider": (
                {
                    "name": article.provider.name,
                    "url": str(article.provider.url) if article.provider.url else None,
                }
                if article.provider
                else None
            ),
            "thumbnail": (
                {
                    "url": str(article.thumbnail.url),
                    "width": article.thumbnail.width,
                    "height": article.thumbnail.height,
                }
                if article.thumbnail
                else None
            ),
            "related_tickers": article.related_tickers,
            "tags": article.tags,
            "fetched_at": article.fetched_at.isoformat(),
            "metadata": article.metadata,
            "summary_ja": article.summary_ja,
            "category": article.category,
            "sentiment": article.sentiment,
        }


# Export all public symbols
__all__ = [
    "FileSink",
    "WriteMode",
]

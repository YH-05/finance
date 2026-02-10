"""Batch processing for SEC EDGAR filing data.

This module provides batch-level fetching and extraction classes that
parallelize operations across multiple CIK/ticker symbols or filings
using ThreadPoolExecutor.

Features
--------
- Parallel filing fetch across multiple CIK/ticker symbols
- Parallel text extraction across multiple filings
- Parallel section extraction across multiple filings
- tqdm progress bars for monitoring batch progress
- Partial-failure tolerance (failed items stored as Exception in results)

Notes
-----
Both BatchFetcher and BatchExtractor use ThreadPoolExecutor because the
underlying edgartools library performs I/O-bound network requests and
HTML parsing. ProcessPoolExecutor is avoided due to potential pickle
serialization issues with edgartools objects.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

from tqdm import tqdm

from edgar.extractors.section import SectionExtractor
from edgar.extractors.text import TextExtractor
from edgar.fetcher import EdgarFetcher
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from edgar.types import FilingType

logger = get_logger(__name__)


def _run_batch[T, R](
    items: list[T],
    key_fn: Callable[[T], str],
    task_fn: Callable[[T], R],
    desc: str,
    max_workers: int,
) -> dict[str, R | Exception]:
    """Execute tasks in parallel using ThreadPoolExecutor with progress tracking.

    This is the common batch execution helper that encapsulates the
    ThreadPoolExecutor + tqdm + partial-failure-tolerance pattern used
    throughout this module.

    Parameters
    ----------
    items : list[T]
        The input items to process in parallel
    key_fn : Callable[[T], str]
        Function to extract a string key from each item for the result dict
    task_fn : Callable[[T], R]
        Function to execute for each item. Receives the item and returns
        the result value. If it raises, the exception is stored in the
        result dict under the item's key.
    desc : str
        Description shown in the tqdm progress bar
    max_workers : int
        Maximum number of concurrent threads

    Returns
    -------
    dict[str, R | Exception]
        Mapping of item keys to results on success, or Exception on failure
    """
    results: dict[str, R | Exception] = {}

    if not items:
        return results

    total = len(items)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {executor.submit(task_fn, item): key_fn(item) for item in items}

        with tqdm(total=total, desc=desc) as pbar:
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as exc:
                    results[key] = exc
                    logger.warning(
                        "Batch task failed",
                        key=key,
                        error=str(exc),
                        error_type=type(exc).__name__,
                    )
                pbar.update(1)

    return results


class BatchFetcher:
    """Batch fetcher for SEC EDGAR filings across multiple companies.

    Wraps EdgarFetcher to provide parallel filing retrieval for multiple
    CIK numbers or ticker symbols using ThreadPoolExecutor.

    Parameters
    ----------
    fetcher : EdgarFetcher | None
        An existing EdgarFetcher instance. If None, a new instance is created.

    Attributes
    ----------
    _fetcher : EdgarFetcher
        The underlying fetcher instance

    Examples
    --------
    >>> batch = BatchFetcher()
    >>> results = batch.fetch_batch(["AAPL", "MSFT"], FilingType.FORM_10K, limit=5)
    >>> for ticker, filings_or_error in results.items():
    ...     if isinstance(filings_or_error, Exception):
    ...         print(f"{ticker}: error - {filings_or_error}")
    ...     else:
    ...         print(f"{ticker}: {len(filings_or_error)} filings")
    """

    def __init__(self, fetcher: EdgarFetcher | None = None) -> None:
        """Initialize BatchFetcher.

        Parameters
        ----------
        fetcher : EdgarFetcher | None
            An existing EdgarFetcher instance. If None, a new default
            instance is created.
        """
        self._fetcher = fetcher if fetcher is not None else EdgarFetcher()
        logger.debug("Initializing BatchFetcher")

    def fetch_batch(
        self,
        cik_or_tickers: list[str],
        form: FilingType,
        limit: int = 10,
        max_workers: int = 5,
    ) -> dict[str, list[Any] | Exception]:
        """Fetch filings for multiple companies in parallel.

        Uses ThreadPoolExecutor to parallelize I/O-bound SEC EDGAR requests.
        If a single company's fetch fails, the exception is stored in the
        result dict and processing continues for other companies.

        Parameters
        ----------
        cik_or_tickers : list[str]
            List of CIK numbers or ticker symbols (e.g., ["AAPL", "MSFT"])
        form : FilingType
            The filing form type to filter by
        limit : int, default=10
            Maximum number of filings to return per company
        max_workers : int, default=5
            Maximum number of concurrent threads

        Returns
        -------
        dict[str, list[Any] | Exception]
            Mapping of CIK/ticker to a list of Filing objects on success,
            or an Exception instance on failure

        Examples
        --------
        >>> batch = BatchFetcher()
        >>> results = batch.fetch_batch(
        ...     ["AAPL", "MSFT"], FilingType.FORM_10K, limit=3
        ... )
        """
        logger.info(
            "Starting batch fetch",
            total=len(cik_or_tickers),
            form=form.value,
            limit=limit,
            max_workers=max_workers,
        )

        results = _run_batch(
            items=cik_or_tickers,
            key_fn=lambda ticker: ticker,
            task_fn=lambda ticker: self._fetcher.fetch(ticker, form, limit),
            desc="Fetching filings",
            max_workers=max_workers,
        )

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failure_count = len(cik_or_tickers) - success_count

        logger.info(
            "Batch fetch completed",
            total=len(cik_or_tickers),
            success_count=success_count,
            failure_count=failure_count,
        )

        return results

    def fetch_latest_batch(
        self,
        cik_or_tickers: list[str],
        form: FilingType,
        max_workers: int = 5,
    ) -> dict[str, Any | None | Exception]:
        """Fetch the latest filing for multiple companies in parallel.

        Uses ThreadPoolExecutor to parallelize I/O-bound SEC EDGAR requests.
        Each company returns at most one filing (the latest). If a single
        company's fetch fails, the exception is stored in the result dict.

        Parameters
        ----------
        cik_or_tickers : list[str]
            List of CIK numbers or ticker symbols (e.g., ["AAPL", "MSFT"])
        form : FilingType
            The filing form type to filter by
        max_workers : int, default=5
            Maximum number of concurrent threads

        Returns
        -------
        dict[str, Any | None | Exception]
            Mapping of CIK/ticker to the latest Filing object (or None
            if no filings found), or an Exception instance on failure

        Examples
        --------
        >>> batch = BatchFetcher()
        >>> results = batch.fetch_latest_batch(
        ...     ["AAPL", "MSFT"], FilingType.FORM_10K
        ... )
        """
        logger.info(
            "Starting batch fetch latest",
            total=len(cik_or_tickers),
            form=form.value,
            max_workers=max_workers,
        )

        results = _run_batch(
            items=cik_or_tickers,
            key_fn=lambda ticker: ticker,
            task_fn=lambda ticker: self._fetcher.fetch_latest(ticker, form),
            desc="Fetching latest filings",
            max_workers=max_workers,
        )

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failure_count = len(cik_or_tickers) - success_count

        logger.info(
            "Batch fetch latest completed",
            total=len(cik_or_tickers),
            success_count=success_count,
            failure_count=failure_count,
        )

        return results

    def __repr__(self) -> str:
        """Return string representation."""
        return f"BatchFetcher(fetcher={self._fetcher!r})"


class BatchExtractor:
    """Batch extractor for parallel text and section extraction from filings.

    Wraps TextExtractor and SectionExtractor to provide parallel extraction
    across multiple Filing objects using ThreadPoolExecutor.

    Parameters
    ----------
    text_extractor : TextExtractor | None
        An existing TextExtractor instance. If None, a new instance is created.
    section_extractor : SectionExtractor | None
        An existing SectionExtractor instance. If None, a new instance is created.

    Attributes
    ----------
    _text_extractor : TextExtractor
        The underlying text extractor instance
    _section_extractor : SectionExtractor
        The underlying section extractor instance

    Examples
    --------
    >>> batch_ext = BatchExtractor()
    >>> texts = batch_ext.extract_text_batch(filings)
    >>> sections = batch_ext.extract_sections_batch(
    ...     filings, ["item_1", "item_7"]
    ... )
    """

    def __init__(
        self,
        text_extractor: TextExtractor | None = None,
        section_extractor: SectionExtractor | None = None,
    ) -> None:
        """Initialize BatchExtractor.

        Parameters
        ----------
        text_extractor : TextExtractor | None
            An existing TextExtractor instance. If None, a new default
            instance is created.
        section_extractor : SectionExtractor | None
            An existing SectionExtractor instance. If None, a new default
            instance is created.
        """
        self._text_extractor = (
            text_extractor if text_extractor is not None else TextExtractor()
        )
        self._section_extractor = (
            section_extractor if section_extractor is not None else SectionExtractor()
        )
        logger.debug("Initializing BatchExtractor")

    def extract_text_batch(
        self,
        filings: list[Any],
        max_workers: int = 4,
    ) -> dict[str, str | Exception]:
        """Extract text from multiple filings in parallel.

        Uses ThreadPoolExecutor to parallelize text extraction. Each filing's
        result is keyed by its accession number. If extraction fails for a
        filing, the exception is stored in the result dict.

        Parameters
        ----------
        filings : list[Any]
            List of edgartools Filing objects with ``accession_number``
            attribute and ``.text()`` method
        max_workers : int, default=4
            Maximum number of concurrent threads

        Returns
        -------
        dict[str, str | Exception]
            Mapping of accession number to extracted text on success,
            or an Exception instance on failure

        Examples
        --------
        >>> batch_ext = BatchExtractor()
        >>> texts = batch_ext.extract_text_batch(filings, max_workers=4)
        >>> for acc_no, text_or_error in texts.items():
        ...     if isinstance(text_or_error, Exception):
        ...         print(f"{acc_no}: error - {text_or_error}")
        ...     else:
        ...         print(f"{acc_no}: {len(text_or_error)} chars")
        """
        logger.info(
            "Starting batch text extraction",
            total=len(filings),
            max_workers=max_workers,
        )

        indexed_filings = list(enumerate(filings))

        results = _run_batch(
            items=indexed_filings,
            key_fn=lambda item: getattr(item[1], "accession_number", str(item[0])),
            task_fn=lambda item: self._text_extractor.extract_text(item[1]),
            desc="Extracting text",
            max_workers=max_workers,
        )

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failure_count = len(filings) - success_count

        logger.info(
            "Batch text extraction completed",
            total=len(filings),
            success_count=success_count,
            failure_count=failure_count,
        )

        return results

    def extract_sections_batch(
        self,
        filings: list[Any],
        section_keys: list[str],
        max_workers: int = 4,
    ) -> dict[str, dict[str, str | None] | Exception]:
        """Extract sections from multiple filings in parallel.

        Uses ThreadPoolExecutor to parallelize section extraction. Each
        filing's result is keyed by its accession number and contains a
        dict mapping section keys to extracted text (or None if not found).
        If extraction fails for a filing, the exception is stored.

        Parameters
        ----------
        filings : list[Any]
            List of edgartools Filing objects with ``accession_number``
            attribute and text extraction methods
        section_keys : list[str]
            List of section key identifiers to extract
            (e.g., ["item_1", "item_1a", "item_7"])
        max_workers : int, default=4
            Maximum number of concurrent threads

        Returns
        -------
        dict[str, dict[str, str | None] | Exception]
            Mapping of accession number to a dict of section key to
            extracted text (or None), or an Exception on failure

        Examples
        --------
        >>> batch_ext = BatchExtractor()
        >>> sections = batch_ext.extract_sections_batch(
        ...     filings, ["item_1", "item_7"]
        ... )
        """
        logger.info(
            "Starting batch section extraction",
            total=len(filings),
            section_keys=section_keys,
            max_workers=max_workers,
        )

        indexed_filings = list(enumerate(filings))

        def _extract_sections(item: tuple[int, Any]) -> dict[str, str | None]:
            """Extract all requested sections from a single filing."""
            _index, filing = item
            sections: dict[str, str | None] = {}
            for section_key in section_keys:
                sections[section_key] = self._section_extractor.extract_section(
                    filing, section_key
                )
            return sections

        results = _run_batch(
            items=indexed_filings,
            key_fn=lambda item: getattr(item[1], "accession_number", str(item[0])),
            task_fn=_extract_sections,
            desc="Extracting sections",
            max_workers=max_workers,
        )

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failure_count = len(filings) - success_count

        logger.info(
            "Batch section extraction completed",
            total=len(filings),
            success_count=success_count,
            failure_count=failure_count,
        )

        return results

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"BatchExtractor("
            f"text_extractor={self._text_extractor!r}, "
            f"section_extractor={self._section_extractor!r})"
        )


__all__ = [
    "BatchExtractor",
    "BatchFetcher",
    "_run_batch",
]

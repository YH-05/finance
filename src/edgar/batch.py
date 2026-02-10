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
    from edgar.types import FilingType

logger = get_logger(__name__)


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
        total = len(cik_or_tickers)
        logger.info(
            "Starting batch fetch",
            total=total,
            form=form.value,
            limit=limit,
            max_workers=max_workers,
        )

        results: dict[str, list[Any] | Exception] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(
                    self._fetcher.fetch,
                    cik_or_ticker,
                    form,
                    limit,
                ): cik_or_ticker
                for cik_or_ticker in cik_or_tickers
            }

            with tqdm(total=total, desc="Fetching filings") as pbar:
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        filings = future.result()
                        results[ticker] = filings
                        logger.debug(
                            "Batch fetch succeeded",
                            cik_or_ticker=ticker,
                            filing_count=len(filings),
                        )
                    except Exception as exc:
                        results[ticker] = exc
                        logger.warning(
                            "Batch fetch failed for item",
                            cik_or_ticker=ticker,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        )
                    pbar.update(1)

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failure_count = total - success_count

        logger.info(
            "Batch fetch completed",
            total=total,
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
        total = len(cik_or_tickers)
        logger.info(
            "Starting batch fetch latest",
            total=total,
            form=form.value,
            max_workers=max_workers,
        )

        results: dict[str, Any | None | Exception] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(
                    self._fetcher.fetch_latest,
                    cik_or_ticker,
                    form,
                ): cik_or_ticker
                for cik_or_ticker in cik_or_tickers
            }

            with tqdm(total=total, desc="Fetching latest filings") as pbar:
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        filing = future.result()
                        results[ticker] = filing
                        logger.debug(
                            "Batch fetch latest succeeded",
                            cik_or_ticker=ticker,
                            found=filing is not None,
                        )
                    except Exception as exc:
                        results[ticker] = exc
                        logger.warning(
                            "Batch fetch latest failed for item",
                            cik_or_ticker=ticker,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        )
                    pbar.update(1)

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failure_count = total - success_count

        logger.info(
            "Batch fetch latest completed",
            total=total,
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
        total = len(filings)
        logger.info(
            "Starting batch text extraction",
            total=total,
            max_workers=max_workers,
        )

        results: dict[str, str | Exception] = {}

        def _extract_single(filing: Any, index: int) -> tuple[str, str]:
            """Extract text from a single filing.

            Parameters
            ----------
            filing : Any
                The filing object to extract text from
            index : int
                Fallback index for key if accession_number is not available

            Returns
            -------
            tuple[str, str]
                Tuple of (accession_number, extracted_text)
            """
            return (
                getattr(filing, "accession_number", str(index)),
                self._text_extractor.extract_text(filing),
            )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_key = {}
            for i, filing in enumerate(filings):
                key = getattr(filing, "accession_number", str(i))
                future = executor.submit(_extract_single, filing, i)
                future_to_key[future] = key

            with tqdm(total=total, desc="Extracting text") as pbar:
                for future in as_completed(future_to_key):
                    key = future_to_key[future]
                    try:
                        acc_no, text = future.result()
                        results[acc_no] = text
                        logger.debug(
                            "Batch text extraction succeeded",
                            accession_number=acc_no,
                            text_length=len(text),
                        )
                    except Exception as exc:
                        results[key] = exc
                        logger.warning(
                            "Batch text extraction failed for filing",
                            accession_number=key,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        )
                    pbar.update(1)

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failure_count = total - success_count

        logger.info(
            "Batch text extraction completed",
            total=total,
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
        total = len(filings)
        logger.info(
            "Starting batch section extraction",
            total=total,
            section_keys=section_keys,
            max_workers=max_workers,
        )

        results: dict[str, dict[str, str | None] | Exception] = {}

        def _extract_sections_single(
            filing: Any,
            index: int,
        ) -> tuple[str, dict[str, str | None]]:
            """Extract sections from a single filing.

            Parameters
            ----------
            filing : Any
                The filing object to extract sections from
            index : int
                Fallback index for key if accession_number is not available

            Returns
            -------
            tuple[str, dict[str, str | None]]
                Tuple of (accession_number, sections_dict)
            """
            acc_no = getattr(filing, "accession_number", str(index))
            sections: dict[str, str | None] = {}
            for section_key in section_keys:
                sections[section_key] = self._section_extractor.extract_section(
                    filing, section_key
                )
            return acc_no, sections

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_key = {}
            for i, filing in enumerate(filings):
                key = getattr(filing, "accession_number", str(i))
                future = executor.submit(_extract_sections_single, filing, i)
                future_to_key[future] = key

            with tqdm(total=total, desc="Extracting sections") as pbar:
                for future in as_completed(future_to_key):
                    key = future_to_key[future]
                    try:
                        acc_no, sections = future.result()
                        results[acc_no] = sections
                        found_count = sum(1 for v in sections.values() if v is not None)
                        logger.debug(
                            "Batch section extraction succeeded",
                            accession_number=acc_no,
                            requested_sections=len(section_keys),
                            found_sections=found_count,
                        )
                    except Exception as exc:
                        results[key] = exc
                        logger.warning(
                            "Batch section extraction failed for filing",
                            accession_number=key,
                            error=str(exc),
                            error_type=type(exc).__name__,
                        )
                    pbar.update(1)

        success_count = sum(1 for v in results.values() if not isinstance(v, Exception))
        failure_count = total - success_count

        logger.info(
            "Batch section extraction completed",
            total=total,
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
]

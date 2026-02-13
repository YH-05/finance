"""Report text extraction from PDF and HTML documents.

This module provides the ``ReportParser`` class for extracting text content
and metadata from PDF files (via PyMuPDF) and HTML documents (via trafilatura).

Features
--------
- PDF text extraction with page-level concatenation
- HTML text extraction using trafilatura (same library as news pipeline)
- Metadata extraction (title, author, date) from both formats
- PDF date string parsing (D:YYYYMMDDHHmmSS format)

Examples
--------
>>> from market.industry.downloaders.report_parser import ReportParser
>>> parser = ReportParser()
>>> result = parser.parse_pdf(Path("report.pdf"))
>>> print(result.text[:100])
>>> print(result.metadata.title)

See Also
--------
market.industry.downloaders.pdf_downloader : PDF download with deduplication.
news.extractors.trafilatura : Trafilatura-based extraction in the news pipeline.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from trafilatura import extract as trafilatura_extract
from trafilatura import extract_metadata as trafilatura_extract_metadata

from market.industry.types import ParsedContent, ReportMetadata
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

# Lazy import for pymupdf (heavy dependency)
_PYMUPDF_AVAILABLE = True
try:
    import pymupdf
except ImportError:
    _PYMUPDF_AVAILABLE = False

logger = get_logger(__name__)

# Regex for PDF date format: D:YYYYMMDDHHmmSS with optional timezone
_PDF_DATE_PATTERN = re.compile(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})")


class ReportParser:
    """Parser for extracting text and metadata from PDF and HTML documents.

    Uses PyMuPDF for PDF extraction and trafilatura for HTML extraction,
    following the same patterns as the existing news pipeline.

    Parameters
    ----------
    min_text_length : int
        Minimum text length to consider extraction successful.
        Defaults to 100 characters.

    Examples
    --------
    >>> parser = ReportParser()
    >>> pdf_result = parser.parse_pdf(Path("report.pdf"))
    >>> html_result = parser.parse_html("<html>...</html>")
    """

    def __init__(self, min_text_length: int = 100) -> None:
        self.min_text_length: int = min_text_length

        logger.debug(
            "ReportParser initialized",
            min_text_length=min_text_length,
        )

    # =========================================================================
    # PDF Extraction
    # =========================================================================

    def parse_pdf(self, pdf_path: Path) -> ParsedContent:
        """Extract text and metadata from a PDF file.

        Opens the PDF using PyMuPDF, extracts text from each page,
        concatenates the results, and extracts document metadata.

        Parameters
        ----------
        pdf_path : Path
            Path to the PDF file.

        Returns
        -------
        ParsedContent
            Extracted text, metadata, and page count.

        Raises
        ------
        FileNotFoundError
            If the PDF file does not exist.
        RuntimeError
            If the PDF cannot be opened or parsed.
        ImportError
            If pymupdf is not installed.

        Examples
        --------
        >>> result = parser.parse_pdf(Path("report.pdf"))
        >>> print(f"Extracted {len(result.text)} chars from {result.page_count} pages")
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not _PYMUPDF_AVAILABLE:
            raise ImportError("pymupdf is not installed. Install with: uv add pymupdf")

        logger.info("Parsing PDF", pdf_path=str(pdf_path))

        doc = pymupdf.open(str(pdf_path))

        try:
            # Extract text from all pages
            page_texts: list[str] = []
            for page in doc:
                text = str(page.get_text())
                page_texts.append(text)

            full_text = "\n\n".join(page_texts).strip()
            page_count = len(doc)

            # Extract metadata
            raw_metadata: dict[str, str] = dict(doc.metadata) if doc.metadata else {}
            metadata = self._extract_pdf_metadata(raw_metadata)

            logger.info(
                "PDF parsed successfully",
                pdf_path=str(pdf_path),
                page_count=page_count,
                text_length=len(full_text),
                has_title=metadata.title is not None,
            )

            return ParsedContent(
                text=full_text,
                source_format="pdf",
                metadata=metadata,
                page_count=page_count,
            )

        finally:
            doc.close()

    def _extract_pdf_metadata(self, raw_metadata: dict[str, str]) -> ReportMetadata:
        """Extract structured metadata from raw PDF metadata dictionary.

        Parameters
        ----------
        raw_metadata : dict[str, str]
            Raw metadata from PyMuPDF's ``doc.metadata``.

        Returns
        -------
        ReportMetadata
            Structured metadata with title, author, and date.
        """
        title = raw_metadata.get("title") or None
        author = raw_metadata.get("author") or None
        date_str = raw_metadata.get("creationDate")
        date = self._parse_pdf_date(date_str)

        return ReportMetadata(
            title=title,
            author=author,
            date=date,
        )

    def _parse_pdf_date(self, date_str: str | None) -> datetime | None:
        """Parse a PDF date string into a datetime object.

        PDF dates follow the format ``D:YYYYMMDDHHmmSS`` with optional
        timezone offset (e.g. ``D:20260115120000+00'00'``).

        Parameters
        ----------
        date_str : str | None
            The PDF date string to parse. May be ``None`` or empty.

        Returns
        -------
        datetime | None
            The parsed datetime (UTC), or ``None`` if parsing fails.

        Examples
        --------
        >>> parser._parse_pdf_date("D:20260115120000")
        datetime.datetime(2026, 1, 15, 12, 0, tzinfo=datetime.timezone.utc)
        >>> parser._parse_pdf_date("invalid")
        """
        if not date_str:
            return None

        match = _PDF_DATE_PATTERN.search(date_str)
        if not match:
            logger.debug(
                "Could not parse PDF date string",
                date_str=date_str,
            )
            return None

        try:
            year, month, day, hour, minute, second = (int(g) for g in match.groups())
            return datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
                tzinfo=timezone.utc,
            )
        except (ValueError, OverflowError) as e:
            logger.debug(
                "Invalid PDF date components",
                date_str=date_str,
                error=str(e),
            )
            return None

    # =========================================================================
    # HTML Extraction
    # =========================================================================

    def parse_html(self, html_content: str) -> ParsedContent:
        """Extract text and metadata from HTML content.

        Uses trafilatura for text extraction and metadata parsing,
        following the same approach as the news pipeline's
        ``TrafilaturaExtractor``.

        Parameters
        ----------
        html_content : str
            Raw HTML content to parse.

        Returns
        -------
        ParsedContent
            Extracted text and metadata. Text is empty string if
            extraction yields no content.

        Examples
        --------
        >>> result = parser.parse_html("<html><body><p>Report...</p></body></html>")
        >>> print(result.text)
        """
        logger.info(
            "Parsing HTML content",
            html_length=len(html_content),
        )

        # Extract text using trafilatura
        extracted_text = trafilatura_extract(html_content)
        text = extracted_text if extracted_text else ""

        # Extract metadata
        metadata = self._extract_html_metadata(html_content)

        logger.info(
            "HTML parsed successfully",
            text_length=len(text),
            has_title=metadata.title is not None if metadata else False,
        )

        return ParsedContent(
            text=text,
            source_format="html",
            metadata=metadata,
        )

    def _extract_html_metadata(self, html_content: str) -> ReportMetadata | None:
        """Extract metadata from HTML content using trafilatura.

        Parameters
        ----------
        html_content : str
            Raw HTML content.

        Returns
        -------
        ReportMetadata | None
            Extracted metadata, or ``None`` if extraction fails.
        """
        try:
            meta_result = trafilatura_extract_metadata(html_content)

            title = getattr(meta_result, "title", None) or None
            author = getattr(meta_result, "author", None) or None
            date_str = getattr(meta_result, "date", None)

            date: datetime | None = None
            if date_str:
                try:
                    date = datetime.strptime(str(date_str), "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    logger.debug(
                        "Could not parse HTML date",
                        date_str=str(date_str),
                    )

            return ReportMetadata(
                title=title,
                author=author,
                date=date,
            )

        except Exception as e:
            logger.debug(
                "HTML metadata extraction failed",
                error=str(e),
            )
            return None


__all__ = ["ReportParser"]

"""PDF link detection and download handler.

Provides utilities to detect PDF URLs, find PDF links within HTML content,
and download PDF files to local storage with metadata tracking.

Designed for the AI investment value chain tracking pipeline where
company press releases and reports are often published as PDFs.

Examples
--------
URL-based PDF detection:

    >>> is_pdf_url("https://example.com/report.pdf")
    True
    >>> is_pdf_url("https://example.com/article.html")
    False

HTML PDF link extraction:

    >>> html = '<a href="https://example.com/report.pdf">Report</a>'
    >>> find_pdf_links(html)
    ['https://example.com/report.pdf']

Download a PDF:

    >>> import asyncio
    >>> handler = PdfHandler()
    >>> metadata = asyncio.run(handler.download("https://example.com/report.pdf", "nvidia"))
    >>> metadata.filename
    'report.pdf'
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from lxml.html import fromstring

from .types import PdfMetadata


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from utils_core.logging import get_logger

        return get_logger(__name__, module="pdf_handler")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_BASE_DIR = Path("data/raw/ai-research/pdfs")
"""Default directory for storing downloaded PDFs."""

_HTTPX_TIMEOUT = 30
"""Timeout in seconds for PDF download requests."""

_DEFAULT_FILENAME = "document.pdf"
"""Fallback filename when URL path does not contain a filename."""

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
"""User-Agent header for HTTP requests."""


# ---------------------------------------------------------------------------
# is_pdf_url
# ---------------------------------------------------------------------------


def is_pdf_url(url: str) -> bool:
    """Check whether a URL points to a PDF file by its extension.

    Examines the URL path (ignoring query parameters and fragments)
    to determine if the file extension is ``.pdf`` (case-insensitive).

    Parameters
    ----------
    url : str
        URL to check.

    Returns
    -------
    bool
        True if the URL path ends with ``.pdf``, False otherwise.

    Examples
    --------
    >>> is_pdf_url("https://example.com/report.pdf")
    True
    >>> is_pdf_url("https://example.com/report.pdf?token=abc")
    True
    >>> is_pdf_url("https://example.com/article.html")
    False
    """
    if not url:
        return False

    parsed = urlparse(url)
    return parsed.path.lower().endswith(".pdf")


# ---------------------------------------------------------------------------
# find_pdf_links
# ---------------------------------------------------------------------------


def find_pdf_links(html: str) -> list[str]:
    """Find all PDF links in an HTML document.

    Parses the HTML and extracts ``href`` attributes from ``<a>`` tags
    whose targets end with ``.pdf`` (case-insensitive). Duplicate URLs
    are removed while preserving order.

    Parameters
    ----------
    html : str
        Raw HTML content to search for PDF links.

    Returns
    -------
    list[str]
        List of unique PDF URLs found in the HTML, in document order.

    Examples
    --------
    >>> html = '<a href="report.pdf">PDF</a><a href="page.html">HTML</a>'
    >>> find_pdf_links(html)
    ['report.pdf']
    """
    if not html:
        return []

    try:
        doc = fromstring(html)
    except Exception:
        logger.warning("Failed to parse HTML for PDF link detection")
        return []

    seen: set[str] = set()
    pdf_links: list[str] = []

    for anchor in doc.iter("a"):
        href = anchor.get("href")
        if href is None:
            continue

        if is_pdf_url(href) and href not in seen:
            seen.add(href)
            pdf_links.append(href)

    logger.debug("PDF links found in HTML", count=len(pdf_links))
    return pdf_links


# ---------------------------------------------------------------------------
# _extract_filename
# ---------------------------------------------------------------------------


def _extract_filename(url: str) -> str:
    """Extract the PDF filename from a URL.

    Parses the URL path to get the last path segment as the filename.
    Falls back to ``document.pdf`` if no valid filename is found.

    Parameters
    ----------
    url : str
        URL to extract the filename from.

    Returns
    -------
    str
        Extracted or default filename.
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    if not path:
        return _DEFAULT_FILENAME

    filename = Path(path).name
    if not filename or not filename.lower().endswith(".pdf"):
        return _DEFAULT_FILENAME

    return filename


# ---------------------------------------------------------------------------
# PdfHandler
# ---------------------------------------------------------------------------


class PdfHandler:
    """Handler for downloading and managing PDF files.

    Downloads PDFs from remote URLs to a local directory structure
    organized by company key and date.

    Files are stored at:
        ``{base_dir}/{company_key}/{date}_{filename}.pdf``

    Parameters
    ----------
    base_dir : Path | None
        Base directory for storing downloaded PDFs. Defaults to
        ``data/raw/ai-research/pdfs``.

    Attributes
    ----------
    base_dir : Path
        Resolved base directory path.

    Examples
    --------
    >>> handler = PdfHandler()
    >>> metadata = await handler.download(
    ...     "https://example.com/report.pdf",
    ...     "nvidia",
    ... )
    >>> metadata.filename
    'report.pdf'
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir if base_dir is not None else _DEFAULT_BASE_DIR
        logger.debug("PdfHandler initialized", base_dir=str(self.base_dir))

    async def download(self, url: str, company_key: str) -> PdfMetadata:
        """Download a PDF file and return its metadata.

        Fetches the PDF from the given URL and saves it to:
            ``{base_dir}/{company_key}/{date}_{filename}``

        The company subdirectory is created automatically if it
        does not exist.

        Parameters
        ----------
        url : str
            Remote URL of the PDF to download.
        company_key : str
            Company identifier used to organize the download directory.

        Returns
        -------
        PdfMetadata
            Metadata about the downloaded PDF including local path.

        Raises
        ------
        httpx.HTTPStatusError
            If the HTTP response indicates an error (4xx or 5xx).
        httpx.HTTPError
            If a network or connection error occurs.
        """
        filename = _extract_filename(url)
        today = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d")
        dated_filename = f"{today}_{filename}"

        # Ensure company directory exists
        company_dir = self.base_dir / company_key
        company_dir.mkdir(parents=True, exist_ok=True)

        local_path = company_dir / dated_filename

        logger.info(
            "Downloading PDF",
            url=url,
            company_key=company_key,
            local_path=str(local_path),
        )

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_HTTPX_TIMEOUT),
            headers={"User-Agent": _DEFAULT_USER_AGENT},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            local_path.write_bytes(response.content)

        logger.info(
            "PDF downloaded successfully",
            url=url,
            company_key=company_key,
            local_path=str(local_path),
            size_bytes=len(response.content),
        )

        return PdfMetadata(
            url=url,
            local_path=str(local_path),
            company_key=company_key,
            filename=filename,
        )

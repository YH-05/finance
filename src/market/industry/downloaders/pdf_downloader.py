"""PDF downloader with size limiting and hash-based deduplication.

This module provides the ``PDFDownloader`` class for downloading PDF reports
from URLs with the following features:

- Maximum file size enforcement (default 50 MB)
- SHA-256 content hash computation for deduplication
- In-memory hash registry to prevent re-downloading identical content
- Async download via httpx
- Graceful error handling for network and HTTP errors

Examples
--------
>>> from market.industry.downloaders.pdf_downloader import PDFDownloader
>>> downloader = PDFDownloader(download_dir=Path("data/raw/industry_reports"))
>>> result = await downloader.download("https://example.com/report.pdf")
>>> result.success
True

See Also
--------
market.industry.downloaders.report_parser : Text extraction from downloaded PDFs.
market.industry.scrapers.base : BaseScraper with 2-layer fallback for HTML pages.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import httpx

from market.industry.types import DownloadResult
from utils_core.logging import get_logger

logger = get_logger(__name__)

# 50 MB default maximum file size
DEFAULT_MAX_FILE_SIZE: int = 50 * 1024 * 1024
"""Default maximum file size in bytes (50 MB)."""

DEFAULT_TIMEOUT: float = 30.0
"""Default HTTP request timeout in seconds."""


class PDFDownloader:
    """Async PDF downloader with size limits and deduplication.

    Downloads PDF files from URLs, enforces a maximum file size,
    computes SHA-256 hashes for deduplication, and saves files to
    a configurable directory.

    Parameters
    ----------
    download_dir : Path
        Directory where downloaded PDFs are saved. Created if it
        does not exist.
    max_file_size : int
        Maximum allowed file size in bytes. Downloads exceeding this
        limit are rejected. Defaults to ``DEFAULT_MAX_FILE_SIZE`` (50 MB).
    timeout : float
        HTTP request timeout in seconds. Defaults to ``DEFAULT_TIMEOUT`` (30s).

    Attributes
    ----------
    download_dir : Path
        The download directory.
    max_file_size : int
        The file size limit in bytes.
    timeout : float
        The HTTP timeout in seconds.

    Examples
    --------
    >>> from pathlib import Path
    >>> downloader = PDFDownloader(download_dir=Path("/tmp/pdfs"))
    >>> result = await downloader.download("https://example.com/report.pdf")
    """

    def __init__(
        self,
        download_dir: Path,
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.download_dir: Path = download_dir
        self.max_file_size: int = max_file_size
        self.timeout: float = timeout

        # In-memory hash registry: hash -> file path
        self._hash_registry: dict[str, Path] = {}

        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "PDFDownloader initialized",
            download_dir=str(download_dir),
            max_file_size_mb=max_file_size / (1024 * 1024),
            timeout=timeout,
        )

    # =========================================================================
    # Public API
    # =========================================================================

    async def download(self, url: str) -> DownloadResult:
        """Download a PDF from the given URL.

        Fetches the PDF content, validates the file size, computes the
        SHA-256 hash for deduplication, and saves the file locally.

        Parameters
        ----------
        url : str
            The URL of the PDF to download.

        Returns
        -------
        DownloadResult
            The result of the download operation. On success, contains
            the local file path, content hash, and file size. On failure,
            contains an error message.

        Examples
        --------
        >>> result = await downloader.download("https://example.com/report.pdf")
        >>> if result.success:
        ...     print(f"Saved to {result.file_path}")
        """
        logger.info("Starting PDF download", url=url)

        try:
            response = await self._fetch_content(url)

            # Check Content-Length header first (pre-download size check)
            content_length_str = response.headers.get("content-length")
            if content_length_str:
                content_length = int(content_length_str)
                if content_length > self.max_file_size:
                    logger.warning(
                        "File size exceeds limit (Content-Length header)",
                        url=url,
                        content_length=content_length,
                        max_file_size=self.max_file_size,
                    )
                    return DownloadResult(
                        success=False,
                        url=url,
                        error_message=(
                            f"File size {content_length} bytes exceeds "
                            f"limit of {self.max_file_size} bytes"
                        ),
                    )

            content: bytes = response.content

            # Check actual content size
            if len(content) > self.max_file_size:
                logger.warning(
                    "File size exceeds limit",
                    url=url,
                    actual_size=len(content),
                    max_file_size=self.max_file_size,
                )
                return DownloadResult(
                    success=False,
                    url=url,
                    error_message=(
                        f"File size {len(content)} bytes exceeds "
                        f"limit of {self.max_file_size} bytes"
                    ),
                )

            # Compute SHA-256 hash
            content_hash = hashlib.sha256(content).hexdigest()

            # Check for duplicate
            if self.has_hash(content_hash):
                existing_path = self.get_path_by_hash(content_hash)
                logger.info(
                    "Duplicate content detected, skipping save",
                    url=url,
                    content_hash=content_hash,
                    existing_path=str(existing_path),
                )
                return DownloadResult(
                    success=True,
                    url=url,
                    file_path=str(existing_path) if existing_path else None,
                    content_hash=content_hash,
                    file_size=len(content),
                    is_duplicate=True,
                )

            # Determine file path
            file_name = self._generate_filename(url, content_hash)
            file_path = self.download_dir / file_name

            # Save to disk
            file_path.write_bytes(content)

            # Register hash
            self.register_hash(content_hash, file_path)

            logger.info(
                "PDF downloaded successfully",
                url=url,
                file_path=str(file_path),
                file_size=len(content),
                content_hash=content_hash,
            )

            return DownloadResult(
                success=True,
                url=url,
                file_path=str(file_path),
                content_hash=content_hash,
                file_size=len(content),
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error during download",
                url=url,
                status_code=e.response.status_code,
                error=str(e),
            )
            return DownloadResult(
                success=False,
                url=url,
                error_message=f"HTTP {e.response.status_code}: {e}",
            )

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.TimeoutException) as e:
            logger.error(
                "Network error during download",
                url=url,
                error_type=type(e).__name__,
                error=str(e),
            )
            return DownloadResult(
                success=False,
                url=url,
                error_message=f"{type(e).__name__}: {e}",
            )

        except Exception as e:
            logger.error(
                "Unexpected error during download",
                url=url,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True,
            )
            return DownloadResult(
                success=False,
                url=url,
                error_message=f"Unexpected error: {e}",
            )

    # =========================================================================
    # Hash Registry
    # =========================================================================

    def has_hash(self, content_hash: str) -> bool:
        """Check if a content hash is already registered.

        Parameters
        ----------
        content_hash : str
            SHA-256 hex digest to check.

        Returns
        -------
        bool
            ``True`` if the hash is already in the registry.
        """
        return content_hash in self._hash_registry

    def register_hash(self, content_hash: str, file_path: Path) -> None:
        """Register a content hash with its file path.

        Parameters
        ----------
        content_hash : str
            SHA-256 hex digest of the file content.
        file_path : Path
            Local path where the file is stored.
        """
        self._hash_registry[content_hash] = file_path

    def get_path_by_hash(self, content_hash: str) -> Path | None:
        """Look up a file path by its content hash.

        Parameters
        ----------
        content_hash : str
            SHA-256 hex digest to look up.

        Returns
        -------
        Path | None
            The file path if found, ``None`` otherwise.
        """
        return self._hash_registry.get(content_hash)

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    async def _fetch_content(self, url: str) -> httpx.Response:
        """Fetch content from a URL using httpx.

        Parameters
        ----------
        url : str
            The URL to fetch.

        Returns
        -------
        httpx.Response
            The HTTP response.

        Raises
        ------
        httpx.HTTPStatusError
            If the server returns a non-2xx status code.
        httpx.ConnectError
            If the connection fails.
        httpx.ReadTimeout
            If the request times out.
        """
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response

    def _generate_filename(self, url: str, content_hash: str) -> str:
        """Generate a unique filename from URL and content hash.

        Uses the last path component of the URL if it ends with .pdf,
        otherwise generates a name from the first 12 characters of the hash.

        Parameters
        ----------
        url : str
            The source URL.
        content_hash : str
            SHA-256 hex digest of the content.

        Returns
        -------
        str
            The generated filename.
        """
        parsed = urlparse(url)
        url_path = parsed.path.rstrip("/")

        if url_path.lower().endswith(".pdf"):
            # Use URL filename with hash prefix for uniqueness
            base_name = Path(url_path).name
            return f"{content_hash[:12]}_{base_name}"

        # Fallback: hash-based filename
        return f"{content_hash[:12]}.pdf"


__all__ = ["DEFAULT_MAX_FILE_SIZE", "PDFDownloader"]

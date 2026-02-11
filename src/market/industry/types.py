"""Type definitions for the market.industry module.

This module provides Pydantic model definitions for industry report scraping
including:

- Source tier classification (API, Scraping, Media)
- Industry report data model (IndustryReport)
- Scraping result container (ScrapingResult)
- Peer group definition (PeerGroup)
- Scraping configuration (ScrapingConfig)
- Retry configuration (RetryConfig)
- Download result container (DownloadResult)
- Report metadata (ReportMetadata)
- Parsed content container (ParsedContent)

All model classes use ``frozen=True`` to ensure immutability, following the
same pattern as ``market.etfcom.types`` and ``market.nasdaq.types``.

See Also
--------
market.etfcom.types : Similar type-definition pattern for the ETF.com module.
market.nasdaq.types : Similar type-definition pattern for the NASDAQ module.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# =============================================================================
# Enum Definitions
# =============================================================================


class SourceTier(str, Enum):
    """Classification tier for industry report sources.

    Tiers indicate the data acquisition method and reliability level:

    - API: Direct API access (highest reliability, e.g. BLS, Census Bureau)
    - SCRAPING: Web scraping of public articles (medium reliability,
      e.g. McKinsey, BCG, Goldman Sachs)
    - MEDIA: Industry-specific media sources (configuration-driven,
      e.g. sector-specific publications)

    Parameters
    ----------
    value : str
        The tier identifier string.

    Examples
    --------
    >>> SourceTier.API
    <SourceTier.API: 'api'>
    >>> str(SourceTier.API)
    'api'
    """

    API = "api"
    SCRAPING = "scraping"
    MEDIA = "media"


# =============================================================================
# Data Model Definitions
# =============================================================================


class IndustryReport(BaseModel, frozen=True):
    """A single industry report record.

    Represents a report or article collected from a consulting firm,
    investment bank, government agency, or industry media source.

    Parameters
    ----------
    source : str
        Name of the report source (e.g. ``"McKinsey"``, ``"BLS"``).
    title : str
        Title of the report or article.
    url : str
        URL of the original report.
    published_at : datetime
        Publication date and time.
    sector : str
        GICS-style sector classification (e.g. ``"Technology"``).
    sub_sector : str | None
        Sub-sector classification (e.g. ``"Semiconductors"``).
        Defaults to ``None``.
    summary : str | None
        Brief summary or abstract of the report.
        Defaults to ``None``.
    content : str | None
        Full text content of the report (if extracted).
        Defaults to ``None``.
    tier : SourceTier
        Source tier classification. Defaults to ``SourceTier.SCRAPING``.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> report = IndustryReport(
    ...     source="McKinsey",
    ...     title="Semiconductor Outlook 2026",
    ...     url="https://mckinsey.com/insights/semiconductor-outlook",
    ...     published_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
    ...     sector="Technology",
    ...     sub_sector="Semiconductors",
    ...     tier=SourceTier.SCRAPING,
    ... )
    >>> report.source
    'McKinsey'
    """

    source: str
    title: str
    url: str
    published_at: datetime
    sector: str
    sub_sector: str | None = None
    summary: str | None = None
    content: str | None = None
    tier: SourceTier = SourceTier.SCRAPING


class ScrapingResult(BaseModel, frozen=True):
    """Container for scraping operation results.

    Encapsulates the outcome of a single scraping operation, including
    success/failure status, collected reports, and error information.

    Parameters
    ----------
    success : bool
        Whether the scraping operation succeeded.
    source : str
        Name of the scraping source.
    url : str
        The URL that was scraped.
    reports : list[IndustryReport]
        List of collected industry reports. Defaults to empty list.
    error_message : str | None
        Error message if the operation failed. Defaults to ``None``.

    Examples
    --------
    >>> result = ScrapingResult(
    ...     success=True,
    ...     source="McKinsey",
    ...     url="https://mckinsey.com/insights",
    ...     reports=[],
    ... )
    >>> result.success
    True
    """

    success: bool
    source: str
    url: str
    reports: list[IndustryReport] = Field(default_factory=list)
    error_message: str | None = None


class PeerGroup(BaseModel, frozen=True):
    """Peer group definition for competitive analysis.

    Defines a group of companies within a sector/sub-sector for
    comparison and competitive positioning analysis.

    Parameters
    ----------
    sector : str
        GICS-style sector classification (e.g. ``"Technology"``).
    sub_sector : str
        Sub-sector classification (e.g. ``"Semiconductors"``).
    companies : list[str]
        List of ticker symbols in the peer group.
    description : str | None
        Optional description of the peer group.
        Defaults to ``None``.

    Examples
    --------
    >>> group = PeerGroup(
    ...     sector="Technology",
    ...     sub_sector="Semiconductors",
    ...     companies=["NVDA", "AMD", "INTC", "TSM", "AVGO"],
    ...     description="Major semiconductor manufacturers",
    ... )
    >>> group.companies
    ['NVDA', 'AMD', 'INTC', 'TSM', 'AVGO']
    """

    sector: str
    sub_sector: str
    companies: list[str]
    description: str | None = None


# =============================================================================
# Configuration Models
# =============================================================================


class ScrapingConfig(BaseModel, frozen=True):
    """Configuration for industry report scraping behaviour.

    Controls polite delays, TLS fingerprint impersonation, Playwright
    headless mode, and request timeout. Default values are aligned with
    ``market.etfcom.types.ScrapingConfig`` to maintain consistency.

    Parameters
    ----------
    polite_delay : float
        Minimum wait time between consecutive requests in seconds
        (default: 2.0).
    delay_jitter : float
        Random jitter added to polite delay in seconds
        (default: 1.0).
    user_agents : tuple[str, ...]
        User-Agent strings for HTTP request rotation.  When empty the
        default list is used at runtime (default: ``()``).
    impersonate : str
        curl_cffi TLS fingerprint impersonation target
        (default: ``'chrome'``).
    timeout : float
        HTTP request timeout in seconds (default: 30.0).
    headless : bool
        Whether to run Playwright in headless mode (default: True).

    Examples
    --------
    >>> config = ScrapingConfig(polite_delay=3.0, headless=False)
    >>> config.polite_delay
    3.0
    """

    polite_delay: float = 2.0
    delay_jitter: float = 1.0
    user_agents: tuple[str, ...] = ()
    impersonate: str = "chrome"
    timeout: float = 30.0
    headless: bool = True


class RetryConfig(BaseModel, frozen=True):
    """Configuration for retry behaviour with exponential backoff.

    Parameters
    ----------
    max_attempts : int
        Maximum number of retry attempts (default: 3).
        Must be between 1 and 10.
    initial_delay : float
        Initial delay between retries in seconds (default: 1.0).
    max_delay : float
        Maximum delay between retries in seconds (default: 30.0).
    exponential_base : float
        Base for exponential backoff calculation (default: 2.0).
    jitter : bool
        Whether to add random jitter to delays (default: True).

    Examples
    --------
    >>> config = RetryConfig(max_attempts=5, initial_delay=0.5)
    >>> config.max_attempts
    5
    """

    max_attempts: int = Field(default=3, ge=1, le=10)
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


# =============================================================================
# Download & Parsing Models
# =============================================================================


class DownloadResult(BaseModel, frozen=True):
    """Result of a PDF download operation.

    Encapsulates the outcome of downloading a PDF file, including
    file location, content hash for deduplication, and size information.

    Parameters
    ----------
    success : bool
        Whether the download succeeded.
    url : str
        The URL that was downloaded.
    file_path : str | None
        Local file path where the PDF was saved.
        ``None`` if the download failed.
    content_hash : str | None
        SHA-256 hex digest of the downloaded content.
        Used for deduplication. ``None`` if the download failed.
    file_size : int | None
        Size of the downloaded file in bytes. ``None`` if the download failed.
    is_duplicate : bool
        Whether this content was already downloaded (hash match).
        Defaults to ``False``.
    error_message : str | None
        Error description if the download failed. Defaults to ``None``.

    Examples
    --------
    >>> result = DownloadResult(
    ...     success=True,
    ...     url="https://example.com/report.pdf",
    ...     file_path="/data/raw/industry_reports/report.pdf",
    ...     content_hash="a1b2c3...",
    ...     file_size=1048576,
    ... )
    >>> result.success
    True
    """

    success: bool
    url: str
    file_path: str | None = None
    content_hash: str | None = None
    file_size: int | None = None
    is_duplicate: bool = False
    error_message: str | None = None


class ReportMetadata(BaseModel, frozen=True):
    """Metadata extracted from a report document.

    Holds document-level metadata such as title, author, and publication
    date. Fields are optional since not all documents provide metadata.

    Parameters
    ----------
    title : str | None
        Document title. Defaults to ``None``.
    author : str | None
        Document author or organisation. Defaults to ``None``.
    date : datetime | None
        Publication or creation date. Defaults to ``None``.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> meta = ReportMetadata(
    ...     title="Semiconductor Outlook",
    ...     author="McKinsey",
    ...     date=datetime(2026, 1, 15, tzinfo=timezone.utc),
    ... )
    >>> meta.title
    'Semiconductor Outlook'
    """

    title: str | None = None
    author: str | None = None
    date: datetime | None = None


class ParsedContent(BaseModel, frozen=True):
    """Container for parsed report content.

    Holds extracted text, metadata, and parsing information from a
    PDF or HTML document.

    Parameters
    ----------
    text : str
        Extracted text content. Empty string if extraction yielded
        no text.
    source_format : str
        Format of the source document (``"pdf"`` or ``"html"``).
    metadata : ReportMetadata | None
        Extracted document metadata. Defaults to ``None``.
    page_count : int | None
        Number of pages (PDF only). Defaults to ``None``.

    Examples
    --------
    >>> content = ParsedContent(
    ...     text="The semiconductor industry...",
    ...     source_format="pdf",
    ...     page_count=42,
    ... )
    >>> content.source_format
    'pdf'
    """

    text: str
    source_format: str
    metadata: ReportMetadata | None = None
    page_count: int | None = None


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    "DownloadResult",
    "IndustryReport",
    "ParsedContent",
    "PeerGroup",
    "ReportMetadata",
    "RetryConfig",
    "ScrapingConfig",
    "ScrapingResult",
    "SourceTier",
]

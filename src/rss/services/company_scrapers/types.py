"""Data types and exception classes for the company scrapers package.

Defines frozen dataclasses for configuration, scraping results, and metadata,
as well as a hierarchy of custom exceptions for scraping error handling.

All data types use frozen dataclasses for immutability and safety in
concurrent scraping operations.
"""

from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# Investment context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InvestmentContext:
    """Investment context for a company.

    Associates a company with its stock tickers, industry sectors,
    and relevant keywords for investment analysis.

    Attributes
    ----------
    tickers : tuple[str, ...]
        Stock ticker symbols (e.g., ("NVDA",), ("MSFT", "GOOGL"))
    sectors : tuple[str, ...]
        Industry sectors (e.g., ("Semiconductor", "Data Center"))
    keywords : tuple[str, ...]
        Keywords for investment relevance filtering
    """

    tickers: tuple[str, ...] = ()
    sectors: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Company configuration
# ---------------------------------------------------------------------------

type SourceType = Literal["blog", "newsroom", "rss", "press_release"]


@dataclass(frozen=True)
class CompanyConfig:
    """Configuration for a company to scrape.

    Defines scraping parameters for a single company including
    target URLs, CSS selectors, and investment context.

    Attributes
    ----------
    key : str
        Unique identifier for the company (e.g., "openai", "nvidia_ai")
    name : str
        Display name (e.g., "OpenAI", "NVIDIA")
    category : str
        Category key (e.g., "ai_llm", "gpu_chips")
    blog_url : str
        Primary blog/news URL to scrape
    article_list_selector : str
        CSS selector for article list items on the blog page
    article_title_selector : str
        CSS selector for article titles
    article_date_selector : str
        CSS selector for article dates
    requires_playwright : bool
        Whether Playwright is needed for JS-rendered content
    rate_limit_seconds : float
        Minimum interval between requests to this domain
    investment_context : InvestmentContext
        Investment context (tickers, sectors, keywords)
    """

    key: str
    name: str
    category: str
    blog_url: str
    article_list_selector: str = "article"
    article_title_selector: str = "h2"
    article_date_selector: str = "time"
    requires_playwright: bool = False
    rate_limit_seconds: float = 3.0
    investment_context: InvestmentContext = field(
        default_factory=InvestmentContext,
    )


# ---------------------------------------------------------------------------
# Scraped article data
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScrapedArticle:
    """A single scraped article with extracted content.

    Represents the result of scraping one article page, including
    the extracted text and any attached PDF information.

    Attributes
    ----------
    url : str
        Article URL
    title : str
        Article title
    text : str
        Extracted article body text
    source_type : SourceType
        How the article was obtained
    pdf : str | None
        URL of the main PDF attachment, if any
    attached_pdfs : tuple[str, ...]
        URLs of additional PDF attachments found in the article
    """

    url: str
    title: str
    text: str
    source_type: SourceType = "blog"
    pdf: str | None = None
    attached_pdfs: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Scrape result (per company)
# ---------------------------------------------------------------------------

type ValidationStatus = Literal["valid", "partial", "failed"]


@dataclass(frozen=True)
class CompanyScrapeResult:
    """Result of scraping a single company's blog/newsroom.

    Aggregates all articles scraped from one company along with
    validation status.

    Attributes
    ----------
    company : str
        Company key (matches CompanyConfig.key)
    articles : tuple[ScrapedArticle, ...]
        Scraped articles
    validation : ValidationStatus
        Overall validation status of the scrape result
    """

    company: str
    articles: tuple[ScrapedArticle, ...] = ()
    validation: ValidationStatus = "valid"


# ---------------------------------------------------------------------------
# Article metadata (lightweight, before full scrape)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArticleMetadata:
    """Lightweight article metadata extracted from a listing page.

    Used before fetching the full article content. Contains only
    the information available from the blog index/listing page.

    Attributes
    ----------
    url : str
        Article URL
    title : str
        Article title
    date : str | None
        Publication date string (ISO 8601 preferred), None if unavailable
    """

    url: str
    title: str
    date: str | None = None


# ---------------------------------------------------------------------------
# PDF metadata
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PdfMetadata:
    """Metadata for a downloaded PDF file.

    Tracks the relationship between a remote PDF URL, its local
    storage path, and the company it belongs to.

    Attributes
    ----------
    url : str
        Remote PDF URL
    local_path : str
        Local file path where the PDF is stored
    company_key : str
        Company key that the PDF belongs to
    filename : str
        Original or derived filename of the PDF
    """

    url: str
    local_path: str
    company_key: str
    filename: str


# ---------------------------------------------------------------------------
# Structure report (for monitoring selector health)
# ---------------------------------------------------------------------------


@dataclass
class StructureReport:
    """Report on the health of CSS selectors for a company's blog page.

    Used to detect when a company's blog structure has changed and
    selectors need updating. Not frozen because it may be updated
    incrementally during scraping.

    Attributes
    ----------
    company : str
        Company key
    article_list_hits : int
        Number of elements matching the article list selector
    title_found_count : int
        Number of article titles successfully extracted
    date_found_count : int
        Number of article dates successfully extracted
    hit_rate : float
        Ratio of successful extractions to total attempts (0.0-1.0)
    """

    company: str
    article_list_hits: int = 0
    title_found_count: int = 0
    date_found_count: int = 0
    hit_rate: float = 0.0


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class ScrapingError(Exception):
    """Base exception for all company scraping errors.

    All scraping-related exceptions inherit from this class,
    allowing callers to catch all scraping errors with a single
    except clause.

    Attributes
    ----------
    domain : str
        The domain where the error occurred
    url : str
        The URL that caused the error
    """

    def __init__(self, message: str, *, domain: str, url: str) -> None:
        super().__init__(message)
        self.domain = domain
        self.url = url


class RateLimitError(ScrapingError):
    """Raised when a rate limit (HTTP 429) is encountered.

    Indicates that the scraper has been rate-limited by the target
    server. Callers should back off and retry after a delay.

    Attributes
    ----------
    retry_after : float | None
        Suggested retry delay in seconds from the Retry-After header,
        None if not provided by the server
    """

    def __init__(
        self,
        message: str,
        *,
        domain: str,
        url: str,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, domain=domain, url=url)
        self.retry_after = retry_after


class StructureChangedError(ScrapingError):
    """Raised when a company's blog structure has changed.

    Indicates that the CSS selectors configured for a company no
    longer match the page structure, typically because the company
    redesigned their blog. The selectors need to be updated.

    Attributes
    ----------
    selector : str
        The CSS selector that failed to match
    """

    def __init__(
        self,
        message: str,
        *,
        domain: str,
        url: str,
        selector: str,
    ) -> None:
        super().__init__(message, domain=domain, url=url)
        self.selector = selector


class BotDetectionError(ScrapingError):
    """Raised when the scraper is detected as a bot.

    Indicates that the target server has identified the request
    as automated and blocked it. May require different user agents,
    headers, or Playwright-based rendering.
    """

    pass

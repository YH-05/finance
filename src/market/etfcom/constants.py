"""Constants for ETF.com scraping module.

This module defines all constants used by the ETF.com scraping module,
including bot-blocking countermeasure settings, URL patterns, CSS selectors,
Playwright stealth configuration, and REST API settings.

Constants are organized into the following categories:

1. Bot-blocking countermeasures (User-Agent rotation, TLS fingerprint
   impersonation targets, polite delays)
2. Playwright stealth settings (viewport, initialization scripts)
3. URL patterns (base URL, screener, profile templates)
4. CSS selectors (data extraction targets)
5. Default configuration (stability wait, retry limits)
6. REST API settings (API URLs, headers, cache, concurrency)

Notes
-----
All constants use ``typing.Final`` type annotations to prevent reassignment.
The ``__all__`` list exports all public constants for use by other modules.

The User-Agent strings and browser impersonation targets are based on
real browser configurations to avoid bot detection by ETF.com.

See Also
--------
market.fred.constants : Similar constant pattern used by the FRED module.
market.yfinance.fetcher : Browser impersonation targets reference.
"""

from typing import Final

# ---------------------------------------------------------------------------
# 1. Bot-blocking countermeasure constants
# ---------------------------------------------------------------------------

DEFAULT_USER_AGENTS: Final[list[str]] = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Firefox on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
]
"""Default User-Agent strings for HTTP requests.

Contains 12 real browser User-Agent strings covering Chrome, Firefox,
Safari, and Edge on Windows, macOS, and Linux platforms.
Rotated randomly to avoid bot detection.
"""

BROWSER_IMPERSONATE_TARGETS: Final[list[str]] = [
    "chrome",
    "chrome110",
    "chrome120",
    "edge99",
    "safari15_3",
]
"""Browser impersonation targets for curl_cffi TLS fingerprint.

These mimic real browser TLS fingerprints to avoid bot detection.
Aligned with ``market.yfinance.fetcher.BROWSER_IMPERSONATE_TARGETS``.
"""

DEFAULT_POLITE_DELAY: Final[float] = 2.0
"""Default polite delay between requests in seconds.

A minimum wait time between consecutive requests to avoid
overloading the ETF.com server and triggering rate limiting.
"""

DEFAULT_DELAY_JITTER: Final[float] = 1.0
"""Random jitter added to the polite delay in seconds.

Adds randomness to request timing to appear more human-like.
The actual delay is ``DEFAULT_POLITE_DELAY + random(0, DEFAULT_DELAY_JITTER)``.
"""

DEFAULT_TIMEOUT: Final[float] = 30.0
"""Default HTTP request timeout in seconds.

Maximum time to wait for a response before raising a timeout error.
"""

DEFAULT_HEADERS: Final[dict[str, str]] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
"""Default HTTP headers for requests.

Mimics standard browser headers to avoid bot detection.
The User-Agent header is set separately via ``DEFAULT_USER_AGENTS``.
"""

# ---------------------------------------------------------------------------
# 2. Playwright stealth constants
# ---------------------------------------------------------------------------

STEALTH_VIEWPORT: Final[dict[str, int]] = {
    "width": 1920,
    "height": 1080,
}
"""Default viewport size for Playwright stealth mode.

Uses a common 1080p desktop resolution to appear as a real user.
"""

STEALTH_INIT_SCRIPT: Final[str] = """\
// Hide navigator.webdriver property
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// Override WebGL vendor and renderer
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) {
        return 'Intel Inc.';
    }
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter.call(this, parameter);
};

// Add chrome.runtime to appear as a Chrome extension environment
if (!window.chrome) {
    window.chrome = {};
}
if (!window.chrome.runtime) {
    window.chrome.runtime = {};
}
"""
"""JavaScript initialization script for Playwright stealth mode.

Hides automation indicators from bot detection scripts:

- ``navigator.webdriver``: Set to undefined (default is true in automation).
- WebGL vendor/renderer: Overridden to Intel values instead of generic ones.
- ``chrome.runtime``: Added to simulate a Chrome extension environment.
"""

# ---------------------------------------------------------------------------
# 3. URL constants
# ---------------------------------------------------------------------------

ETFCOM_BASE_URL: Final[str] = "https://www.etf.com"
"""Base URL for ETF.com website."""

SCREENER_URL: Final[str] = "https://www.etf.com/topics/etf-screener"
"""URL for the ETF.com screener page."""

PROFILE_URL_TEMPLATE: Final[str] = "https://www.etf.com/{ticker}"
"""URL template for ETF profile pages.

Format with a ticker symbol to get the profile URL.

Examples
--------
>>> PROFILE_URL_TEMPLATE.format(ticker="SPY")
'https://www.etf.com/SPY'
"""

FUND_FLOWS_URL_TEMPLATE: Final[str] = "https://www.etf.com/{ticker}#702"
"""URL template for ETF fund flows pages.

Format with a ticker symbol to get the fund flows URL.
The ``#702`` anchor points to the fund flows section.

Examples
--------
>>> FUND_FLOWS_URL_TEMPLATE.format(ticker="SPY")
'https://www.etf.com/SPY#702'
"""

# ---------------------------------------------------------------------------
# 4. CSS selector constants
# ---------------------------------------------------------------------------

SUMMARY_DATA_ID: Final[str] = "[data-testid='summary-data']"
"""CSS selector for the ETF summary data section."""

CLASSIFICATION_DATA_ID: Final[str] = "[data-testid='classification-data']"
"""CSS selector for the ETF classification data section."""

FLOW_TABLE_ID: Final[str] = "[data-testid='fund-flows-table']"
"""CSS selector for the fund flows table."""

COOKIE_CONSENT_SELECTOR: Final[str] = "button#onetrust-accept-btn-handler"
"""CSS selector for the cookie consent accept button."""

DISPLAY_100_SELECTOR: Final[str] = "select.per-page-select option[value='100']"
"""CSS selector for the 'Display 100' option in pagination."""

NEXT_PAGE_SELECTOR: Final[str] = "a.pagination-next:not(.disabled)"
"""CSS selector for the next page button in pagination."""

# ---------------------------------------------------------------------------
# 5. Default settings
# ---------------------------------------------------------------------------

DEFAULT_STABILITY_WAIT: Final[float] = 2.0
"""Default wait time in seconds for page stability after navigation.

Allows dynamic content to finish loading before extraction.
"""

DEFAULT_MAX_RETRIES: Final[int] = 3
"""Default maximum number of retry attempts for failed operations."""

# ---------------------------------------------------------------------------
# 6. REST API constants
# ---------------------------------------------------------------------------

ETFCOM_API_BASE_URL: Final[str] = "https://api-prod.etf.com"
"""Base URL for ETF.com REST API.

The internal production API endpoint used for programmatic data access.
Unlike the scraping-based ``ETFCOM_BASE_URL``, this targets the REST API
server directly.
"""

TICKERS_API_URL: Final[str] = "https://api-prod.etf.com/private/apps/fundflows/tickers"
"""URL for the ETF.com tickers list API endpoint.

Returns a JSON array of all available ETF tickers with their fund IDs,
names, and other metadata. Used to resolve ticker symbols to fund IDs
required by the fund flows query endpoint.
"""

FUND_DETAILS_API_URL: Final[str] = (
    "https://api-prod.etf.com/private/apps/fundflows/fund-details"
)
"""URL for the ETF.com fund details API endpoint.

Returns detailed fund information including AUM, expense ratio, and
other metadata for a specific fund.
"""

FUND_FLOWS_QUERY: Final[str] = (
    "https://api-prod.etf.com/private/apps/fundflows/fund-flows-query"
)
"""URL for the ETF.com fund flows query API endpoint.

Accepts POST requests with a fund ID to return historical daily fund
flow data including NAV, NAV change, premium/discount, fund flows,
shares outstanding, and AUM.
"""

API_HEADERS: Final[dict[str, str]] = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "Origin": "https://www.etf.com",
    "Referer": "https://www.etf.com/",
}
"""HTTP headers for REST API requests.

These headers mimic a browser making an XHR/fetch request from the
ETF.com website. The ``Origin`` and ``Referer`` headers are required
to pass the API's CORS checks. ``Content-Type`` is set to JSON for
POST request payloads.
"""

DEFAULT_TICKER_CACHE_TTL_HOURS: Final[int] = 24
"""Default TTL (time-to-live) for the ticker list file cache in hours.

The ticker list (~5,000 entries) is expensive to fetch. Caching locally
avoids repeated API calls. A 24-hour TTL balances freshness with
performance.
"""

DEFAULT_TICKER_CACHE_DIR: Final[str] = "data/raw/etfcom"
"""Default directory for the ticker list file cache.

Ticker list JSON files are stored here with timestamps for TTL
validation. Follows the project convention of ``data/raw/<source>/``.
"""

DEFAULT_MAX_CONCURRENCY: Final[int] = 5
"""Default maximum number of concurrent API requests.

Controls the ``asyncio.Semaphore`` limit for parallel fund flow
fetches. A conservative default to avoid triggering rate limiting
on the ETF.com API.
"""

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "API_HEADERS",
    "BROWSER_IMPERSONATE_TARGETS",
    "CLASSIFICATION_DATA_ID",
    "COOKIE_CONSENT_SELECTOR",
    "DEFAULT_DELAY_JITTER",
    "DEFAULT_HEADERS",
    "DEFAULT_MAX_CONCURRENCY",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_POLITE_DELAY",
    "DEFAULT_STABILITY_WAIT",
    "DEFAULT_TICKER_CACHE_DIR",
    "DEFAULT_TICKER_CACHE_TTL_HOURS",
    "DEFAULT_TIMEOUT",
    "DEFAULT_USER_AGENTS",
    "DISPLAY_100_SELECTOR",
    "ETFCOM_API_BASE_URL",
    "ETFCOM_BASE_URL",
    "FLOW_TABLE_ID",
    "FUND_DETAILS_API_URL",
    "FUND_FLOWS_QUERY",
    "FUND_FLOWS_URL_TEMPLATE",
    "NEXT_PAGE_SELECTOR",
    "PROFILE_URL_TEMPLATE",
    "SCREENER_URL",
    "STEALTH_INIT_SCRIPT",
    "STEALTH_VIEWPORT",
    "SUMMARY_DATA_ID",
    "TICKERS_API_URL",
]

"""Pytest configuration and shared fixtures for market.etfcom test suite.

This module provides reusable fixtures for testing the ETF.com scraping module,
including mock HTML responses, zero-delay configurations, mock sessions, and
mock browser instances. These fixtures are designed to be shared across all
Wave test files (unit, property, integration).

Fixtures
--------
sample_scraping_config : ScrapingConfig
    Test-friendly ScrapingConfig with zero delays.
sample_retry_config : RetryConfig
    Test-friendly RetryConfig with single retry and minimal delay.
sample_screener_html : str
    Mock ETF.com screener page HTML containing 5 ETF rows.
sample_profile_html : str
    Mock ETF.com SPY profile page HTML with summary and classification data.
sample_fund_flows_html : str
    Mock ETF.com fund flows page HTML with flow table data.
mock_curl_response : MagicMock
    MagicMock simulating a curl_cffi Response with status_code=200.
mock_session : MagicMock
    MagicMock simulating an ETFComSession instance.
mock_browser : AsyncMock
    AsyncMock simulating an ETFComBrowserMixin instance.

See Also
--------
tests.market.conftest : Parent-level market package fixtures.
market.etfcom.types : ScrapingConfig and RetryConfig definitions.
market.etfcom.session : ETFComSession class.
market.etfcom.browser : ETFComBrowserMixin class.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from market.etfcom.types import RetryConfig, ScrapingConfig

# =============================================================================
# Configuration fixtures
# =============================================================================


@pytest.fixture
def sample_scraping_config() -> ScrapingConfig:
    """Create a test-friendly ScrapingConfig with zero delays.

    All delay-related parameters are set to zero to avoid slow tests.
    headless is True (default) for CI compatibility.

    Returns
    -------
    ScrapingConfig
        A ScrapingConfig with zero polite_delay, zero delay_jitter,
        zero stability_wait, and minimal timeout.
    """
    return ScrapingConfig(
        polite_delay=0.0,
        delay_jitter=0.0,
        user_agents=("TestAgent/1.0",),
        impersonate="chrome",
        timeout=5.0,
        headless=True,
        stability_wait=0.0,
        max_page_retries=1,
    )


@pytest.fixture
def sample_retry_config() -> RetryConfig:
    """Create a test-friendly RetryConfig with single retry and minimal delay.

    Minimizes retry overhead in tests while still testing retry logic.

    Returns
    -------
    RetryConfig
        A RetryConfig with max_attempts=1, initial_delay=0.0,
        max_delay=0.0, exponential_base=2.0, jitter=False.
    """
    return RetryConfig(
        max_attempts=1,
        initial_delay=0.0,
        max_delay=0.0,
        exponential_base=2.0,
        jitter=False,
    )


# =============================================================================
# Mock HTML fixtures
# =============================================================================


@pytest.fixture
def sample_screener_html() -> str:
    """Create mock ETF.com screener page HTML with 5 ETF rows.

    Contains a realistic HTML table structure matching the ETF.com screener
    page, with 5 ETF entries (SPY, VOO, IVV, QQQ, VTI) including ticker,
    name, AUM, expense ratio, and segment columns.

    Returns
    -------
    str
        HTML string mimicking the ETF.com screener page structure.
    """
    return """\
<!DOCTYPE html>
<html lang="en">
<head><title>ETF Screener | ETF.com</title></head>
<body>
<div id="etf-screener">
  <table class="screener-table">
    <thead>
      <tr>
        <th>Ticker</th>
        <th>Fund Name</th>
        <th>AUM</th>
        <th>Expense Ratio</th>
        <th>Segment</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><a href="/SPY">SPY</a></td>
        <td>SPDR S&amp;P 500 ETF Trust</td>
        <td>$500.00B</td>
        <td>0.09%</td>
        <td>Equity: U.S. - Large Cap</td>
      </tr>
      <tr>
        <td><a href="/VOO">VOO</a></td>
        <td>Vanguard S&amp;P 500 ETF</td>
        <td>$751.49B</td>
        <td>0.03%</td>
        <td>Equity: U.S. - Large Cap</td>
      </tr>
      <tr>
        <td><a href="/IVV">IVV</a></td>
        <td>iShares Core S&amp;P 500 ETF</td>
        <td>$450.00B</td>
        <td>0.03%</td>
        <td>Equity: U.S. - Large Cap</td>
      </tr>
      <tr>
        <td><a href="/QQQ">QQQ</a></td>
        <td>Invesco QQQ Trust</td>
        <td>$280.00B</td>
        <td>0.20%</td>
        <td>Equity: U.S. - Large Cap Growth</td>
      </tr>
      <tr>
        <td><a href="/VTI">VTI</a></td>
        <td>Vanguard Total Stock Market ETF</td>
        <td>$380.00B</td>
        <td>0.03%</td>
        <td>Equity: U.S. - Total Market</td>
      </tr>
    </tbody>
  </table>
  <div class="pagination">
    <select class="per-page-select">
      <option value="25">25</option>
      <option value="50">50</option>
      <option value="100">100</option>
    </select>
    <a class="pagination-next" href="?page=2">Next</a>
  </div>
</div>
</body>
</html>"""


@pytest.fixture
def sample_profile_html() -> str:
    """Create mock ETF.com SPY profile page HTML.

    Contains summary-data and classification-data sections matching
    the ETF.com profile page structure, with realistic SPY fund data.

    Returns
    -------
    str
        HTML string mimicking the ETF.com profile page for SPY.
    """
    return """\
<!DOCTYPE html>
<html lang="en">
<head><title>SPY | SPDR S&amp;P 500 ETF Trust | ETF.com</title></head>
<body>
<div class="fund-header">
  <h1>SPDR S&amp;P 500 ETF Trust</h1>
  <span class="ticker">SPY</span>
</div>
<div data-testid="summary-data">
  <table>
    <tbody>
      <tr><td>Issuer</td><td>State Street</td></tr>
      <tr><td>Inception Date</td><td>01/22/93</td></tr>
      <tr><td>Expense Ratio</td><td>0.09%</td></tr>
      <tr><td>AUM</td><td>$500.00B</td></tr>
      <tr><td>Index Tracked</td><td>S&amp;P 500</td></tr>
    </tbody>
  </table>
</div>
<div data-testid="classification-data">
  <table>
    <tbody>
      <tr><td>Segment</td><td>Equity: U.S. - Large Cap</td></tr>
      <tr><td>Structure</td><td>Unit Investment Trust</td></tr>
      <tr><td>Asset Class</td><td>Equity</td></tr>
      <tr><td>Category</td><td>Size and Style</td></tr>
      <tr><td>Focus</td><td>Large Cap</td></tr>
      <tr><td>Niche</td><td>Broad-based</td></tr>
      <tr><td>Region</td><td>North America</td></tr>
      <tr><td>Geography</td><td>U.S.</td></tr>
      <tr><td>Weighting Methodology</td><td>Market Cap</td></tr>
      <tr><td>Selection Methodology</td><td>Committee</td></tr>
      <tr><td>Segment Benchmark</td><td>MSCI USA Large Cap</td></tr>
    </tbody>
  </table>
</div>
<button id="onetrust-accept-btn-handler">Accept Cookies</button>
</body>
</html>"""


@pytest.fixture
def sample_fund_flows_html() -> str:
    """Create mock ETF.com fund flows page HTML.

    Contains a fund-flows-table section matching the ETF.com fund flows
    page structure, with sample daily flow data for SPY.

    Returns
    -------
    str
        HTML string mimicking the ETF.com fund flows page for SPY.
    """
    return """\
<!DOCTYPE html>
<html lang="en">
<head><title>SPY Fund Flows | ETF.com</title></head>
<body>
<div class="fund-header">
  <h1>SPY Fund Flows</h1>
</div>
<div data-testid="fund-flows-table">
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Net Flows ($M)</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>2025-09-10</td><td>2,787.59</td></tr>
      <tr><td>2025-09-09</td><td>-1,234.56</td></tr>
      <tr><td>2025-09-08</td><td>-104.61</td></tr>
      <tr><td>2025-09-05</td><td>3,456.78</td></tr>
      <tr><td>2025-09-04</td><td>987.65</td></tr>
    </tbody>
  </table>
</div>
</body>
</html>"""


# =============================================================================
# Mock object fixtures
# =============================================================================


@pytest.fixture
def mock_curl_response() -> MagicMock:
    """Create a MagicMock simulating a successful curl_cffi Response.

    The mock response has status_code=200 and a text body containing
    a minimal HTML page.

    Returns
    -------
    MagicMock
        A MagicMock with status_code=200 and text/content attributes.
    """
    response = MagicMock()
    response.status_code = 200
    response.text = "<html><body>OK</body></html>"
    response.content = b"<html><body>OK</body></html>"
    response.headers = {"Content-Type": "text/html; charset=utf-8"}
    return response


@pytest.fixture
def mock_session(
    sample_scraping_config: ScrapingConfig,
    sample_retry_config: RetryConfig,
    mock_curl_response: MagicMock,
) -> MagicMock:
    """Create a MagicMock simulating an ETFComSession instance.

    The mock session's get() and get_with_retry() methods return
    the mock_curl_response fixture by default.

    Parameters
    ----------
    sample_scraping_config : ScrapingConfig
        Zero-delay scraping configuration.
    sample_retry_config : RetryConfig
        Single-retry configuration.
    mock_curl_response : MagicMock
        Mock HTTP response.

    Returns
    -------
    MagicMock
        A MagicMock mimicking ETFComSession with get/get_with_retry/
        rotate_session/close methods.
    """
    session = MagicMock()
    session._config = sample_scraping_config
    session._retry_config = sample_retry_config
    session.get.return_value = mock_curl_response
    session.get_with_retry.return_value = mock_curl_response
    session.rotate_session.return_value = None
    session.close.return_value = None
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    return session


@pytest.fixture
def mock_browser(
    sample_scraping_config: ScrapingConfig,
    sample_retry_config: RetryConfig,
) -> AsyncMock:
    """Create an AsyncMock simulating an ETFComBrowserMixin instance.

    The mock browser's async methods (_ensure_browser, _navigate,
    _get_page_html, etc.) return sensible defaults for testing.

    Parameters
    ----------
    sample_scraping_config : ScrapingConfig
        Zero-delay scraping configuration.
    sample_retry_config : RetryConfig
        Single-retry configuration.

    Returns
    -------
    AsyncMock
        An AsyncMock mimicking ETFComBrowserMixin with async methods.
    """
    browser = AsyncMock()
    browser._config = sample_scraping_config
    browser._retry_config = sample_retry_config
    browser._playwright = None
    browser._browser = None
    browser._context = None

    # Async methods
    browser._ensure_browser = AsyncMock()
    browser._navigate = AsyncMock(return_value=AsyncMock())
    browser._get_page_html = AsyncMock(
        return_value="<html><body>Mock Page</body></html>"
    )
    browser._get_page_html_with_retry = AsyncMock(
        return_value="<html><body>Mock Page</body></html>"
    )
    browser._accept_cookies = AsyncMock()
    browser._wait_for_content_loaded = AsyncMock()
    browser._click_display_100 = AsyncMock()
    browser._create_stealth_context = AsyncMock()
    browser.close = AsyncMock()

    # Async context manager support
    browser.__aenter__ = AsyncMock(return_value=browser)
    browser.__aexit__ = AsyncMock(return_value=False)

    return browser

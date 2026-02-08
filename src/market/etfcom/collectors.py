"""ETF.com data collectors for tickers, fundamentals, and fund flows.

This module provides three ``DataCollector`` subclasses for scraping
ETF data from ETF.com:

- ``TickerCollector``: Scrapes the screener page for ETF ticker lists.
- ``FundamentalsCollector``: Scrapes individual ETF profile pages for
  key-value fundamental data (summary + classification).
- ``FundFlowsCollector``: Scrapes the fund flows page for daily flow data.

``FundamentalsCollector`` and ``FundFlowsCollector`` use a two-tier
HTML retrieval strategy: curl_cffi (via ``ETFComSession``) is the
primary method, with Playwright (via ``ETFComBrowserMixin``) as a
fallback when curl_cffi encounters bot-blocking or returns empty content.

Features
--------
- DataCollector abstract base class compliance (fetch/validate interface)
- curl_cffi-first + Playwright-fallback HTML retrieval
- Playwright-based browser automation via ETFComBrowserMixin
- Dependency injection for session and browser instances (testability)
- Pagination support (100 items per page) for TickerCollector
- ``'--'`` placeholder conversion to NaN / None
- BeautifulSoup HTML table parsing
- Comma-separated number parsing for fund flows

Examples
--------
>>> from market.etfcom.collectors import TickerCollector
>>> collector = TickerCollector()
>>> df = collector.collect()
>>> print(df.head())
  ticker                       name       issuer  ...
0    SPY  SPDR S&P 500 ETF Trust  State Street  ...

>>> from market.etfcom.collectors import FundamentalsCollector
>>> collector = FundamentalsCollector()
>>> df = collector.fetch(tickers=["SPY", "VOO"])

>>> from market.etfcom.collectors import FundFlowsCollector
>>> collector = FundFlowsCollector()
>>> df = collector.fetch(ticker="SPY")

See Also
--------
market.base_collector : DataCollector abstract base class.
market.etfcom.browser : ETFComBrowserMixin for Playwright operations.
market.etfcom.session : curl_cffi-based session for non-JS pages.
market.etfcom.constants : CSS selectors and URL constants.
market.tsa : TSAPassengerDataCollector (similar DataCollector pattern).
"""

from __future__ import annotations

import asyncio
import math
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup, Tag

from market.base_collector import DataCollector
from market.etfcom.browser import ETFComBrowserMixin
from market.etfcom.constants import (
    CLASSIFICATION_DATA_ID,
    FLOW_TABLE_ID,
    FUND_FLOWS_URL_TEMPLATE,
    NEXT_PAGE_SELECTOR,
    PROFILE_URL_TEMPLATE,
    SCREENER_URL,
    SUMMARY_DATA_ID,
)
from market.etfcom.errors import ETFComBlockedError
from market.etfcom.session import ETFComSession
from market.etfcom.types import RetryConfig, ScrapingConfig
from utils_core.logging import get_logger

logger = get_logger(__name__)

# Column name mapping from raw screener table headers to snake_case
_COLUMN_MAP: dict[str, str] = {
    "ticker": "ticker",
    "fund name": "name",
    "issuer": "issuer",
    "segment": "category",
    "expense ratio": "expense_ratio",
    "aum": "aum",
}

# Placeholder value used by ETF.com for missing data
_PLACEHOLDER = "--"


class TickerCollector(DataCollector):
    """Collector for ETF ticker list from ETF.com screener page.

    Scrapes the ETF.com screener page to extract a complete list of ETF
    tickers with basic metadata (name, issuer, category, expense_ratio,
    aum). Uses Playwright for JavaScript-rendered page content.

    The browser instance can be injected via the constructor for testing
    (dependency injection pattern).

    Parameters
    ----------
    browser : ETFComBrowserMixin | None
        Pre-configured browser instance. If None, a new instance is
        created internally using the provided config.
    config : ScrapingConfig | None
        Scraping configuration. Used when creating a new browser
        instance (ignored if browser is provided).

    Attributes
    ----------
    _browser_instance : ETFComBrowserMixin | None
        Injected browser instance (None if creating internally).
    _config : ScrapingConfig
        The scraping configuration.

    Examples
    --------
    >>> collector = TickerCollector()
    >>> df = collector.fetch()
    >>> print(f"Found {len(df)} ETFs")

    >>> # With dependency injection for testing
    >>> mock_browser = AsyncMock()
    >>> collector = TickerCollector(browser=mock_browser)
    """

    def __init__(
        self,
        browser: ETFComBrowserMixin | None = None,
        config: ScrapingConfig | None = None,
    ) -> None:
        """Initialize TickerCollector with optional browser and config.

        Parameters
        ----------
        browser : ETFComBrowserMixin | None
            Pre-configured browser instance for dependency injection.
            If None, a new ETFComBrowserMixin is created when fetch() is called.
        config : ScrapingConfig | None
            Scraping configuration. Defaults to ``ScrapingConfig()``.
        """
        self._browser_instance: ETFComBrowserMixin | None = browser
        self._config: ScrapingConfig = config or ScrapingConfig()

        logger.info(
            "TickerCollector initialized",
            browser_injected=browser is not None,
            headless=self._config.headless,
        )

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch all ETF tickers from the ETF.com screener page.

        Delegates to ``_async_fetch()`` via ``asyncio.run()``.

        Parameters
        ----------
        **kwargs : Any
            Additional keyword arguments (currently unused).

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: ticker, name, issuer, category,
            expense_ratio, aum.

        Raises
        ------
        ETFComTimeoutError
            If the screener page fails to load.

        Examples
        --------
        >>> collector = TickerCollector()
        >>> df = collector.fetch()
        >>> print(df.columns.tolist())
        ['ticker', 'name', 'issuer', 'category', 'expense_ratio', 'aum']
        """
        logger.info("Starting ticker collection from ETF.com screener")
        return asyncio.run(self._async_fetch(**kwargs))

    async def _async_fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Asynchronously fetch all ETF tickers from the screener page.

        Workflow:
        1. Start browser (or use injected instance)
        2. Navigate to screener page
        3. Accept cookie consent
        4. Switch to 100 items per page
        5. Loop: extract table HTML -> parse rows -> check next page
        6. Combine all rows into a DataFrame

        Parameters
        ----------
        **kwargs : Any
            Additional keyword arguments (currently unused).

        Returns
        -------
        pd.DataFrame
            DataFrame containing all ETF ticker data.
        """
        all_rows: list[dict[str, str | None]] = []

        # Use injected browser or create a new one
        if self._browser_instance is not None:
            browser = self._browser_instance
            should_close = False
        else:
            browser = ETFComBrowserMixin(config=self._config)
            should_close = True

        try:
            # Ensure browser is ready
            await browser._ensure_browser()

            # Navigate to screener page
            logger.info("Navigating to screener page", url=SCREENER_URL)
            page = await browser._navigate(SCREENER_URL)

            # Accept cookie consent
            await browser._accept_cookies(page)

            # Switch to 100 items per page
            await browser._click_display_100(page)

            # Wait for table content to stabilize
            await asyncio.sleep(self._config.stability_wait)

            # Pagination loop
            page_number = 1
            while True:
                logger.debug(
                    "Scraping screener page",
                    page_number=page_number,
                )

                # Get current page HTML
                html: str = await page.content()
                rows = self._parse_screener_table(html)
                all_rows.extend(rows)

                logger.debug(
                    "Page scraped",
                    page_number=page_number,
                    row_count=len(rows),
                    total_rows=len(all_rows),
                )

                # Check for next page
                next_button = await page.query_selector(NEXT_PAGE_SELECTOR)
                if next_button is None:
                    logger.info(
                        "Last page reached",
                        page_number=page_number,
                        total_rows=len(all_rows),
                    )
                    break

                # Click next page
                await next_button.click()
                await asyncio.sleep(self._config.stability_wait)
                page_number += 1

            # Close the page
            await page.close()

        finally:
            if should_close:
                await browser.close()

        # Convert rows to DataFrame
        df = self._rows_to_dataframe(all_rows)

        logger.info(
            "Ticker collection completed",
            total_tickers=len(df),
            columns=list(df.columns) if not df.empty else [],
        )

        return df

    def _parse_screener_table(self, html: str) -> list[dict[str, str | None]]:
        """Parse the ETF screener HTML table into a list of row dicts.

        Extracts ticker, name, issuer, category, expense_ratio, and aum
        from the table body rows. The ``'--'`` placeholder values are
        converted to ``None``.

        Parameters
        ----------
        html : str
            Full HTML content of the screener page.

        Returns
        -------
        list[dict[str, str | None]]
            List of dicts, each representing one ETF row.
            Keys: ticker, name, issuer, category, expense_ratio, aum.
            Values are None where the original value was ``'--'``.
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")

        if table is None:
            logger.warning("No table found in screener HTML")
            return []

        # Extract header names for column mapping
        headers: list[str] = []
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                headers = [
                    th.get_text(strip=True).lower() for th in header_row.find_all("th")
                ]

        # Extract table body rows
        tbody = table.find("tbody")
        if tbody is None:
            logger.warning("No tbody found in screener table")
            return []

        rows: list[dict[str, str | None]] = []

        for tr in tbody.find_all("tr"):
            cells = tr.find_all("td")
            if not cells:
                continue

            cell_values: list[str] = []
            for cell in cells:
                # Extract text, handling <a> tags
                text = cell.get_text(strip=True)
                cell_values.append(text)

            # Map cell values to column names
            row: dict[str, str | None] = {}
            for i, header in enumerate(headers):
                if i >= len(cell_values):
                    break

                mapped_key = _COLUMN_MAP.get(header)
                if mapped_key is None:
                    continue

                value = cell_values[i]
                # Convert '--' placeholder to None
                if value == _PLACEHOLDER:
                    row[mapped_key] = None
                else:
                    row[mapped_key] = value

            # Only add rows that have at least a ticker
            if row.get("ticker"):
                rows.append(row)

        logger.debug(
            "Screener table parsed",
            row_count=len(rows),
        )

        return rows

    def _rows_to_dataframe(self, rows: list[dict[str, str | None]]) -> pd.DataFrame:
        """Convert a list of row dicts to a pandas DataFrame.

        Parameters
        ----------
        rows : list[dict[str, str | None]]
            List of dicts from ``_parse_screener_table()``.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: ticker, name, issuer, category,
            expense_ratio, aum. Returns an empty DataFrame with the
            correct columns if the input list is empty.
        """
        if not rows:
            logger.debug("No rows to convert, returning empty DataFrame")
            return pd.DataFrame(
                columns=pd.Index(
                    ["ticker", "name", "issuer", "category", "expense_ratio", "aum"]
                )
            )

        df = pd.DataFrame(rows)

        # Ensure all required columns exist
        for col in ["ticker", "name", "issuer", "category", "expense_ratio", "aum"]:
            if col not in df.columns:
                df[col] = None

        logger.debug(
            "Rows converted to DataFrame",
            row_count=len(df),
            columns=list(df.columns),
        )

        return df

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the fetched ticker data.

        Checks that the DataFrame:
        - Is not empty
        - Contains the ``ticker`` column

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid, False otherwise.

        Examples
        --------
        >>> collector = TickerCollector()
        >>> df = pd.DataFrame({"ticker": ["SPY"], "name": ["SPDR"]})
        >>> collector.validate(df)
        True
        >>> collector.validate(pd.DataFrame())
        False
        """
        if df.empty:
            logger.warning("Validation failed: DataFrame is empty")
            return False

        if "ticker" not in df.columns:
            logger.warning(
                "Validation failed: 'ticker' column not found",
                actual_columns=list(df.columns),
            )
            return False

        logger.debug(
            "Validation passed",
            row_count=len(df),
        )
        return True


# Minimum content length to consider a curl_cffi response as valid.
# Responses shorter than this threshold indicate empty or error pages
# and trigger a Playwright fallback.
_MIN_CONTENT_LENGTH: int = 500

# Key mapping from raw ETF.com profile labels to snake_case field names.
# Used by FundamentalsCollector._parse_profile() to normalise the
# key-value pairs extracted from #summary-data and #classification-data.
_PROFILE_KEY_MAP: dict[str, str] = {
    "issuer": "issuer",
    "inception date": "inception_date",
    "expense ratio": "expense_ratio",
    "aum": "aum",
    "index tracked": "index_tracked",
    "segment": "segment",
    "structure": "structure",
    "asset class": "asset_class",
    "category": "category",
    "focus": "focus",
    "niche": "niche",
    "region": "region",
    "geography": "geography",
    "weighting methodology": "index_weighting_methodology",
    "index weighting methodology": "index_weighting_methodology",
    "selection methodology": "index_selection_methodology",
    "index selection methodology": "index_selection_methodology",
    "segment benchmark": "segment_benchmark",
}

# Required columns for FundamentalsCollector validation.
_FUNDAMENTALS_REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {"ticker", "issuer", "expense_ratio", "aum"}
)

# Required columns for FundFlowsCollector validation.
_FUND_FLOWS_REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {"date", "ticker", "net_flows"}
)


class FundamentalsCollector(DataCollector):
    """Collector for ETF fundamental data from ETF.com profile pages.

    Scrapes the ETF.com profile page (``etf.com/{ticker}``) for each
    requested ticker, extracting key-value data from the
    ``#summary-data`` and ``#classification-index-data`` sections.

    Uses a two-tier HTML retrieval strategy:

    1. **curl_cffi** (via ``ETFComSession.get_with_retry()``): fast,
       low-overhead HTTP request with TLS fingerprint impersonation.
    2. **Playwright** (via ``ETFComBrowserMixin._get_page_html_with_retry()``):
       full browser rendering as fallback when curl_cffi is blocked or
       returns empty content.

    Parameters
    ----------
    session : ETFComSession | None
        Pre-configured curl_cffi session. If None, a new session is
        created internally.
    browser : ETFComBrowserMixin | None
        Pre-configured Playwright browser. If None, created on demand
        when fallback is needed.
    config : ScrapingConfig | None
        Scraping configuration. Defaults to ``ScrapingConfig()``.
    retry_config : RetryConfig | None
        Retry configuration. Defaults to ``RetryConfig()``.

    Examples
    --------
    >>> collector = FundamentalsCollector()
    >>> df = collector.fetch(tickers=["SPY", "VOO"])
    >>> print(df.columns.tolist())
    ['ticker', 'issuer', 'inception_date', 'expense_ratio', ...]

    >>> # With dependency injection for testing
    >>> collector = FundamentalsCollector(session=mock_session)
    """

    def __init__(
        self,
        session: ETFComSession | None = None,
        browser: ETFComBrowserMixin | None = None,
        config: ScrapingConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize FundamentalsCollector with optional session, browser, and config.

        Parameters
        ----------
        session : ETFComSession | None
            Pre-configured curl_cffi session for dependency injection.
            If None, a new ETFComSession is created when fetch() is called.
        browser : ETFComBrowserMixin | None
            Pre-configured Playwright browser for dependency injection.
            If None, a new ETFComBrowserMixin is created when fallback is needed.
        config : ScrapingConfig | None
            Scraping configuration. Defaults to ``ScrapingConfig()``.
        retry_config : RetryConfig | None
            Retry configuration. Defaults to ``RetryConfig()``.
        """
        self._session_instance: ETFComSession | None = session
        self._browser_instance: ETFComBrowserMixin | None = browser
        self._config: ScrapingConfig = config or ScrapingConfig()
        self._retry_config: RetryConfig = retry_config or RetryConfig()

        logger.info(
            "FundamentalsCollector initialized",
            session_injected=session is not None,
            browser_injected=browser is not None,
        )

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch fundamental data for the specified ETF tickers.

        Iterates over the given tickers sequentially, scraping each
        ETF profile page and extracting key-value data from the
        ``#summary-data`` and ``#classification-index-data`` sections.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments. Expected:
            - tickers (list[str]): List of ETF ticker symbols to fetch.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns corresponding to the profile fields
            (ticker, issuer, inception_date, expense_ratio, aum,
            index_tracked, segment, structure, asset_class, category,
            focus, niche, region, geography,
            index_weighting_methodology, index_selection_methodology,
            segment_benchmark). Returns an empty DataFrame if tickers
            is empty.

        Examples
        --------
        >>> collector = FundamentalsCollector()
        >>> df = collector.fetch(tickers=["SPY", "VOO"])
        >>> print(df["ticker"].tolist())
        ['SPY', 'VOO']
        """
        tickers: list[str] = kwargs.get("tickers", [])

        if not tickers:
            logger.info("No tickers provided, returning empty DataFrame")
            return pd.DataFrame()

        logger.info(
            "Starting fundamentals collection",
            ticker_count=len(tickers),
        )

        # Resolve session: use injected or create new
        session = self._session_instance
        should_close_session = False
        if session is None:
            session = ETFComSession(
                config=self._config, retry_config=self._retry_config
            )
            should_close_session = True

        all_records: list[dict[str, str | None]] = []

        try:
            for ticker in tickers:
                url = PROFILE_URL_TEMPLATE.format(ticker=ticker)
                logger.debug(
                    "Fetching fundamentals",
                    ticker=ticker,
                    url=url,
                )

                try:
                    html = self._get_html(url)
                    record = self._parse_profile(html, ticker)
                    all_records.append(record)

                    logger.debug(
                        "Fundamentals fetched",
                        ticker=ticker,
                        field_count=len(record),
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to fetch fundamentals",
                        ticker=ticker,
                        error=str(e),
                    )
                    # Add a minimal record with just the ticker
                    all_records.append({"ticker": ticker})
        finally:
            if should_close_session:
                session.close()

        if not all_records:
            return pd.DataFrame()

        df = pd.DataFrame(all_records)

        logger.info(
            "Fundamentals collection completed",
            total_tickers=len(df),
            columns=list(df.columns) if not df.empty else [],
        )

        return df

    def _get_html(self, url: str) -> str:
        """Retrieve HTML content using curl_cffi with Playwright fallback.

        1. Tries ``ETFComSession.get_with_retry(url)`` via curl_cffi.
        2. If the response is valid and has sufficient content, returns it.
        3. If blocked (``ETFComBlockedError``) or content is too short,
           falls back to ``ETFComBrowserMixin._get_page_html_with_retry(url)``.

        Parameters
        ----------
        url : str
            The URL to fetch HTML from.

        Returns
        -------
        str
            The HTML content of the page.

        Raises
        ------
        ETFComBlockedError
            If both curl_cffi and Playwright fail.
        ETFComTimeoutError
            If Playwright fails with a timeout.
        """
        session = self._session_instance
        if session is None:
            session = ETFComSession(
                config=self._config, retry_config=self._retry_config
            )

        try:
            response = session.get_with_retry(url)
            html: str = response.text

            # Check if content is sufficient
            if len(html) >= _MIN_CONTENT_LENGTH:
                logger.debug(
                    "HTML retrieved via curl_cffi",
                    url=url,
                    content_length=len(html),
                )
                return html

            logger.debug(
                "curl_cffi response too short, falling back to Playwright",
                url=url,
                content_length=len(html),
            )

        except ETFComBlockedError:
            logger.debug(
                "curl_cffi blocked, falling back to Playwright",
                url=url,
            )

        # Fallback to Playwright
        return self._get_html_via_playwright(url)

    def _get_html_via_playwright(self, url: str) -> str:
        """Retrieve HTML content via Playwright browser.

        Parameters
        ----------
        url : str
            The URL to fetch HTML from.

        Returns
        -------
        str
            The HTML content of the page.
        """
        browser = self._browser_instance
        should_close = False
        if browser is None:
            browser = ETFComBrowserMixin(
                config=self._config, retry_config=self._retry_config
            )
            should_close = True

        try:
            loop = asyncio.new_event_loop()
            try:
                html: str = loop.run_until_complete(
                    self._async_get_html_via_playwright(browser, url)
                )
                return html
            finally:
                loop.close()
        finally:
            if should_close:
                close_loop = asyncio.new_event_loop()
                try:
                    close_loop.run_until_complete(browser.close())
                finally:
                    close_loop.close()

    async def _async_get_html_via_playwright(
        self,
        browser: ETFComBrowserMixin,
        url: str,
    ) -> str:
        """Asynchronously retrieve HTML via Playwright.

        Parameters
        ----------
        browser : ETFComBrowserMixin
            Browser instance to use.
        url : str
            The URL to fetch.

        Returns
        -------
        str
            The HTML content.
        """
        await browser._ensure_browser()
        html: str = await browser._get_page_html_with_retry(url)
        logger.debug(
            "HTML retrieved via Playwright",
            url=url,
            content_length=len(html),
        )
        return html

    def _parse_profile(self, html: str, ticker: str) -> dict[str, str | None]:
        """Parse an ETF profile page HTML to extract key-value data.

        Extracts data from the ``[data-testid='summary-data']`` and
        ``[data-testid='classification-data']`` sections. Each section
        contains a table with key-value rows (``<tr><td>Key</td><td>Value</td></tr>``).

        The ``'--'`` placeholder is converted to ``None``.

        Parameters
        ----------
        html : str
            Full HTML content of the ETF profile page.
        ticker : str
            The ETF ticker symbol (added to the result dict).

        Returns
        -------
        dict[str, str | None]
            Dictionary of parsed field values, keyed by snake_case names.
            Always includes ``ticker``. Other fields may be absent if
            the sections are not found in the HTML.

        Examples
        --------
        >>> collector = FundamentalsCollector()
        >>> data = collector._parse_profile(html, "SPY")
        >>> data["ticker"]
        'SPY'
        >>> data["issuer"]
        'State Street'
        """
        soup = BeautifulSoup(html, "html.parser")
        result: dict[str, str | None] = {"ticker": ticker}

        # Extract from both data sections
        for selector in [SUMMARY_DATA_ID, CLASSIFICATION_DATA_ID]:
            container = soup.select_one(selector)
            if container is None:
                logger.debug(
                    "Section not found in profile HTML",
                    ticker=ticker,
                    selector=selector,
                )
                continue

            table_tag = container.find("table")
            if table_tag is None or not isinstance(table_tag, Tag):
                continue

            tbody_tag = table_tag.find("tbody")
            if tbody_tag is None or not isinstance(tbody_tag, Tag):
                continue

            for tr in tbody_tag.find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) != 2:
                    continue

                raw_key = cells[0].get_text(strip=True).lower()
                raw_value = cells[1].get_text(strip=True)

                # Map to snake_case field name
                field_name = _PROFILE_KEY_MAP.get(raw_key)
                if field_name is None:
                    logger.debug(
                        "Unknown profile field, skipping",
                        ticker=ticker,
                        raw_key=raw_key,
                    )
                    continue

                # Convert '--' placeholder to None
                if raw_value == _PLACEHOLDER:
                    result[field_name] = None
                else:
                    result[field_name] = raw_value

        logger.debug(
            "Profile parsed",
            ticker=ticker,
            field_count=len(result),
        )

        return result

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the fetched fundamentals data.

        Checks that the DataFrame:
        - Is not empty
        - Contains the required columns (ticker, issuer, expense_ratio, aum)

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid, False otherwise.

        Examples
        --------
        >>> collector = FundamentalsCollector()
        >>> df = pd.DataFrame({"ticker": ["SPY"], "issuer": ["State Street"],
        ...                     "expense_ratio": ["0.09%"], "aum": ["$500B"]})
        >>> collector.validate(df)
        True
        """
        if df.empty:
            logger.warning("Validation failed: DataFrame is empty")
            return False

        missing = _FUNDAMENTALS_REQUIRED_COLUMNS - set(df.columns)
        if missing:
            logger.warning(
                "Validation failed: missing required columns",
                missing_columns=list(missing),
                actual_columns=list(df.columns),
            )
            return False

        logger.debug(
            "Validation passed",
            row_count=len(df),
        )
        return True


class FundFlowsCollector(DataCollector):
    """Collector for ETF fund flow data from ETF.com.

    Scrapes the ETF.com fund flows page for a given ticker, extracting
    daily net flow data from the fund flows table.

    Uses a two-tier HTML retrieval strategy:

    1. **curl_cffi** (via ``ETFComSession.get_with_retry()``): fast,
       low-overhead HTTP request with TLS fingerprint impersonation.
    2. **Playwright** (via ``ETFComBrowserMixin._get_page_html_with_retry()``):
       full browser rendering as fallback when curl_cffi is blocked or
       returns empty content.

    Parameters
    ----------
    session : ETFComSession | None
        Pre-configured curl_cffi session. If None, a new session is
        created internally.
    browser : ETFComBrowserMixin | None
        Pre-configured Playwright browser. If None, created on demand.
    config : ScrapingConfig | None
        Scraping configuration. Defaults to ``ScrapingConfig()``.
    retry_config : RetryConfig | None
        Retry configuration. Defaults to ``RetryConfig()``.

    Examples
    --------
    >>> collector = FundFlowsCollector()
    >>> df = collector.fetch(ticker="SPY")
    >>> print(df.columns.tolist())
    ['date', 'ticker', 'net_flows']
    """

    def __init__(
        self,
        session: ETFComSession | None = None,
        browser: ETFComBrowserMixin | None = None,
        config: ScrapingConfig | None = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize FundFlowsCollector with optional session, browser, and config.

        Parameters
        ----------
        session : ETFComSession | None
            Pre-configured curl_cffi session for dependency injection.
        browser : ETFComBrowserMixin | None
            Pre-configured Playwright browser for dependency injection.
        config : ScrapingConfig | None
            Scraping configuration. Defaults to ``ScrapingConfig()``.
        retry_config : RetryConfig | None
            Retry configuration. Defaults to ``RetryConfig()``.
        """
        self._session_instance: ETFComSession | None = session
        self._browser_instance: ETFComBrowserMixin | None = browser
        self._config: ScrapingConfig = config or ScrapingConfig()
        self._retry_config: RetryConfig = retry_config or RetryConfig()

        logger.info(
            "FundFlowsCollector initialized",
            session_injected=session is not None,
            browser_injected=browser is not None,
        )

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch fund flow data for the specified ETF ticker.

        Parameters
        ----------
        **kwargs : Any
            Keyword arguments. Expected:
            - ticker (str): ETF ticker symbol to fetch fund flows for.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, ticker, net_flows.
            Returns an empty DataFrame if no data is found.

        Examples
        --------
        >>> collector = FundFlowsCollector()
        >>> df = collector.fetch(ticker="SPY")
        >>> print(df.head())
               date ticker  net_flows
        0  2025-09-10    SPY    2787.59
        """
        ticker: str = kwargs.get("ticker", "")

        if not ticker:
            logger.info("No ticker provided, returning empty DataFrame")
            return pd.DataFrame()

        url = FUND_FLOWS_URL_TEMPLATE.format(ticker=ticker)
        logger.info(
            "Starting fund flows collection",
            ticker=ticker,
            url=url,
        )

        # Resolve session
        session = self._session_instance
        should_close_session = False
        if session is None:
            session = ETFComSession(
                config=self._config, retry_config=self._retry_config
            )
            should_close_session = True

        try:
            html = self._get_html(url)
        finally:
            if should_close_session:
                session.close()

        rows = self._parse_fund_flows_table(html)

        if not rows:
            logger.warning(
                "No fund flow data found",
                ticker=ticker,
            )
            return pd.DataFrame(columns=pd.Index(["date", "ticker", "net_flows"]))

        # Add ticker to each row
        for row in rows:
            row["ticker"] = ticker

        df = pd.DataFrame(rows)

        logger.info(
            "Fund flows collection completed",
            ticker=ticker,
            row_count=len(df),
        )

        return df

    def _get_html(self, url: str) -> str:
        """Retrieve HTML content using curl_cffi with Playwright fallback.

        Uses the same two-tier strategy as FundamentalsCollector:
        curl_cffi first, Playwright on failure or empty content.

        Parameters
        ----------
        url : str
            The URL to fetch HTML from.

        Returns
        -------
        str
            The HTML content of the page.
        """
        session = self._session_instance
        if session is None:
            session = ETFComSession(
                config=self._config, retry_config=self._retry_config
            )

        try:
            response = session.get_with_retry(url)
            html: str = response.text

            if len(html) >= _MIN_CONTENT_LENGTH:
                logger.debug(
                    "HTML retrieved via curl_cffi",
                    url=url,
                    content_length=len(html),
                )
                return html

            logger.debug(
                "curl_cffi response too short, falling back to Playwright",
                url=url,
                content_length=len(html),
            )

        except ETFComBlockedError:
            logger.debug(
                "curl_cffi blocked, falling back to Playwright",
                url=url,
            )

        # Fallback to Playwright
        browser = self._browser_instance
        should_close = False
        if browser is None:
            browser = ETFComBrowserMixin(
                config=self._config, retry_config=self._retry_config
            )
            should_close = True

        try:
            loop = asyncio.new_event_loop()
            try:
                html = loop.run_until_complete(
                    self._async_get_html_via_playwright(browser, url)
                )
                return html
            finally:
                loop.close()
        finally:
            if should_close:
                close_loop = asyncio.new_event_loop()
                try:
                    close_loop.run_until_complete(browser.close())
                finally:
                    close_loop.close()

    async def _async_get_html_via_playwright(
        self,
        browser: ETFComBrowserMixin,
        url: str,
    ) -> str:
        """Asynchronously retrieve HTML via Playwright.

        Parameters
        ----------
        browser : ETFComBrowserMixin
            Browser instance to use.
        url : str
            The URL to fetch.

        Returns
        -------
        str
            The HTML content.
        """
        await browser._ensure_browser()
        html: str = await browser._get_page_html_with_retry(url)
        logger.debug(
            "HTML retrieved via Playwright",
            url=url,
            content_length=len(html),
        )
        return html

    def _parse_fund_flows_table(self, html: str) -> list[dict[str, Any]]:
        """Parse the fund flows HTML table into a list of row dicts.

        Extracts date and net flow values from the
        ``[data-testid='fund-flows-table']`` section. Comma-separated
        numbers (e.g. ``"2,787.59"``) are converted to floats.
        The ``'--'`` placeholder is converted to ``NaN``.

        Parameters
        ----------
        html : str
            Full HTML content of the fund flows page.

        Returns
        -------
        list[dict[str, Any]]
            List of dicts with keys ``date`` (str) and ``net_flows`` (float).
            Returns an empty list if the table is not found.

        Examples
        --------
        >>> collector = FundFlowsCollector()
        >>> rows = collector._parse_fund_flows_table(html)
        >>> rows[0]
        {'date': '2025-09-10', 'net_flows': 2787.59}
        """
        soup = BeautifulSoup(html, "html.parser")

        # Find the fund flows table container
        container = soup.select_one(FLOW_TABLE_ID)
        if container is None:
            logger.warning("Fund flows table not found in HTML")
            return []

        table_tag = container.find("table")
        if table_tag is None or not isinstance(table_tag, Tag):
            logger.warning("No table found in fund flows container")
            return []

        tbody_tag = table_tag.find("tbody")
        if tbody_tag is None or not isinstance(tbody_tag, Tag):
            logger.warning("No tbody found in fund flows table")
            return []

        rows: list[dict[str, Any]] = []

        for tr in tbody_tag.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 2:
                continue

            date_text = cells[0].get_text(strip=True)
            flow_text = cells[1].get_text(strip=True)

            # Convert '--' placeholder to NaN
            if flow_text == _PLACEHOLDER:
                net_flows: float = math.nan
            else:
                # Remove commas and convert to float
                try:
                    net_flows = float(flow_text.replace(",", ""))
                except ValueError:
                    logger.debug(
                        "Failed to parse net flows value",
                        date=date_text,
                        raw_value=flow_text,
                    )
                    net_flows = math.nan

            rows.append({"date": date_text, "net_flows": net_flows})

        logger.debug(
            "Fund flows table parsed",
            row_count=len(rows),
        )

        return rows

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the fetched fund flow data.

        Checks that the DataFrame:
        - Is not empty
        - Contains the required columns (date, ticker, net_flows)

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to validate.

        Returns
        -------
        bool
            True if the data is valid, False otherwise.

        Examples
        --------
        >>> collector = FundFlowsCollector()
        >>> df = pd.DataFrame({"date": ["2025-09-10"], "ticker": ["SPY"],
        ...                     "net_flows": [2787.59]})
        >>> collector.validate(df)
        True
        """
        if df.empty:
            logger.warning("Validation failed: DataFrame is empty")
            return False

        missing = _FUND_FLOWS_REQUIRED_COLUMNS - set(df.columns)
        if missing:
            logger.warning(
                "Validation failed: missing required columns",
                missing_columns=list(missing),
                actual_columns=list(df.columns),
            )
            return False

        logger.debug(
            "Validation passed",
            row_count=len(df),
        )
        return True


__all__ = ["FundFlowsCollector", "FundamentalsCollector", "TickerCollector"]

"""ETF.com screener page ticker collector.

This module provides the ``TickerCollector`` class for scraping the complete
list of ETF tickers and basic metadata from the ETF.com screener page
(https://www.etf.com/topics/etf-screener).

The screener page requires JavaScript rendering, so Playwright
(``ETFComBrowserMixin``) is used instead of curl_cffi. The collector
navigates the paginated screener, extracting ticker, name, issuer,
category, expense_ratio, and aum from each table row.

Features
--------
- DataCollector abstract base class compliance (fetch/validate interface)
- Playwright-based browser automation via ETFComBrowserMixin
- Dependency injection for browser instance (testability)
- Pagination support (100 items per page)
- ``'--'`` placeholder conversion to NaN
- BeautifulSoup HTML table parsing

Examples
--------
>>> from market.etfcom.collectors import TickerCollector
>>> collector = TickerCollector()
>>> df = collector.collect()
>>> print(df.head())
  ticker                       name       issuer  ...
0    SPY  SPDR S&P 500 ETF Trust  State Street  ...

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
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup

from market.base_collector import DataCollector
from market.etfcom.browser import ETFComBrowserMixin
from market.etfcom.constants import NEXT_PAGE_SELECTOR, SCREENER_URL
from market.etfcom.types import ScrapingConfig
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


__all__ = ["TickerCollector"]

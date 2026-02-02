"""TSA Passenger Data Collector module.

This module provides the TSAPassengerDataCollector class for collecting
TSA checkpoint passenger volume data from the official TSA website.

The data is scraped from https://www.tsa.gov/travel/passenger-volumes
and includes daily passenger counts at TSA checkpoints.

Examples
--------
>>> from market.tsa import TSAPassengerDataCollector
>>> collector = TSAPassengerDataCollector()
>>> df = collector.collect(start_date="2024-01-01", end_date="2024-01-31")
>>> print(df.head())
        Date  Numbers
0 2024-01-31  2500000
1 2024-01-30  2400000
"""

import datetime
import re
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from market.base_collector import DataCollector
from utils_core.logging import get_logger

logger = get_logger(__name__)

TSA_BASE_URL = "https://www.tsa.gov/travel/passenger-volumes"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.124 Safari/537.36"
)
REQUEST_TIMEOUT = 30


class TSAPassengerDataCollector(DataCollector):
    """Collector for TSA checkpoint passenger volume data.

    This class scrapes daily passenger volume data from the TSA website
    (https://www.tsa.gov/travel/passenger-volumes). It inherits from
    the DataCollector base class and implements the required fetch()
    and validate() methods.

    The TSA publishes daily checkpoint throughput numbers, which are
    useful for analyzing air travel trends and comparing current
    volumes to historical data.

    Attributes
    ----------
    url : str
        Base URL for the TSA passenger volumes page.

    Examples
    --------
    >>> collector = TSAPassengerDataCollector()
    >>> df = collector.fetch(start_date="2024-01-01", end_date="2024-01-31")
    >>> print(f"Collected {len(df)} days of data")
    Collected 31 days of data

    >>> # Fetch data for a specific year
    >>> df = collector.fetch(year=2023)
    >>> print(df["Numbers"].mean())
    2345678.0
    """

    def __init__(self) -> None:
        """Initialize the TSAPassengerDataCollector.

        Sets up the base URL for the TSA passenger volumes page.
        """
        self.url = TSA_BASE_URL

    def fetch(self, **kwargs: Any) -> pd.DataFrame:
        """Fetch TSA passenger data from the website.

        Scrapes the TSA website for checkpoint passenger volume data.
        Optionally filters the data by date range or fetches data for
        a specific year.

        Parameters
        ----------
        start_date : str, optional
            Start date for filtering in YYYY-MM-DD format.
        end_date : str, optional
            End date for filtering in YYYY-MM-DD format.
        year : int, optional
            Specific year to fetch data for (2019 onwards).
            If provided, fetches data from the year-specific page.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns:
            - Date: datetime, the date of the checkpoint data
            - Numbers: int, the number of passengers

        Raises
        ------
        requests.exceptions.RequestException
            If the HTTP request fails.

        Examples
        --------
        >>> collector = TSAPassengerDataCollector()
        >>> df = collector.fetch(start_date="2024-01-01", end_date="2024-01-31")
        >>> print(df.columns.tolist())
        ['Date', 'Numbers']
        """
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")
        year = kwargs.get("year")

        url = self.url
        if year:
            url = f"{self.url}/{year}"

        logger.debug(
            "Fetching TSA passenger data",
            url=url,
            start_date=start_date,
            end_date=end_date,
            year=year,
        )

        headers = {"User-Agent": DEFAULT_USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        df = self._parse_html_table(response.content)

        if start_date or end_date:
            df = self._filter_by_date_range(df, start_date, end_date)

        logger.info(
            "TSA passenger data fetched successfully",
            row_count=len(df),
            date_range=(
                f"{df['Date'].min()} to {df['Date'].max()}" if not df.empty else "N/A"
            ),
        )

        return df

    def _parse_html_table(self, html_content: bytes) -> pd.DataFrame:
        """Parse the HTML table containing passenger data.

        Parameters
        ----------
        html_content : bytes
            Raw HTML content from the TSA website.

        Returns
        -------
        pd.DataFrame
            Parsed DataFrame with Date and Numbers columns.
            Returns empty DataFrame if no table is found.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.find("table")

        if not table:
            logger.warning("No table found in HTML content")
            return pd.DataFrame(
                {
                    "Date": pd.Series(dtype="datetime64[ns]"),
                    "Numbers": pd.Series(dtype="int64"),
                }
            )

        dates: list[datetime.datetime] = []
        numbers: list[int] = []

        tbody = table.find("tbody")
        if not tbody:
            logger.warning("No tbody found in table")
            return pd.DataFrame(
                {
                    "Date": pd.Series(dtype="datetime64[ns]"),
                    "Numbers": pd.Series(dtype="int64"),
                }
            )

        rows = tbody.find_all("tr")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                date_text = cells[0].get_text(strip=True)
                number_text = cells[1].get_text(strip=True)
                number_clean = re.sub(r"[,]", "", number_text)

                try:
                    date_obj = datetime.datetime.strptime(date_text, "%m/%d/%Y")
                    dates.append(date_obj)
                    numbers.append(int(number_clean))
                except (ValueError, TypeError) as e:
                    logger.debug(
                        "Failed to parse row data",
                        date_text=date_text,
                        number_text=number_text,
                        error=str(e),
                    )
                    continue

        df = (
            pd.DataFrame({"Date": dates, "Numbers": numbers})
            .assign(Date=lambda x: pd.to_datetime(x["Date"]))
            .sort_values("Date", ascending=False)
            .reset_index(drop=True)
        )

        return df

    def _filter_by_date_range(
        self,
        df: pd.DataFrame,
        start_date: str | None,
        end_date: str | None,
    ) -> pd.DataFrame:
        """Filter DataFrame by date range.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to filter.
        start_date : str | None
            Start date in YYYY-MM-DD format.
        end_date : str | None
            End date in YYYY-MM-DD format.

        Returns
        -------
        pd.DataFrame
            Filtered DataFrame.
        """
        if df.empty:
            return df

        result = df.copy()

        if start_date:
            start_dt = pd.to_datetime(start_date)
            mask = result["Date"] >= start_dt
            result = result.loc[mask]

        if end_date:
            end_dt = pd.to_datetime(end_date)
            mask = result["Date"] <= end_dt
            result = result.loc[mask]

        return result.reset_index(drop=True)

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the fetched TSA passenger data.

        Checks that the DataFrame:
        - Is not empty
        - Contains required columns (Date, Numbers)
        - Has no negative passenger counts

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
        >>> collector = TSAPassengerDataCollector()
        >>> df = pd.DataFrame({
        ...     "Date": pd.to_datetime(["2024-01-15"]),
        ...     "Numbers": [2500000]
        ... })
        >>> collector.validate(df)
        True
        """
        if df.empty:
            logger.warning("Validation failed: DataFrame is empty")
            return False

        required_columns = {"Date", "Numbers"}
        if not required_columns.issubset(set(df.columns)):
            logger.warning(
                "Validation failed: Missing required columns",
                required=list(required_columns),
                actual=list(df.columns),
            )
            return False

        if (df["Numbers"] < 0).any():
            logger.warning("Validation failed: Negative passenger counts found")
            return False

        logger.debug("Validation passed", row_count=len(df))
        return True


__all__ = ["TSAPassengerDataCollector"]

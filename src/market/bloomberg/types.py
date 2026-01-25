"""Type definitions for market.bloomberg module.

This module provides type definitions for Bloomberg data fetching including:

- Security identifier types (IDType)
- Data periodicity (Periodicity)
- Data source configurations (DataSource)
- Fetch options (BloombergFetchOptions)
- Data results (BloombergDataResult)
- News data structures (NewsStory)
- Field metadata (FieldInfo)

Examples
--------
>>> from market.bloomberg.types import BloombergFetchOptions, IDType
>>> options = BloombergFetchOptions(
...     securities=["AAPL US Equity"],
...     fields=["PX_LAST"],
... )
>>> options.id_type
<IDType.TICKER: 'ticker'>
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd


class IDType(str, Enum):
    """Security identifier types for Bloomberg.

    Attributes
    ----------
    TICKER : str
        Bloomberg ticker symbol (e.g., "AAPL US Equity")
    SEDOL : str
        Stock Exchange Daily Official List identifier
    CUSIP : str
        Committee on Uniform Securities Identification Procedures
    ISIN : str
        International Securities Identification Number
    FIGI : str
        Financial Instrument Global Identifier
    """

    TICKER = "ticker"
    SEDOL = "sedol"
    CUSIP = "cusip"
    ISIN = "isin"
    FIGI = "figi"


class Periodicity(str, Enum):
    """Data periodicity/frequency for Bloomberg historical data.

    Attributes
    ----------
    DAILY : str
        Daily data
    WEEKLY : str
        Weekly data
    MONTHLY : str
        Monthly data
    QUARTERLY : str
        Quarterly data
    YEARLY : str
        Yearly data
    """

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class DataSource(str, Enum):
    """Data source types for market data fetching.

    Attributes
    ----------
    BLOOMBERG : str
        Bloomberg Terminal data source
    """

    BLOOMBERG = "bloomberg"


@dataclass
class OverrideOption:
    """Bloomberg override option for data fetching.

    Parameters
    ----------
    field : str
        The Bloomberg field to override (e.g., "CRNCY")
    value : str | int | float
        The override value

    Examples
    --------
    >>> override = OverrideOption(field="CRNCY", value="USD")
    >>> override.field
    'CRNCY'
    """

    field: str
    value: str | int | float


@dataclass
class BloombergFetchOptions:
    """Options for Bloomberg data fetching operations.

    Parameters
    ----------
    securities : list[str]
        List of securities to fetch (e.g., ["AAPL US Equity"])
    fields : list[str]
        List of Bloomberg fields to fetch (e.g., ["PX_LAST", "PX_VOLUME"])
    id_type : IDType
        Type of security identifier (default: TICKER)
    start_date : datetime | str | None
        Start date for historical data
    end_date : datetime | str | None
        End date for historical data
    periodicity : Periodicity
        Data frequency (default: DAILY)
    overrides : list[OverrideOption]
        List of override options

    Examples
    --------
    >>> options = BloombergFetchOptions(
    ...     securities=["AAPL US Equity"],
    ...     fields=["PX_LAST"],
    ... )
    >>> options.id_type
    <IDType.TICKER: 'ticker'>
    """

    securities: list[str]
    fields: list[str]
    id_type: IDType = IDType.TICKER
    start_date: datetime | str | None = None
    end_date: datetime | str | None = None
    periodicity: Periodicity = Periodicity.DAILY
    overrides: list[OverrideOption] = field(default_factory=list)


@dataclass
class BloombergDataResult:
    """Result of a Bloomberg data fetch operation.

    Parameters
    ----------
    security : str
        The security that was fetched
    data : pd.DataFrame
        The fetched data
    source : DataSource
        Data source used (BLOOMBERG)
    fetched_at : datetime
        Timestamp when data was fetched
    from_cache : bool
        Whether data was retrieved from cache
    metadata : dict[str, Any]
        Additional metadata

    Examples
    --------
    >>> result = BloombergDataResult(
    ...     security="AAPL US Equity",
    ...     data=df,
    ...     source=DataSource.BLOOMBERG,
    ...     fetched_at=datetime.now(),
    ... )
    >>> result.is_empty
    False
    """

    security: str
    data: pd.DataFrame
    source: DataSource
    fetched_at: datetime
    from_cache: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        """Check if the result contains no data."""
        return self.data.empty

    @property
    def row_count(self) -> int:
        """Get the number of rows in the data."""
        return len(self.data)


@dataclass
class NewsStory:
    """Bloomberg news story/article.

    Parameters
    ----------
    story_id : str
        Unique Bloomberg story identifier
    headline : str
        News headline
    datetime : datetime
        Publication datetime
    body : str | None
        Full article body (optional)
    source : str | None
        News source (e.g., "Bloomberg News")

    Examples
    --------
    >>> story = NewsStory(
    ...     story_id="BBG123456789",
    ...     headline="Apple Reports Q4 Earnings",
    ...     datetime=datetime(2024, 1, 15, 9, 30),
    ... )
    """

    story_id: str
    headline: str
    datetime: datetime
    body: str | None = None
    source: str | None = None


@dataclass
class FieldInfo:
    """Bloomberg field metadata.

    Parameters
    ----------
    field_id : str
        Bloomberg field mnemonic (e.g., "PX_LAST")
    field_name : str
        Human-readable field name
    description : str
        Field description
    data_type : str
        Data type of the field (e.g., "Double", "String")

    Examples
    --------
    >>> info = FieldInfo(
    ...     field_id="PX_LAST",
    ...     field_name="Last Price",
    ...     description="The last traded price",
    ...     data_type="Double",
    ... )
    """

    field_id: str
    field_name: str
    description: str
    data_type: str


__all__ = [
    "BloombergDataResult",
    "BloombergFetchOptions",
    "DataSource",
    "FieldInfo",
    "IDType",
    "NewsStory",
    "OverrideOption",
    "Periodicity",
]

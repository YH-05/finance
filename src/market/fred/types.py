"""Type definitions for the market.fred package.

This module provides type definitions for FRED data fetching including:
- Data source and interval enums
- Configuration dataclasses
- Result dataclasses
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd

# =============================================================================
# Enums
# =============================================================================


class DataSource(str, Enum):
    """Data source types for market data fetching.

    Attributes
    ----------
    YFINANCE : str
        Yahoo Finance data source
    FRED : str
        Federal Reserve Economic Data
    LOCAL : str
        Local cache/database
    BLOOMBERG : str
        Bloomberg Terminal data source
    FACTSET : str
        FactSet data source
    """

    YFINANCE = "yfinance"
    FRED = "fred"
    LOCAL = "local"
    BLOOMBERG = "bloomberg"
    FACTSET = "factset"


class Interval(str, Enum):
    """Data interval/frequency.

    Attributes
    ----------
    DAILY : str
        Daily data (1d)
    WEEKLY : str
        Weekly data (1wk)
    MONTHLY : str
        Monthly data (1mo)
    HOURLY : str
        Hourly data (1h)
    MINUTE : str
        Minute data (1m)
    """

    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"
    HOURLY = "1h"
    MINUTE = "1m"


# =============================================================================
# Configuration Dataclasses
# =============================================================================


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry behavior.

    Parameters
    ----------
    max_attempts : int
        Maximum number of retry attempts (default: 3)
    initial_delay : float
        Initial delay between retries in seconds (default: 1.0)
    max_delay : float
        Maximum delay between retries in seconds (default: 60.0)
    exponential_base : float
        Base for exponential backoff calculation (default: 2.0)
    jitter : bool
        Whether to add random jitter to delays (default: True)

    Examples
    --------
    >>> config = RetryConfig(max_attempts=5, initial_delay=0.5)
    >>> config.max_attempts
    5
    """

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass(frozen=True)
class CacheConfig:
    """Configuration for cache behavior.

    Parameters
    ----------
    enabled : bool
        Whether caching is enabled (default: True)
    ttl_seconds : int
        Time-to-live for cache entries in seconds (default: 3600)
    max_entries : int
        Maximum number of cache entries (default: 1000)
    db_path : str | None
        Path to SQLite database file (default: None, uses in-memory)

    Examples
    --------
    >>> config = CacheConfig(ttl_seconds=7200, max_entries=500)
    >>> config.ttl_seconds
    7200
    """

    enabled: bool = True
    ttl_seconds: int = 3600
    max_entries: int = 1000
    db_path: str | None = None


@dataclass
class FetchOptions:
    """Options for data fetching operations.

    Parameters
    ----------
    symbols : list[str]
        List of symbols to fetch
    start_date : datetime | str | None
        Start date for data range
    end_date : datetime | str | None
        End date for data range
    interval : Interval
        Data interval (default: DAILY)
    source : DataSource
        Data source (default: YFINANCE)
    use_cache : bool
        Whether to use cache (default: True)
    retry_config : RetryConfig | None
        Retry configuration

    Examples
    --------
    >>> options = FetchOptions(
    ...     symbols=["GDP", "CPIAUCSL"],
    ...     start_date="2024-01-01",
    ...     interval=Interval.MONTHLY,
    ... )
    """

    symbols: list[str]
    start_date: datetime | str | None = None
    end_date: datetime | str | None = None
    interval: Interval = Interval.DAILY
    source: DataSource = DataSource.YFINANCE
    use_cache: bool = True
    retry_config: RetryConfig | None = None


# =============================================================================
# Result Dataclasses
# =============================================================================


@dataclass
class MarketDataResult:
    """Result of a market data fetch operation.

    Parameters
    ----------
    symbol : str
        The symbol that was fetched
    data : pd.DataFrame
        The fetched data. Format depends on source:
        - YFINANCE: OHLCV columns (open, high, low, close, volume)
        - FRED: Single 'value' column with time series data
    source : DataSource
        Data source used
    fetched_at : datetime
        Timestamp when data was fetched
    from_cache : bool
        Whether data was retrieved from cache
    metadata : dict[str, Any]
        Additional metadata

    Examples
    --------
    >>> result = MarketDataResult(
    ...     symbol="GDP",
    ...     data=df,
    ...     source=DataSource.FRED,
    ...     fetched_at=datetime.now(),
    ...     from_cache=False,
    ... )
    """

    symbol: str
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


__all__ = [
    "CacheConfig",
    "DataSource",
    "FetchOptions",
    "Interval",
    "MarketDataResult",
    "RetryConfig",
]

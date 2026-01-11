"""Common type definitions for the market_analysis package.

This module provides type definitions for market data analysis including:
- Data source configurations
- Market data results
- Analysis results
- Retry and cache configurations
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict

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
    """

    YFINANCE = "yfinance"
    FRED = "fred"
    LOCAL = "local"


class AssetType(str, Enum):
    """Asset type classification.

    Attributes
    ----------
    STOCK : str
        Individual stocks
    INDEX : str
        Market indices (e.g., S&P 500, Nikkei 225)
    FOREX : str
        Foreign exchange pairs
    COMMODITY : str
        Commodities (gold, oil, etc.)
    BOND : str
        Bond yields and prices
    CRYPTO : str
        Cryptocurrencies
    """

    STOCK = "stock"
    INDEX = "index"
    FOREX = "forex"
    COMMODITY = "commodity"
    BOND = "bond"
    CRYPTO = "crypto"


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
    ...     symbols=["AAPL", "GOOGL"],
    ...     start_date="2024-01-01",
    ...     interval=Interval.DAILY,
    ... )
    """

    symbols: list[str]
    start_date: datetime | str | None = None
    end_date: datetime | str | None = None
    interval: Interval = Interval.DAILY
    source: DataSource = DataSource.YFINANCE
    use_cache: bool = True
    retry_config: RetryConfig | None = None


@dataclass
class AnalysisOptions:
    """Options for analysis operations.

    Parameters
    ----------
    indicators : list[str]
        List of indicators to calculate (e.g., ["sma", "ema", "rsi"])
    window_sizes : list[int]
        Window sizes for moving averages (default: [20, 50, 200])
    include_returns : bool
        Whether to include return calculations (default: True)
    include_volatility : bool
        Whether to include volatility calculations (default: True)
    annualization_factor : int
        Factor for annualizing returns/volatility (default: 252 for daily data)

    Examples
    --------
    >>> options = AnalysisOptions(
    ...     indicators=["sma", "rsi"],
    ...     window_sizes=[10, 20, 50],
    ... )
    """

    indicators: list[str] = field(default_factory=lambda: ["sma", "ema"])
    window_sizes: list[int] = field(default_factory=lambda: [20, 50, 200])
    include_returns: bool = True
    include_volatility: bool = True
    annualization_factor: int = 252


@dataclass
class ChartOptions:
    """Options for chart generation.

    Parameters
    ----------
    chart_type : str
        Type of chart ("line", "candlestick", "ohlc")
    width : int
        Chart width in pixels (default: 1200)
    height : int
        Chart height in pixels (default: 600)
    title : str | None
        Chart title
    show_volume : bool
        Whether to show volume subplot (default: True)
    indicators : list[str]
        Technical indicators to overlay
    theme : str
        Chart theme ("light", "dark")

    Examples
    --------
    >>> options = ChartOptions(
    ...     chart_type="candlestick",
    ...     title="AAPL Price Chart",
    ... )
    """

    chart_type: str = "line"
    width: int = 1200
    height: int = 600
    title: str | None = None
    show_volume: bool = True
    indicators: list[str] = field(default_factory=list)
    theme: str = "light"


@dataclass
class ExportOptions:
    """Options for data export.

    Parameters
    ----------
    format : str
        Export format ("csv", "json", "parquet", "sqlite")
    output_path : str | None
        Output file path
    include_metadata : bool
        Whether to include metadata (default: True)
    compression : str | None
        Compression method (e.g., "gzip", "zstd")

    Examples
    --------
    >>> options = ExportOptions(format="csv", output_path="./data/export.csv")
    """

    format: str = "csv"
    output_path: str | None = None
    include_metadata: bool = True
    compression: str | None = None


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
        The fetched OHLCV data
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
    ...     symbol="AAPL",
    ...     data=df,
    ...     source=DataSource.YFINANCE,
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


@dataclass
class AnalysisResult:
    """Result of an analysis operation.

    Parameters
    ----------
    symbol : str
        The symbol that was analyzed
    data : pd.DataFrame
        The analysis results
    indicators : dict[str, pd.Series]
        Calculated indicators
    statistics : dict[str, float]
        Summary statistics
    analyzed_at : datetime
        Timestamp of analysis

    Examples
    --------
    >>> result = AnalysisResult(
    ...     symbol="AAPL",
    ...     data=df,
    ...     indicators={"sma_20": sma_series},
    ...     statistics={"mean_return": 0.05},
    ... )
    """

    symbol: str
    data: pd.DataFrame
    indicators: dict[str, pd.Series] = field(default_factory=dict)
    statistics: dict[str, float] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class CorrelationResult:
    """Result of a correlation analysis.

    Parameters
    ----------
    symbols : list[str]
        Symbols included in the analysis
    correlation_matrix : pd.DataFrame
        Correlation matrix
    period : str
        Analysis period description
    method : str
        Correlation method used ("pearson", "spearman", "kendall")

    Examples
    --------
    >>> result = CorrelationResult(
    ...     symbols=["AAPL", "GOOGL", "MSFT"],
    ...     correlation_matrix=corr_df,
    ...     period="1Y",
    ...     method="pearson",
    ... )
    """

    symbols: list[str]
    correlation_matrix: pd.DataFrame
    period: str
    method: str = "pearson"


# =============================================================================
# Agent Output Types
# =============================================================================


@dataclass
class AgentOutputMetadata:
    """Metadata for agent-consumable output.

    Parameters
    ----------
    generated_at : datetime
        Timestamp of generation
    version : str
        Output format version
    source : str
        Source module/function
    symbols : list[str]
        Symbols included
    period : str
        Data period
    """

    generated_at: datetime
    version: str = "1.0"
    source: str = ""
    symbols: list[str] = field(default_factory=list)
    period: str = ""


@dataclass
class AgentOutput:
    """Structured output for AI agents.

    Parameters
    ----------
    metadata : AgentOutputMetadata
        Output metadata
    summary : str
        Human-readable summary
    data : dict[str, Any]
        Structured data
    recommendations : list[str]
        Analysis-based recommendations
    """

    metadata: AgentOutputMetadata
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": {
                "generated_at": self.metadata.generated_at.isoformat(),
                "version": self.metadata.version,
                "source": self.metadata.source,
                "symbols": self.metadata.symbols,
                "period": self.metadata.period,
            },
            "summary": self.summary,
            "data": self.data,
            "recommendations": self.recommendations,
        }


# =============================================================================
# TypedDicts for Compatibility
# =============================================================================


class OHLCVDict(TypedDict):
    """OHLCV data dictionary."""

    open: float
    high: float
    low: float
    close: float
    volume: int
    date: str


class IndicatorDict(TypedDict, total=False):
    """Technical indicator values."""

    sma: float
    ema: float
    rsi: float
    macd: float
    macd_signal: float
    bollinger_upper: float
    bollinger_lower: float


# =============================================================================
# Literal Types
# =============================================================================

# Status types
type ProcessorStatus = Literal["success", "error", "pending"]
type ValidationStatus = Literal["valid", "invalid", "skipped"]

# Log types
type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Chart types
type ChartType = Literal["line", "candlestick", "ohlc", "area"]
type ExportFormat = Literal["csv", "json", "parquet", "sqlite"]

# JSON types
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | Mapping[str, "JSONValue"] | list["JSONValue"]
type JSONObject = Mapping[str, JSONValue]

# =============================================================================
# __all__ Export
# =============================================================================

__all__ = [
    "AgentOutput",
    "AgentOutputMetadata",
    "AnalysisOptions",
    "AnalysisResult",
    "AssetType",
    "CacheConfig",
    "ChartOptions",
    "ChartType",
    "CorrelationResult",
    "DataSource",
    "ExportFormat",
    "ExportOptions",
    "FetchOptions",
    "IndicatorDict",
    "Interval",
    "JSONObject",
    "JSONPrimitive",
    "JSONValue",
    "LogFormat",
    "LogLevel",
    "MarketDataResult",
    "OHLCVDict",
    "ProcessorStatus",
    "RetryConfig",
    "ValidationStatus",
]

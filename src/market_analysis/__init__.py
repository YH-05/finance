"""market_analysis package.

A Python library for market data fetching, analysis, and visualization.

Examples
--------
>>> from market_analysis import Analyzer, TickerRegistry
>>> registry = TickerRegistry()
>>> mag7 = registry.get_group("MAGNIFICENT_7")
>>> print(mag7)
['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
"""

# Analysis classes
from .analysis import Analyzer, CorrelationAnalyzer, IndicatorCalculator

# Errors
from .errors import (
    AnalysisError,
    CacheError,
    DataFetchError,
    ErrorCode,
    ExportError,
    MarketAnalysisError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

# Types
from .types import (
    AgentOutput,
    AgentOutputMetadata,
    AnalysisOptions,
    AnalysisResult,
    AssetType,
    CacheConfig,
    ChartOptions,
    CorrelationResult,
    DataSource,
    ExportOptions,
    FetchOptions,
    Interval,
    MarketDataResult,
    RetryConfig,
)

# Utilities
from .utils import (
    PRESET_GROUPS,
    TickerInfo,
    TickerRegistry,
    get_logger,
    get_ticker_registry,
)

__all__ = [
    # Analysis
    "Analyzer",
    "CorrelationAnalyzer",
    "IndicatorCalculator",
    # Ticker Registry
    "PRESET_GROUPS",
    "TickerInfo",
    "TickerRegistry",
    "get_ticker_registry",
    # Types
    "AgentOutput",
    "AgentOutputMetadata",
    "AnalysisOptions",
    "AnalysisResult",
    "AssetType",
    "CacheConfig",
    "ChartOptions",
    "CorrelationResult",
    "DataSource",
    "ExportOptions",
    "FetchOptions",
    "Interval",
    "MarketDataResult",
    "RetryConfig",
    # Errors
    "AnalysisError",
    "CacheError",
    "DataFetchError",
    "ErrorCode",
    "ExportError",
    "MarketAnalysisError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    # Utilities
    "get_logger",
]

__version__ = "0.1.0"

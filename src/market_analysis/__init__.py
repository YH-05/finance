"""market_analysis package.

A Python library for market data fetching, analysis, and visualization.

Examples
--------
>>> from market_analysis import MarketData, Analysis
>>> data = MarketData()
>>> stock_df = data.fetch_stock("AAPL", start="2024-01-01")
>>> analysis = Analysis(stock_df)
>>> analysis.add_sma(20).add_returns()
"""

# Public API
# Analysis classes (internal)
from .analysis import Analyzer, CorrelationAnalyzer, IndicatorCalculator
from .api import Analysis, MarketData

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

# Export
from .export import DataExporter

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
    # Public API
    "Analysis",
    "MarketData",
    # Analysis (internal)
    "Analyzer",
    "CorrelationAnalyzer",
    "IndicatorCalculator",
    # Export
    "DataExporter",
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

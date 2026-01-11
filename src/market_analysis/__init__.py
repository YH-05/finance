"""market_analysis package.

A Python library for market data fetching, analysis, and visualization.
"""

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
from .utils.logging_config import get_logger

__all__ = [
    "AgentOutput",
    "AgentOutputMetadata",
    "AnalysisError",
    "AnalysisOptions",
    "AnalysisResult",
    "AssetType",
    "CacheConfig",
    "CacheError",
    "ChartOptions",
    "CorrelationResult",
    "DataFetchError",
    "DataSource",
    "ErrorCode",
    "ExportError",
    "ExportOptions",
    "FetchOptions",
    "Interval",
    "MarketAnalysisError",
    "MarketDataResult",
    "RateLimitError",
    "RetryConfig",
    "TimeoutError",
    "ValidationError",
    "get_logger",
]

__version__ = "0.1.0"

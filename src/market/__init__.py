"""Market package for financial market data analysis.

This package provides core infrastructure for market data handling including:
- Data fetching (Yahoo Finance, FRED, etc.)
- Data export (JSON, CSV, SQLite, Agent-optimized JSON)
- Type definitions for market data
- JSON schema definitions for validation
- Error handling

Submodules
----------
yfinance
    Yahoo Finance data fetcher
fred
    Federal Reserve Economic Data (FRED) API integration
etfcom
    ETF.com scraper (ticker, fundamentals, fund flows)
factset
    FactSet API integration (planned)
export
    Data export utilities
alternative
    Alternative data sources (planned)
schema
    JSON schema definitions (Pydantic V2 models)

Public API
----------
DataExporter
    Export market data to various formats
DataSource
    Data source enum (YFINANCE, FRED, LOCAL, BLOOMBERG, FACTSET)
MarketDataResult
    Result of market data fetch operation
AnalysisResult
    Result of analysis operation
AgentOutput
    Structured output for AI agents
ExportError
    Exception for export operations
StockDataMetadata
    Metadata for stock price data
EconomicDataMetadata
    Metadata for economic indicator data
MarketConfig
    Complete market data configuration
"""

from .errors import (
    BloombergConnectionError,
    BloombergDataError,
    BloombergError,
    BloombergSessionError,
    BloombergValidationError,
    CacheError,
    DataFetchError,
    ErrorCode,
    ExportError,
    FREDError,
    FREDFetchError,
    FREDValidationError,
    MarketError,
    ValidationError,
)
from .etfcom import (
    ETFComBlockedError,
    ETFComError,
    ETFComScrapingError,
    ETFComTimeoutError,
    FundamentalsCollector,
    FundFlowsCollector,
    TickerCollector,
)
from .export import DataExporter
from .schema import (
    CacheConfig,
    DataSourceConfig,
    DateRange,
    EconomicDataMetadata,
    ExportConfig,
    MarketConfig,
    StockDataMetadata,
    validate_config,
    validate_economic_metadata,
    validate_stock_metadata,
)
from .types import (
    AgentOutput,
    AgentOutputMetadata,
    AnalysisResult,
    DataSource,
    MarketDataResult,
)

__all__ = [
    "AgentOutput",
    "AgentOutputMetadata",
    "AnalysisResult",
    # Bloomberg errors
    "BloombergConnectionError",
    "BloombergDataError",
    "BloombergError",
    "BloombergSessionError",
    "BloombergValidationError",
    # Core
    "CacheConfig",
    "CacheError",
    "DataExporter",
    "DataFetchError",
    "DataSource",
    "DataSourceConfig",
    "DateRange",
    # ETF.com
    "ETFComBlockedError",
    "ETFComError",
    "ETFComScrapingError",
    "ETFComTimeoutError",
    "EconomicDataMetadata",
    "ErrorCode",
    "ExportConfig",
    "ExportError",
    # FRED errors
    "FREDError",
    "FREDFetchError",
    "FREDValidationError",
    "FundFlowsCollector",
    "FundamentalsCollector",
    "MarketConfig",
    "MarketDataResult",
    "MarketError",
    "StockDataMetadata",
    "TickerCollector",
    "ValidationError",
    "validate_config",
    "validate_economic_metadata",
    "validate_stock_metadata",
]

__version__ = "0.1.0"

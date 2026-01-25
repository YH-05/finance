"""Market package for financial market data analysis.

This package provides core infrastructure for market data handling including:
- Data fetching (Yahoo Finance, FRED, etc.)
- Data export (JSON, CSV, SQLite, Agent-optimized JSON)
- Type definitions for market data
- Error handling

Submodules
----------
yfinance
    Yahoo Finance data fetcher
fred
    Federal Reserve Economic Data (FRED) API integration
export
    Data export utilities

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
"""

from .errors import CacheError, ErrorCode, ExportError, MarketError
from .export import DataExporter
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
    "CacheError",
    "DataExporter",
    "DataSource",
    "ErrorCode",
    "ExportError",
    "MarketDataResult",
    "MarketError",
]

__version__ = "0.1.0"

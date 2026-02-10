"""Edgar package for SEC EDGAR filing data extraction.

This package provides tools for fetching and processing SEC EDGAR filings
using the edgartools library as the underlying data source.

Features
--------
- Filing type classification (10-K, 10-Q, 13F)
- Section extraction from filings (Item 1, Item 1A, Item 7, Item 8)
- Configuration management with SEC EDGAR identity
- Caching for downloaded filings
- Error handling with detailed context

Public API
----------
FilingType
    Enum for SEC filing form types (10-K, 10-Q, 13F)
SectionKey
    Enum for filing section identifiers
EdgarResult
    Dataclass for filing extraction results
EdgarConfig
    Configuration for SEC EDGAR access
EdgarError
    Base exception for edgar operations
FilingNotFoundError
    Exception for filing retrieval failures
SectionNotFoundError
    Exception for section extraction failures
CacheError
    Exception for cache operation failures
RateLimitError
    Exception for rate limiting
CacheManager
    SQLite-based cache manager for filing text
"""

from .cache import CacheManager
from .config import (
    EdgarConfig,
    load_config,
    set_identity,
)
from .errors import (
    CacheError,
    EdgarError,
    FilingNotFoundError,
    RateLimitError,
    SectionNotFoundError,
)
from .fetcher import EdgarFetcher
from .types import (
    EdgarResult,
    FilingType,
    SectionKey,
)

__all__ = [
    "CacheError",
    "CacheManager",
    "EdgarConfig",
    "EdgarError",
    "EdgarFetcher",
    "EdgarResult",
    "FilingNotFoundError",
    "FilingType",
    "RateLimitError",
    "SectionKey",
    "SectionNotFoundError",
    "load_config",
    "set_identity",
]

__version__ = "0.1.0"

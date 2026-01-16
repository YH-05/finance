"""Core functionality of the market_analysis package."""

from .base_fetcher import STANDARD_COLUMNS, BaseDataFetcher
from .bloomberg_fetcher import (
    BLOOMBERG_AVAILABLE,
    BLOOMBERG_SYMBOL_PATTERN,
    BloombergFetcher,
)
from .data_fetcher_factory import DataFetcherFactory
from .factset_fetcher import FACTSET_AVAILABLE, FACTSET_SYMBOL_PATTERN, FactSetFetcher
from .fred_fetcher import FRED_API_KEY_ENV, FRED_SERIES_PATTERN, FREDFetcher
from .mock_fetchers import (
    MockBloombergFetcher,
    MockFactSetFetcher,
    generate_mock_constituents,
    generate_mock_financial_data,
    generate_mock_ohlcv,
)
from .yfinance_fetcher import YFINANCE_SYMBOL_PATTERN, YFinanceFetcher

__all__ = [
    "BLOOMBERG_AVAILABLE",
    "BLOOMBERG_SYMBOL_PATTERN",
    "FACTSET_AVAILABLE",
    "FACTSET_SYMBOL_PATTERN",
    "FRED_API_KEY_ENV",
    "FRED_SERIES_PATTERN",
    "STANDARD_COLUMNS",
    "YFINANCE_SYMBOL_PATTERN",
    "BaseDataFetcher",
    "BloombergFetcher",
    "DataFetcherFactory",
    "FREDFetcher",
    "FactSetFetcher",
    "MockBloombergFetcher",
    "MockFactSetFetcher",
    "YFinanceFetcher",
    "generate_mock_constituents",
    "generate_mock_financial_data",
    "generate_mock_ohlcv",
]

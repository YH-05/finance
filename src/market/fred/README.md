# market.fred

FRED (Federal Reserve Economic Data) API integration for fetching economic indicator data.

## Overview

This package provides functionality for fetching economic indicator data from the Federal Reserve Economic Data (FRED) service, including:

- GDP, CPI, unemployment rate, interest rates
- Treasury yields, money supply data
- Employment statistics, inflation indicators

## Installation

The package is part of the `market` namespace. Ensure you have the required dependencies:

```bash
uv add fredapi
```

## Configuration

### API Key

Set your FRED API key via environment variable:

```bash
export FRED_API_KEY="your_api_key_here"
```

Or pass it directly when creating the fetcher:

```python
fetcher = FREDFetcher(api_key="your_api_key_here")
```

Get your API key from: https://fred.stlouisfed.org/docs/api/api_key.html

## Usage

### Basic Usage

```python
from market.fred import FREDFetcher
from market.fred.types import FetchOptions

# Create fetcher (uses FRED_API_KEY env var)
fetcher = FREDFetcher()

# Fetch GDP data
options = FetchOptions(
    symbols=["GDP"],
    start_date="2020-01-01",
    end_date="2024-12-31",
)
results = fetcher.fetch(options)

# Access the data
for result in results:
    print(f"{result.symbol}: {len(result.data)} rows")
    print(result.data.head())
```

### Multiple Series

```python
options = FetchOptions(
    symbols=["GDP", "CPIAUCSL", "UNRATE", "DGS10"],
    start_date="2020-01-01",
)
results = fetcher.fetch(options)
```

### With Caching

```python
from market.fred.cache import SQLiteCache
from market.fred.types import CacheConfig

# Create a persistent cache
cache_config = CacheConfig(
    ttl_seconds=86400,  # 24 hours
    db_path="./data/fred_cache.db",
)
cache = SQLiteCache(cache_config)

fetcher = FREDFetcher(cache=cache, cache_config=cache_config)
```

### With Retry

```python
from market.fred.types import RetryConfig

retry_config = RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    exponential_base=2.0,
)

fetcher = FREDFetcher(retry_config=retry_config)
```

### Get Series Information

```python
info = fetcher.get_series_info("GDP")
print(info["title"])  # "Gross Domestic Product"
print(info["frequency"])  # "Quarterly"
```

### Symbol Validation

```python
# Valid FRED series IDs are uppercase letters, numbers, and underscores
fetcher.validate_symbol("GDP")       # True
fetcher.validate_symbol("CPIAUCSL")  # True
fetcher.validate_symbol("DGS10")     # True
fetcher.validate_symbol("T10Y2Y")    # True

fetcher.validate_symbol("gdp")       # False (lowercase)
fetcher.validate_symbol("123ABC")    # False (starts with number)
```

## Common FRED Series IDs

| Series ID | Description |
|-----------|-------------|
| GDP | Gross Domestic Product |
| CPIAUCSL | Consumer Price Index |
| UNRATE | Unemployment Rate |
| FEDFUNDS | Federal Funds Rate |
| DGS10 | 10-Year Treasury Constant Maturity Rate |
| T10Y2Y | 10-Year Treasury Minus 2-Year Treasury |
| SP500 | S&P 500 Index |
| M2SL | M2 Money Stock |
| PAYEMS | Total Nonfarm Payrolls |

## API Reference

### FREDFetcher

Main class for fetching FRED data.

**Parameters:**
- `api_key` (str | None): FRED API key. If None, reads from FRED_API_KEY env var.
- `cache` (SQLiteCache | None): Cache instance for storing fetched data.
- `cache_config` (CacheConfig | None): Configuration for cache behavior.
- `retry_config` (RetryConfig | None): Configuration for retry behavior.

**Methods:**
- `fetch(options: FetchOptions) -> list[MarketDataResult]`: Fetch data for specified series.
- `validate_symbol(symbol: str) -> bool`: Validate a FRED series ID.
- `get_series_info(series_id: str) -> dict`: Get metadata about a series.

### FetchOptions

Options for data fetching operations.

**Fields:**
- `symbols` (list[str]): List of FRED series IDs to fetch.
- `start_date` (datetime | str | None): Start date for data range.
- `end_date` (datetime | str | None): End date for data range.
- `interval` (Interval): Data interval (default: DAILY).
- `use_cache` (bool): Whether to use cache (default: True).

### Exceptions

- `FREDValidationError`: Raised for input validation failures.
- `FREDFetchError`: Raised for data fetching failures.

## Module Structure

```
market/fred/
    __init__.py       # Package exports
    constants.py      # Constants (FRED_API_KEY_ENV, FRED_SERIES_PATTERN)
    errors.py         # Exception classes
    types.py          # Type definitions (FetchOptions, MarketDataResult, etc.)
    cache.py          # SQLiteCache for data caching
    base_fetcher.py   # Abstract base class
    fetcher.py        # FREDFetcher implementation
    README.md         # This file
```

# market.factset

FactSet API integration for fetching financial data (planned).

## Status

**Not yet implemented** - This is a placeholder module for future FactSet integration.

## Planned Features

### Company Data
- Financial statements (income statement, balance sheet, cash flow)
- Key ratios and metrics
- Segment-level data

### Market Data
- Global equity prices
- Fixed income data
- Currency and commodity data

### Analyst Data
- Consensus estimates
- Earnings revisions
- Price targets

### Ownership Data
- Institutional holdings
- Fund ownership
- Insider transactions

## Prerequisites

FactSet integration will require:
- FactSet API subscription
- API credentials (username/serial number and API key)
- Python SDK: `factset-sdk-utils`

## Planned API

```python
# Planned usage (not yet implemented)
from market.factset import FactSetFetcher
from market.factset.types import FetchOptions

fetcher = FactSetFetcher(
    username="your_username",
    api_key="your_api_key",
)

options = FetchOptions(
    symbols=["AAPL-US", "MSFT-US"],
    start_date="2024-01-01",
)
results = fetcher.fetch(options)
```

## Module Structure (Planned)

```
market/factset/
    __init__.py       # Package exports
    constants.py      # Constants (API endpoints, etc.)
    errors.py         # Exception classes
    types.py          # Type definitions (FetchOptions, etc.)
    fetcher.py        # FactSetFetcher implementation
    README.md         # This file
```

## Related Resources

- [FactSet Developer Portal](https://developer.factset.com/)
- [FactSet Python SDK](https://github.com/factset/enterprise-sdk)
- [market.fred](../fred/README.md) - FRED integration (implemented)
- [market.yfinance](../yfinance/README.md) - Yahoo Finance integration (implemented)

## Timeline

This module is part of Phase 1 of the market package refactoring.
See: `docs/project/python-packages-refactoring.md`

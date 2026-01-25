"""Constants for market.bloomberg module.

This module provides constants for Bloomberg API integration:

- Connection settings (host, port)
- Bloomberg service endpoints
- Identifier type prefixes
- Valid periodicities

Examples
--------
>>> from market.bloomberg.constants import DEFAULT_HOST, DEFAULT_PORT
>>> print(f"Bloomberg Terminal at {DEFAULT_HOST}:{DEFAULT_PORT}")
Bloomberg Terminal at localhost:8194
"""

from typing import Final

# =============================================================================
# Connection Settings
# =============================================================================

DEFAULT_HOST: Final[str] = "localhost"
"""Default Bloomberg Terminal host address.

The Bloomberg Terminal typically runs locally on the user's machine.
"""

DEFAULT_PORT: Final[int] = 8194
"""Default Bloomberg Terminal port.

Port 8194 is the standard port for Bloomberg BLPAPI connections.
"""

# =============================================================================
# Service Endpoints
# =============================================================================

REF_DATA_SERVICE: Final[str] = "//blp/refdata"
"""Bloomberg Reference Data Service endpoint.

Used for fetching historical data, reference data, and bulk data requests.
"""

NEWS_SERVICE: Final[str] = "//blp/news"
"""Bloomberg News Service endpoint.

Used for fetching news articles and headlines.
"""

API_FIELDS_SERVICE: Final[str] = "//blp/apiflds"
"""Bloomberg API Fields Service endpoint.

Used for querying field metadata and descriptions.
"""

# =============================================================================
# Identifier Mappings
# =============================================================================

ID_TYPE_PREFIXES: Final[dict[str, str]] = {
    "ticker": "",
    "sedol": "/sedol/",
    "cusip": "/cusip/",
    "isin": "/isin/",
    "figi": "/figi/",
}
"""Mapping of identifier types to Bloomberg prefix format.

Each identifier type has a specific prefix format required by Bloomberg API.
The ticker type uses no prefix as it's the default identifier format.
"""

# =============================================================================
# Valid Values
# =============================================================================

VALID_PERIODICITIES: Final[list[str]] = [
    "DAILY",
    "WEEKLY",
    "MONTHLY",
    "QUARTERLY",
    "SEMI_ANNUALLY",
    "YEARLY",
]
"""Valid data periodicity values for Bloomberg historical data requests.

These values correspond to Bloomberg's accepted frequency parameters.
"""

__all__ = [
    "API_FIELDS_SERVICE",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "ID_TYPE_PREFIXES",
    "NEWS_SERVICE",
    "REF_DATA_SERVICE",
    "VALID_PERIODICITIES",
]

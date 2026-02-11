"""Government statistics API clients for industry data.

This sub-package provides API client implementations for government
statistical agencies:

Clients
-------
BLSClient
    Client for the BLS (Bureau of Labor Statistics) API v2.0.
CensusClient
    Client for the Census Bureau API (international trade data).

See Also
--------
market.fred : FRED API client (reference implementation for API clients).
market.industry.scrapers : Web scraper implementations.
"""

from market.industry.api_clients.bls import BLSClient
from market.industry.api_clients.census import CensusClient

__all__ = [
    "BLSClient",
    "CensusClient",
]

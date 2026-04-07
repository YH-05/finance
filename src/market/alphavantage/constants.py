"""Constants for Alpha Vantage API client module.

This module defines all constants used by the Alpha Vantage API client,
including the API base URL, SSRF prevention whitelist, environment
variable names, rate limit defaults, and HTTP configuration values.

See Also
--------
market.jquants.constants : Similar constant pattern used by the J-Quants module.
"""

from typing import Final

# ---------------------------------------------------------------------------
# 1. API URL constants
# ---------------------------------------------------------------------------

BASE_URL: Final[str] = "https://www.alphavantage.co/query"
"""Base URL for the Alpha Vantage API.

All API requests are constructed by appending query parameters
to this base URL (e.g., ``BASE_URL + "?function=TIME_SERIES_DAILY"``).
"""

# ---------------------------------------------------------------------------
# 2. Security constants
# ---------------------------------------------------------------------------

ALLOWED_HOSTS: Final[frozenset[str]] = frozenset({"www.alphavantage.co"})
"""Whitelist of allowed hostnames for SSRF prevention (CWE-918).

Only requests to these hosts are permitted by the Alpha Vantage session layer.
Requests to any other host will raise ``ValueError``.
"""

MAX_RESPONSE_BODY_LOG: Final[int] = 200
"""Maximum number of characters to log from response bodies (CWE-209).

Prevents sensitive data from being exposed in log messages by truncating
response body content to this length.
"""

# ---------------------------------------------------------------------------
# 3. Environment variable names
# ---------------------------------------------------------------------------

ALPHA_VANTAGE_API_KEY_ENV: Final[str] = "ALPHA_VANTAGE_API_KEY"
"""Environment variable name for Alpha Vantage API key (single-key fallback)."""

ALPHA_VANTAGE_API_KEYS_ENV: Final[str] = "ALPHA_VANTAGE_API_KEYS"
"""Environment variable name for comma-separated Alpha Vantage API keys.

When set, multiple keys are parsed and used for rotation.
Takes precedence over ``ALPHA_VANTAGE_API_KEY_ENV``.

Example: ``ALPHA_VANTAGE_API_KEYS=key1,key2,key3``
"""

DEFAULT_DAILY_LIMIT_PER_KEY: Final[int] = 25
"""Default daily request limit per API key for the free tier.

Alpha Vantage free tier allows 25 requests per day per key.
With 4 keys, this gives 100 requests/day total.
"""

# ---------------------------------------------------------------------------
# 4. Rate limit default values
# ---------------------------------------------------------------------------

DEFAULT_REQUESTS_PER_MINUTE: Final[int] = 5
"""Default maximum number of API requests per minute.

Alpha Vantage free tier allows 25 requests per day (up to 5/minute).
This default targets the free tier. Premium plans can raise this value.
"""

DEFAULT_REQUESTS_PER_HOUR: Final[int] = 20
"""Default maximum number of API requests per hour.

Set to 20 to stay safely within the free tier limit of 25 requests per day.
"""

# ---------------------------------------------------------------------------
# 5. HTTP default configuration values
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT: Final[float] = 30.0
"""Default HTTP request timeout in seconds."""

DEFAULT_POLITE_DELAY: Final[float] = 12.0
"""Default polite delay between requests in seconds.

12 seconds corresponds to the 5 requests/minute free tier limit
(60s / 5 = 12s per request). Prevents accidental exhaustion of the
25 requests/day quota.
"""

DEFAULT_DELAY_JITTER: Final[float] = 0.5
"""Random jitter added to the polite delay in seconds."""

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "ALLOWED_HOSTS",
    "ALPHA_VANTAGE_API_KEYS_ENV",
    "ALPHA_VANTAGE_API_KEY_ENV",
    "BASE_URL",
    "DEFAULT_DAILY_LIMIT_PER_KEY",
    "DEFAULT_DELAY_JITTER",
    "DEFAULT_POLITE_DELAY",
    "DEFAULT_REQUESTS_PER_HOUR",
    "DEFAULT_REQUESTS_PER_MINUTE",
    "DEFAULT_TIMEOUT",
    "MAX_RESPONSE_BODY_LOG",
]

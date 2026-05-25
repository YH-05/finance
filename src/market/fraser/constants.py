"""Constants for FRASER REST API client module.

This module defines all constants used by the FRASER REST API client,
including the API base URL, SSRF prevention whitelist, environment
variable names, rate limit defaults, HTTP configuration values,
known title IDs, and document type subdirectory mapping.

See Also
--------
market.alphavantage.constants : Similar constant pattern used by the
    Alpha Vantage module (constant structure + CWE annotation style).
"""

from typing import Final

# ---------------------------------------------------------------------------
# 1. API URL constants
# ---------------------------------------------------------------------------

BASE_URL: Final[str] = "https://fraser.stlouisfed.org/api"
"""Base URL for the FRASER REST API.

All API requests are constructed by appending path segments and query
parameters to this base URL (e.g., ``BASE_URL + "/title/677"``).
"""

# ---------------------------------------------------------------------------
# 2. Security constants
# ---------------------------------------------------------------------------

ALLOWED_HOSTS: Final[frozenset[str]] = frozenset({"fraser.stlouisfed.org"})
"""Whitelist of allowed hostnames for SSRF prevention (CWE-918).

Only requests to these hosts are permitted by the FRASER session layer.
Requests to any other host will raise ``ValueError``.
"""

MAX_RESPONSE_BODY_LOG: Final[int] = 2048
"""Maximum number of characters to log from response bodies (CWE-209).

Prevents sensitive data from being exposed in log messages by truncating
response body content to this length.
"""

# ---------------------------------------------------------------------------
# 3. Environment variable names
# ---------------------------------------------------------------------------

FRASER_API_KEY_ENV: Final[str] = "FRASER_API_KEY"
"""Environment variable name for FRASER API key.

The FRASER API key is issued via ``POST /api/api_key`` and is required
for authenticated endpoints.
"""

# ---------------------------------------------------------------------------
# 4. Rate limit default values
# ---------------------------------------------------------------------------

DEFAULT_REQUESTS_PER_MINUTE: Final[int] = 30
"""Default maximum number of API requests per minute.

FRASER API enforces 30 requests/minute per API key.
"""

DEFAULT_REQUESTS_PER_HOUR: Final[int] = 1800
"""Default maximum number of API requests per hour.

Computed as ``DEFAULT_REQUESTS_PER_MINUTE * 60`` to keep the hourly
ceiling aligned with the per-minute limit (30 * 60 = 1800).
"""

# ---------------------------------------------------------------------------
# 5. HTTP default configuration values
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT: Final[float] = 30.0
"""Default HTTP request timeout in seconds."""

# ---------------------------------------------------------------------------
# 6. Document type metadata
# ---------------------------------------------------------------------------

KNOWN_TITLE_IDS: Final[dict[str, int | None]] = {
    "fomc_minutes": 677,
    "fomc_statements": None,
    "fomc_press_conferences": None,
    "beige_book": None,
    "monetary_policy_report": None,
    "frb_speeches": None,
}
"""Mapping of document type keys to their FRASER title IDs.

Only ``fomc_minutes`` (677) is confirmed. The remaining ``None`` values
are to be populated by the ``scripts/discover_titles.py`` CLI added in
task-2 of PR1 (manual fill-in, no automatic AST rewriting per HF1).
"""

DOC_TYPE_SUBDIRS: Final[dict[str, str]] = {
    "fomc_minutes": "fomc/minutes",
    "fomc_statements": "fomc/statements",
    "fomc_press_conferences": "fomc/press_conferences",
    "beige_book": "beige_book",
    "monetary_policy_report": "monetary_policy",
    "frb_speeches": "speeches",
}
"""Mapping of document type keys to their on-disk subdirectory layout.

Used by the downloader to choose the destination directory under the
configured ``download_dir`` root.
"""

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "ALLOWED_HOSTS",
    "BASE_URL",
    "DEFAULT_REQUESTS_PER_HOUR",
    "DEFAULT_REQUESTS_PER_MINUTE",
    "DEFAULT_TIMEOUT",
    "DOC_TYPE_SUBDIRS",
    "FRASER_API_KEY_ENV",
    "KNOWN_TITLE_IDS",
    "MAX_RESPONSE_BODY_LOG",
]

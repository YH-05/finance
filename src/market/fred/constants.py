"""Constants for FRED data fetching.

This module provides constants used throughout the market.fred package.
"""

import re
from typing import Final

# Environment variable name for FRED API key
FRED_API_KEY_ENV: Final[str] = "FRED_API_KEY"

# Valid FRED series ID pattern (uppercase letters, numbers, underscores)
# Must start with an uppercase letter
FRED_SERIES_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9_]*$")

__all__ = [
    "FRED_API_KEY_ENV",
    "FRED_SERIES_PATTERN",
]

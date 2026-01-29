"""Utility functions for the rss package.

Note: Logging functionality has been migrated to utils_core.logging.
Import get_logger from utils_core.logging instead.
"""

from rss.utils.url_normalizer import (
    calculate_title_similarity,
    is_duplicate,
    normalize_url,
)

__all__: list[str] = [
    "calculate_title_similarity",
    "is_duplicate",
    "normalize_url",
]

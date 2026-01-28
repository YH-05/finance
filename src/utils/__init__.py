"""Utils - Alias package for utils_core.

This module provides backward compatibility for `from utils.logging import ...`.
The actual implementation is in utils_core.
"""

from utils_core import __version__

__all__ = ["__version__"]

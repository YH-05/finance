"""Configuration package (deprecated).

.. deprecated:: 0.x
    This package is deprecated and will be removed in v1.0.0.
    Use `utils_core.settings` instead for environment variable management.

    Migration guide:
    - Replace `from configuration import ...` with `from utils_core.settings import ...`
    - Use `get_log_level()`, `get_log_format()`, `get_log_dir()`, `get_project_env()`
"""

import warnings

warnings.warn(
    "The 'configuration' package is deprecated and will be removed in v1.0.0. "
    "Please use 'utils_core.settings' instead. "
    "See utils_core.settings documentation for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)

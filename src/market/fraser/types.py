"""Type definitions for the market.fraser module.

This module provides type definitions for FRASER REST API data retrieval
including:

- Configuration dataclasses (``FraserConfig``, ``RetryConfig``,
  ``FetchOptions``).
- Document type Enum (``DocType``).

All dataclasses use ``frozen=True`` to ensure immutability.
``FraserConfig.api_key`` uses ``repr=False`` to prevent the API key
from leaking into log messages or stack traces (CWE-532).

See Also
--------
market.alphavantage.types : Similar frozen-dataclass + ``__post_init__``
    validation pattern for the Alpha Vantage module.
market.fraser.constants : Default values referenced by ``FraserConfig``.
market.fraser.errors : ``FraserValidationError`` raised by
    ``FraserConfig.__post_init__``.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from market.fraser.constants import (
    BASE_URL,
    DEFAULT_REQUESTS_PER_HOUR,
    DEFAULT_REQUESTS_PER_MINUTE,
    DEFAULT_TIMEOUT,
)
from market.fraser.errors import FraserValidationError

# =============================================================================
# Configuration Dataclasses
# =============================================================================


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry behaviour with exponential backoff.

    Parameters
    ----------
    max_attempts : int
        Maximum number of retry attempts (default: 5).
    base_wait : float
        Initial wait between retries in seconds (default: 1.0).
    max_wait : float
        Maximum wait between retries in seconds (default: 60.0).

    Examples
    --------
    >>> config = RetryConfig(max_attempts=3, base_wait=2.0)
    >>> config.max_attempts
    3
    """

    max_attempts: int = 5
    base_wait: float = 1.0
    max_wait: float = 60.0


@dataclass(frozen=True)
class FraserConfig:
    """Configuration for FRASER REST API client.

    Controls authentication credentials, HTTP behaviour, rate limiting,
    and retry policy.

    Parameters
    ----------
    api_key : str
        FRASER API key. If empty, read from ``FRASER_API_KEY``
        environment variable at runtime. Excluded from ``repr`` output
        for security (CWE-532).
    base_url : str
        Base URL for the FRASER REST API (default: ``BASE_URL``).
    timeout : float
        HTTP request timeout in seconds (default: ``DEFAULT_TIMEOUT``
        = 30.0). Must be ``> 0``.
    requests_per_minute : int
        Maximum number of API requests per minute (default:
        ``DEFAULT_REQUESTS_PER_MINUTE`` = 30). Must be ``>= 1``.
    requests_per_hour : int
        Maximum number of API requests per hour (default:
        ``DEFAULT_REQUESTS_PER_HOUR`` = 1800).
    retry_config : RetryConfig
        Retry policy for transient failures.

    Raises
    ------
    FraserValidationError
        If ``timeout <= 0`` or ``requests_per_minute < 1``.

    Examples
    --------
    >>> config = FraserConfig(api_key="demo")
    >>> config.timeout
    30.0
    >>> "demo" not in repr(config)  # api_key is hidden (CWE-532)
    True
    """

    api_key: str = field(default="", repr=False)
    base_url: str = BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE
    requests_per_hour: int = DEFAULT_REQUESTS_PER_HOUR
    retry_config: RetryConfig = field(default_factory=RetryConfig)

    def __post_init__(self) -> None:
        """Validate configuration value ranges.

        Raises
        ------
        FraserValidationError
            If ``timeout <= 0`` or ``requests_per_minute < 1``.
        """
        if self.timeout <= 0:
            raise FraserValidationError(
                f"timeout must be positive, got {self.timeout}",
                field="timeout",
                value=self.timeout,
            )
        if self.requests_per_minute < 1:
            raise FraserValidationError(
                f"requests_per_minute must be >= 1, got {self.requests_per_minute}",
                field="requests_per_minute",
                value=self.requests_per_minute,
            )


@dataclass(frozen=True)
class FetchOptions:
    """Options for FRASER API fetch requests.

    Parameters
    ----------
    use_cache : bool
        Whether to use cached data if available (default: True).
    prefer : str
        Preferred asset format when both PDF and text are available
        (default: ``"txt"``).
    download_dir : Path | None
        Optional override for the download destination directory.
        When ``None``, the collector's default download directory is
        used.

    Examples
    --------
    >>> options = FetchOptions(use_cache=False, prefer="pdf")
    >>> options.use_cache
    False
    >>> options.prefer
    'pdf'
    """

    use_cache: bool = True
    prefer: str = "txt"
    download_dir: Path | None = None


# =============================================================================
# Document Type Enum
# =============================================================================


class DocType(str, Enum):
    """FRASER document type identifier.

    Inherits from ``str`` so members may be used directly as dictionary
    keys (e.g., into ``KNOWN_TITLE_IDS`` / ``DOC_TYPE_SUBDIRS``) and
    serialised without manual conversion.

    Members
    -------
    FOMC_MINUTES
        Federal Open Market Committee minutes.
    FOMC_STATEMENTS
        FOMC policy statements.
    FOMC_PRESS_CONFERENCES
        FOMC chair press conference transcripts.
    BEIGE_BOOK
        Federal Reserve Beige Book.
    FRB_SPEECHES
        Federal Reserve Board speeches.
    MONETARY_POLICY_REPORT
        Monetary Policy Report to the Congress.

    Examples
    --------
    >>> DocType.FOMC_MINUTES.value
    'fomc_minutes'
    >>> DocType.FOMC_MINUTES == "fomc_minutes"
    True
    """

    FOMC_MINUTES = "fomc_minutes"
    FOMC_STATEMENTS = "fomc_statements"
    FOMC_PRESS_CONFERENCES = "fomc_press_conferences"
    BEIGE_BOOK = "beige_book"
    FRB_SPEECHES = "frb_speeches"
    MONETARY_POLICY_REPORT = "monetary_policy_report"


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    "DocType",
    "FetchOptions",
    "FraserConfig",
    "RetryConfig",
]

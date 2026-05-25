"""FRASER REST API client package.

This package provides a client for the FRASER REST API
(https://fraser.stlouisfed.org/api) to retrieve Federal Reserve archive
documents such as FOMC minutes/statements/press conferences, Beige Book
reports, Federal Reserve Board speeches, and Monetary Policy Reports.

Modules
-------
constants : API URL, environment variable names, default configuration.
errors : Exception hierarchy for FRASER API operations (7 classes,
    direct ``Exception`` inheritance to avoid circular imports).
types : Configuration dataclasses (``FraserConfig``, ``RetryConfig``,
    ``FetchOptions``) and the ``DocType`` enum.
rate_limiter : Re-exports ``DualWindowRateLimiter`` from
    ``market.alphavantage.rate_limiter`` and provides
    ``get_fraser_rate_limiter`` factory.
models : Pydantic V2 response models for FRASER API data.

Notes
-----
This package follows the same module structure as ``market.alphavantage``
and ``market.polymarket`` to keep new-API onboarding consistent. The
error hierarchy intentionally inherits directly from ``Exception``
(not from ``MarketError``) to avoid circular imports.
"""

from market.fraser.errors import (
    FraserAPIError,
    FraserAuthError,
    FraserDownloadError,
    FraserError,
    FraserNotFoundError,
    FraserParseError,
    FraserRateLimitError,
    FraserValidationError,
)
from market.fraser.models import (
    BeigeBookReport,
    FOMCMeeting,
    FraserAuthor,
    FraserItem,
    FraserLocation,
    FraserSubject,
    FraserTheme,
    FraserTimelineEvent,
    FraserTitle,
    FraserTocEntry,
    FRBSpeech,
    MonetaryPolicyReport,
)
from market.fraser.rate_limiter import (
    DualWindowRateLimiter,
    get_fraser_rate_limiter,
)
from market.fraser.session import FraserSession
from market.fraser.types import (
    DocType,
    FetchOptions,
    FraserConfig,
    RetryConfig,
)

__all__ = [
    "BeigeBookReport",
    "DocType",
    "DualWindowRateLimiter",
    "FOMCMeeting",
    "FRBSpeech",
    "FetchOptions",
    "FraserAPIError",
    "FraserAuthError",
    "FraserAuthor",
    "FraserConfig",
    "FraserDownloadError",
    "FraserError",
    "FraserItem",
    "FraserLocation",
    "FraserNotFoundError",
    "FraserParseError",
    "FraserRateLimitError",
    "FraserSession",
    "FraserSubject",
    "FraserTheme",
    "FraserTimelineEvent",
    "FraserTitle",
    "FraserTocEntry",
    "FraserValidationError",
    "MonetaryPolicyReport",
    "RetryConfig",
    "get_fraser_rate_limiter",
]

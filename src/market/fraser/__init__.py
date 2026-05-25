"""market.fraser - FRASER REST API subpackage.

The public surface is intentionally minimal (10 symbols) so that the
package boundary stays stable while internal modules continue to
evolve. Internal helpers (``FraserSession``, ``FraserDownloader``,
parser functions, etc.) remain importable from their respective
submodules but are excluded from the package ``__all__`` to discourage
cross-package coupling.

Public surface (10 symbols)
---------------------------
FraserClient
    High-level FRASER REST API client.
FOMCMinutesFetcher
    Concrete fetcher for FOMC Minutes documents.
FOMCStatementsFetcher
    Concrete fetcher for FOMC policy Statement documents.
FOMCPressConferencesFetcher
    Concrete fetcher for FOMC chair Press Conference transcripts.
FraserConfig
    Configuration dataclass (auth, HTTP timeout, rate limits).
FOMCMeeting
    Pydantic V2 domain model for FOMC meeting documents.
FraserError
    Base exception for the FRASER subpackage.
FraserAuthError
    Raised on authentication / authorisation failures.
FraserParseError
    Raised on response parsing failures.
FraserRateLimitError
    Raised when the FRASER rate limit is exceeded.

Examples
--------
>>> from market.fraser import FOMCMinutesFetcher
>>> fetcher = FOMCMinutesFetcher()  # doctest: +SKIP
>>> minutes = fetcher.list_minutes(year_range=(2024, 2024))  # doctest: +SKIP
"""

from market.fraser.client import FraserClient
from market.fraser.errors import (
    FraserAuthError,
    FraserError,
    FraserParseError,
    FraserRateLimitError,
)
from market.fraser.fetchers.fomc import (
    FOMCMinutesFetcher,
    FOMCPressConferencesFetcher,
    FOMCStatementsFetcher,
)
from market.fraser.models import FOMCMeeting
from market.fraser.types import FraserConfig

__version__ = "0.1.0"

__all__ = [
    "FOMCMeeting",
    "FOMCMinutesFetcher",
    "FOMCPressConferencesFetcher",
    "FOMCStatementsFetcher",
    "FraserAuthError",
    "FraserClient",
    "FraserConfig",
    "FraserError",
    "FraserParseError",
    "FraserRateLimitError",
]

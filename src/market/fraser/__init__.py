"""market.fraser - FRASER REST API subpackage.

The public surface stays curated so the package boundary is stable
while internal modules continue to evolve. Internal helpers
(``FraserSession``, ``FraserDownloader``, parser functions, etc.)
remain importable from their respective submodules but are excluded
from the package ``__all__`` to discourage cross-package coupling.

Public surface (16 symbols)
---------------------------
FraserClient
    High-level FRASER REST API client.
FOMCMinutesFetcher
    Concrete fetcher for FOMC Minutes documents.
FOMCStatementsFetcher
    Concrete fetcher for FOMC policy Statement documents.
FOMCPressConferencesFetcher
    Concrete fetcher for FOMC chair Press Conference transcripts.
BeigeBookFetcher
    Concrete fetcher for Beige Book reports with parallel download.
FRBSpeechFetcher
    Concrete fetcher for FRB speeches with speaker filtering.
MonetaryPolicyReportFetcher
    Concrete fetcher for Monetary Policy Reports to the Congress.
FraserConfig
    Configuration dataclass (auth, HTTP timeout, rate limits).
FOMCMeeting
    Pydantic V2 domain model for FOMC meeting documents.
BeigeBookReport
    Pydantic V2 domain model for Beige Book reports.
FRBSpeech
    Pydantic V2 domain model for FRB speeches.
MonetaryPolicyReport
    Pydantic V2 domain model for Monetary Policy Reports.
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
>>> from market.fraser import BeigeBookFetcher, FRBSpeechFetcher
>>> bb = BeigeBookFetcher()  # doctest: +SKIP
>>> reports = bb.fetch_all((2023, 2024), max_workers=4)  # doctest: +SKIP
>>> speeches = FRBSpeechFetcher().list_speeches(  # doctest: +SKIP
...     year_range=(2024, 2024), speaker="Powell"
... )
"""

from market.fraser.client import FraserClient
from market.fraser.errors import (
    FraserAuthError,
    FraserError,
    FraserParseError,
    FraserRateLimitError,
)
from market.fraser.fetchers.beige_book import BeigeBookFetcher
from market.fraser.fetchers.fomc import (
    FOMCMinutesFetcher,
    FOMCPressConferencesFetcher,
    FOMCStatementsFetcher,
)
from market.fraser.fetchers.monetary_policy import MonetaryPolicyReportFetcher
from market.fraser.fetchers.speeches import FRBSpeechFetcher
from market.fraser.models import (
    BeigeBookReport,
    FOMCMeeting,
    FRBSpeech,
    MonetaryPolicyReport,
)
from market.fraser.types import FraserConfig

__version__ = "0.1.0"

__all__ = [
    "BeigeBookFetcher",
    "BeigeBookReport",
    "FOMCMeeting",
    "FOMCMinutesFetcher",
    "FOMCPressConferencesFetcher",
    "FOMCStatementsFetcher",
    "FRBSpeech",
    "FRBSpeechFetcher",
    "FraserAuthError",
    "FraserClient",
    "FraserConfig",
    "FraserError",
    "FraserParseError",
    "FraserRateLimitError",
    "MonetaryPolicyReport",
    "MonetaryPolicyReportFetcher",
]

"""Fetcher subpackage for ``market.fraser``.

Re-exports the abstract :class:`BaseFraserFetcher` base class plus all
concrete fetcher classes:

- :class:`FOMCMinutesFetcher` — FOMC minutes (PR3).
- :class:`FOMCStatementsFetcher` — FOMC policy statements (PR4 前半).
- :class:`FOMCPressConferencesFetcher` — FOMC press conference
  transcripts (PR4 前半).
- :class:`BeigeBookFetcher` — Beige Book reports with parallel
  download support (PR4 後半).
- :class:`FRBSpeechFetcher` — Federal Reserve Board speeches with
  optional speaker filtering (PR4 後半).
- :class:`MonetaryPolicyReportFetcher` — Monetary Policy Reports to the
  Congress, PDF-first (PR4 後半).

See Also
--------
market.fraser.fetchers.base : Abstract base class.
market.fraser.fetchers.fomc : FOMC-specific fetchers.
market.fraser.fetchers.beige_book : Beige Book fetcher.
market.fraser.fetchers.speeches : FRB speech fetcher.
market.fraser.fetchers.monetary_policy : Monetary Policy Report fetcher.
"""

from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.fetchers.beige_book import BeigeBookFetcher
from market.fraser.fetchers.fomc import (
    FOMCMinutesFetcher,
    FOMCPressConferencesFetcher,
    FOMCStatementsFetcher,
)
from market.fraser.fetchers.monetary_policy import MonetaryPolicyReportFetcher
from market.fraser.fetchers.speeches import FRBSpeechFetcher

__all__ = [
    "BaseFraserFetcher",
    "BeigeBookFetcher",
    "FOMCMinutesFetcher",
    "FOMCPressConferencesFetcher",
    "FOMCStatementsFetcher",
    "FRBSpeechFetcher",
    "MonetaryPolicyReportFetcher",
]

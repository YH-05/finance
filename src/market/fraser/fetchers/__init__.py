"""Fetcher subpackage for ``market.fraser``.

Re-exports the abstract :class:`BaseFraserFetcher` base class and the
three concrete FOMC fetchers (Minutes from PR3, Statements + Press
Conferences from PR4 前半). Subsequent PRs extend this module with the
remaining Beige Book / Speeches / Monetary Policy Report fetchers.

See Also
--------
market.fraser.fetchers.base : Abstract base class.
market.fraser.fetchers.fomc : FOMC-specific fetchers.
"""

from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.fetchers.fomc import (
    FOMCMinutesFetcher,
    FOMCPressConferencesFetcher,
    FOMCStatementsFetcher,
)

__all__ = [
    "BaseFraserFetcher",
    "FOMCMinutesFetcher",
    "FOMCPressConferencesFetcher",
    "FOMCStatementsFetcher",
]

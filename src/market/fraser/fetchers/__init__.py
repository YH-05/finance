"""Fetcher subpackage for ``market.fraser``.

Re-exports the abstract :class:`BaseFraserFetcher` base class and the
concrete :class:`FOMCMinutesFetcher` introduced by PR3. Subsequent PRs
extend this module with additional FOMC and Beige Book fetchers.

See Also
--------
market.fraser.fetchers.base : Abstract base class.
market.fraser.fetchers.fomc : FOMC-specific fetchers.
"""

from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.fetchers.fomc import FOMCMinutesFetcher

__all__ = ["BaseFraserFetcher", "FOMCMinutesFetcher"]

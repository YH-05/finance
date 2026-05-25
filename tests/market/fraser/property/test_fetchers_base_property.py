"""Property tests for ``BaseFraserFetcher._filter_by_year_range``.

The filter is a small but central helper used by every concrete fetcher
to narrow ``list_items`` results to a calendar window. The invariants
below guarantee that:

1. Every returned item's ``date.year`` falls within ``[start, end]``.
2. Reversed windows (``start > end``) return an empty list.
3. The function always returns ``list`` — never ``None`` or raises.
"""

from __future__ import annotations

import datetime as _dt

from hypothesis import given, settings
from hypothesis import strategies as st

from market.fraser.fetchers.base import BaseFraserFetcher
from market.fraser.models import FraserItem
from market.fraser.types import DocType


class _DummyFetcher(BaseFraserFetcher):
    """Minimal concrete fetcher exposing the protected filter for tests."""

    @property
    def doc_type(self) -> DocType:
        return DocType.FOMC_MINUTES

    def __init__(self) -> None:
        # Bypass the real client / downloader wiring: property tests only
        # call ``_filter_by_year_range`` which has no dependencies on
        # those collaborators.
        self._client = None
        self._downloader = None


_FETCHER = _DummyFetcher()


def _make_item(year: int) -> FraserItem:
    """Construct a minimal FraserItem with the given year."""
    return FraserItem(
        item_id=year * 1000,
        title=f"item-{year}",
        date=_dt.date(year, 1, 1),
    )


class TestFilterByYearRangeProperty:
    """Property tests for the year-range filter."""

    @given(
        years=st.lists(
            st.integers(min_value=1900, max_value=2100),
            min_size=0,
            max_size=50,
        ),
        start=st.integers(min_value=1900, max_value=2100),
        end=st.integers(min_value=1900, max_value=2100),
    )
    @settings(max_examples=100)
    def test_プロパティ_戻り値のyearは全てwindow内(
        self,
        years: list[int],
        start: int,
        end: int,
    ) -> None:
        items = [_make_item(y) for y in years]

        filtered = _FETCHER._filter_by_year_range(items, (start, end))

        for item in filtered:
            assert start <= item.date.year <= end

    @given(
        years=st.lists(
            st.integers(min_value=1900, max_value=2100),
            min_size=1,
            max_size=20,
        ),
        start=st.integers(min_value=2050, max_value=2100),
        end=st.integers(min_value=1900, max_value=2049),
    )
    @settings(max_examples=50)
    def test_プロパティ_反転windowで空リスト(
        self,
        years: list[int],
        start: int,
        end: int,
    ) -> None:
        # By construction start > end → no year can satisfy
        # ``start <= y <= end`` so the result must be empty.
        items = [_make_item(y) for y in years]

        filtered = _FETCHER._filter_by_year_range(items, (start, end))

        assert filtered == []

    @given(
        years=st.lists(
            st.integers(min_value=1900, max_value=2100),
            min_size=0,
            max_size=20,
        ),
        start=st.integers(min_value=1900, max_value=2100),
        end=st.integers(min_value=1900, max_value=2100),
    )
    @settings(max_examples=50)
    def test_プロパティ_常にlistを返す(
        self,
        years: list[int],
        start: int,
        end: int,
    ) -> None:
        items = [_make_item(y) for y in years]

        filtered = _FETCHER._filter_by_year_range(items, (start, end))

        assert isinstance(filtered, list)
        # All elements (if any) are FraserItem instances.
        assert all(isinstance(i, FraserItem) for i in filtered)

"""Property-based tests for ``market.fraser.parser``.

Verifies the central invariant that the parser only ever raises
:class:`FraserParseError` for invalid inputs — Pydantic
``ValidationError`` instances must never leak out to callers. This
matches the design contract that the rest of the package relies on
when handling failures.

Coverage
--------
- ``parse_items`` on arbitrary single-item payloads either returns a
  ``list[FraserItem]`` or raises :class:`FraserParseError`. No other
  exception type is permitted.
- ``parse_item`` on arbitrary dict inputs has the same invariant.
- :class:`FraserParseError` instances always carry non-empty
  ``raw_data`` and ``field`` attributes (regression guard for the
  error contract documented in :mod:`market.fraser.errors`).

See Also
--------
market.fraser.parser : Module under test.
market.fraser.errors : :class:`FraserParseError` definition.
"""

from __future__ import annotations

from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from market.fraser.errors import FraserParseError
from market.fraser.models import FraserItem
from market.fraser.parser import parse_item, parse_items

# =============================================================================
# Strategies
# =============================================================================

# Reusable strategy for "any JSON-serialisable scalar".
_json_scalar: st.SearchStrategy[Any] = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(10**9), max_value=10**9),
    st.floats(allow_nan=False, allow_infinity=False, width=32),
    st.text(max_size=32),
)

# Arbitrary item-like payload: dict whose keys are short strings and
# values are JSON scalars. Most of these payloads will fail Pydantic
# validation (no ``itemId`` / ``title`` / ``date``) and must surface as
# ``FraserParseError`` — never ``ValidationError``.
_arbitrary_item_payload: st.SearchStrategy[dict[str, Any]] = st.dictionaries(
    keys=st.text(min_size=1, max_size=12),
    values=_json_scalar,
    min_size=0,
    max_size=8,
)


# =============================================================================
# Property tests for parse_items
# =============================================================================


class TestParseItemsProperty:
    """``parse_items`` must never raise ``ValidationError`` directly."""

    @given(payload=_arbitrary_item_payload)
    @settings(max_examples=100)
    def test_プロパティ_parse_items単一辞書はFraserItemかFraserParseError(
        self,
        payload: dict[str, Any],
    ) -> None:
        """``parse_items({'items': [arbitrary]})`` either parses or raises FraserParseError."""
        wrapped = {"items": [payload]}
        try:
            result = parse_items(wrapped)
        except FraserParseError as exc:
            # ``FraserParseError`` carries diagnostic metadata.
            assert isinstance(exc.raw_data, str)
            assert exc.raw_data != ""
            assert isinstance(exc.field, str)
            assert exc.field != ""
        except ValidationError:
            # Pydantic errors must NOT leak out of the parser.
            msg = (
                "ValidationError leaked from parse_items — should be wrapped "
                "as FraserParseError"
            )
            raise AssertionError(msg) from None
        else:
            assert isinstance(result, list)
            assert all(isinstance(item, FraserItem) for item in result)

    @given(
        payloads=st.lists(_arbitrary_item_payload, min_size=0, max_size=5),
    )
    @settings(max_examples=50)
    def test_プロパティ_parse_items複数辞書はlistまたはFraserParseError(
        self,
        payloads: list[dict[str, Any]],
    ) -> None:
        wrapped = {"items": payloads}
        try:
            result = parse_items(wrapped)
        except FraserParseError as exc:
            assert isinstance(exc.raw_data, str)
            assert exc.raw_data != ""
            assert isinstance(exc.field, str)
        except ValidationError:
            msg = "ValidationError leaked from parse_items"
            raise AssertionError(msg) from None
        else:
            assert isinstance(result, list)
            assert len(result) == len(payloads)
            assert all(isinstance(item, FraserItem) for item in result)

    @given(payload=_arbitrary_item_payload)
    @settings(max_examples=100)
    def test_プロパティ_parse_item任意辞書はFraserItemかFraserParseError(
        self,
        payload: dict[str, Any],
    ) -> None:
        """``parse_item`` mirrors the same contract on a single payload."""
        try:
            result = parse_item(payload)
        except FraserParseError as exc:
            assert isinstance(exc.raw_data, str)
            assert exc.raw_data != ""
            assert isinstance(exc.field, str)
            assert exc.field != ""
        except ValidationError:
            msg = "ValidationError leaked from parse_item"
            raise AssertionError(msg) from None
        else:
            assert isinstance(result, FraserItem)


# =============================================================================
# Property tests for the well-formed-item path
# =============================================================================


class TestParseItemsWellFormedProperty:
    """Well-formed items always round-trip cleanly."""

    @given(
        item_id=st.integers(min_value=1, max_value=10**9),
        title=st.text(min_size=1, max_size=120),
        year=st.integers(min_value=1900, max_value=2099),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
    )
    @settings(max_examples=100)
    def test_プロパティ_最小限フィールドで常にFraserItem返却(
        self,
        item_id: int,
        title: str,
        year: int,
        month: int,
        day: int,
    ) -> None:
        """A payload with just ``itemId``, ``title``, ``date`` always parses."""
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        payload = {"itemId": item_id, "title": title, "date": date_str}
        result = parse_items({"items": [payload]})
        assert len(result) == 1
        item = result[0]
        assert item.item_id == item_id
        assert item.title == title
        assert item.date.year == year

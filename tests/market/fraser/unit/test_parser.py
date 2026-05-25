"""Tests for ``market.fraser.parser`` module.

Verifies that the parser wrappers transform raw JSON into Pydantic models
and raise :class:`FraserParseError` (with ``raw_data`` / ``field`` /
``cause`` populated, and the original ``ValidationError`` chained via
``raise ... from``) when required fields are missing.

See Also
--------
market.fraser.parser : Module under test.
market.fraser.errors : ``FraserParseError`` definition.
market.fraser.models : Pydantic models used as parse targets.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from market.fraser.errors import FraserParseError
from market.fraser.parser import (
    parse_authors,
    parse_item,
    parse_items,
    parse_subjects,
    parse_themes,
    parse_timeline,
    parse_title,
    parse_toc,
)

# ---------------------------------------------------------------------------
# parse_items / parse_item
# ---------------------------------------------------------------------------


class TestParseItems:
    """Verify :func:`parse_items` happy paths and failure modes."""

    def test_正常系_FOMC形式のレスポンスをパース成功(
        self, sample_fomc_items_response: dict[str, Any]
    ) -> None:
        items = parse_items(sample_fomc_items_response)
        assert len(items) == 5
        assert items[0].item_id == 1001
        assert items[0].title.startswith("Minutes")
        assert items[2].date.year == 2024

    def test_正常系_リスト形式の入力もパース成功(self) -> None:
        payload = [
            {"itemId": 10, "title": "X", "date": "2024-01-01"},
            {"itemId": 11, "title": "Y", "date": "2024-02-01"},
        ]
        items = parse_items(payload)
        assert [i.item_id for i in items] == [10, 11]

    def test_異常系_itemsキー欠損でFraserParseError(self) -> None:
        with pytest.raises(FraserParseError) as exc_info:
            parse_items({"meta": {}})
        err = exc_info.value
        assert err.field == "items"
        # raw_data must contain the original JSON for debuggability.
        assert "meta" in err.raw_data

    def test_異常系_itemsが配列でないとFraserParseError(self) -> None:
        with pytest.raises(FraserParseError) as exc_info:
            parse_items({"items": {"not": "a list"}})
        assert exc_info.value.field == "items"

    def test_異常系_必須フィールド欠損で詳細エラー(self) -> None:
        # Drop the required ``itemId`` from the first entry.
        bad_payload = {
            "items": [
                {"title": "no item_id", "date": "2024-01-01"},
            ]
        }
        with pytest.raises(FraserParseError) as exc_info:
            parse_items(bad_payload)

        err = exc_info.value
        # Pydantic reports the missing field by its serialised alias
        # (``itemId``) when ``populate_by_name=True`` is in effect.
        assert err.field in {"item_id", "itemId"}
        # raw_data should retain the original JSON.
        assert "no item_id" in err.raw_data
        # The cause should be a Pydantic ValidationError.
        assert isinstance(err.cause, ValidationError)
        # raise ... from ... chaining.
        assert err.__cause__ is err.cause


class TestParseItem:
    """Verify :func:`parse_item` for the single-item path."""

    def test_正常系_camelCaseで構築成功(self) -> None:
        data = {"itemId": 42, "title": "OK", "date": "2024-05-25"}
        item = parse_item(data)
        assert item.item_id == 42
        assert item.title == "OK"
        assert item.date.year == 2024

    def test_異常系_dateフィールド欠損で例外(self) -> None:
        data = {"itemId": 42, "title": "OK"}
        with pytest.raises(FraserParseError) as exc_info:
            parse_item(data)
        assert "date" in exc_info.value.field


# ---------------------------------------------------------------------------
# parse_title
# ---------------------------------------------------------------------------


class TestParseTitle:
    def test_正常系_最小ペイロードで構築(self) -> None:
        title = parse_title({"titleId": 677, "name": "FOMC"})
        assert title.title_id == 677
        assert title.name == "FOMC"

    def test_異常系_titleIdなしで例外(self) -> None:
        with pytest.raises(FraserParseError) as exc_info:
            parse_title({"name": "no id"})
        assert exc_info.value.field in {"title_id", "titleId"}
        assert isinstance(exc_info.value.cause, ValidationError)


# ---------------------------------------------------------------------------
# parse_toc / parse_authors / parse_subjects / parse_themes / parse_timeline
# ---------------------------------------------------------------------------


class TestParseAuxiliaryCollections:
    """Verify the small auxiliary parsers accept both shapes."""

    def test_正常系_toc配列を直接受け取れる(self) -> None:
        entries = parse_toc([{"label": "Intro", "page": 1}])
        assert len(entries) == 1
        assert entries[0].label == "Intro"

    def test_正常系_toc_dict_with_key(self) -> None:
        entries = parse_toc({"toc": [{"label": "Body", "page": 2}]})
        assert entries[0].page == 2

    def test_正常系_authorsの基本パース(self) -> None:
        authors = parse_authors([{"name": "A", "authorId": 1}])
        assert authors[0].author_id == 1

    def test_正常系_subjectsの基本パース(self) -> None:
        subjects = parse_subjects([{"name": "macro", "subjectId": 10}])
        assert subjects[0].subject_id == 10

    def test_正常系_themesの基本パース(self) -> None:
        themes = parse_themes([{"name": "policy", "themeId": 100}])
        assert themes[0].theme_id == 100

    def test_正常系_timelineの基本パース(self) -> None:
        events = parse_timeline(
            [{"label": "Founded", "eventDate": "1913", "description": "Fed"}]
        )
        assert events[0].label == "Founded"
        assert events[0].event_date is not None
        assert events[0].event_date.year == 1913

    def test_異常系_authorsが配列でないと例外(self) -> None:
        with pytest.raises(FraserParseError) as exc_info:
            parse_authors({"authors": {"not": "a list"}})
        assert exc_info.value.field == "authors"

"""Unit tests for ``market.fraser.models`` module.

Covers:

- Sample FOMC items payload parses end-to-end (5 items, mixed date
  formats).
- camelCase aliases (``itemId``, ``titleId``, ``pdfUrl``, ``textUrl``)
  map to snake_case fields when ``populate_by_name=True``.
- ``FraserLocation.pdf_url`` accepts ``None`` and ``list[str]``.
- ``FOMCMeeting`` / ``BeigeBookReport`` / ``FRBSpeech`` /
  ``MonetaryPolicyReport`` derive from ``FraserItem``.
- ``field_validator('date')`` handles ``YYYY-MM-DD`` / ``YYYY-MM`` /
  ``YYYY`` formats.
- ``FraserTitle`` requires ``title_id`` and ``name``.
- ``extra='ignore'`` keeps unknown fields out of the model.
"""

from datetime import date

import pytest
from pydantic import ValidationError

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

# =============================================================================
# FraserLocation tests
# =============================================================================


class TestFraserLocation:
    """Tests for ``FraserLocation``."""

    def test_正常系_pdf_url_text_url_None(self) -> None:
        loc = FraserLocation()
        assert loc.pdf_url is None
        assert loc.text_url is None

    def test_正常系_camelCaseエイリアスでpdfUrlを受け付ける(self) -> None:
        loc = FraserLocation.model_validate(
            {"pdfUrl": ["https://x/a.pdf"], "textUrl": ["https://x/a.txt"]}
        )
        assert loc.pdf_url == ["https://x/a.pdf"]
        assert loc.text_url == ["https://x/a.txt"]

    def test_正常系_snake_caseでも作成可能(self) -> None:
        loc = FraserLocation(pdf_url=["https://x/b.pdf"])
        assert loc.pdf_url == ["https://x/b.pdf"]
        assert loc.text_url is None

    def test_エッジケース_extra_ignoreで未知フィールドを無視(self) -> None:
        loc = FraserLocation.model_validate(
            {"pdfUrl": ["https://x"], "unknownField": "ignored"}
        )
        assert loc.pdf_url == ["https://x"]
        assert not hasattr(loc, "unknownField")


# =============================================================================
# FraserItem tests
# =============================================================================


class TestFraserItem:
    """Tests for ``FraserItem`` base model."""

    def test_正常系_最小構成で作成できる(self) -> None:
        item = FraserItem.model_validate(
            {"itemId": 1, "title": "Sample", "date": "2024-01-31"}
        )
        assert item.item_id == 1
        assert item.title == "Sample"
        assert item.date == date(2024, 1, 31)

    def test_正常系_camelCaseエイリアスでitemIdが解釈される(self) -> None:
        item = FraserItem.model_validate(
            {"itemId": 42, "titleId": 677, "title": "x", "date": "2024-01-01"}
        )
        assert item.item_id == 42
        assert item.title_id == 677

    def test_異常系_item_id欠落でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            FraserItem.model_validate({"title": "x", "date": "2024-01-01"})

    def test_異常系_title欠落でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            FraserItem.model_validate({"itemId": 1, "date": "2024-01-01"})

    def test_異常系_date欠落でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            FraserItem.model_validate({"itemId": 1, "title": "x"})


class TestFraserItemDateFormats:
    """Tests for ``field_validator('date', mode='before')`` formats."""

    def test_正常系_YYYYMMDD形式(self) -> None:
        item = FraserItem.model_validate(
            {"itemId": 1, "title": "x", "date": "2024-03-20"}
        )
        assert item.date == date(2024, 3, 20)

    def test_正常系_YYYYMM形式(self) -> None:
        item = FraserItem.model_validate({"itemId": 1, "title": "x", "date": "2024-04"})
        # YYYY-MM should normalise to the first day of the month.
        assert item.date == date(2024, 4, 1)

    def test_正常系_YYYY形式(self) -> None:
        item = FraserItem.model_validate({"itemId": 1, "title": "x", "date": "1995"})
        assert item.date == date(1995, 1, 1)

    def test_正常系_dateオブジェクトを直接受け付ける(self) -> None:
        item = FraserItem.model_validate(
            {"itemId": 1, "title": "x", "date": date(2024, 5, 10)}
        )
        assert item.date == date(2024, 5, 10)


class TestFraserItemOptionalNested:
    """Tests for optional nested fields on ``FraserItem``."""

    def test_正常系_locationを保持する(self) -> None:
        item = FraserItem.model_validate(
            {
                "itemId": 1,
                "title": "x",
                "date": "2024-01-01",
                "location": {"pdfUrl": ["https://x/1.pdf"]},
            }
        )
        assert item.location is not None
        assert item.location.pdf_url == ["https://x/1.pdf"]

    def test_正常系_authors_subjects_themesを保持する(self) -> None:
        item = FraserItem.model_validate(
            {
                "itemId": 1,
                "title": "x",
                "date": "2024-01-01",
                "authors": [{"name": "Alice", "authorId": 10}],
                "subjects": [{"name": "Monetary Policy", "subjectId": 20}],
                "themes": [{"name": "Banking", "themeId": 30}],
            }
        )
        assert item.authors is not None and item.authors[0].name == "Alice"
        assert item.authors[0].author_id == 10
        assert item.subjects is not None and item.subjects[0].subject_id == 20
        assert item.themes is not None and item.themes[0].theme_id == 30


# =============================================================================
# Sample fixture parsing
# =============================================================================


class TestSampleFomcItemsResponse:
    """Tests using the ``sample_fomc_items_response`` fixture."""

    def test_正常系_5件全てパース成功(
        self, sample_fomc_items_response: dict[str, object]
    ) -> None:
        raw_items = sample_fomc_items_response["items"]
        assert isinstance(raw_items, list)
        parsed = [FraserItem.model_validate(it) for it in raw_items]
        assert len(parsed) == 5
        # All items have item_id, title, and a date set.
        for item in parsed:
            assert item.item_id is not None
            assert item.title
            assert item.date is not None

    def test_正常系_部分日付フォーマットが混在しても全件パース(
        self, sample_fomc_items_response: dict[str, object]
    ) -> None:
        raw_items = sample_fomc_items_response["items"]
        assert isinstance(raw_items, list)
        parsed = [FraserItem.model_validate(it) for it in raw_items]
        dates = [item.date for item in parsed]
        # YYYY-MM-DD
        assert date(2024, 1, 31) in dates
        # YYYY-MM normalised to first of month
        assert date(2024, 4, 1) in dates
        # YYYY normalised to first of year
        assert date(1995, 1, 1) in dates


# =============================================================================
# Domain model tests
# =============================================================================


class TestFOMCMeeting:
    """Tests for ``FOMCMeeting``."""

    def test_正常系_FraserItem派生(self) -> None:
        assert issubclass(FOMCMeeting, FraserItem)

    def test_正常系_meeting_date_meeting_typeを保持(self) -> None:
        meeting = FOMCMeeting.model_validate(
            {
                "itemId": 1,
                "title": "FOMC Minutes",
                "date": "2024-01-31",
                "meetingDate": "2024-01-30",
                "meetingType": "regular",
            }
        )
        assert meeting.meeting_date == date(2024, 1, 30)
        assert meeting.meeting_type == "regular"

    def test_正常系_meeting_dateがNoneでも作成可能(self) -> None:
        meeting = FOMCMeeting.model_validate(
            {"itemId": 1, "title": "x", "date": "2024-01-01"}
        )
        assert meeting.meeting_date is None


class TestBeigeBookReport:
    """Tests for ``BeigeBookReport``."""

    def test_正常系_FraserItem派生(self) -> None:
        assert issubclass(BeigeBookReport, FraserItem)

    def test_正常系_district保持(self) -> None:
        report = BeigeBookReport.model_validate(
            {
                "itemId": 2,
                "title": "Beige Book",
                "date": "2024-01-17",
                "district": "national",
            }
        )
        assert report.district == "national"


class TestFRBSpeech:
    """Tests for ``FRBSpeech``."""

    def test_正常系_FraserItem派生(self) -> None:
        assert issubclass(FRBSpeech, FraserItem)

    def test_正常系_speaker_venue保持(self) -> None:
        speech = FRBSpeech.model_validate(
            {
                "itemId": 3,
                "title": "Speech",
                "date": "2024-02-01",
                "speaker": "Jerome Powell",
                "venue": "Washington, DC",
            }
        )
        assert speech.speaker == "Jerome Powell"
        assert speech.venue == "Washington, DC"


class TestMonetaryPolicyReport:
    """Tests for ``MonetaryPolicyReport``."""

    def test_正常系_FraserItem派生(self) -> None:
        assert issubclass(MonetaryPolicyReport, FraserItem)

    def test_正常系_report_period保持(self) -> None:
        report = MonetaryPolicyReport.model_validate(
            {
                "itemId": 4,
                "title": "MPR",
                "date": "2024-02-21",
                "reportPeriod": "February 2024",
            }
        )
        assert report.report_period == "February 2024"


# =============================================================================
# Auxiliary model tests
# =============================================================================


class TestFraserTitle:
    """Tests for ``FraserTitle``."""

    def test_正常系_必須フィールドで作成(self) -> None:
        title = FraserTitle.model_validate({"titleId": 677, "name": "FOMC"})
        assert title.title_id == 677
        assert title.name == "FOMC"
        assert title.item_count is None

    def test_異常系_title_id欠落でValidationError(self) -> None:
        with pytest.raises(ValidationError):
            FraserTitle.model_validate({"name": "FOMC"})


class TestFraserTocEntry:
    """Tests for ``FraserTocEntry``."""

    def test_正常系_全フィールドオプショナル(self) -> None:
        entry = FraserTocEntry()
        assert entry.label is None
        assert entry.page is None
        assert entry.anchor is None


class TestFraserAuthor:
    """Tests for ``FraserAuthor``."""

    def test_正常系_authorIdエイリアス(self) -> None:
        author = FraserAuthor.model_validate({"name": "Jane Doe", "authorId": 7})
        assert author.author_id == 7


class TestFraserSubject:
    """Tests for ``FraserSubject``."""

    def test_正常系_subjectIdエイリアス(self) -> None:
        subject = FraserSubject.model_validate({"name": "Monetary", "subjectId": 11})
        assert subject.subject_id == 11


class TestFraserTheme:
    """Tests for ``FraserTheme``."""

    def test_正常系_themeIdエイリアス(self) -> None:
        theme = FraserTheme.model_validate({"name": "Banking", "themeId": 22})
        assert theme.theme_id == 22


class TestFraserTimelineEvent:
    """Tests for ``FraserTimelineEvent``."""

    def test_正常系_event_dateを部分形式で受け付ける(self) -> None:
        event = FraserTimelineEvent.model_validate(
            {"label": "Founded", "eventDate": "1913"}
        )
        assert event.event_date == date(1913, 1, 1)

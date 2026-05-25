"""Pydantic V2 response models for the FRASER REST API module.

This module provides Pydantic models for validating and serialising
FRASER REST API responses. All models use
``ConfigDict(extra='ignore', populate_by_name=True)`` so that:

- Forward compatibility is preserved when FRASER adds new fields.
- Both API camelCase names (``itemId``, ``pdfUrl``) and Python
  snake_case names (``item_id``, ``pdf_url``) can be used to
  instantiate models.

Required fields are intentionally minimal (``item_id``, ``title``,
``date`` on ``FraserItem``); every other field is optional with a
default of ``None`` so that the parser can ingest partial responses
without crashing.

Models
------
- FraserTitle: FRASER title (top-level collection) descriptor.
- FraserItem: Generic FRASER item (base for domain models).
- FraserLocation: Asset location descriptor (pdf_url / text_url).
- FraserTocEntry: Table-of-contents entry.
- FraserAuthor: Author / contributor descriptor.
- FraserSubject: Subject tag.
- FraserTheme: Theme tag.
- FraserTimelineEvent: Timeline event entry.
- FOMCMeeting: FOMC meeting document (minutes/statement/press conf).
- BeigeBookReport: Beige Book report.
- FRBSpeech: Federal Reserve Board speech.
- MonetaryPolicyReport: Monetary Policy Report to the Congress.

See Also
--------
market.polymarket.models : Reference implementation for
    ``ConfigDict(extra='ignore', populate_by_name=True)`` +
    ``Field(alias='camelCase')`` patterns.
"""

from datetime import date as date_cls
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils_core.logging import get_logger

logger = get_logger(__name__)

# Common Pydantic model config for FRASER models.
# - ``extra='ignore'`` keeps the parser tolerant of new FRASER fields.
# - ``populate_by_name=True`` allows both API camelCase aliases and
#   snake_case field names to be used to instantiate models.
_FRASER_MODEL_CONFIG: ConfigDict = ConfigDict(
    extra="ignore",
    populate_by_name=True,
)


# Accepted ``date`` input formats. Ordered from most specific to least
# specific so that ambiguous strings (e.g., ``"2024"``) fall through to
# the year-only parser.
_DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",
    "%Y-%m",
    "%Y",
)


def _coerce_date(v: Any) -> Any:
    """Coerce a date input into a ``datetime.date`` instance.

    Accepts ``date`` / ``datetime`` objects, integer or string years,
    and partial date strings (``"YYYY"``, ``"YYYY-MM"``, ``"YYYY-MM-DD"``).
    Returns ``None`` unchanged.

    Parameters
    ----------
    v : Any
        Raw input from the Pydantic validator. The function intentionally
        accepts ``Any`` because FRASER returns date fields in multiple
        formats.

    Returns
    -------
    Any
        A ``datetime.date`` when the input can be parsed; the original
        input otherwise (Pydantic will raise its standard validation
        error for unparseable values).

    Notes
    -----
    Partial date strings (``"YYYY"``, ``"YYYY-MM"``) are normalised to
    the first day of the relevant period (``Jan 1`` / day ``1``).
    """
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date_cls):
        return v
    if isinstance(v, int):
        # Year-only integer (e.g., 2024 -> 2024-01-01).
        try:
            return date_cls(v, 1, 1)
        except (ValueError, OverflowError):
            return v
    if not isinstance(v, str):
        return v
    text = v.strip()
    if not text:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return v


# =============================================================================
# Auxiliary models
# =============================================================================


class FraserLocation(BaseModel):
    """Asset location descriptor for a FRASER item.

    The FRASER API returns lists of URLs (one per page or rendition).
    Both PDF and text URLs are optional; an item may expose neither,
    one, or both.

    Parameters
    ----------
    pdf_url : list[str] | None
        URLs to PDF renditions, when available. Mapped from
        ``pdfUrl`` in the API JSON.
    text_url : list[str] | None
        URLs to plain-text renditions, when available. Mapped from
        ``textUrl`` in the API JSON.

    Examples
    --------
    >>> loc = FraserLocation.model_validate({"pdfUrl": ["https://x/a.pdf"]})
    >>> loc.pdf_url
    ['https://x/a.pdf']
    """

    model_config = _FRASER_MODEL_CONFIG

    pdf_url: list[str] | None = Field(default=None, alias="pdfUrl")
    text_url: list[str] | None = Field(default=None, alias="textUrl")


class FraserTocEntry(BaseModel):
    """Table-of-contents entry for a FRASER item.

    Parameters
    ----------
    label : str | None
        Display label.
    page : int | None
        Page number within the item, when applicable.
    anchor : str | None
        Internal anchor identifier, when applicable.

    Examples
    --------
    >>> entry = FraserTocEntry(label="Introduction", page=1)
    >>> entry.label
    'Introduction'
    """

    model_config = _FRASER_MODEL_CONFIG

    label: str | None = Field(default=None)
    page: int | None = Field(default=None)
    anchor: str | None = Field(default=None)


class FraserAuthor(BaseModel):
    """Author / contributor descriptor for a FRASER item.

    Parameters
    ----------
    name : str | None
        Author display name.
    role : str | None
        Author role (e.g., ``"author"``, ``"editor"``).
    author_id : int | None
        FRASER internal author identifier. Mapped from ``authorId``.

    Examples
    --------
    >>> author = FraserAuthor.model_validate({"name": "Jane", "authorId": 1})
    >>> author.author_id
    1
    """

    model_config = _FRASER_MODEL_CONFIG

    name: str | None = Field(default=None)
    role: str | None = Field(default=None)
    author_id: int | None = Field(default=None, alias="authorId")


class FraserSubject(BaseModel):
    """Subject tag attached to a FRASER item.

    Parameters
    ----------
    name : str | None
        Subject display name.
    subject_id : int | None
        FRASER internal subject identifier. Mapped from ``subjectId``.
    """

    model_config = _FRASER_MODEL_CONFIG

    name: str | None = Field(default=None)
    subject_id: int | None = Field(default=None, alias="subjectId")


class FraserTheme(BaseModel):
    """Theme tag attached to a FRASER item.

    Parameters
    ----------
    name : str | None
        Theme display name.
    theme_id : int | None
        FRASER internal theme identifier. Mapped from ``themeId``.
    """

    model_config = _FRASER_MODEL_CONFIG

    name: str | None = Field(default=None)
    theme_id: int | None = Field(default=None, alias="themeId")


class FraserTimelineEvent(BaseModel):
    """Timeline event entry for a FRASER title / item.

    Parameters
    ----------
    label : str | None
        Event display label.
    event_date : date_cls | None
        Event date (parsed from ``YYYY-MM-DD`` / ``YYYY-MM`` / ``YYYY``).
        Mapped from ``eventDate`` in the API JSON.
    description : str | None
        Free-text description.
    """

    model_config = _FRASER_MODEL_CONFIG

    label: str | None = Field(default=None)
    event_date: date_cls | None = Field(default=None, alias="eventDate")
    description: str | None = Field(default=None)

    @field_validator("event_date", mode="before")
    @classmethod
    def _parse_event_date(cls, v: Any) -> Any:
        """Coerce ``event_date`` via ``_coerce_date``."""
        return _coerce_date(v)


# =============================================================================
# Title model
# =============================================================================


class FraserTitle(BaseModel):
    """FRASER title (top-level collection) descriptor.

    A FRASER title typically aggregates many items (issues, reports,
    transcripts). Required fields are minimal so that the parser can
    handle partial responses; expand cautiously in future PRs.

    Parameters
    ----------
    title_id : int
        FRASER internal title identifier (required). Mapped from
        ``titleId``.
    name : str
        Title display name (required).
    description : str | None
        Free-text description.
    publisher : str | None
        Publishing organisation.
    item_count : int | None
        Number of items belonging to this title. Mapped from
        ``itemCount``.

    Examples
    --------
    >>> title = FraserTitle.model_validate({"titleId": 677, "name": "FOMC"})
    >>> title.title_id
    677
    """

    model_config = _FRASER_MODEL_CONFIG

    title_id: int = Field(..., alias="titleId")
    name: str = Field(...)
    description: str | None = Field(default=None)
    publisher: str | None = Field(default=None)
    item_count: int | None = Field(default=None, alias="itemCount")


# =============================================================================
# Base item model
# =============================================================================


class FraserItem(BaseModel):
    """Generic FRASER item (base for domain-specific models).

    Required fields are intentionally minimal (``item_id``, ``title``,
    ``date``) so that the parser remains tolerant of partial or
    evolving FRASER schemas.

    Parameters
    ----------
    item_id : int
        FRASER internal item identifier (required). Mapped from
        ``itemId``.
    title : str
        Item display title (required).
    date : date
        Primary publication / event date (required). Parsed from
        ``YYYY-MM-DD`` / ``YYYY-MM`` / ``YYYY`` strings via
        ``_coerce_date``.
    title_id : int | None
        Parent title identifier. Mapped from ``titleId``.
    description : str | None
        Item description / abstract.
    location : FraserLocation | None
        Asset location descriptor (PDF / TXT URLs).
    toc : list[FraserTocEntry] | None
        Table of contents entries.
    authors : list[FraserAuthor] | None
        Author / contributor list.
    subjects : list[FraserSubject] | None
        Subject tags.
    themes : list[FraserTheme] | None
        Theme tags.
    timeline : list[FraserTimelineEvent] | None
        Timeline events associated with this item.

    Examples
    --------
    >>> item = FraserItem.model_validate({
    ...     "itemId": 1, "title": "FOMC Minutes", "date": "2024-01-31"
    ... })
    >>> item.item_id
    1
    >>> item.date.year
    2024
    """

    model_config = _FRASER_MODEL_CONFIG

    item_id: int = Field(..., alias="itemId")
    title: str = Field(...)
    date: date_cls = Field(...)
    title_id: int | None = Field(default=None, alias="titleId")
    description: str | None = Field(default=None)
    location: FraserLocation | None = Field(default=None)
    toc: list[FraserTocEntry] | None = Field(default=None)
    authors: list[FraserAuthor] | None = Field(default=None)
    subjects: list[FraserSubject] | None = Field(default=None)
    themes: list[FraserTheme] | None = Field(default=None)
    timeline: list[FraserTimelineEvent] | None = Field(default=None)

    @field_validator("date", mode="before")
    @classmethod
    def _parse_date(cls, v: Any) -> Any:
        """Coerce ``date`` via ``_coerce_date``.

        Accepts ``YYYY-MM-DD``, ``YYYY-MM``, ``YYYY`` strings as well
        as ``date`` / ``datetime`` / ``int`` inputs.
        """
        return _coerce_date(v)


# =============================================================================
# Domain models
# =============================================================================


class FOMCMeeting(FraserItem):
    """FOMC meeting document (minutes, statement, or press conference).

    Inherits all fields from ``FraserItem``. The ``meeting_date`` and
    ``meeting_type`` fields are optional metadata commonly attached
    to FOMC documents in FRASER.

    Parameters
    ----------
    meeting_date : date_cls | None
        Date of the underlying FOMC meeting. Mapped from
        ``meetingDate``.
    meeting_type : str | None
        Type tag (e.g., ``"regular"``, ``"intermeeting"``). Mapped
        from ``meetingType``.
    """

    meeting_date: date_cls | None = Field(default=None, alias="meetingDate")
    meeting_type: str | None = Field(default=None, alias="meetingType")

    @field_validator("meeting_date", mode="before")
    @classmethod
    def _parse_meeting_date(cls, v: Any) -> Any:
        """Coerce ``meeting_date`` via ``_coerce_date``."""
        return _coerce_date(v)


class BeigeBookReport(FraserItem):
    """Beige Book report.

    Inherits all fields from ``FraserItem``.

    Parameters
    ----------
    district : str | None
        Federal Reserve District covered by the report (or
        ``"national"`` for the summary). Mapped from ``district``.
    """

    district: str | None = Field(default=None)


class FRBSpeech(FraserItem):
    """Federal Reserve Board speech.

    Inherits all fields from ``FraserItem``.

    Parameters
    ----------
    speaker : str | None
        Speaker display name.
    venue : str | None
        Location / venue where the speech was delivered.
    """

    speaker: str | None = Field(default=None)
    venue: str | None = Field(default=None)


class MonetaryPolicyReport(FraserItem):
    """Monetary Policy Report to the Congress.

    Inherits all fields from ``FraserItem``.

    Parameters
    ----------
    report_period : str | None
        Reporting period label (e.g., ``"February 2024"``). Mapped
        from ``reportPeriod``.
    """

    report_period: str | None = Field(default=None, alias="reportPeriod")


__all__ = [
    "BeigeBookReport",
    "FOMCMeeting",
    "FRBSpeech",
    "FraserAuthor",
    "FraserItem",
    "FraserLocation",
    "FraserSubject",
    "FraserTheme",
    "FraserTimelineEvent",
    "FraserTitle",
    "FraserTocEntry",
    "MonetaryPolicyReport",
]

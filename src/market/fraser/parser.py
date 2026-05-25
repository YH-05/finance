"""Response parsing utilities for the FRASER REST API module.

This module contains thin wrappers that convert raw FRASER JSON
payloads into Pydantic V2 models. Each parser catches
:class:`pydantic.ValidationError` and re-raises it as a
:class:`market.fraser.errors.FraserParseError` so that the rest of the
package can rely on a single, FRASER-specific exception hierarchy.

The wrappers intentionally remain stateless and free of HTTP I/O — they
operate solely on already-decoded JSON dictionaries provided by the
session / client layer.

See Also
--------
market.fraser.models : Pydantic V2 response models used as parse targets.
market.fraser.errors : ``FraserParseError`` raised on validation failure.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError

from market.fraser.constants import MAX_RESPONSE_BODY_LOG
from market.fraser.errors import FraserParseError
from market.fraser.models import (
    FraserAuthor,
    FraserItem,
    FraserSubject,
    FraserTheme,
    FraserTimelineEvent,
    FraserTitle,
    FraserTocEntry,
)
from utils_core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_missing_field(exc: ValidationError) -> str:
    """Extract the dotted-path name of the first invalid / missing field.

    Pydantic's ``ValidationError.errors()`` returns a list of dicts where
    each ``loc`` tuple identifies a problem location. This helper joins
    the first ``loc`` into a single string for inclusion in
    :class:`FraserParseError`.

    Parameters
    ----------
    exc : ValidationError
        The Pydantic validation error.

    Returns
    -------
    str
        Dotted-path field name (e.g., ``"items.0.item_id"``) or
        ``"<unknown>"`` when no error details are available.
    """
    errors = exc.errors()
    if not errors:
        return "<unknown>"
    loc = errors[0].get("loc", ())
    if not loc:
        return "<unknown>"
    return ".".join(str(part) for part in loc)


def _truncated_raw(data: Any) -> str:
    """Serialise ``data`` to JSON, truncated to ``MAX_RESPONSE_BODY_LOG``.

    Used as the ``raw_data`` payload of :class:`FraserParseError` so
    that log files and error reports do not balloon with full FRASER
    responses (CWE-209 / log-bloat mitigation).

    Parameters
    ----------
    data : Any
        Object to serialise.

    Returns
    -------
    str
        UTF-8-friendly JSON string truncated to
        :data:`MAX_RESPONSE_BODY_LOG` characters.
    """
    try:
        rendered = json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        rendered = repr(data)
    return rendered[:MAX_RESPONSE_BODY_LOG]


def _parse_with_model[T: BaseModel](
    model: type[T],
    data: Any,
    *,
    object_label: str | None = None,
) -> T:
    """Validate ``data`` against ``model``, wrapping failures.

    Parameters
    ----------
    model : type[BaseModel]
        Pydantic model used as the validation target.
    data : Any
        Raw payload (typically a ``dict`` from ``response.json()``).
    object_label : str | None
        Optional label inserted into the error message; defaults to the
        model class name.

    Returns
    -------
    BaseModel
        Validated model instance.

    Raises
    ------
    FraserParseError
        When ``model.model_validate`` raises ``ValidationError``.
    """
    label = object_label or model.__name__
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        field = _extract_missing_field(exc)
        message = f"Failed to parse {label}: {field}"
        logger.error(
            "FRASER parse failed",
            target=label,
            field=field,
            exc_info=True,
        )
        raise FraserParseError(
            message=message,
            raw_data=_truncated_raw(data),
            field=field,
            cause=exc,
        ) from exc


def _require_list(data: Any, *, container_key: str | None = None) -> list[Any]:
    """Return ``data`` as a list, raising :class:`FraserParseError` otherwise.

    FRASER list endpoints return either a top-level JSON array or an
    object such as ``{"items": [...]}``. Callers pass ``container_key``
    when they expect the wrapped form; the helper unwraps it.

    Parameters
    ----------
    data : Any
        Raw payload.
    container_key : str | None
        Optional key to look up inside ``data`` (e.g., ``"items"``).

    Returns
    -------
    list[Any]
        The list payload.

    Raises
    ------
    FraserParseError
        If ``data`` is not a list (or the expected container does not
        hold a list).
    """
    if container_key is not None:
        if not isinstance(data, dict) or container_key not in data:
            raise FraserParseError(
                message=f"Expected '{container_key}' key in response",
                raw_data=_truncated_raw(data),
                field=container_key,
                cause=None,
            )
        inner = data[container_key]
        if not isinstance(inner, list):
            raise FraserParseError(
                message=f"Expected list under '{container_key}'",
                raw_data=_truncated_raw(data),
                field=container_key,
                cause=None,
            )
        return inner

    if not isinstance(data, list):
        raise FraserParseError(
            message="Expected a JSON array",
            raw_data=_truncated_raw(data),
            field="<root>",
            cause=None,
        )
    return data


# ---------------------------------------------------------------------------
# Title / item parsers
# ---------------------------------------------------------------------------


def parse_title(data: dict[str, Any]) -> FraserTitle:
    """Parse a FRASER title payload into :class:`FraserTitle`.

    Parameters
    ----------
    data : dict[str, Any]
        Decoded JSON object describing a single title.

    Returns
    -------
    FraserTitle
        Validated title model.

    Raises
    ------
    FraserParseError
        When required title fields are missing or malformed.
    """
    return _parse_with_model(FraserTitle, data)


def parse_item(data: dict[str, Any]) -> FraserItem:
    """Parse a FRASER item payload into :class:`FraserItem`.

    Parameters
    ----------
    data : dict[str, Any]
        Decoded JSON object describing a single item.

    Returns
    -------
    FraserItem
        Validated item model.

    Raises
    ------
    FraserParseError
        When required item fields are missing or malformed.
    """
    return _parse_with_model(FraserItem, data)


def parse_items(data: dict[str, Any] | list[Any]) -> list[FraserItem]:
    """Parse a FRASER items collection into a list of :class:`FraserItem`.

    Accepts either:

    - A dict containing an ``"items"`` key whose value is a list, or
    - A bare list of item dicts.

    Parameters
    ----------
    data : dict[str, Any] | list[Any]
        Decoded JSON payload.

    Returns
    -------
    list[FraserItem]
        Parsed items in the same order as the input.

    Raises
    ------
    FraserParseError
        When the payload shape is unexpected or any individual item
        fails validation.
    """
    items_list = (
        _require_list(data, container_key="items")
        if isinstance(data, dict)
        else _require_list(data)
    )
    return [parse_item(entry) for entry in items_list]


def parse_toc(data: dict[str, Any] | list[Any]) -> list[FraserTocEntry]:
    """Parse a table-of-contents payload into :class:`FraserTocEntry` list."""
    entries = (
        _require_list(data, container_key="toc")
        if isinstance(data, dict) and "toc" in data
        else _require_list(data)
    )
    return [_parse_with_model(FraserTocEntry, entry) for entry in entries]


def parse_authors(data: dict[str, Any] | list[Any]) -> list[FraserAuthor]:
    """Parse an authors payload into :class:`FraserAuthor` list."""
    entries = (
        _require_list(data, container_key="authors")
        if isinstance(data, dict) and "authors" in data
        else _require_list(data)
    )
    return [_parse_with_model(FraserAuthor, entry) for entry in entries]


def parse_subjects(data: dict[str, Any] | list[Any]) -> list[FraserSubject]:
    """Parse a subjects payload into :class:`FraserSubject` list."""
    entries = (
        _require_list(data, container_key="subjects")
        if isinstance(data, dict) and "subjects" in data
        else _require_list(data)
    )
    return [_parse_with_model(FraserSubject, entry) for entry in entries]


def parse_themes(data: dict[str, Any] | list[Any]) -> list[FraserTheme]:
    """Parse a themes payload into :class:`FraserTheme` list."""
    entries = (
        _require_list(data, container_key="themes")
        if isinstance(data, dict) and "themes" in data
        else _require_list(data)
    )
    return [_parse_with_model(FraserTheme, entry) for entry in entries]


def parse_timeline(data: dict[str, Any] | list[Any]) -> list[FraserTimelineEvent]:
    """Parse a timeline payload into :class:`FraserTimelineEvent` list."""
    entries = (
        _require_list(data, container_key="timeline")
        if isinstance(data, dict) and "timeline" in data
        else _require_list(data)
    )
    return [_parse_with_model(FraserTimelineEvent, entry) for entry in entries]


__all__ = [
    "parse_authors",
    "parse_item",
    "parse_items",
    "parse_subjects",
    "parse_themes",
    "parse_timeline",
    "parse_title",
    "parse_toc",
]

"""Common type definitions for the rss package."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Literal, TypedDict

# Status types
type ProcessorStatus = Literal["success", "error", "pending"]
type ValidationStatus = Literal["valid", "invalid", "skipped"]


# Common data structures
class ItemDict(TypedDict):
    """Typed dictionary for item data."""

    id: int
    name: str
    value: int


class ItemDictWithStatus(ItemDict):
    """Extended item dictionary with status."""

    status: ProcessorStatus
    processed: bool


class ConfigDict(TypedDict, total=False):
    """Typed dictionary for configuration data."""

    name: str
    max_items: int
    enable_validation: bool
    debug: bool
    timeout: float


class ErrorInfo(TypedDict):
    """Typed dictionary for error information."""

    code: str
    message: str
    details: Mapping[str, str | int | None]


# Result types
class ProcessingResult(TypedDict):
    """Result of a processing operation."""

    status: ProcessorStatus
    data: list[ItemDict]
    errors: list[ErrorInfo]
    processed_count: int
    skipped_count: int


class ValidationResult(TypedDict):
    """Result of a validation operation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


# JSON types
type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | Mapping[str, "JSONValue"] | list["JSONValue"]
type JSONObject = Mapping[str, JSONValue]

# File operation types
type FileOperation = Literal["read", "write", "append", "delete"]
type FileFormat = Literal["json", "yaml", "csv", "txt"]

# Sorting and filtering
type SortOrder = Literal["asc", "desc"]
type FilterOperator = Literal["eq", "ne", "gt", "lt", "gte", "lte", "in", "contains"]


# Structured logging types
class LogContext(TypedDict, total=False):
    """Context information for structured logging."""

    user_id: str | int | None
    request_id: str | None
    session_id: str | None
    trace_id: str | None
    module: str | None
    function: str | None
    line_number: int | None
    extra: Mapping[str, JSONValue]


class LogEvent(TypedDict):
    """Structured log event."""

    event: str
    level: Literal["debug", "info", "warning", "error", "critical"]
    timestamp: str
    logger: str
    context: LogContext | None
    exception: str | None
    duration_ms: float | None


# Log formatting types
type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# RSS-specific types


class FetchInterval(str, Enum):
    """Feed fetch interval."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class FetchStatus(str, Enum):
    """Feed fetch status."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


@dataclass
class Feed:
    """Feed information model.

    Attributes
    ----------
    feed_id : str
        Unique identifier (UUID v4 format)
    url : str
        Feed URL (HTTP/HTTPS only)
    title : str
        Feed title
    category : str
        Feed category (e.g., "finance", "economics")
    fetch_interval : FetchInterval
        Fetch interval
    created_at : str
        Creation timestamp (ISO 8601 format)
    updated_at : str
        Last update timestamp (ISO 8601 format)
    last_fetched : str | None
        Last fetch timestamp (ISO 8601 format)
    last_status : FetchStatus
        Last fetch status
    enabled : bool
        Whether the feed is enabled
    """

    feed_id: str
    url: str
    title: str
    category: str
    fetch_interval: FetchInterval
    created_at: str
    updated_at: str
    last_fetched: str | None
    last_status: FetchStatus
    enabled: bool


@dataclass
class FeedItem:
    """Feed item model.

    Attributes
    ----------
    item_id : str
        Unique identifier (UUID v4 format)
    title : str
        Item title
    link : str
        Item URL
    published : str
        Publication timestamp (ISO 8601 format)
    summary : str
        Item summary
    content : str
        Full content
    author : str | None
        Author name
    fetched_at : str
        Fetch timestamp (ISO 8601 format)
    """

    item_id: str
    title: str
    link: str
    published: str
    summary: str
    content: str
    author: str | None
    fetched_at: str


@dataclass
class FeedsData:
    """Feed registry data.

    Attributes
    ----------
    version : str
        Data format version
    feeds : list[Feed]
        List of feeds
    """

    version: str
    feeds: list[Feed]


@dataclass
class FeedItemsData:
    """Feed items data.

    Attributes
    ----------
    version : str
        Data format version
    feed_id : str
        Feed identifier
    items : list[FeedItem]
        List of feed items
    """

    version: str
    feed_id: str
    items: list[FeedItem]


@dataclass
class HTTPResponse:
    """HTTP response model.

    Attributes
    ----------
    status_code : int
        HTTP status code
    content : str
        Response content
    headers : Mapping[str, str]
        Response headers
    """

    status_code: int
    content: str
    headers: Mapping[str, str]


@dataclass
class FetchResult:
    """Feed fetch result.

    Attributes
    ----------
    feed_id : str
        Feed identifier
    success : bool
        Whether the fetch was successful
    items_count : int
        Total number of items fetched
    new_items : int
        Number of new items (not duplicates)
    error_message : str | None
        Error message if failed
    """

    feed_id: str
    success: bool
    items_count: int
    new_items: int
    error_message: str | None

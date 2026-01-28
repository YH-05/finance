"""RSS feed management package.

This package provides functionality for managing, fetching, and reading RSS feeds.

Main Components
---------------
FeedManager
    Manages feed registration, updates, and deletion.
FeedFetcher
    Fetches RSS/Atom feeds from URLs and parses content.
FeedReader
    Reads and filters stored feed items.
BatchScheduler
    Schedules and executes batch feed fetching operations.

Data Models
-----------
Feed
    Feed information model.
FeedItem
    Feed item (article/entry) model.
FetchResult
    Result of a feed fetch operation.
FetchInterval
    Enum for feed fetch intervals (daily, weekly, manual).
FetchStatus
    Enum for fetch status (success, failure, pending).
BatchStats
    Statistics from a batch fetch operation.

Exceptions
----------
RSSError
    Base exception for all RSS package errors.
FeedNotFoundError
    Raised when a feed is not found.
FeedAlreadyExistsError
    Raised when attempting to add a duplicate feed.
FeedFetchError
    Raised when fetching a feed fails.
FeedParseError
    Raised when parsing a feed fails.
InvalidURLError
    Raised when a URL is invalid.
FileLockError
    Raised when file lock acquisition fails.

Examples
--------
>>> from rss import FeedManager, FeedFetcher, FeedReader, BatchScheduler
>>> from rss import Feed, FeedItem, FetchResult, BatchStats
>>> from rss import RSSError, FeedNotFoundError
"""

from utils_core.logging import get_logger

from .exceptions import (
    FeedAlreadyExistsError,
    FeedFetchError,
    FeedNotFoundError,
    FeedParseError,
    FileLockError,
    InvalidURLError,
    RSSError,
)
from .services import BatchScheduler, FeedFetcher, FeedManager, FeedReader
from .types import BatchStats, Feed, FeedItem, FetchInterval, FetchResult, FetchStatus

__all__ = [
    "BatchScheduler",
    "BatchStats",
    "Feed",
    "FeedAlreadyExistsError",
    "FeedFetchError",
    "FeedFetcher",
    "FeedItem",
    "FeedManager",
    "FeedNotFoundError",
    "FeedParseError",
    "FeedReader",
    "FetchInterval",
    "FetchResult",
    "FetchStatus",
    "FileLockError",
    "InvalidURLError",
    "RSSError",
    "get_logger",
]

__version__ = "0.1.0"

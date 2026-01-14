"""Custom exceptions for RSS feed management.

This module defines all exceptions used throughout the RSS package.
All custom exceptions inherit from RSSError for easy catching.
"""


class RSSError(Exception):
    """Base exception for all RSS package errors.

    This is the root exception class for the RSS package.
    All custom exceptions inherit from this class to allow
    catching all RSS-related errors with a single except clause.

    Examples
    --------
    >>> try:
    ...     raise RSSError("Something went wrong")
    ... except RSSError as e:
    ...     print(f"RSS error occurred: {e}")
    RSS error occurred: Something went wrong
    """


class FeedNotFoundError(RSSError):
    """Feed not found error.

    Raised when attempting to access or manipulate a feed that does not exist
    in the feed registry.

    Parameters
    ----------
    message : str
        Error message describing which feed was not found.
        Should include the feed ID for debugging.

    Examples
    --------
    >>> feed_id = "550e8400-e29b-41d4-a716-446655440000"
    >>> raise FeedNotFoundError(f"Feed not found: {feed_id}")
    Traceback (most recent call last):
    ...
    FeedNotFoundError: Feed not found: 550e8400-e29b-41d4-a716-446655440000
    """


class FeedAlreadyExistsError(RSSError):
    """Feed already exists error.

    Raised when attempting to register a feed with a URL that is already
    registered in the feed registry.

    Parameters
    ----------
    message : str
        Error message describing the duplicate feed.
        Should include the URL for debugging.

    Examples
    --------
    >>> url = "https://example.com/feed.xml"
    >>> raise FeedAlreadyExistsError(f"Feed already exists: {url}")
    Traceback (most recent call last):
    ...
    FeedAlreadyExistsError: Feed already exists: https://example.com/feed.xml
    """


class FeedFetchError(RSSError):
    """Feed fetch error.

    Raised when fetching a feed fails due to network issues, HTTP errors,
    or timeouts. This error is raised after all retry attempts have been exhausted.

    Parameters
    ----------
    message : str
        Error message describing the fetch failure.
        Should include HTTP status code or error details.

    Examples
    --------
    >>> raise FeedFetchError("Failed to fetch feed: HTTP 404 Not Found")
    Traceback (most recent call last):
    ...
    FeedFetchError: Failed to fetch feed: HTTP 404 Not Found

    >>> raise FeedFetchError("Failed to fetch feed: Connection timeout after 3 retries")
    Traceback (most recent call last):
    ...
    FeedFetchError: Failed to fetch feed: Connection timeout after 3 retries
    """


class FeedParseError(RSSError):
    """Feed parse error.

    Raised when parsing a feed fails due to invalid XML/HTML structure,
    missing required fields, or unexpected format.

    Parameters
    ----------
    message : str
        Error message describing the parse failure.
        Should include details about what went wrong.

    Examples
    --------
    >>> raise FeedParseError("Failed to parse feed: Invalid XML structure")
    Traceback (most recent call last):
    ...
    FeedParseError: Failed to parse feed: Invalid XML structure

    >>> raise FeedParseError("Failed to parse feed: Missing required 'title' field")
    Traceback (most recent call last):
    ...
    FeedParseError: Failed to parse feed: Missing required 'title' field
    """


class InvalidURLError(RSSError):
    """Invalid URL error.

    Raised when a URL fails validation, such as having an unsupported scheme
    (not HTTP/HTTPS) or invalid format.

    Parameters
    ----------
    message : str
        Error message describing the invalid URL.
        Should include the URL and reason for rejection.

    Examples
    --------
    >>> url = "ftp://example.com/feed.xml"
    >>> raise InvalidURLError(f"Invalid URL format: {url}. Only HTTP/HTTPS allowed.")
    Traceback (most recent call last):
    ...
    InvalidURLError: Invalid URL format: ftp://example.com/feed.xml. Only HTTP/HTTPS allowed.

    >>> raise InvalidURLError("Invalid URL format: not-a-url")
    Traceback (most recent call last):
    ...
    InvalidURLError: Invalid URL format: not-a-url
    """


class FileLockError(RSSError):
    """File lock error.

    Raised when failing to acquire a file lock within the specified timeout period.
    This typically indicates that another process is currently accessing the file.

    Parameters
    ----------
    message : str
        Error message describing the lock failure.
        Should include the lock file path and timeout duration.

    Examples
    --------
    >>> lock_file = "/tmp/.feeds.lock"
    >>> raise FileLockError(f"Failed to acquire lock: {lock_file}. Timeout after 10s.")
    Traceback (most recent call last):
    ...
    FileLockError: Failed to acquire lock: /tmp/.feeds.lock. Timeout after 10s.
    """

"""Custom exceptions for the rss package."""


class RSSError(Exception):
    """Base exception for all RSS package errors.

    This is the base class for all custom exceptions raised by the rss package.
    All package-specific exceptions should inherit from this class.

    Examples
    --------
    >>> try:
    ...     raise RSSError("An error occurred")
    ... except RSSError as e:
    ...     print(f"Caught RSS error: {e}")
    Caught RSS error: An error occurred
    """

    pass


class FeedNotFoundError(RSSError):
    """Exception raised when a feed is not found.

    This exception is raised when attempting to access a feed that doesn't
    exist in the feed registry.

    Parameters
    ----------
    feed_id : str
        The ID of the feed that was not found

    Examples
    --------
    >>> raise FeedNotFoundError("Feed with ID '123' not found")
    Traceback (most recent call last):
        ...
    FeedNotFoundError: Feed with ID '123' not found
    """

    pass


class FeedAlreadyExistsError(RSSError):
    """Exception raised when attempting to add a feed that already exists.

    This exception is raised when trying to register a feed with a URL that
    is already registered in the feed registry.

    Parameters
    ----------
    url : str
        The URL of the feed that already exists

    Examples
    --------
    >>> raise FeedAlreadyExistsError("Feed with URL 'https://example.com/feed' already exists")
    Traceback (most recent call last):
        ...
    FeedAlreadyExistsError: Feed with URL 'https://example.com/feed' already exists
    """

    pass


class FeedFetchError(RSSError):
    """Exception raised when fetching a feed fails.

    This exception is raised when an HTTP request to fetch a feed fails,
    including network errors, timeouts, and HTTP errors (4xx, 5xx).

    Parameters
    ----------
    url : str
        The URL of the feed that failed to fetch
    status_code : int, optional
        The HTTP status code if available
    error : str
        Description of the error

    Examples
    --------
    >>> raise FeedFetchError("Failed to fetch feed from https://example.com/feed: Connection timeout")
    Traceback (most recent call last):
        ...
    FeedFetchError: Failed to fetch feed from https://example.com/feed: Connection timeout
    """

    pass


class FeedParseError(RSSError):
    """Exception raised when parsing a feed fails.

    This exception is raised when the feed content cannot be parsed as valid
    RSS 2.0 or Atom format, or when the parsed structure is invalid.

    Parameters
    ----------
    url : str
        The URL of the feed that failed to parse
    error : str
        Description of the parsing error

    Examples
    --------
    >>> raise FeedParseError("Failed to parse feed from https://example.com/feed: Invalid XML")
    Traceback (most recent call last):
        ...
    FeedParseError: Failed to parse feed from https://example.com/feed: Invalid XML
    """

    pass


class InvalidURLError(RSSError):
    """Exception raised when a URL is invalid.

    This exception is raised when URL validation fails, such as when the URL
    doesn't use HTTP/HTTPS scheme or has invalid format.

    Parameters
    ----------
    url : str
        The invalid URL
    reason : str
        The reason why the URL is invalid

    Examples
    --------
    >>> raise InvalidURLError("Invalid URL 'ftp://example.com': Only HTTP/HTTPS schemes are allowed")
    Traceback (most recent call last):
        ...
    InvalidURLError: Invalid URL 'ftp://example.com': Only HTTP/HTTPS schemes are allowed
    """

    pass


class FileLockError(RSSError):
    """Exception raised when file lock acquisition fails.

    This exception is raised when a file lock cannot be acquired within the
    specified timeout period, indicating that another process is holding the lock.

    Parameters
    ----------
    lock_file : str
        Path to the lock file
    timeout : float
        Timeout duration in seconds

    Examples
    --------
    >>> raise FileLockError("Failed to acquire lock for .feeds.lock after 10.0 seconds")
    Traceback (most recent call last):
        ...
    FileLockError: Failed to acquire lock for .feeds.lock after 10.0 seconds
    """

    pass

"""File lock management for RSS feed data.

This module provides thread-safe and process-safe file locking mechanisms
for managing concurrent access to RSS feed data files (feeds.json and items.json).
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock, Timeout

from ..exceptions import FileLockError
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class LockManager:
    """Manage file locks for RSS feed data files.

    This class provides context managers for acquiring and releasing locks
    on feeds.json and items.json files, ensuring safe concurrent access
    from multiple processes or threads.

    Parameters
    ----------
    data_dir : Path
        Root directory where RSS feed data is stored

    Attributes
    ----------
    data_dir : Path
        Root directory for RSS feed data
    default_timeout : float
        Default timeout in seconds for lock acquisition (default: 10.0)

    Examples
    --------
    >>> from pathlib import Path
    >>> manager = LockManager(Path("data/raw/rss"))
    >>> with manager.lock_feeds():
    ...     # Safely read/write feeds.json
    ...     pass

    >>> with manager.lock_items("feed-id-123"):
    ...     # Safely read/write items.json for feed-id-123
    ...     pass
    """

    def __init__(self, data_dir: Path, *, default_timeout: float = 10.0) -> None:
        """Initialize LockManager.

        Parameters
        ----------
        data_dir : Path
            Root directory where RSS feed data is stored
        default_timeout : float, default=10.0
            Default timeout in seconds for lock acquisition

        Raises
        ------
        ValueError
            If default_timeout is not positive
        """
        if default_timeout <= 0:
            logger.error(
                "Invalid timeout value",
                timeout=default_timeout,
                error="timeout must be positive",
            )
            raise ValueError(f"timeout must be positive, got {default_timeout}")

        self.data_dir = data_dir
        self.default_timeout = default_timeout
        logger.debug(
            "LockManager initialized",
            data_dir=str(data_dir),
            default_timeout=default_timeout,
        )

    @contextmanager
    def lock_feeds(
        self, *, timeout: float | None = None
    ) -> Generator[None, None, None]:
        """Acquire lock for feeds.json file.

        This context manager ensures exclusive access to feeds.json,
        preventing concurrent modifications from multiple processes or threads.

        Parameters
        ----------
        timeout : float, optional
            Timeout in seconds for lock acquisition.
            If None, uses default_timeout.

        Yields
        ------
        None
            Context where feeds.json is locked

        Raises
        ------
        FileLockError
            If lock cannot be acquired within timeout period

        Examples
        --------
        >>> manager = LockManager(Path("data/raw/rss"))
        >>> with manager.lock_feeds():
        ...     # Read or write feeds.json safely
        ...     pass

        >>> with manager.lock_feeds(timeout=5.0):
        ...     # Use custom timeout
        ...     pass
        """
        lock_timeout = timeout if timeout is not None else self.default_timeout
        lock_file = self.data_dir / ".feeds.lock"

        logger.debug(
            "Attempting to acquire feeds lock",
            lock_file=str(lock_file),
            timeout=lock_timeout,
        )

        lock = FileLock(lock_file, timeout=lock_timeout)

        try:
            with lock:
                logger.debug(
                    "Feeds lock acquired",
                    lock_file=str(lock_file),
                    timeout=lock_timeout,
                )
                yield
                logger.debug(
                    "Releasing feeds lock",
                    lock_file=str(lock_file),
                )
        except Timeout as e:
            logger.error(
                "Failed to acquire feeds lock",
                lock_file=str(lock_file),
                timeout=lock_timeout,
                error=str(e),
            )
            raise FileLockError(
                f"Failed to acquire lock for {lock_file} after {lock_timeout} seconds"
            ) from e

    @contextmanager
    def lock_items(
        self, feed_id: str, *, timeout: float | None = None
    ) -> Generator[None, None, None]:
        """Acquire lock for items.json file of a specific feed.

        This context manager ensures exclusive access to a feed's items.json,
        preventing concurrent modifications from multiple processes or threads.

        Parameters
        ----------
        feed_id : str
            UUID of the feed whose items.json should be locked
        timeout : float, optional
            Timeout in seconds for lock acquisition.
            If None, uses default_timeout.

        Yields
        ------
        None
            Context where items.json is locked

        Raises
        ------
        FileLockError
            If lock cannot be acquired within timeout period
        ValueError
            If feed_id is empty

        Examples
        --------
        >>> manager = LockManager(Path("data/raw/rss"))
        >>> with manager.lock_items("550e8400-e29b-41d4-a716-446655440000"):
        ...     # Read or write items.json safely
        ...     pass

        >>> with manager.lock_items("feed-id", timeout=5.0):
        ...     # Use custom timeout
        ...     pass
        """
        if not feed_id:
            logger.error(
                "Invalid feed_id",
                feed_id=feed_id,
                error="feed_id cannot be empty",
            )
            raise ValueError("feed_id cannot be empty")

        lock_timeout = timeout if timeout is not None else self.default_timeout
        lock_file = self.data_dir / feed_id / ".items.lock"

        logger.debug(
            "Attempting to acquire items lock",
            feed_id=feed_id,
            lock_file=str(lock_file),
            timeout=lock_timeout,
        )

        # Ensure feed directory exists
        lock_file.parent.mkdir(parents=True, exist_ok=True)

        lock = FileLock(lock_file, timeout=lock_timeout)

        try:
            with lock:
                logger.debug(
                    "Items lock acquired",
                    feed_id=feed_id,
                    lock_file=str(lock_file),
                    timeout=lock_timeout,
                )
                yield
                logger.debug(
                    "Releasing items lock",
                    feed_id=feed_id,
                    lock_file=str(lock_file),
                )
        except Timeout as e:
            logger.error(
                "Failed to acquire items lock",
                feed_id=feed_id,
                lock_file=str(lock_file),
                timeout=lock_timeout,
                error=str(e),
            )
            raise FileLockError(
                f"Failed to acquire lock for {lock_file} after {lock_timeout} seconds"
            ) from e

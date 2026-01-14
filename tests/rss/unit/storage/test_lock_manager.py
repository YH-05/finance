"""Unit tests for LockManager."""

import threading
import time
from pathlib import Path

import pytest

from rss.exceptions import FileLockError
from rss.storage.lock_manager import LockManager


class TestLockManagerInit:
    """Test LockManager initialization."""

    def test_init_with_default_timeout(self, tmp_path: Path) -> None:
        """Test initialization with default timeout."""
        manager = LockManager(tmp_path)
        assert manager.data_dir == tmp_path
        assert manager.default_timeout == 10.0

    def test_init_with_custom_timeout(self, tmp_path: Path) -> None:
        """Test initialization with custom timeout."""
        manager = LockManager(tmp_path, default_timeout=5.0)
        assert manager.data_dir == tmp_path
        assert manager.default_timeout == 5.0

    def test_init_with_invalid_timeout(self, tmp_path: Path) -> None:
        """Test initialization with invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            LockManager(tmp_path, default_timeout=0.0)

        with pytest.raises(ValueError, match="timeout must be positive"):
            LockManager(tmp_path, default_timeout=-1.0)


class TestLockFeeds:
    """Test lock_feeds context manager."""

    def test_lock_feeds_creates_lock_file(self, tmp_path: Path) -> None:
        """Test that lock_feeds creates .feeds.lock file."""
        manager = LockManager(tmp_path)
        lock_file = tmp_path / ".feeds.lock"

        assert not lock_file.exists()

        with manager.lock_feeds():
            # Lock file should exist while lock is held
            assert lock_file.exists()

        # Lock file should still exist after release (FileLock behavior)
        assert lock_file.exists()

    def test_lock_feeds_acquires_and_releases(self, tmp_path: Path) -> None:
        """Test that lock_feeds successfully acquires and releases lock."""
        manager = LockManager(tmp_path)

        # Should be able to acquire lock
        with manager.lock_feeds():
            pass  # Lock acquired

        # Should be able to acquire lock again after release
        with manager.lock_feeds():
            pass  # Lock re-acquired

    def test_lock_feeds_with_custom_timeout(self, tmp_path: Path) -> None:
        """Test lock_feeds with custom timeout."""
        manager = LockManager(tmp_path, default_timeout=10.0)

        with manager.lock_feeds(timeout=0.5):
            pass  # Lock acquired with custom timeout

    def test_lock_feeds_timeout_raises_error(self, tmp_path: Path) -> None:
        """Test that lock_feeds raises FileLockError on timeout."""
        manager = LockManager(tmp_path)

        def hold_lock() -> None:
            with manager.lock_feeds():
                time.sleep(2.0)  # Hold lock for 2 seconds

        # Start thread that holds the lock
        thread = threading.Thread(target=hold_lock)
        thread.start()

        # Wait a bit to ensure first lock is acquired
        time.sleep(0.1)

        # Try to acquire lock with short timeout - should fail
        with (
            pytest.raises(
                FileLockError, match=r"Failed to acquire lock.*after 0.5 seconds"
            ),
            manager.lock_feeds(timeout=0.5),
        ):
            pass

        # Wait for thread to finish
        thread.join()

    def test_lock_feeds_concurrent_access(self, tmp_path: Path) -> None:
        """Test that lock_feeds prevents concurrent access."""
        manager = LockManager(tmp_path)
        counter_file = tmp_path / "counter.txt"
        counter_file.write_text("0")

        def increment_counter() -> None:
            with manager.lock_feeds():
                # Read current value
                current = int(counter_file.read_text())
                # Simulate some processing time
                time.sleep(0.01)
                # Write incremented value
                counter_file.write_text(str(current + 1))

        # Run 10 threads concurrently
        threads = [threading.Thread(target=increment_counter) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Counter should be exactly 10 if locking works correctly
        assert int(counter_file.read_text()) == 10


class TestLockItems:
    """Test lock_items context manager."""

    def test_lock_items_creates_lock_file(self, tmp_path: Path) -> None:
        """Test that lock_items creates .items.lock file."""
        manager = LockManager(tmp_path)
        feed_id = "test-feed-id"
        lock_file = tmp_path / feed_id / ".items.lock"

        assert not lock_file.exists()

        with manager.lock_items(feed_id):
            # Lock file should exist while lock is held
            assert lock_file.exists()

        # Lock file should still exist after release
        assert lock_file.exists()

    def test_lock_items_creates_feed_directory(self, tmp_path: Path) -> None:
        """Test that lock_items creates feed directory if it doesn't exist."""
        manager = LockManager(tmp_path)
        feed_id = "new-feed-id"
        feed_dir = tmp_path / feed_id

        assert not feed_dir.exists()

        with manager.lock_items(feed_id):
            # Feed directory should be created
            assert feed_dir.exists()
            assert feed_dir.is_dir()

    def test_lock_items_acquires_and_releases(self, tmp_path: Path) -> None:
        """Test that lock_items successfully acquires and releases lock."""
        manager = LockManager(tmp_path)
        feed_id = "test-feed"

        # Should be able to acquire lock
        with manager.lock_items(feed_id):
            pass  # Lock acquired

        # Should be able to acquire lock again after release
        with manager.lock_items(feed_id):
            pass  # Lock re-acquired

    def test_lock_items_with_custom_timeout(self, tmp_path: Path) -> None:
        """Test lock_items with custom timeout."""
        manager = LockManager(tmp_path, default_timeout=10.0)
        feed_id = "test-feed"

        with manager.lock_items(feed_id, timeout=0.5):
            pass  # Lock acquired with custom timeout

    def test_lock_items_timeout_raises_error(self, tmp_path: Path) -> None:
        """Test that lock_items raises FileLockError on timeout."""
        manager = LockManager(tmp_path)
        feed_id = "test-feed"

        def hold_lock() -> None:
            with manager.lock_items(feed_id):
                time.sleep(2.0)  # Hold lock for 2 seconds

        # Start thread that holds the lock
        thread = threading.Thread(target=hold_lock)
        thread.start()

        # Wait a bit to ensure first lock is acquired
        time.sleep(0.1)

        # Try to acquire lock with short timeout - should fail
        with (
            pytest.raises(
                FileLockError, match=r"Failed to acquire lock.*after 0.5 seconds"
            ),
            manager.lock_items(feed_id, timeout=0.5),
        ):
            pass

        # Wait for thread to finish
        thread.join()

    def test_lock_items_with_empty_feed_id(self, tmp_path: Path) -> None:
        """Test that lock_items raises ValueError for empty feed_id."""
        manager = LockManager(tmp_path)

        with (
            pytest.raises(ValueError, match="feed_id cannot be empty"),
            manager.lock_items(""),
        ):
            pass

    def test_lock_items_concurrent_access(self, tmp_path: Path) -> None:
        """Test that lock_items prevents concurrent access to same feed."""
        manager = LockManager(tmp_path)
        feed_id = "test-feed"
        counter_file = tmp_path / feed_id / "counter.txt"
        counter_file.parent.mkdir(parents=True, exist_ok=True)
        counter_file.write_text("0")

        def increment_counter() -> None:
            with manager.lock_items(feed_id):
                # Read current value
                current = int(counter_file.read_text())
                # Simulate some processing time
                time.sleep(0.01)
                # Write incremented value
                counter_file.write_text(str(current + 1))

        # Run 10 threads concurrently
        threads = [threading.Thread(target=increment_counter) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Counter should be exactly 10 if locking works correctly
        assert int(counter_file.read_text()) == 10

    def test_lock_items_different_feeds_independent(self, tmp_path: Path) -> None:
        """Test that locks for different feeds are independent."""
        manager = LockManager(tmp_path)
        feed_id_1 = "feed-1"
        feed_id_2 = "feed-2"

        # Acquire lock for feed-1
        with manager.lock_items(feed_id_1), manager.lock_items(feed_id_2):
            # Should be able to acquire lock for feed-2 concurrently
            pass  # Both locks held simultaneously


class TestLockManagerIntegration:
    """Integration tests for LockManager."""

    def test_lock_feeds_and_items_together(self, tmp_path: Path) -> None:
        """Test that feeds and items locks can be held simultaneously."""
        manager = LockManager(tmp_path)
        feed_id = "test-feed"

        # Should be able to hold both locks at once
        with manager.lock_feeds(), manager.lock_items(feed_id):
            pass  # Both locks acquired

    def test_nested_same_lock_fails(self, tmp_path: Path) -> None:
        """Test that nested acquisition of same lock fails (not reentrant)."""
        manager = LockManager(tmp_path)

        with manager.lock_feeds():  # noqa: SIM117
            # Trying to acquire the same lock again should timeout
            # (FileLock is not reentrant by default)
            with (
                pytest.raises(FileLockError, match="Failed to acquire lock"),
                manager.lock_feeds(timeout=0.1),
            ):
                pass

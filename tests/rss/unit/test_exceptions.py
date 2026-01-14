"""Unit tests for exceptions module."""

import pytest


class TestRSSError:
    """Test RSSError base exception."""

    def test_正常系_基底例外クラスがExceptionを継承する(self) -> None:
        """RSSErrorがExceptionを継承していることを確認。"""
        from rss.exceptions import RSSError

        # RSSErrorがExceptionのサブクラスであることを確認
        assert issubclass(RSSError, Exception)

    def test_正常系_メッセージ付きで例外を生成できる(self) -> None:
        """メッセージ付きでRSSErrorを生成できることを確認。"""
        from rss.exceptions import RSSError

        error = RSSError("Test error message")
        assert str(error) == "Test error message"

    def test_正常系_例外をraiseできる(self) -> None:
        """RSSErrorを正常にraiseできることを確認。"""
        from rss.exceptions import RSSError

        with pytest.raises(RSSError, match="Test error"):
            raise RSSError("Test error")


class TestFeedNotFoundError:
    """Test FeedNotFoundError exception."""

    def test_正常系_RSSErrorを継承する(self) -> None:
        """FeedNotFoundErrorがRSSErrorを継承していることを確認。"""
        from rss.exceptions import FeedNotFoundError, RSSError

        assert issubclass(FeedNotFoundError, RSSError)

    def test_正常系_フィードIDを含むエラーメッセージ(self) -> None:
        """フィードIDを含むエラーメッセージを生成できることを確認。"""
        from rss.exceptions import FeedNotFoundError

        feed_id = "550e8400-e29b-41d4-a716-446655440000"
        error = FeedNotFoundError(f"Feed not found: {feed_id}")
        assert feed_id in str(error)

    def test_正常系_例外をraiseできる(self) -> None:
        """FeedNotFoundErrorを正常にraiseできることを確認。"""
        from rss.exceptions import FeedNotFoundError

        with pytest.raises(FeedNotFoundError, match="Feed not found"):
            raise FeedNotFoundError("Feed not found: abc123")


class TestFeedAlreadyExistsError:
    """Test FeedAlreadyExistsError exception."""

    def test_正常系_RSSErrorを継承する(self) -> None:
        """FeedAlreadyExistsErrorがRSSErrorを継承していることを確認。"""
        from rss.exceptions import FeedAlreadyExistsError, RSSError

        assert issubclass(FeedAlreadyExistsError, RSSError)

    def test_正常系_URLを含むエラーメッセージ(self) -> None:
        """URLを含むエラーメッセージを生成できることを確認。"""
        from rss.exceptions import FeedAlreadyExistsError

        url = "https://example.com/feed.xml"
        error = FeedAlreadyExistsError(f"Feed already exists: {url}")
        assert url in str(error)

    def test_正常系_例外をraiseできる(self) -> None:
        """FeedAlreadyExistsErrorを正常にraiseできることを確認。"""
        from rss.exceptions import FeedAlreadyExistsError

        with pytest.raises(FeedAlreadyExistsError, match="already exists"):
            raise FeedAlreadyExistsError(
                "Feed already exists: https://example.com/feed.xml"
            )


class TestFeedFetchError:
    """Test FeedFetchError exception."""

    def test_正常系_RSSErrorを継承する(self) -> None:
        """FeedFetchErrorがRSSErrorを継承していることを確認。"""
        from rss.exceptions import FeedFetchError, RSSError

        assert issubclass(FeedFetchError, RSSError)

    def test_正常系_HTTPステータスコードを含むエラーメッセージ(self) -> None:
        """HTTPステータスコードを含むエラーメッセージを生成できることを確認。"""
        from rss.exceptions import FeedFetchError

        error = FeedFetchError("Failed to fetch feed: HTTP 404")
        assert "404" in str(error)

    def test_正常系_例外をraiseできる(self) -> None:
        """FeedFetchErrorを正常にraiseできることを確認。"""
        from rss.exceptions import FeedFetchError

        with pytest.raises(FeedFetchError, match="Failed to fetch"):
            raise FeedFetchError("Failed to fetch feed: Connection timeout")


class TestFeedParseError:
    """Test FeedParseError exception."""

    def test_正常系_RSSErrorを継承する(self) -> None:
        """FeedParseErrorがRSSErrorを継承していることを確認。"""
        from rss.exceptions import FeedParseError, RSSError

        assert issubclass(FeedParseError, RSSError)

    def test_正常系_パースエラー詳細を含むエラーメッセージ(self) -> None:
        """パースエラー詳細を含むエラーメッセージを生成できることを確認。"""
        from rss.exceptions import FeedParseError

        error = FeedParseError("Failed to parse feed: Invalid XML structure")
        assert "Invalid XML" in str(error)

    def test_正常系_例外をraiseできる(self) -> None:
        """FeedParseErrorを正常にraiseできることを確認。"""
        from rss.exceptions import FeedParseError

        with pytest.raises(FeedParseError, match="Failed to parse"):
            raise FeedParseError("Failed to parse feed: Unexpected format")


class TestInvalidURLError:
    """Test InvalidURLError exception."""

    def test_正常系_RSSErrorを継承する(self) -> None:
        """InvalidURLErrorがRSSErrorを継承していることを確認。"""
        from rss.exceptions import InvalidURLError, RSSError

        assert issubclass(InvalidURLError, RSSError)

    def test_正常系_無効なURLを含むエラーメッセージ(self) -> None:
        """無効なURLを含むエラーメッセージを生成できることを確認。"""
        from rss.exceptions import InvalidURLError

        invalid_url = "ftp://invalid.com/feed"
        error = InvalidURLError(
            f"Invalid URL format: {invalid_url}. Only HTTP/HTTPS allowed."
        )
        assert invalid_url in str(error)

    def test_正常系_例外をraiseできる(self) -> None:
        """InvalidURLErrorを正常にraiseできることを確認。"""
        from rss.exceptions import InvalidURLError

        with pytest.raises(InvalidURLError, match="Invalid URL"):
            raise InvalidURLError("Invalid URL format: not-a-url")


class TestFileLockError:
    """Test FileLockError exception."""

    def test_正常系_RSSErrorを継承する(self) -> None:
        """FileLockErrorがRSSErrorを継承していることを確認。"""
        from rss.exceptions import FileLockError, RSSError

        assert issubclass(FileLockError, RSSError)

    def test_正常系_ロックファイルパスを含むエラーメッセージ(self) -> None:
        """ロックファイルパスを含むエラーメッセージを生成できることを確認。"""
        from rss.exceptions import FileLockError

        lock_file = "/tmp/.feeds.lock"
        error = FileLockError(f"Failed to acquire lock: {lock_file}")
        assert lock_file in str(error)

    def test_正常系_例外をraiseできる(self) -> None:
        """FileLockErrorを正常にraiseできることを確認。"""
        from rss.exceptions import FileLockError

        with pytest.raises(FileLockError, match="Failed to acquire lock"):
            raise FileLockError("Failed to acquire lock: timeout after 10s")


class TestExceptionInheritanceChain:
    """Test exception inheritance chain."""

    def test_正常系_全例外がRSSErrorを継承する(self) -> None:
        """全ての例外クラスがRSSErrorを継承していることを確認。"""
        from rss.exceptions import (
            FeedAlreadyExistsError,
            FeedFetchError,
            FeedNotFoundError,
            FeedParseError,
            FileLockError,
            InvalidURLError,
            RSSError,
        )

        exceptions = [
            FeedNotFoundError,
            FeedAlreadyExistsError,
            FeedFetchError,
            FeedParseError,
            InvalidURLError,
            FileLockError,
        ]

        for exc_class in exceptions:
            assert issubclass(
                exc_class, RSSError
            ), f"{exc_class.__name__} should inherit from RSSError"

    def test_正常系_RSSError例外でキャッチできる(self) -> None:
        """全ての例外がRSSErrorでキャッチできることを確認。"""
        from rss.exceptions import FeedNotFoundError, RSSError

        with pytest.raises(RSSError):
            raise FeedNotFoundError("Test")

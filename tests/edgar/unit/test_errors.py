"""Unit tests for edgar.errors module.

Tests for EdgarError base class and specific error types.
"""

import pytest

from edgar.errors import (
    CacheError,
    EdgarError,
    FilingNotFoundError,
    RateLimitError,
    SectionNotFoundError,
)


class TestEdgarError:
    """Tests for EdgarError base class."""

    def test_正常系_EdgarErrorはメッセージとコンテキストを持つ(self) -> None:
        """EdgarError should store message and context.

        Verify that EdgarError can be instantiated with a message
        and context dictionary, and that these are accessible.
        """
        context = {"cik": "0001234567", "form_type": "10-K"}
        error = EdgarError("Failed to fetch filing", context=context)

        assert str(error) == "Failed to fetch filing"
        assert error.message == "Failed to fetch filing"
        assert error.context == context

    def test_正常系_EdgarErrorはコンテキストなしで作成できる(self) -> None:
        """EdgarError should work without context.

        Verify that EdgarError can be instantiated with only a message,
        defaulting to an empty context dictionary.
        """
        error = EdgarError("Simple error message")

        assert str(error) == "Simple error message"
        assert error.context == {}


class TestFilingNotFoundError:
    """Tests for FilingNotFoundError."""

    def test_正常系_FilingNotFoundErrorはEdgarErrorを継承(self) -> None:
        """FilingNotFoundError should inherit from EdgarError.

        Verify that FilingNotFoundError is a subclass of EdgarError.
        """
        assert issubclass(FilingNotFoundError, EdgarError)

    def test_正常系_FilingNotFoundErrorはメッセージとコンテキストを持つ(self) -> None:
        """FilingNotFoundError should store message and context.

        Verify that FilingNotFoundError works like EdgarError.
        """
        context = {"cik": "0001234567", "form_type": "10-K"}
        error = FilingNotFoundError("Filing not found", context=context)

        assert "Filing not found" in str(error)
        assert error.context == context


class TestSectionNotFoundError:
    """Tests for SectionNotFoundError."""

    def test_正常系_SectionNotFoundErrorはEdgarErrorを継承(self) -> None:
        """SectionNotFoundError should inherit from EdgarError.

        Verify that SectionNotFoundError is a subclass of EdgarError.
        """
        assert issubclass(SectionNotFoundError, EdgarError)

    def test_正常系_SectionNotFoundErrorはメッセージとコンテキストを持つ(self) -> None:
        """SectionNotFoundError should store message and context.

        Verify that SectionNotFoundError works like EdgarError.
        """
        context = {"section_key": "item_1", "filing_id": "0001234567-24-000001"}
        error = SectionNotFoundError("Section not found", context=context)

        assert "Section not found" in str(error)
        assert error.context == context


class TestCacheError:
    """Tests for CacheError."""

    def test_正常系_CacheErrorはEdgarErrorを継承(self) -> None:
        """CacheError should inherit from EdgarError.

        Verify that CacheError is a subclass of EdgarError.
        """
        assert issubclass(CacheError, EdgarError)

    def test_正常系_CacheErrorはメッセージとコンテキストを持つ(self) -> None:
        """CacheError should store message and context.

        Verify that CacheError works like EdgarError.
        """
        context = {"operation": "write", "path": "/cache/filing.json"}
        error = CacheError("Cache operation failed", context=context)

        assert "Cache operation failed" in str(error)
        assert error.context == context


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_正常系_RateLimitErrorはEdgarErrorを継承(self) -> None:
        """RateLimitError should inherit from EdgarError.

        Verify that RateLimitError is a subclass of EdgarError.
        """
        assert issubclass(RateLimitError, EdgarError)

    def test_正常系_RateLimitErrorはメッセージとコンテキストを持つ(self) -> None:
        """RateLimitError should store message and context.

        Verify that RateLimitError works like EdgarError.
        """
        context = {"retry_after": 10, "requests_per_second": 10}
        error = RateLimitError("Rate limit exceeded", context=context)

        assert "Rate limit exceeded" in str(error)
        assert error.context == context

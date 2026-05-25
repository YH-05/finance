"""Tests for ``market.fraser.errors`` module.

Covers the 7-class FRASER exception hierarchy:

- Each class is a subclass of ``FraserError`` and of ``Exception``.
- None of the classes inherits from ``market.errors.MarketError``
  (HF1 confirmed direct ``Exception`` inheritance).
- Constructor-set attributes are preserved (``url``, ``status_code``,
  ``response_body``, ``retry_after``, ``raw_data``, ``field``,
  ``cause``, ``value``).
"""

import pytest

from market.errors import MarketError
from market.fraser import errors
from market.fraser.errors import (
    FraserAPIError,
    FraserAuthError,
    FraserDownloadError,
    FraserError,
    FraserNotFoundError,
    FraserParseError,
    FraserRateLimitError,
    FraserValidationError,
)


class TestFraserErrorBase:
    """Tests for ``FraserError`` base class."""

    def test_正常系_Exceptionを継承(self) -> None:
        assert issubclass(FraserError, Exception)

    def test_正常系_MarketErrorを継承しない(self) -> None:
        """HF1: FRASER errors must not inherit from ``MarketError``.

        Inheriting from ``MarketError`` would force ``market.fraser``
        to import ``market.errors`` and risks circular dependencies.
        """
        assert not issubclass(FraserError, MarketError)

    def test_正常系_メッセージが設定される(self) -> None:
        error = FraserError("test error")
        assert error.message == "test error"
        assert str(error) == "test error"

    def test_正常系_raiseできる(self) -> None:
        with pytest.raises(FraserError, match="test error"):
            raise FraserError("test error")


class TestFraserAuthError:
    """Tests for ``FraserAuthError`` (401 / 403)."""

    def test_正常系_FraserErrorを継承(self) -> None:
        assert issubclass(FraserAuthError, FraserError)

    def test_正常系_MarketErrorを継承しない(self) -> None:
        assert not issubclass(FraserAuthError, MarketError)

    def test_正常系_メッセージが設定される(self) -> None:
        error = FraserAuthError("Invalid API key")
        assert error.message == "Invalid API key"

    def test_正常系_FraserErrorでキャッチ可能(self) -> None:
        with pytest.raises(FraserError):
            raise FraserAuthError("Auth failed")


class TestFraserRateLimitError:
    """Tests for ``FraserRateLimitError`` (429 + Retry-After)."""

    def test_正常系_FraserErrorを継承(self) -> None:
        assert issubclass(FraserRateLimitError, FraserError)

    def test_正常系_retry_after保持(self) -> None:
        error = FraserRateLimitError("Rate limit exceeded", retry_after=120.5)
        assert error.retry_after == 120.5
        assert error.message == "Rate limit exceeded"

    def test_正常系_retry_afterデフォルトNone(self) -> None:
        error = FraserRateLimitError("Rate limit")
        assert error.retry_after is None


class TestFraserNotFoundError:
    """Tests for ``FraserNotFoundError`` (404)."""

    def test_正常系_FraserErrorを継承(self) -> None:
        assert issubclass(FraserNotFoundError, FraserError)

    def test_正常系_メッセージが設定される(self) -> None:
        error = FraserNotFoundError("Title 999 not found")
        assert error.message == "Title 999 not found"


class TestFraserAPIError:
    """Tests for ``FraserAPIError`` (4xx / 5xx generic)."""

    def test_正常系_FraserErrorを継承(self) -> None:
        assert issubclass(FraserAPIError, FraserError)

    def test_正常系_属性が正しく設定される(self) -> None:
        error = FraserAPIError(
            "API returned HTTP 500",
            url="https://fraser.stlouisfed.org/api/title/677",
            status_code=500,
            response_body='{"error": "Internal Server Error"}',
        )
        assert error.message == "API returned HTTP 500"
        assert error.url == "https://fraser.stlouisfed.org/api/title/677"
        assert error.status_code == 500
        assert error.response_body == '{"error": "Internal Server Error"}'


class TestFraserParseError:
    """Tests for ``FraserParseError``."""

    def test_正常系_FraserErrorを継承(self) -> None:
        assert issubclass(FraserParseError, FraserError)

    def test_正常系_属性が正しく設定される(self) -> None:
        underlying = ValueError("invalid date")
        error = FraserParseError(
            "Failed to parse response",
            raw_data='{"items": []}',
            field="items",
            cause=underlying,
        )
        assert error.message == "Failed to parse response"
        assert error.raw_data == '{"items": []}'
        assert error.field == "items"
        assert error.cause is underlying

    def test_正常系_causeデフォルトNone(self) -> None:
        error = FraserParseError("bad", raw_data="", field="x")
        assert error.cause is None


class TestFraserDownloadError:
    """Tests for ``FraserDownloadError``."""

    def test_正常系_FraserErrorを継承(self) -> None:
        assert issubclass(FraserDownloadError, FraserError)

    def test_正常系_属性が正しく設定される(self) -> None:
        underlying = OSError("disk full")
        error = FraserDownloadError(
            "Download failed",
            url="https://fraser.stlouisfed.org/files/doc/1.pdf",
            cause=underlying,
        )
        assert error.url == "https://fraser.stlouisfed.org/files/doc/1.pdf"
        assert error.cause is underlying

    def test_正常系_causeデフォルトNone(self) -> None:
        error = FraserDownloadError("fail", url="https://x")
        assert error.cause is None


class TestFraserValidationError:
    """Tests for ``FraserValidationError``."""

    def test_正常系_FraserErrorを継承(self) -> None:
        assert issubclass(FraserValidationError, FraserError)

    def test_正常系_属性が正しく設定される(self) -> None:
        error = FraserValidationError(
            "timeout must be positive",
            field="timeout",
            value=-1.0,
        )
        assert error.message == "timeout must be positive"
        assert error.field == "timeout"
        assert error.value == -1.0


class TestErrorHierarchy:
    """Cross-cutting tests for the exception hierarchy."""

    SUBCLASSES = (
        FraserAuthError,
        FraserRateLimitError,
        FraserNotFoundError,
        FraserAPIError,
        FraserParseError,
        FraserDownloadError,
        FraserValidationError,
    )

    def test_正常系_全エラーがFraserErrorのサブクラス(self) -> None:
        for cls in self.SUBCLASSES:
            assert issubclass(cls, FraserError), (
                f"{cls.__name__} does not inherit from FraserError"
            )

    def test_正常系_全エラーがException直接継承パスを持つ(self) -> None:
        """Every subclass should reach ``Exception`` through ``FraserError``.

        Combined with the ``FraserError`` test ensuring direct
        ``Exception`` inheritance, this covers the full hierarchy.
        """
        for cls in self.SUBCLASSES:
            assert issubclass(cls, Exception)

    def test_正常系_どのクラスもMarketErrorを継承しない(self) -> None:
        for cls in (FraserError, *self.SUBCLASSES):
            assert not issubclass(cls, MarketError), (
                f"{cls.__name__} must not inherit from MarketError"
            )


class TestAllExports:
    """Tests for ``__all__`` completeness."""

    def test_正常系_allが定義されている(self) -> None:
        assert hasattr(errors, "__all__")

    def test_正常系_全例外クラスがallに含まれる(self) -> None:
        expected = {
            "FraserAPIError",
            "FraserAuthError",
            "FraserDownloadError",
            "FraserError",
            "FraserNotFoundError",
            "FraserParseError",
            "FraserRateLimitError",
            "FraserValidationError",
        }
        assert set(errors.__all__) == expected

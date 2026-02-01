"""Unit tests for custom exception classes in the news package."""

import pytest
from news.core.errors import (
    NewsError,
    RateLimitError,
    SourceError,
    ValidationError,
)


class TestNewsError:
    """Test NewsError base exception."""

    def test_正常系_メッセージで作成できる(self) -> None:
        """NewsErrorをメッセージで作成できることを確認。"""
        error = NewsError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_正常系_Exceptionを継承している(self) -> None:
        """NewsErrorがExceptionを継承していることを確認。"""
        error = NewsError("Test error")
        assert isinstance(error, Exception)

    def test_正常系_raiseでキャッチできる(self) -> None:
        """NewsErrorをraiseしてキャッチできることを確認。"""
        with pytest.raises(NewsError, match="Test error"):
            raise NewsError("Test error")


class TestSourceError:
    """Test SourceError exception."""

    def test_正常系_必須パラメータのみで作成できる(self) -> None:
        """SourceErrorを必須パラメータのみで作成できることを確認。"""
        error = SourceError(
            message="Failed to fetch data",
            source="yfinance",
        )

        assert str(error) == "Failed to fetch data"
        assert error.source == "yfinance"
        assert error.ticker is None
        assert error.cause is None
        assert error.retryable is False

    def test_正常系_全パラメータで作成できる(self) -> None:
        """SourceErrorを全パラメータで作成できることを確認。"""
        original_error = ConnectionError("Connection refused")
        error = SourceError(
            message="Failed to fetch AAPL news",
            source="yfinance",
            ticker="AAPL",
            cause=original_error,
            retryable=True,
        )

        assert str(error) == "Failed to fetch AAPL news"
        assert error.source == "yfinance"
        assert error.ticker == "AAPL"
        assert error.cause is original_error
        assert error.retryable is True

    def test_正常系_NewsErrorを継承している(self) -> None:
        """SourceErrorがNewsErrorを継承していることを確認。"""
        error = SourceError(message="Test", source="test")
        assert isinstance(error, NewsError)
        assert isinstance(error, Exception)

    def test_正常系_raiseでキャッチできる(self) -> None:
        """SourceErrorをraiseしてキャッチできることを確認。"""
        with pytest.raises(SourceError, match="Test source error"):
            raise SourceError(message="Test source error", source="yfinance")

    def test_正常系_NewsErrorとしてもキャッチできる(self) -> None:
        """SourceErrorをNewsErrorとしてキャッチできることを確認。"""
        with pytest.raises(NewsError):
            raise SourceError(message="Test", source="yfinance")


class TestValidationError:
    """Test ValidationError exception."""

    def test_正常系_全パラメータで作成できる(self) -> None:
        """ValidationErrorを全パラメータで作成できることを確認。"""
        error = ValidationError(
            message="Invalid ticker format",
            field="ticker",
            value="",
        )

        assert str(error) == "Invalid ticker format"
        assert error.field == "ticker"
        assert error.value == ""

    def test_正常系_様々な型の値で作成できる(self) -> None:
        """ValidationErrorを様々な型の値で作成できることを確認。"""
        # None
        error_none = ValidationError(
            message="Value is None",
            field="data",
            value=None,
        )
        assert error_none.value is None

        # 数値
        error_int = ValidationError(
            message="Value out of range",
            field="count",
            value=-1,
        )
        assert error_int.value == -1

        # リスト
        error_list = ValidationError(
            message="Invalid list",
            field="items",
            value=["a", "b"],
        )
        assert error_list.value == ["a", "b"]

    def test_正常系_NewsErrorを継承している(self) -> None:
        """ValidationErrorがNewsErrorを継承していることを確認。"""
        error = ValidationError(message="Test", field="test", value="x")
        assert isinstance(error, NewsError)
        assert isinstance(error, Exception)

    def test_正常系_raiseでキャッチできる(self) -> None:
        """ValidationErrorをraiseしてキャッチできることを確認。"""
        with pytest.raises(ValidationError, match="Invalid ticker"):
            raise ValidationError(
                message="Invalid ticker",
                field="ticker",
                value="ABC DEF",
            )

    def test_正常系_NewsErrorとしてもキャッチできる(self) -> None:
        """ValidationErrorをNewsErrorとしてキャッチできることを確認。"""
        with pytest.raises(NewsError):
            raise ValidationError(message="Test", field="test", value="x")


class TestRateLimitError:
    """Test RateLimitError exception."""

    def test_正常系_ソースのみで作成できる(self) -> None:
        """RateLimitErrorをソースのみで作成できることを確認。"""
        error = RateLimitError(source="yfinance")

        assert str(error) == "Rate limit exceeded for yfinance"
        assert error.source == "yfinance"
        assert error.retryable is True
        assert error.retry_after is None

    def test_正常系_retry_afterを指定できる(self) -> None:
        """RateLimitErrorにretry_afterを指定できることを確認。"""
        error = RateLimitError(source="yfinance", retry_after=60.0)

        assert str(error) == "Rate limit exceeded for yfinance"
        assert error.source == "yfinance"
        assert error.retryable is True
        assert error.retry_after == 60.0

    def test_正常系_SourceErrorを継承している(self) -> None:
        """RateLimitErrorがSourceErrorを継承していることを確認。"""
        error = RateLimitError(source="test")
        assert isinstance(error, SourceError)
        assert isinstance(error, NewsError)
        assert isinstance(error, Exception)

    def test_正常系_retryableが常にTrue(self) -> None:
        """RateLimitErrorのretryableが常にTrueであることを確認。"""
        error = RateLimitError(source="test")
        assert error.retryable is True

    def test_正常系_raiseでキャッチできる(self) -> None:
        """RateLimitErrorをraiseしてキャッチできることを確認。"""
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            raise RateLimitError(source="yfinance")

    def test_正常系_SourceErrorとしてもキャッチできる(self) -> None:
        """RateLimitErrorをSourceErrorとしてキャッチできることを確認。"""
        with pytest.raises(SourceError):
            raise RateLimitError(source="yfinance")

    def test_正常系_NewsErrorとしてもキャッチできる(self) -> None:
        """RateLimitErrorをNewsErrorとしてキャッチできることを確認。"""
        with pytest.raises(NewsError):
            raise RateLimitError(source="yfinance")


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_正常系_例外階層が正しい(self) -> None:
        """例外クラスの継承階層が正しいことを確認。"""
        # NewsError は Exception の直接のサブクラス
        assert issubclass(NewsError, Exception)
        assert NewsError.__bases__ == (Exception,)

        # SourceError は NewsError のサブクラス
        assert issubclass(SourceError, NewsError)

        # ValidationError は NewsError のサブクラス
        assert issubclass(ValidationError, NewsError)

        # RateLimitError は SourceError のサブクラス
        assert issubclass(RateLimitError, SourceError)
        assert issubclass(RateLimitError, NewsError)

    def test_正常系_MROが正しい順序(self) -> None:
        """Method Resolution Order（MRO）が正しいことを確認。"""
        # RateLimitError の MRO
        mro_names = [cls.__name__ for cls in RateLimitError.__mro__]
        assert mro_names[:4] == [
            "RateLimitError",
            "SourceError",
            "NewsError",
            "Exception",
        ]

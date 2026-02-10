"""Unit tests for market.nasdaq.errors module.

NASDAQ API エラークラスのテストスイート。
4つのエラークラス（NasdaqError, NasdaqAPIError,
NasdaqRateLimitError, NasdaqParseError）の動作を検証する。

Test TODO List:
- [x] NasdaqError: base exception with message attribute
- [x] NasdaqAPIError: API response error with url, status_code, response_body
- [x] NasdaqRateLimitError: rate limit error with url, retry_after
- [x] NasdaqParseError: parse error with raw_data, field
- [x] Exception hierarchy validation
- [x] Common usage patterns (try-except, raise, cause chaining)
- [x] __all__ exports
"""

import pytest

from market.nasdaq.errors import (
    NasdaqAPIError,
    NasdaqError,
    NasdaqParseError,
    NasdaqRateLimitError,
)

# =============================================================================
# NasdaqError (base exception)
# =============================================================================


class TestNasdaqError:
    """NasdaqError 基底例外クラスのテスト。"""

    def test_正常系_メッセージで初期化できる(self) -> None:
        """NasdaqError がメッセージで初期化されること。"""
        error = NasdaqError("NASDAQ API operation failed")

        assert error.message == "NASDAQ API operation failed"
        assert str(error) == "NASDAQ API operation failed"

    def test_正常系_Exceptionを直接継承している(self) -> None:
        """NasdaqError が Exception を直接継承していること。"""
        assert issubclass(NasdaqError, Exception)
        # NasdaqError の直接の基底クラスに Exception が含まれること
        assert Exception in NasdaqError.__bases__

    def test_正常系_raiseで例外として使用可能(self) -> None:
        """raise で例外として使用できること。"""
        with pytest.raises(NasdaqError, match="test error"):
            raise NasdaqError("test error")

    def test_正常系_message属性にアクセスできる(self) -> None:
        """message 属性が正しく設定されること。"""
        error = NasdaqError("some error message")

        assert hasattr(error, "message")
        assert error.message == "some error message"


# =============================================================================
# NasdaqAPIError
# =============================================================================


class TestNasdaqAPIError:
    """NasdaqAPIError (APIレスポンスエラー) のテスト。"""

    def test_正常系_全パラメータで初期化(self) -> None:
        """NasdaqAPIError が全パラメータで初期化されること。"""
        error = NasdaqAPIError(
            "API returned HTTP 500",
            url="https://api.nasdaq.com/api/screener/stocks",
            status_code=500,
            response_body='{"error": "Internal Server Error"}',
        )

        assert error.message == "API returned HTTP 500"
        assert error.url == "https://api.nasdaq.com/api/screener/stocks"
        assert error.status_code == 500
        assert error.response_body == '{"error": "Internal Server Error"}'

    def test_正常系_NasdaqErrorを継承している(self) -> None:
        """NasdaqAPIError が NasdaqError を継承していること。"""
        assert issubclass(NasdaqAPIError, NasdaqError)

        error = NasdaqAPIError(
            "api error",
            url="https://api.nasdaq.com/api/screener/stocks",
            status_code=400,
            response_body="Bad Request",
        )
        assert isinstance(error, NasdaqError)
        assert isinstance(error, Exception)

    def test_正常系_strでメッセージが表示される(self) -> None:
        """str() でエラーメッセージが表示されること。"""
        error = NasdaqAPIError(
            "API returned HTTP 403",
            url="https://api.nasdaq.com/api/screener/stocks",
            status_code=403,
            response_body="Forbidden",
        )

        assert "API returned HTTP 403" in str(error)

    def test_正常系_NasdaqErrorでキャッチできる(self) -> None:
        """NasdaqError でキャッチできること。"""
        with pytest.raises(NasdaqError):
            raise NasdaqAPIError(
                "API error",
                url="https://api.nasdaq.com/api/screener/stocks",
                status_code=500,
                response_body="error",
            )

    def test_正常系_HTTP4xxステータスコードで初期化可能(self) -> None:
        """HTTP 4xx ステータスコードで初期化できること。"""
        error = NasdaqAPIError(
            "Bad Request",
            url="https://api.nasdaq.com/api/screener/stocks",
            status_code=400,
            response_body="Bad Request",
        )

        assert error.status_code == 400

    def test_正常系_HTTP5xxステータスコードで初期化可能(self) -> None:
        """HTTP 5xx ステータスコードで初期化できること。"""
        error = NasdaqAPIError(
            "Internal Server Error",
            url="https://api.nasdaq.com/api/screener/stocks",
            status_code=500,
            response_body="Internal Server Error",
        )

        assert error.status_code == 500


# =============================================================================
# NasdaqRateLimitError
# =============================================================================


class TestNasdaqRateLimitError:
    """NasdaqRateLimitError (レートリミット) のテスト。"""

    def test_正常系_全パラメータで初期化(self) -> None:
        """NasdaqRateLimitError が全パラメータで初期化されること。"""
        error = NasdaqRateLimitError(
            "Rate limit exceeded",
            url="https://api.nasdaq.com/api/screener/stocks",
            retry_after=60,
        )

        assert error.message == "Rate limit exceeded"
        assert error.url == "https://api.nasdaq.com/api/screener/stocks"
        assert error.retry_after == 60

    def test_正常系_NasdaqErrorを継承している(self) -> None:
        """NasdaqRateLimitError が NasdaqError を継承していること。"""
        assert issubclass(NasdaqRateLimitError, NasdaqError)

        error = NasdaqRateLimitError(
            "rate limited",
            url="https://api.nasdaq.com/api/screener/stocks",
            retry_after=30,
        )
        assert isinstance(error, NasdaqError)
        assert isinstance(error, Exception)

    def test_正常系_strでメッセージが表示される(self) -> None:
        """str() でエラーメッセージが表示されること。"""
        error = NasdaqRateLimitError(
            "Too many requests, retry after 60s",
            url="https://api.nasdaq.com/api/screener/stocks",
            retry_after=60,
        )

        assert "Too many requests, retry after 60s" in str(error)

    def test_正常系_NasdaqErrorでキャッチできる(self) -> None:
        """NasdaqError でキャッチできること。"""
        with pytest.raises(NasdaqError):
            raise NasdaqRateLimitError(
                "rate limited",
                url="https://api.nasdaq.com/api/screener/stocks",
                retry_after=120,
            )

    def test_正常系_retry_afterがNoneでも初期化可能(self) -> None:
        """retry_after が None でも初期化できること。"""
        error = NasdaqRateLimitError(
            "rate limited",
            url="https://api.nasdaq.com/api/screener/stocks",
            retry_after=None,
        )

        assert error.retry_after is None

    def test_正常系_url属性がNoneでも初期化可能(self) -> None:
        """url が None でも初期化できること (リクエストURL不明の場合)。"""
        error = NasdaqRateLimitError(
            "rate limited",
            url=None,
            retry_after=60,
        )

        assert error.url is None
        assert error.retry_after == 60


# =============================================================================
# NasdaqParseError
# =============================================================================


class TestNasdaqParseError:
    """NasdaqParseError (パースエラー) のテスト。"""

    def test_正常系_全パラメータで初期化(self) -> None:
        """NasdaqParseError が全パラメータで初期化されること。"""
        error = NasdaqParseError(
            "Failed to parse stock screener response",
            raw_data='{"invalid": "json"}',
            field="rows",
        )

        assert error.message == "Failed to parse stock screener response"
        assert error.raw_data == '{"invalid": "json"}'
        assert error.field == "rows"

    def test_正常系_NasdaqErrorを継承している(self) -> None:
        """NasdaqParseError が NasdaqError を継承していること。"""
        assert issubclass(NasdaqParseError, NasdaqError)

        error = NasdaqParseError(
            "parse error",
            raw_data="bad data",
            field="ticker",
        )
        assert isinstance(error, NasdaqError)
        assert isinstance(error, Exception)

    def test_正常系_strでメッセージが表示される(self) -> None:
        """str() でエラーメッセージが表示されること。"""
        error = NasdaqParseError(
            "Unexpected response format",
            raw_data="not json",
            field="data",
        )

        assert "Unexpected response format" in str(error)

    def test_正常系_NasdaqErrorでキャッチできる(self) -> None:
        """NasdaqError でキャッチできること。"""
        with pytest.raises(NasdaqError):
            raise NasdaqParseError(
                "parse error",
                raw_data="bad",
                field="field",
            )

    def test_正常系_raw_dataがNoneでも初期化可能(self) -> None:
        """raw_data が None でも初期化できること。"""
        error = NasdaqParseError(
            "parse error",
            raw_data=None,
            field="rows",
        )

        assert error.raw_data is None
        assert error.field == "rows"

    def test_正常系_field属性がNoneでも初期化可能(self) -> None:
        """field が None でも初期化できること。"""
        error = NasdaqParseError(
            "parse error",
            raw_data="some data",
            field=None,
        )

        assert error.raw_data == "some data"
        assert error.field is None


# =============================================================================
# Exception Hierarchy
# =============================================================================


class TestExceptionHierarchy:
    """例外クラスの継承階層テスト。"""

    def test_正常系_全サブクラスがNasdaqErrorを継承(self) -> None:
        """全サブクラスが NasdaqError を継承していること。"""
        assert issubclass(NasdaqAPIError, NasdaqError)
        assert issubclass(NasdaqRateLimitError, NasdaqError)
        assert issubclass(NasdaqParseError, NasdaqError)

    def test_正常系_NasdaqErrorがExceptionを直接継承(self) -> None:
        """NasdaqError が Exception を直接継承していること。"""
        assert issubclass(NasdaqError, Exception)
        assert Exception in NasdaqError.__bases__

    def test_正常系_サブクラスはExceptionのインスタンスである(self) -> None:
        """サブクラスのインスタンスが Exception のインスタンスであること。"""
        api_err = NasdaqAPIError(
            "test",
            url="https://api.nasdaq.com/api/screener/stocks",
            status_code=500,
            response_body="error",
        )
        assert isinstance(api_err, Exception)

        rate_err = NasdaqRateLimitError(
            "test",
            url="https://api.nasdaq.com/api/screener/stocks",
            retry_after=60,
        )
        assert isinstance(rate_err, Exception)

        parse_err = NasdaqParseError(
            "test",
            raw_data="data",
            field="field",
        )
        assert isinstance(parse_err, Exception)


# =============================================================================
# Usage Patterns
# =============================================================================


class TestExceptionUsagePatterns:
    """例外クラスの使用パターンテスト。"""

    def test_正常系_try_exceptで適切にキャッチできる(self) -> None:
        """try-except で適切にキャッチできること。"""

        def fetch_stocks(url: str) -> None:
            raise NasdaqAPIError(
                f"Failed to fetch from {url}",
                url=url,
                status_code=500,
                response_body="Internal Server Error",
            )

        # 具体的な例外でキャッチ
        with pytest.raises(NasdaqAPIError) as exc_info:
            fetch_stocks("https://api.nasdaq.com/api/screener/stocks")

        assert exc_info.value.url == "https://api.nasdaq.com/api/screener/stocks"

        # 基底例外でキャッチ
        with pytest.raises(NasdaqError):
            fetch_stocks("https://api.nasdaq.com/api/screener/stocks")

    def test_正常系_原因チェーンが機能する(self) -> None:
        """例外の from チェーンが正しく機能すること。"""
        original = ConnectionError("Connection refused")

        try:
            raise NasdaqAPIError(
                "API request failed",
                url="https://api.nasdaq.com/api/screener/stocks",
                status_code=503,
                response_body="Service Unavailable",
            ) from original
        except NasdaqAPIError as e:
            assert e.__cause__ is original
            assert isinstance(e.__cause__, ConnectionError)

    def test_正常系_レートリミットのリトライパターン(self) -> None:
        """レートリミットエラーの retry_after を使用したリトライパターン。"""
        error = NasdaqRateLimitError(
            "Rate limit exceeded",
            url="https://api.nasdaq.com/api/screener/stocks",
            retry_after=30,
        )

        # retry_after 属性でリトライ待機時間を取得できること
        assert error.retry_after == 30

    def test_正常系_パースエラーのデバッグパターン(self) -> None:
        """パースエラーの raw_data と field を使用したデバッグパターン。"""
        raw = '{"data": {"rows": null}}'
        error = NasdaqParseError(
            "Expected list for rows field, got null",
            raw_data=raw,
            field="rows",
        )

        # raw_data と field でデバッグ情報にアクセスできること
        assert error.raw_data == raw
        assert error.field == "rows"


# =============================================================================
# Module Exports
# =============================================================================


class TestModuleExports:
    """__all__ エクスポートのテスト。"""

    def test_正常系_全クラスがエクスポートされている(self) -> None:
        """__all__ に全4クラスが含まれていること。"""
        from market.nasdaq import errors

        assert hasattr(errors, "__all__")
        expected = {
            "NasdaqError",
            "NasdaqAPIError",
            "NasdaqRateLimitError",
            "NasdaqParseError",
        }
        assert set(errors.__all__) == expected

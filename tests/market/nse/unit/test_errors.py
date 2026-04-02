"""Unit tests for market.nse.errors module.

NSE API エラークラスのテストスイート。
6つのエラークラス（NseError, NseAPIError, NseRateLimitError,
NseCookieError, NseParseError, NseValidationError）の動作を検証する。

Test TODO List:
- [x] NseError: base exception with message attribute
- [x] NseAPIError: API response error with url, status_code, response_body
- [x] NseRateLimitError: rate limit error with url, retry_after (float)
- [x] NseCookieError: cookie error with url (NSE-specific)
- [x] NseParseError: parse error with raw_data, field
- [x] NseValidationError: validation error with field, value
- [x] Exception hierarchy validation
- [x] Common usage patterns (try-except, raise, cause chaining)
- [x] __all__ exports
"""

import pytest

from market.nse.errors import (
    NseAPIError,
    NseCookieError,
    NseError,
    NseParseError,
    NseRateLimitError,
    NseValidationError,
)

# =============================================================================
# NseError (base exception)
# =============================================================================


class TestNseError:
    """NseError 基底例外クラスのテスト。"""

    def test_正常系_メッセージで初期化できる(self) -> None:
        """NseError がメッセージで初期化されること。"""
        error = NseError("NSE API operation failed")

        assert error.message == "NSE API operation failed"
        assert str(error) == "NSE API operation failed"

    def test_正常系_Exceptionを直接継承している(self) -> None:
        """NseError が Exception を直接継承していること。"""
        assert issubclass(NseError, Exception)
        assert Exception in NseError.__bases__

    def test_正常系_raiseで例外として使用可能(self) -> None:
        """raise で例外として使用できること。"""
        with pytest.raises(NseError, match="test error"):
            raise NseError("test error")

    def test_正常系_message属性にアクセスできる(self) -> None:
        """message 属性が正しく設定されること。"""
        error = NseError("some error message")

        assert hasattr(error, "message")
        assert error.message == "some error message"


# =============================================================================
# NseAPIError
# =============================================================================


class TestNseAPIError:
    """NseAPIError (APIレスポンスエラー) のテスト。"""

    def test_正常系_全パラメータで初期化(self) -> None:
        """NseAPIError が全パラメータで初期化されること。"""
        error = NseAPIError(
            "API returned HTTP 500",
            url="https://www.nseindia.com/api/equity-stockIndices",
            status_code=500,
            response_body='{"error": "Internal Server Error"}',
        )

        assert error.message == "API returned HTTP 500"
        assert error.url == "https://www.nseindia.com/api/equity-stockIndices"
        assert error.status_code == 500
        assert error.response_body == '{"error": "Internal Server Error"}'

    def test_正常系_NseErrorを継承している(self) -> None:
        """NseAPIError が NseError を継承していること。"""
        assert issubclass(NseAPIError, NseError)

        error = NseAPIError(
            "api error",
            url="https://www.nseindia.com/api/equity-stockIndices",
            status_code=400,
            response_body="Bad Request",
        )
        assert isinstance(error, NseError)
        assert isinstance(error, Exception)

    def test_正常系_strでメッセージが表示される(self) -> None:
        """str() でエラーメッセージが表示されること。"""
        error = NseAPIError(
            "API returned HTTP 403",
            url="https://www.nseindia.com/api/equity-stockIndices",
            status_code=403,
            response_body="Forbidden",
        )

        assert "API returned HTTP 403" in str(error)

    def test_正常系_NseErrorでキャッチできる(self) -> None:
        """NseError でキャッチできること。"""
        with pytest.raises(NseError):
            raise NseAPIError(
                "API error",
                url="https://www.nseindia.com/api/equity-stockIndices",
                status_code=500,
                response_body="error",
            )

    def test_正常系_HTTP4xxステータスコードで初期化可能(self) -> None:
        """HTTP 4xx ステータスコードで初期化できること。"""
        error = NseAPIError(
            "Bad Request",
            url="https://www.nseindia.com/api/equity-stockIndices",
            status_code=400,
            response_body="Bad Request",
        )

        assert error.status_code == 400

    def test_正常系_HTTP5xxステータスコードで初期化可能(self) -> None:
        """HTTP 5xx ステータスコードで初期化できること。"""
        error = NseAPIError(
            "Internal Server Error",
            url="https://www.nseindia.com/api/equity-stockIndices",
            status_code=500,
            response_body="Internal Server Error",
        )

        assert error.status_code == 500


# =============================================================================
# NseRateLimitError
# =============================================================================


class TestNseRateLimitError:
    """NseRateLimitError (レートリミット) のテスト。"""

    def test_正常系_全パラメータで初期化(self) -> None:
        """NseRateLimitError が全パラメータで初期化されること。"""
        error = NseRateLimitError(
            "Rate limit exceeded",
            url="https://www.nseindia.com/api/equity-stockIndices",
            retry_after=60.0,
        )

        assert error.message == "Rate limit exceeded"
        assert error.url == "https://www.nseindia.com/api/equity-stockIndices"
        assert error.retry_after == 60.0

    def test_正常系_NseErrorを継承している(self) -> None:
        """NseRateLimitError が NseError を継承していること。"""
        assert issubclass(NseRateLimitError, NseError)

        error = NseRateLimitError(
            "rate limited",
            url="https://www.nseindia.com/api/equity-stockIndices",
            retry_after=30.0,
        )
        assert isinstance(error, NseError)
        assert isinstance(error, Exception)

    def test_正常系_strでメッセージが表示される(self) -> None:
        """str() でエラーメッセージが表示されること。"""
        error = NseRateLimitError(
            "Too many requests, retry after 60s",
            url="https://www.nseindia.com/api/equity-stockIndices",
            retry_after=60.0,
        )

        assert "Too many requests, retry after 60s" in str(error)

    def test_正常系_NseErrorでキャッチできる(self) -> None:
        """NseError でキャッチできること。"""
        with pytest.raises(NseError):
            raise NseRateLimitError(
                "rate limited",
                url="https://www.nseindia.com/api/equity-stockIndices",
                retry_after=120.0,
            )

    def test_正常系_retry_afterがNoneでも初期化可能(self) -> None:
        """retry_after が None でも初期化できること。"""
        error = NseRateLimitError(
            "rate limited",
            url="https://www.nseindia.com/api/equity-stockIndices",
            retry_after=None,
        )

        assert error.retry_after is None

    def test_正常系_url属性がNoneでも初期化可能(self) -> None:
        """url が None でも初期化できること (リクエストURL不明の場合)。"""
        error = NseRateLimitError(
            "rate limited",
            url=None,
            retry_after=60.0,
        )

        assert error.url is None
        assert error.retry_after == 60.0

    def test_正常系_retry_afterがfloat型(self) -> None:
        """retry_after が float 型で格納されること。"""
        error = NseRateLimitError(
            "rate limited",
            url="https://www.nseindia.com/api/equity-stockIndices",
            retry_after=45.5,
        )

        assert isinstance(error.retry_after, float)
        assert error.retry_after == 45.5


# =============================================================================
# NseCookieError (NSE-specific)
# =============================================================================


class TestNseCookieError:
    """NseCookieError (クッキー期限切れ) のテスト。NSE固有の例外。"""

    def test_正常系_全パラメータで初期化(self) -> None:
        """NseCookieError が全パラメータで初期化されること。"""
        error = NseCookieError(
            "NSE session cookie expired. Re-initialise the session.",
            url="https://www.nseindia.com/api/equity-stockIndices",
        )

        assert error.message == "NSE session cookie expired. Re-initialise the session."
        assert error.url == "https://www.nseindia.com/api/equity-stockIndices"

    def test_正常系_NseErrorを継承している(self) -> None:
        """NseCookieError が NseError を継承していること。"""
        assert issubclass(NseCookieError, NseError)

        error = NseCookieError(
            "cookie error",
            url="https://www.nseindia.com/api/equity-stockIndices",
        )
        assert isinstance(error, NseError)
        assert isinstance(error, Exception)

    def test_正常系_strでメッセージが表示される(self) -> None:
        """str() でエラーメッセージが表示されること。"""
        error = NseCookieError(
            "Cookie expired",
            url="https://www.nseindia.com/api/equity-stockIndices",
        )

        assert "Cookie expired" in str(error)

    def test_正常系_NseErrorでキャッチできる(self) -> None:
        """NseError でキャッチできること。"""
        with pytest.raises(NseError):
            raise NseCookieError(
                "cookie expired",
                url="https://www.nseindia.com/api/equity-stockIndices",
            )

    def test_正常系_url属性がNoneでも初期化可能(self) -> None:
        """url が None でも初期化できること。"""
        error = NseCookieError(
            "cookie expired",
            url=None,
        )

        assert error.url is None

    def test_正常系_NseAPIErrorとは別クラス(self) -> None:
        """NseCookieError が NseAPIError とは無関係のクラスであること。"""
        assert not issubclass(NseCookieError, NseAPIError)
        assert not issubclass(NseAPIError, NseCookieError)


# =============================================================================
# NseParseError
# =============================================================================


class TestNseParseError:
    """NseParseError (パースエラー) のテスト。"""

    def test_正常系_全パラメータで初期化(self) -> None:
        """NseParseError が全パラメータで初期化されること。"""
        error = NseParseError(
            "Failed to parse equity indices response",
            raw_data='{"data": null}',
            field="data",
        )

        assert error.message == "Failed to parse equity indices response"
        assert error.raw_data == '{"data": null}'
        assert error.field == "data"

    def test_正常系_NseErrorを継承している(self) -> None:
        """NseParseError が NseError を継承していること。"""
        assert issubclass(NseParseError, NseError)

        error = NseParseError(
            "parse error",
            raw_data="bad data",
            field="lastPrice",
        )
        assert isinstance(error, NseError)
        assert isinstance(error, Exception)

    def test_正常系_strでメッセージが表示される(self) -> None:
        """str() でエラーメッセージが表示されること。"""
        error = NseParseError(
            "Unexpected response format",
            raw_data="not json",
            field="data",
        )

        assert "Unexpected response format" in str(error)

    def test_正常系_NseErrorでキャッチできる(self) -> None:
        """NseError でキャッチできること。"""
        with pytest.raises(NseError):
            raise NseParseError(
                "parse error",
                raw_data="bad",
                field="field",
            )

    def test_正常系_raw_dataがNoneでも初期化可能(self) -> None:
        """raw_data が None でも初期化できること。"""
        error = NseParseError(
            "parse error",
            raw_data=None,
            field="data",
        )

        assert error.raw_data is None
        assert error.field == "data"

    def test_正常系_field属性がNoneでも初期化可能(self) -> None:
        """field が None でも初期化できること。"""
        error = NseParseError(
            "parse error",
            raw_data="some data",
            field=None,
        )

        assert error.raw_data == "some data"
        assert error.field is None


# =============================================================================
# NseValidationError
# =============================================================================


class TestNseValidationError:
    """NseValidationError (バリデーションエラー) のテスト。"""

    def test_正常系_全パラメータで初期化(self) -> None:
        """NseValidationError が全パラメータで初期化されること。"""
        error = NseValidationError(
            "Invalid symbol: must be a non-empty uppercase string",
            field="symbol",
            value="",
        )

        assert error.message == "Invalid symbol: must be a non-empty uppercase string"
        assert error.field == "symbol"
        assert error.value == ""

    def test_正常系_NseErrorを継承している(self) -> None:
        """NseValidationError が NseError を継承していること。"""
        assert issubclass(NseValidationError, NseError)

        error = NseValidationError(
            "validation error",
            field="index",
            value="INVALID",
        )
        assert isinstance(error, NseError)
        assert isinstance(error, Exception)

    def test_正常系_strでメッセージが表示される(self) -> None:
        """str() でエラーメッセージが表示されること。"""
        error = NseValidationError(
            "Invalid index name",
            field="index",
            value="INVALID",
        )

        assert "Invalid index name" in str(error)

    def test_正常系_NseErrorでキャッチできる(self) -> None:
        """NseError でキャッチできること。"""
        with pytest.raises(NseError):
            raise NseValidationError(
                "validation error",
                field="symbol",
                value="abc",
            )

    def test_正常系_valueにNoneを設定可能(self) -> None:
        """value に None を設定できること。"""
        error = NseValidationError(
            "Missing required field",
            field="symbol",
            value=None,
        )

        assert error.value is None

    def test_正常系_valueに様々な型を設定可能(self) -> None:
        """value に様々な型（int, str, list）を設定できること。"""
        error_int = NseValidationError("invalid", field="count", value=42)
        assert error_int.value == 42

        error_str = NseValidationError("invalid", field="symbol", value="bad")
        assert error_str.value == "bad"

        error_list = NseValidationError("invalid", field="symbols", value=[1, 2])
        assert error_list.value == [1, 2]


# =============================================================================
# Exception Hierarchy
# =============================================================================


class TestExceptionHierarchy:
    """例外クラスの継承階層テスト。"""

    def test_正常系_全サブクラスがNseErrorを継承(self) -> None:
        """全サブクラスが NseError を継承していること。"""
        assert issubclass(NseAPIError, NseError)
        assert issubclass(NseRateLimitError, NseError)
        assert issubclass(NseCookieError, NseError)
        assert issubclass(NseParseError, NseError)
        assert issubclass(NseValidationError, NseError)

    def test_正常系_NseErrorがExceptionを直接継承(self) -> None:
        """NseError が Exception を直接継承していること。"""
        assert issubclass(NseError, Exception)
        assert Exception in NseError.__bases__

    def test_正常系_サブクラスはExceptionのインスタンスである(self) -> None:
        """サブクラスのインスタンスが Exception のインスタンスであること。"""
        api_err = NseAPIError(
            "test",
            url="https://www.nseindia.com/api/equity-stockIndices",
            status_code=500,
            response_body="error",
        )
        assert isinstance(api_err, Exception)

        rate_err = NseRateLimitError(
            "test",
            url="https://www.nseindia.com/api/equity-stockIndices",
            retry_after=60.0,
        )
        assert isinstance(rate_err, Exception)

        cookie_err = NseCookieError(
            "test",
            url="https://www.nseindia.com/api/equity-stockIndices",
        )
        assert isinstance(cookie_err, Exception)

        parse_err = NseParseError(
            "test",
            raw_data="data",
            field="field",
        )
        assert isinstance(parse_err, Exception)

        val_err = NseValidationError(
            "test",
            field="symbol",
            value="bad",
        )
        assert isinstance(val_err, Exception)

    def test_正常系_クラス間の継承関係が独立している(self) -> None:
        """サブクラス間は互いに継承関係を持たないこと。"""
        assert not issubclass(NseAPIError, NseRateLimitError)
        assert not issubclass(NseRateLimitError, NseCookieError)
        assert not issubclass(NseCookieError, NseAPIError)
        assert not issubclass(NseParseError, NseValidationError)
        assert not issubclass(NseValidationError, NseParseError)


# =============================================================================
# Usage Patterns
# =============================================================================


class TestExceptionUsagePatterns:
    """例外クラスの使用パターンテスト。"""

    def test_正常系_try_exceptで適切にキャッチできる(self) -> None:
        """try-except で適切にキャッチできること。"""

        def fetch_indices(url: str) -> None:
            raise NseAPIError(
                f"Failed to fetch from {url}",
                url=url,
                status_code=500,
                response_body="Internal Server Error",
            )

        with pytest.raises(NseAPIError) as exc_info:
            fetch_indices("https://www.nseindia.com/api/equity-stockIndices")

        assert exc_info.value.url == "https://www.nseindia.com/api/equity-stockIndices"

        with pytest.raises(NseError):
            fetch_indices("https://www.nseindia.com/api/equity-stockIndices")

    def test_正常系_原因チェーンが機能する(self) -> None:
        """例外の from チェーンが正しく機能すること。"""
        original = ConnectionError("Connection refused")

        try:
            raise NseAPIError(
                "API request failed",
                url="https://www.nseindia.com/api/equity-stockIndices",
                status_code=503,
                response_body="Service Unavailable",
            ) from original
        except NseAPIError as e:
            assert e.__cause__ is original
            assert isinstance(e.__cause__, ConnectionError)

    def test_正常系_クッキーエラーのリフレッシュパターン(self) -> None:
        """NseCookieError でセッション再初期化のパターン。"""
        error = NseCookieError(
            "NSE session cookie expired. Re-initialise the session.",
            url="https://www.nseindia.com/api/equity-stockIndices",
        )

        assert "Re-initialise" in error.message
        assert error.url is not None

    def test_正常系_レートリミットのリトライパターン(self) -> None:
        """レートリミットエラーの retry_after を使用したリトライパターン。"""
        error = NseRateLimitError(
            "Rate limit exceeded",
            url="https://www.nseindia.com/api/equity-stockIndices",
            retry_after=30.0,
        )

        assert error.retry_after == 30.0

    def test_正常系_パースエラーのデバッグパターン(self) -> None:
        """パースエラーの raw_data と field を使用したデバッグパターン。"""
        raw = '{"data": null}'
        error = NseParseError(
            "Expected list for data field, got null",
            raw_data=raw,
            field="data",
        )

        assert error.raw_data == raw
        assert error.field == "data"

    def test_正常系_バリデーションエラーのデバッグパターン(self) -> None:
        """バリデーションエラーの field と value を使用したデバッグパターン。"""
        error = NseValidationError(
            "Expected non-empty string for symbol",
            field="symbol",
            value="",
        )

        assert error.field == "symbol"
        assert error.value == ""


# =============================================================================
# Module Exports
# =============================================================================


class TestModuleExports:
    """__all__ エクスポートのテスト。"""

    def test_正常系_全クラスがエクスポートされている(self) -> None:
        """__all__ に全6クラスが含まれていること。"""
        from market.nse import errors

        assert hasattr(errors, "__all__")
        expected = {
            "NseError",
            "NseAPIError",
            "NseRateLimitError",
            "NseCookieError",
            "NseParseError",
            "NseValidationError",
        }
        assert set(errors.__all__) == expected

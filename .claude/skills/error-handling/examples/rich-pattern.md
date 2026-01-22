# リッチパターン（Market Analysis 方式）

外部 API 連携や詳細なエラー情報が必要な場合のパターンです。

## 特徴

- **エラーコード（Enum）による分類**: プログラム的な判定が可能
- **details フィールド**: 構造化されたコンテキスト情報
- **cause による例外チェーン**: 元の例外を保持
- **to_dict() でシリアライズ**: JSON レスポンスに変換可能

## いつ使うか

- 外部 API との連携
- REST API でエラーレスポンスを返す
- エラーの統計・分析が必要
- 詳細なデバッグ情報が必要

## 実装例

### errors.py

```python
"""Custom exception classes for the package.

This module provides a hierarchy of exception classes for handling
various error conditions with structured error information.
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Error codes for categorizing exceptions.

    str を継承することで JSON シリアライズが容易になります。
    """

    # 汎用
    UNKNOWN = "UNKNOWN"

    # ネットワーク関連
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"

    # API 関連
    API_ERROR = "API_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    AUTH_FAILED = "AUTH_FAILED"

    # データ関連
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    DATA_INVALID = "DATA_INVALID"

    # バリデーション関連
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_FORMAT = "INVALID_FORMAT"


class PackageError(Exception):
    """Base exception for all package errors.

    Parameters
    ----------
    message : str
        Human-readable error message
    code : ErrorCode
        Error code for programmatic handling
    details : dict[str, Any] | None
        Additional context about the error
    cause : Exception | None
        The underlying exception that caused this error

    Examples
    --------
    >>> try:
    ...     raise PackageError(
    ...         "Failed to process data",
    ...         code=ErrorCode.DATA_INVALID,
    ...         details={"field": "date"},
    ...     )
    ... except PackageError as e:
    ...     print(e.code)
    DATA_INVALID
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        """Return a formatted error message."""
        parts = [f"[{self.code.value}] {self.message}"]

        if self.details:
            details_str = ", ".join(
                f"{k}={v!r}" for k, v in self.details.items()
            )
            parts.append(f"Details: {details_str}")

        if self.cause:
            parts.append(
                f"Caused by: {type(self.cause).__name__}: {self.cause}"
            )

        return " | ".join(parts)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"details={self.details!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the error
        """
        result: dict[str, Any] = {
            "error_type": self.__class__.__name__,
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }

        if self.cause:
            result["cause"] = {
                "type": type(self.cause).__name__,
                "message": str(self.cause),
            }

        return result


class DataFetchError(PackageError):
    """Exception raised when data fetching fails.

    Parameters
    ----------
    message : str
        Human-readable error message
    symbol : str | None
        The symbol that failed to fetch
    source : str | None
        The data source that was used
    code : ErrorCode
        Error code (defaults to API_ERROR)
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception
    """

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        source: str | None = None,
        code: ErrorCode = ErrorCode.API_ERROR,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if symbol:
            details["symbol"] = symbol
        if source:
            details["source"] = source

        super().__init__(message, code=code, details=details, cause=cause)
        self.symbol = symbol
        self.source = source


class ValidationError(PackageError):
    """Exception raised when input validation fails.

    Parameters
    ----------
    message : str
        Human-readable error message
    field : str | None
        The field that failed validation
    value : Any
        The invalid value
    code : ErrorCode
        Error code (defaults to INVALID_PARAMETER)
    details : dict[str, Any] | None
        Additional context
    cause : Exception | None
        The underlying exception
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        code: ErrorCode = ErrorCode.INVALID_PARAMETER,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = repr(value)

        super().__init__(message, code=code, details=details, cause=cause)
        self.field = field
        self.value = value


class RateLimitError(DataFetchError):
    """Exception raised when API rate limit is exceeded.

    Parameters
    ----------
    message : str
        Human-readable error message
    retry_after : int | None
        Seconds to wait before retrying
    source : str | None
        The data source
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        source: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = details or {}
        if retry_after:
            details["retry_after_seconds"] = retry_after

        super().__init__(
            message,
            symbol=None,
            source=source,
            code=ErrorCode.RATE_LIMIT,
            details=details,
            cause=cause,
        )
        self.retry_after = retry_after


__all__ = [
    "ErrorCode",
    "PackageError",
    "DataFetchError",
    "ValidationError",
    "RateLimitError",
]
```

### 使用例

```python
from my_package.errors import (
    DataFetchError,
    ValidationError,
    RateLimitError,
    ErrorCode,
)


def fetch_stock_data(symbol: str) -> DataFrame:
    """株価データを取得する

    Raises
    ------
    ValidationError
        symbol が不正な場合
    DataFetchError
        データ取得に失敗した場合
    RateLimitError
        レート制限に達した場合
    """
    if not symbol or not symbol.isalpha():
        raise ValidationError(
            f"Invalid symbol format: {symbol}",
            field="symbol",
            value=symbol,
            code=ErrorCode.INVALID_FORMAT,
        )

    try:
        return api_client.fetch(symbol)
    except RateLimitExceeded as e:
        raise RateLimitError(
            f"Rate limit exceeded for {symbol}",
            retry_after=e.retry_after,
            source="yfinance",
            cause=e,
        ) from e
    except APIError as e:
        raise DataFetchError(
            f"Failed to fetch data for {symbol}",
            symbol=symbol,
            source="yfinance",
            code=ErrorCode.API_ERROR,
            cause=e,
        ) from e
```

### REST API でのエラーレスポンス

```python
from fastapi import FastAPI, HTTPException
from my_package.errors import PackageError

app = FastAPI()


@app.exception_handler(PackageError)
async def package_error_handler(request, exc: PackageError):
    """パッケージ例外を JSON レスポンスに変換"""
    return JSONResponse(
        status_code=get_status_code(exc.code),
        content=exc.to_dict(),
    )


def get_status_code(code: ErrorCode) -> int:
    """ErrorCode から HTTP ステータスコードを決定"""
    mapping = {
        ErrorCode.INVALID_PARAMETER: 400,
        ErrorCode.INVALID_FORMAT: 400,
        ErrorCode.AUTH_FAILED: 401,
        ErrorCode.DATA_NOT_FOUND: 404,
        ErrorCode.RATE_LIMIT: 429,
        ErrorCode.API_ERROR: 502,
        ErrorCode.TIMEOUT: 504,
    }
    return mapping.get(code, 500)
```

### エラーレスポンス例

```json
{
    "error_type": "DataFetchError",
    "code": "API_ERROR",
    "message": "Failed to fetch data for AAPL",
    "details": {
        "symbol": "AAPL",
        "source": "yfinance"
    },
    "cause": {
        "type": "ConnectionError",
        "message": "Connection refused"
    }
}
```

## テスト例

```python
import pytest
from my_package.errors import (
    DataFetchError,
    ValidationError,
    ErrorCode,
)


class TestDataFetchError:
    def test_正常系_エラーコードが設定される(self):
        error = DataFetchError(
            "Failed to fetch",
            symbol="AAPL",
            source="yfinance",
            code=ErrorCode.NETWORK_ERROR,
        )

        assert error.code == ErrorCode.NETWORK_ERROR
        assert error.symbol == "AAPL"
        assert error.source == "yfinance"

    def test_正常系_to_dictでシリアライズできる(self):
        error = DataFetchError(
            "Failed to fetch",
            symbol="AAPL",
        )

        result = error.to_dict()

        assert result["error_type"] == "DataFetchError"
        assert result["code"] == "API_ERROR"
        assert result["details"]["symbol"] == "AAPL"

    def test_正常系_causeが保持される(self):
        original = ValueError("Original error")
        error = DataFetchError(
            "Wrapped error",
            cause=original,
        )

        assert error.cause is original
        assert "ValueError" in error.to_dict()["cause"]["type"]
```

## 参照実装

このプロジェクトでの参照実装：

- `src/market_analysis/errors.py`: Market Analysis パッケージの例外定義

## リッチパターンの利点

1. **プログラム的な分類**: ErrorCode で条件分岐が可能
2. **構造化された情報**: details で任意のコンテキストを保持
3. **シリアライズ対応**: to_dict() で JSON 変換が容易
4. **例外チェーン**: cause で元の例外を保持
5. **統一された出力**: __str__ で一貫したフォーマット

## いつシンプルパターンに戻すべきか

以下の条件が当てはまる場合は、シンプルパターンで十分：

- [ ] エラーのシリアライズが不要
- [ ] エラーコードによる分類が不要
- [ ] 詳細なコンテキスト情報が不要
- [ ] 内部ライブラリとしてのみ使用

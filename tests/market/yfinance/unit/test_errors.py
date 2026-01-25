"""Unit tests for market.yfinance.errors module."""


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_正常系_主要なエラーコードが定義されている(self) -> None:
        """必要なエラーコードが全て定義されていることを確認。"""
        from market.yfinance.errors import ErrorCode

        assert hasattr(ErrorCode, "UNKNOWN")
        assert hasattr(ErrorCode, "API_ERROR")
        assert hasattr(ErrorCode, "INVALID_SYMBOL")
        assert hasattr(ErrorCode, "INVALID_PARAMETER")
        assert hasattr(ErrorCode, "DATA_NOT_FOUND")

    def test_正常系_str型を継承(self) -> None:
        """ErrorCode が str を継承していることを確認。"""
        from market.yfinance.errors import ErrorCode

        assert isinstance(ErrorCode.API_ERROR, str)


class TestMarketError:
    """Tests for MarketError base exception."""

    def test_正常系_基本的な初期化(self) -> None:
        """MarketError が基本パラメータで初期化されることを確認。"""
        from market.yfinance.errors import ErrorCode, MarketError

        error = MarketError("Test error")
        assert error.message == "Test error"
        assert error.code == ErrorCode.UNKNOWN

    def test_正常系_エラーコード付きで初期化(self) -> None:
        """MarketError がエラーコード付きで初期化されることを確認。"""
        from market.yfinance.errors import ErrorCode, MarketError

        error = MarketError("Test error", code=ErrorCode.API_ERROR)
        assert error.code == ErrorCode.API_ERROR

    def test_正常系_詳細情報付きで初期化(self) -> None:
        """MarketError が詳細情報付きで初期化されることを確認。"""
        from market.yfinance.errors import MarketError

        error = MarketError("Test error", details={"key": "value"})
        assert error.details == {"key": "value"}

    def test_正常系_原因例外付きで初期化(self) -> None:
        """MarketError が原因例外付きで初期化されることを確認。"""
        from market.yfinance.errors import MarketError

        cause = ValueError("Original error")
        error = MarketError("Test error", cause=cause)
        assert error.cause == cause

    def test_正常系_to_dictメソッド(self) -> None:
        """MarketError.to_dict() が正しく動作することを確認。"""
        from market.yfinance.errors import ErrorCode, MarketError

        error = MarketError("Test error", code=ErrorCode.API_ERROR)
        result = error.to_dict()

        assert result["message"] == "Test error"
        assert result["code"] == "API_ERROR"


class TestDataFetchError:
    """Tests for DataFetchError exception."""

    def test_正常系_シンボル付きで初期化(self) -> None:
        """DataFetchError がシンボル情報付きで初期化されることを確認。"""
        from market.yfinance.errors import DataFetchError

        error = DataFetchError("Fetch failed", symbol="AAPL")
        assert error.symbol == "AAPL"
        assert "AAPL" in error.details.get("symbol", "")

    def test_正常系_ソース付きで初期化(self) -> None:
        """DataFetchError がソース情報付きで初期化されることを確認。"""
        from market.yfinance.errors import DataFetchError

        error = DataFetchError("Fetch failed", source="yfinance")
        assert error.source == "yfinance"

    def test_正常系_フル情報で初期化(self) -> None:
        """DataFetchError が全情報付きで初期化されることを確認。"""
        from market.yfinance.errors import DataFetchError, ErrorCode

        cause = Exception("API timeout")
        error = DataFetchError(
            "Fetch failed",
            symbol="AAPL",
            source="yfinance",
            code=ErrorCode.API_ERROR,
            cause=cause,
        )

        assert error.symbol == "AAPL"
        assert error.source == "yfinance"
        assert error.code == ErrorCode.API_ERROR
        assert error.cause == cause


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_正常系_フィールド情報付きで初期化(self) -> None:
        """ValidationError がフィールド情報付きで初期化されることを確認。"""
        from market.yfinance.errors import ValidationError

        error = ValidationError("Invalid value", field="symbols")
        assert error.field == "symbols"

    def test_正常系_値付きで初期化(self) -> None:
        """ValidationError が値付きで初期化されることを確認。"""
        from market.yfinance.errors import ValidationError

        error = ValidationError("Invalid value", field="symbols", value=[])
        assert error.value == []

    def test_正常系_デフォルトエラーコードがINVALID_PARAMETER(self) -> None:
        """ValidationError のデフォルトエラーコードが INVALID_PARAMETER であることを確認。"""
        from market.yfinance.errors import ErrorCode, ValidationError

        error = ValidationError("Invalid value")
        assert error.code == ErrorCode.INVALID_PARAMETER

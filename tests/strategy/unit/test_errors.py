"""Unit tests for strategy.errors module.

strategy パッケージのエラー・警告クラスのテスト。
TDDのRedフェーズとして、実装前に失敗するテストを記述。
"""

import warnings

import pytest

from strategy.errors import (
    ConfigurationError,
    DataProviderError,
    DataWarning,
    InsufficientDataError,
    InvalidTickerError,
    NormalizationWarning,
    StrategyError,
    StrategyWarning,
    ValidationError,
)


class TestStrategyError:
    """StrategyError 基底クラスのテスト."""

    def test_正常系_メッセージのみで初期化できる(self) -> None:
        """メッセージのみを指定してStrategyErrorを作成できることを確認."""
        error = StrategyError("Test error message")

        assert error.message == "Test error message"
        assert error.code is None
        assert error.cause is None

    def test_正常系_全属性を指定して初期化できる(self) -> None:
        """message, code, causeを全て指定してStrategyErrorを作成できることを確認."""
        cause = ValueError("Original error")
        error = StrategyError(
            message="Test error message",
            code="TEST_001",
            cause=cause,
        )

        assert error.message == "Test error message"
        assert error.code == "TEST_001"
        assert error.cause is cause

    def test_正常系_Exceptionを継承している(self) -> None:
        """StrategyErrorがExceptionを継承していることを確認."""
        error = StrategyError("Test error")

        assert isinstance(error, Exception)

    def test_正常系_raiseとcatchが正しく動作する(self) -> None:
        """StrategyErrorをraiseしてcatchできることを確認."""
        with pytest.raises(StrategyError) as exc_info:
            raise StrategyError("Test error", code="ERR_001")

        assert exc_info.value.message == "Test error"
        assert exc_info.value.code == "ERR_001"

    def test_正常系_strでメッセージが取得できる(self) -> None:
        """str()でエラーメッセージが取得できることを確認."""
        error = StrategyError("Test error message")

        assert "Test error message" in str(error)


class TestDataProviderError:
    """DataProviderError のテスト."""

    def test_正常系_StrategyErrorを継承している(self) -> None:
        """DataProviderErrorがStrategyErrorを継承していることを確認."""
        error = DataProviderError("Data provider failed")

        assert isinstance(error, StrategyError)
        assert isinstance(error, Exception)

    def test_正常系_メッセージで初期化できる(self) -> None:
        """メッセージを指定してDataProviderErrorを作成できることを確認."""
        error = DataProviderError("Failed to fetch data from provider")

        assert error.message == "Failed to fetch data from provider"

    def test_正常系_codeを指定できる(self) -> None:
        """codeを指定してDataProviderErrorを作成できることを確認."""
        error = DataProviderError(
            message="Provider connection failed",
            code="PROVIDER_001",
        )

        assert error.code == "PROVIDER_001"

    def test_正常系_causeを指定できる(self) -> None:
        """causeを指定してDataProviderErrorを作成できることを確認."""
        original = ConnectionError("Network unreachable")
        error = DataProviderError(
            message="Provider connection failed",
            cause=original,
        )

        assert error.cause is original


class TestInvalidTickerError:
    """InvalidTickerError のテスト."""

    def test_正常系_StrategyErrorを継承している(self) -> None:
        """InvalidTickerErrorがStrategyErrorを継承していることを確認."""
        error = InvalidTickerError("Invalid ticker")

        assert isinstance(error, StrategyError)

    def test_正常系_無効なティッカーでエラーを作成できる(self) -> None:
        """無効なティッカーシンボルを指定してエラーを作成できることを確認."""
        error = InvalidTickerError("Invalid ticker symbol: XXXXX")

        assert "XXXXX" in error.message

    def test_正常系_codeを指定できる(self) -> None:
        """codeを指定してInvalidTickerErrorを作成できることを確認."""
        error = InvalidTickerError(
            message="Ticker not found",
            code="TICKER_001",
        )

        assert error.code == "TICKER_001"


class TestInsufficientDataError:
    """InsufficientDataError のテスト."""

    def test_正常系_StrategyErrorを継承している(self) -> None:
        """InsufficientDataErrorがStrategyErrorを継承していることを確認."""
        error = InsufficientDataError("Insufficient data")

        assert isinstance(error, StrategyError)

    def test_正常系_データ不足エラーを作成できる(self) -> None:
        """データ不足を示すエラーを作成できることを確認."""
        error = InsufficientDataError(
            message="Need at least 200 data points, got 50",
        )

        assert "200" in error.message
        assert "50" in error.message

    def test_正常系_codeとcauseを指定できる(self) -> None:
        """code, causeを指定してInsufficientDataErrorを作成できることを確認."""
        cause = ValueError("Empty dataset")
        error = InsufficientDataError(
            message="Insufficient data for analysis",
            code="DATA_001",
            cause=cause,
        )

        assert error.code == "DATA_001"
        assert error.cause is cause


class TestConfigurationError:
    """ConfigurationError のテスト."""

    def test_正常系_StrategyErrorを継承している(self) -> None:
        """ConfigurationErrorがStrategyErrorを継承していることを確認."""
        error = ConfigurationError("Configuration error")

        assert isinstance(error, StrategyError)

    def test_正常系_設定エラーを作成できる(self) -> None:
        """設定関連のエラーを作成できることを確認."""
        error = ConfigurationError(
            message="Invalid configuration: missing required field 'api_key'",
        )

        assert "api_key" in error.message

    def test_正常系_全属性を指定できる(self) -> None:
        """message, code, causeを全て指定できることを確認."""
        cause = KeyError("api_key")
        error = ConfigurationError(
            message="Configuration validation failed",
            code="CONFIG_001",
            cause=cause,
        )

        assert error.message == "Configuration validation failed"
        assert error.code == "CONFIG_001"
        assert error.cause is cause


class TestValidationError:
    """ValidationError のテスト."""

    def test_正常系_StrategyErrorを継承している(self) -> None:
        """ValidationErrorがStrategyErrorを継承していることを確認."""
        error = ValidationError("Validation failed")

        assert isinstance(error, StrategyError)

    def test_正常系_検証エラーを作成できる(self) -> None:
        """入力値の検証エラーを作成できることを確認."""
        error = ValidationError(
            message="Expected positive number, got -5",
        )

        assert "-5" in error.message

    def test_正常系_codeを指定できる(self) -> None:
        """codeを指定してValidationErrorを作成できることを確認."""
        error = ValidationError(
            message="Invalid date range",
            code="VALIDATION_001",
        )

        assert error.code == "VALIDATION_001"

    def test_正常系_raiseとcatchが正しく動作する(self) -> None:
        """ValidationErrorをraiseしてcatchできることを確認."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Invalid input", code="VAL_001")

        assert exc_info.value.message == "Invalid input"


class TestStrategyWarning:
    """StrategyWarning 基底警告クラスのテスト."""

    def test_正常系_UserWarningを継承している(self) -> None:
        """StrategyWarningがUserWarningを継承していることを確認."""
        warning = StrategyWarning("Test warning")

        assert isinstance(warning, UserWarning)

    def test_正常系_warningsで発行できる(self) -> None:
        """warnings.warnでStrategyWarningを発行できることを確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("Test warning message", StrategyWarning, stacklevel=2)

            assert len(w) == 1
            assert issubclass(w[0].category, StrategyWarning)
            assert "Test warning message" in str(w[0].message)

    def test_正常系_filterwarningsでフィルタリングできる(self) -> None:
        """StrategyWarningをフィルタリングできることを確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings("ignore", category=StrategyWarning)
            warnings.warn("This should be ignored", StrategyWarning, stacklevel=2)

            assert len(w) == 0


class TestDataWarning:
    """DataWarning のテスト."""

    def test_正常系_StrategyWarningを継承している(self) -> None:
        """DataWarningがStrategyWarningを継承していることを確認."""
        warning = DataWarning("Data warning")

        assert isinstance(warning, StrategyWarning)
        assert isinstance(warning, UserWarning)

    def test_正常系_warningsで発行できる(self) -> None:
        """warnings.warnでDataWarningを発行できることを確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("Missing data for some dates", DataWarning, stacklevel=2)

            assert len(w) == 1
            assert issubclass(w[0].category, DataWarning)

    def test_正常系_StrategyWarningとしてcatchできる(self) -> None:
        """DataWarningをStrategyWarningとしてフィルタリングできることを確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings("always", category=StrategyWarning)
            warnings.warn("Data warning", DataWarning, stacklevel=2)

            # DataWarningはStrategyWarningのサブクラスなので捕捉される
            assert len(w) == 1


class TestNormalizationWarning:
    """NormalizationWarning のテスト."""

    def test_正常系_StrategyWarningを継承している(self) -> None:
        """NormalizationWarningがStrategyWarningを継承していることを確認."""
        warning = NormalizationWarning("Normalization warning")

        assert isinstance(warning, StrategyWarning)
        assert isinstance(warning, UserWarning)

    def test_正常系_warningsで発行できる(self) -> None:
        """warnings.warnでNormalizationWarningを発行できることを確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn(
                "Data normalized to 0-1 range", NormalizationWarning, stacklevel=2
            )

            assert len(w) == 1
            assert issubclass(w[0].category, NormalizationWarning)
            assert "normalized" in str(w[0].message)

    def test_正常系_StrategyWarningとしてcatchできる(self) -> None:
        """NormalizationWarningをStrategyWarningとしてフィルタリングできることを確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings("always", category=StrategyWarning)
            warnings.warn("Normalization applied", NormalizationWarning, stacklevel=2)

            assert len(w) == 1


class TestErrorHierarchy:
    """エラー階層構造のテスト."""

    @pytest.mark.parametrize(
        "error_class",
        [
            DataProviderError,
            InvalidTickerError,
            InsufficientDataError,
            ConfigurationError,
            ValidationError,
        ],
    )
    def test_正常系_全てのエラーがStrategyErrorを継承(
        self,
        error_class: type[StrategyError],
    ) -> None:
        """全てのエラークラスがStrategyErrorを継承していることを確認."""
        error = error_class("Test error")

        assert isinstance(error, StrategyError)
        assert isinstance(error, Exception)

    @pytest.mark.parametrize(
        "error_class",
        [
            DataProviderError,
            InvalidTickerError,
            InsufficientDataError,
            ConfigurationError,
            ValidationError,
        ],
    )
    def test_正常系_全てのエラーがmessage属性を持つ(
        self,
        error_class: type[StrategyError],
    ) -> None:
        """全てのエラークラスがmessage属性を持つことを確認."""
        error = error_class("Test message")

        assert hasattr(error, "message")
        assert error.message == "Test message"

    @pytest.mark.parametrize(
        "error_class",
        [
            DataProviderError,
            InvalidTickerError,
            InsufficientDataError,
            ConfigurationError,
            ValidationError,
        ],
    )
    def test_正常系_全てのエラーがcode属性を持つ(
        self,
        error_class: type[StrategyError],
    ) -> None:
        """全てのエラークラスがcode属性を持つことを確認."""
        error = error_class("Test message", code="TEST_CODE")

        assert hasattr(error, "code")
        assert error.code == "TEST_CODE"

    @pytest.mark.parametrize(
        "error_class",
        [
            DataProviderError,
            InvalidTickerError,
            InsufficientDataError,
            ConfigurationError,
            ValidationError,
        ],
    )
    def test_正常系_全てのエラーがcause属性を持つ(
        self,
        error_class: type[StrategyError],
    ) -> None:
        """全てのエラークラスがcause属性を持つことを確認."""
        cause = ValueError("Original error")
        error = error_class("Test message", cause=cause)

        assert hasattr(error, "cause")
        assert error.cause is cause


class TestWarningHierarchy:
    """警告階層構造のテスト."""

    @pytest.mark.parametrize(
        "warning_class",
        [
            DataWarning,
            NormalizationWarning,
        ],
    )
    def test_正常系_全ての警告がStrategyWarningを継承(
        self,
        warning_class: type[StrategyWarning],
    ) -> None:
        """全ての警告クラスがStrategyWarningを継承していることを確認."""
        warning = warning_class("Test warning")

        assert isinstance(warning, StrategyWarning)
        assert isinstance(warning, UserWarning)

    @pytest.mark.parametrize(
        "warning_class",
        [
            DataWarning,
            NormalizationWarning,
        ],
    )
    def test_正常系_全ての警告がwarnings_warnで使用できる(
        self,
        warning_class: type[StrategyWarning],
    ) -> None:
        """全ての警告クラスがwarnings.warnで使用できることを確認."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("Test warning", warning_class, stacklevel=2)

            assert len(w) == 1
            assert issubclass(w[0].category, warning_class)

"""Unit tests for configuration error classes."""

import pytest
from news.core.errors import NewsError


class TestConfigError:
    """Test ConfigError base exception."""

    def test_正常系_メッセージで作成できる(self) -> None:
        """ConfigErrorをメッセージで作成できることを確認。"""
        from news.config.errors import ConfigError

        error = ConfigError("Configuration error occurred")
        assert str(error) == "Configuration error occurred"

    def test_正常系_NewsErrorを継承している(self) -> None:
        """ConfigErrorがNewsErrorを継承していることを確認。"""
        from news.config.errors import ConfigError

        error = ConfigError("Test error")
        assert isinstance(error, NewsError)
        assert isinstance(error, Exception)


class TestConfigParseError:
    """Test ConfigParseError exception."""

    def test_正常系_メッセージとファイルパスで作成できる(self) -> None:
        """ConfigParseErrorをメッセージとファイルパスで作成できることを確認。"""
        from news.config.errors import ConfigParseError

        error = ConfigParseError(
            message="Invalid YAML syntax",
            file_path="/path/to/config.yaml",
        )

        assert "Invalid YAML syntax" in str(error)
        assert error.file_path == "/path/to/config.yaml"

    def test_正常系_causeを指定できる(self) -> None:
        """ConfigParseErrorにcauseを指定できることを確認。"""
        from news.config.errors import ConfigParseError

        original_error = ValueError("Invalid value")
        error = ConfigParseError(
            message="Parse error",
            file_path="/path/to/config.yaml",
            cause=original_error,
        )

        assert error.cause is original_error

    def test_正常系_ConfigErrorを継承している(self) -> None:
        """ConfigParseErrorがConfigErrorを継承していることを確認。"""
        from news.config.errors import ConfigError, ConfigParseError

        error = ConfigParseError(message="Test", file_path="/test")
        assert isinstance(error, ConfigError)
        assert isinstance(error, NewsError)


class TestConfigValidationError:
    """Test ConfigValidationError exception."""

    def test_正常系_メッセージとフィールドで作成できる(self) -> None:
        """ConfigValidationErrorをメッセージとフィールドで作成できることを確認。"""
        from news.config.errors import ConfigValidationError

        error = ConfigValidationError(
            message="Invalid value for max_articles",
            field="settings.max_articles_per_source",
            value=-1,
        )

        assert "Invalid value for max_articles" in str(error)
        assert error.field == "settings.max_articles_per_source"
        assert error.value == -1

    def test_正常系_ConfigErrorを継承している(self) -> None:
        """ConfigValidationErrorがConfigErrorを継承していることを確認。"""
        from news.config.errors import ConfigError, ConfigValidationError

        error = ConfigValidationError(message="Test", field="test", value=None)
        assert isinstance(error, ConfigError)
        assert isinstance(error, NewsError)


class TestExceptionHierarchy:
    """Test configuration exception class hierarchy."""

    def test_正常系_例外階層が正しい(self) -> None:
        """例外クラスの継承階層が正しいことを確認。"""
        from news.config.errors import (
            ConfigError,
            ConfigParseError,
            ConfigValidationError,
        )

        # ConfigError は NewsError のサブクラス
        assert issubclass(ConfigError, NewsError)

        # ConfigParseError は ConfigError のサブクラス
        assert issubclass(ConfigParseError, ConfigError)

        # ConfigValidationError は ConfigError のサブクラス
        assert issubclass(ConfigValidationError, ConfigError)

    def test_正常系_ConfigErrorでキャッチできる(self) -> None:
        """派生例外をConfigErrorでキャッチできることを確認。"""
        from news.config.errors import (
            ConfigError,
            ConfigParseError,
            ConfigValidationError,
        )

        with pytest.raises(ConfigError):
            raise ConfigParseError(message="Parse error", file_path="/test")

        with pytest.raises(ConfigError):
            raise ConfigValidationError(message="Validation error", field="x", value=1)

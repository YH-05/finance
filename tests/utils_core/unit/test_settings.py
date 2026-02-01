"""Unit tests for utils_core.settings module."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from utils_core.settings import (
    get_fred_api_key,
    get_log_dir,
    get_log_format,
    get_log_level,
    get_project_env,
)

if TYPE_CHECKING:
    from utils_core.types import LogFormat, LogLevel


class TestGetFredApiKey:
    """get_fred_api_key() のテスト."""

    def test_正常系_環境変数が設定されている場合にAPIキーを返す(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数が設定されている場合、APIキーを返す."""
        monkeypatch.setenv("FRED_API_KEY", "test_api_key_12345")
        get_fred_api_key.cache_clear()

        result = get_fred_api_key()

        assert result == "test_api_key_12345"

    def test_異常系_環境変数が未設定の場合にValueErrorを発生(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数が未設定の場合、ValueErrorを発生させる."""
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        get_fred_api_key.cache_clear()

        with pytest.raises(ValueError, match="FRED_API_KEY is required"):
            get_fred_api_key()

    def test_遅延読み込み_キャッシュが機能する(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """遅延読み込みとキャッシュが機能することを確認."""
        monkeypatch.setenv("FRED_API_KEY", "cached_key")
        get_fred_api_key.cache_clear()

        # 1回目の呼び出し
        result1 = get_fred_api_key()

        # 環境変数を変更
        monkeypatch.setenv("FRED_API_KEY", "new_key")

        # 2回目の呼び出し（キャッシュされた値が返る）
        result2 = get_fred_api_key()

        assert result1 == result2 == "cached_key"


class TestGetLogLevel:
    """get_log_level() のテスト."""

    @pytest.mark.parametrize(
        ("env_value", "expected"),
        [
            ("DEBUG", "DEBUG"),
            ("INFO", "INFO"),
            ("WARNING", "WARNING"),
            ("ERROR", "ERROR"),
            ("CRITICAL", "CRITICAL"),
            ("debug", "DEBUG"),  # 小文字も受け入れ
            ("info", "INFO"),
        ],
    )
    def test_正常系_有効なログレベルを返す(
        self,
        env_value: str,
        expected: LogLevel,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """有効なログレベルの場合、正しく変換して返す."""
        monkeypatch.setenv("LOG_LEVEL", env_value)
        get_log_level.cache_clear()

        result = get_log_level()

        assert result == expected

    def test_正常系_未設定の場合にINFOを返す(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数が未設定の場合、デフォルト値 INFO を返す."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        get_log_level.cache_clear()

        result = get_log_level()

        assert result == "INFO"

    @pytest.mark.parametrize("invalid_value", ["TRACE", "FATAL", "invalid"])
    def test_異常系_不正なログレベルでValueErrorを発生(
        self, invalid_value: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """不正なログレベルの場合、ValueErrorを発生させる."""
        monkeypatch.setenv("LOG_LEVEL", invalid_value)
        get_log_level.cache_clear()

        with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
            get_log_level()


class TestGetLogFormat:
    """get_log_format() のテスト."""

    @pytest.mark.parametrize(
        ("env_value", "expected"),
        [
            ("json", "json"),
            ("console", "console"),
            ("JSON", "json"),  # 大文字も受け入れ
            ("CONSOLE", "console"),
        ],
    )
    def test_正常系_有効なログフォーマットを返す(
        self,
        env_value: str,
        expected: LogFormat,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """有効なログフォーマットの場合、正しく変換して返す."""
        monkeypatch.setenv("LOG_FORMAT", env_value)
        get_log_format.cache_clear()

        result = get_log_format()

        assert result == expected

    def test_正常系_未設定の場合にconsoleを返す(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数が未設定の場合、デフォルト値 console を返す."""
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        get_log_format.cache_clear()

        result = get_log_format()

        assert result == "console"

    @pytest.mark.parametrize("invalid_value", ["xml", "yaml", "invalid"])
    def test_異常系_不正なログフォーマットでValueErrorを発生(
        self, invalid_value: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """不正なログフォーマットの場合、ValueErrorを発生させる."""
        monkeypatch.setenv("LOG_FORMAT", invalid_value)
        get_log_format.cache_clear()

        with pytest.raises(ValueError, match="Invalid LOG_FORMAT"):
            get_log_format()


class TestGetLogDir:
    """get_log_dir() のテスト."""

    def test_正常系_環境変数が設定されている場合にディレクトリパスを返す(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数が設定されている場合、ディレクトリパスを返す."""
        monkeypatch.setenv("LOG_DIR", "/var/log/finance/")
        get_log_dir.cache_clear()

        result = get_log_dir()

        assert result == "/var/log/finance/"

    def test_正常系_未設定の場合にデフォルト値を返す(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数が未設定の場合、デフォルト値 logs/ を返す."""
        monkeypatch.delenv("LOG_DIR", raising=False)
        get_log_dir.cache_clear()

        result = get_log_dir()

        assert result == "logs/"


class TestGetProjectEnv:
    """get_project_env() のテスト."""

    @pytest.mark.parametrize(
        "env_value",
        ["development", "production", "staging", "test"],
    )
    def test_正常系_環境変数が設定されている場合に環境名を返す(
        self, env_value: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数が設定されている場合、環境名を返す."""
        monkeypatch.setenv("PROJECT_ENV", env_value)
        get_project_env.cache_clear()

        result = get_project_env()

        assert result == env_value

    def test_正常系_未設定の場合にデフォルト値を返す(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数が未設定の場合、デフォルト値 development を返す."""
        monkeypatch.delenv("PROJECT_ENV", raising=False)
        get_project_env.cache_clear()

        result = get_project_env()

        assert result == "development"

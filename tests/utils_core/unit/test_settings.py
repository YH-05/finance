"""Tests for utils_core.settings module.

Issue #2669: settings.py に環境変数取得関数を実装

このテストファイルは TDD の Red フェーズとして作成されています。

テスト対象機能:
- get_fred_api_key() -> str (必須、未設定時エラー)
- get_log_level() -> LogLevel (デフォルト: INFO)
- get_log_format() -> LogFormat (デフォルト: console)
- get_log_dir() -> str (デフォルト: logs/)
- get_project_env() -> str (デフォルト: development)

受け入れ条件:
1. 各環境変数の取得関数が実装されている
2. 必須の環境変数（FRED_API_KEY）が未設定の場合、適切なエラーを発生させる
3. オプションの環境変数にはデフォルト値が設定されている
4. 遅延読み込みが実装されている（初回アクセス時のみ環境変数を読み込む）
5. NumPy形式のDocstringが記述されている
"""

import os
from unittest.mock import patch

import pytest

import utils_core.settings as settings_module


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    """各テスト前にsettingsモジュールのキャッシュをリセットする."""
    settings_module._reset_cache()


class TestGetFredApiKey:
    """get_fred_api_key 関数のテスト."""

    def test_正常系_環境変数からFRED_API_KEYを取得できる(self) -> None:
        from utils_core.settings import get_fred_api_key

        with patch.dict(os.environ, {"FRED_API_KEY": "test-api-key-12345"}, clear=True):
            result = get_fred_api_key()
            assert result == "test-api-key-12345"

    def test_正常系_複数回呼び出しても同じ値が返される(self) -> None:
        from utils_core.settings import get_fred_api_key

        with patch.dict(os.environ, {"FRED_API_KEY": "consistent-key"}, clear=True):
            result1 = get_fred_api_key()
            result2 = get_fred_api_key()
            assert result1 == result2 == "consistent-key"

    def test_異常系_FRED_API_KEY未設定でValueError(self) -> None:
        from utils_core.settings import get_fred_api_key

        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match="FRED_API_KEY"),
        ):
            get_fred_api_key()

    def test_異常系_FRED_API_KEYが空文字列でValueError(self) -> None:
        from utils_core.settings import get_fred_api_key

        with (
            patch.dict(os.environ, {"FRED_API_KEY": ""}, clear=True),
            pytest.raises(ValueError, match="FRED_API_KEY"),
        ):
            get_fred_api_key()

    def test_異常系_FRED_API_KEYが空白のみでValueError(self) -> None:
        from utils_core.settings import get_fred_api_key

        with (
            patch.dict(os.environ, {"FRED_API_KEY": "   "}, clear=True),
            pytest.raises(ValueError, match="FRED_API_KEY"),
        ):
            get_fred_api_key()


class TestGetLogLevel:
    """get_log_level 関数のテスト."""

    def test_正常系_デフォルト値INFOが返される(self) -> None:
        from utils_core.settings import get_log_level

        with patch.dict(os.environ, {}, clear=True):
            result = get_log_level()
            assert result == "INFO"

    def test_正常系_環境変数からLOG_LEVELを取得できる(self) -> None:
        from utils_core.settings import get_log_level

        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            result = get_log_level()
            assert result == "DEBUG"

    def test_正常系_小文字のログレベルが大文字に変換される(self) -> None:
        from utils_core.settings import get_log_level

        with patch.dict(os.environ, {"LOG_LEVEL": "warning"}, clear=True):
            result = get_log_level()
            assert result == "WARNING"

    def test_正常系_有効なログレベルが全て設定可能(self) -> None:
        from utils_core.settings import get_log_level

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings_module._reset_cache()
            with patch.dict(os.environ, {"LOG_LEVEL": level}, clear=True):
                result = get_log_level()
                assert result == level

    def test_異常系_不正なログレベルでValueError(self) -> None:
        from utils_core.settings import get_log_level

        with (
            patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True),
            pytest.raises(
                ValueError,
                match=r"Invalid LOG_LEVEL: 'INVALID'\. "
                r"Valid values are: CRITICAL, DEBUG, ERROR, INFO, WARNING",
            ),
        ):
            get_log_level()

    def test_異常系_空文字のログレベルでValueError(self) -> None:
        """空文字列が設定された場合はValueError（未設定とは異なる）."""
        from utils_core.settings import get_log_level

        with (
            patch.dict(os.environ, {"LOG_LEVEL": ""}, clear=True),
            pytest.raises(ValueError, match="Invalid LOG_LEVEL"),
        ):
            get_log_level()


class TestGetLogFormat:
    """get_log_format 関数のテスト."""

    def test_正常系_デフォルト値consoleが返される(self) -> None:
        from utils_core.settings import get_log_format

        with patch.dict(os.environ, {}, clear=True):
            result = get_log_format()
            assert result == "console"

    def test_正常系_環境変数からLOG_FORMATを取得できる(self) -> None:
        from utils_core.settings import get_log_format

        with patch.dict(os.environ, {"LOG_FORMAT": "json"}, clear=True):
            result = get_log_format()
            assert result == "json"

    def test_正常系_大文字のフォーマットが小文字に変換される(self) -> None:
        from utils_core.settings import get_log_format

        with patch.dict(os.environ, {"LOG_FORMAT": "JSON"}, clear=True):
            result = get_log_format()
            assert result == "json"

    def test_正常系_有効なフォーマットが全て設定可能(self) -> None:
        from utils_core.settings import get_log_format

        for fmt in ["json", "console", "plain"]:
            settings_module._reset_cache()
            with patch.dict(os.environ, {"LOG_FORMAT": fmt}, clear=True):
                result = get_log_format()
                assert result == fmt

    def test_異常系_不正なフォーマットでValueError(self) -> None:
        from utils_core.settings import get_log_format

        with (
            patch.dict(os.environ, {"LOG_FORMAT": "INVALID"}, clear=True),
            pytest.raises(
                ValueError,
                match=r"Invalid LOG_FORMAT: 'invalid'\. Valid values are: console, json, plain",
            ),
        ):
            get_log_format()

    def test_異常系_空文字のフォーマットでValueError(self) -> None:
        """空文字列が設定された場合はValueError（未設定とは異なる）."""
        from utils_core.settings import get_log_format

        with (
            patch.dict(os.environ, {"LOG_FORMAT": ""}, clear=True),
            pytest.raises(ValueError, match="Invalid LOG_FORMAT"),
        ):
            get_log_format()


class TestGetLogDir:
    """get_log_dir 関数のテスト."""

    def test_正常系_デフォルト値logsが返される(self) -> None:
        from utils_core.settings import get_log_dir

        with patch.dict(os.environ, {}, clear=True):
            result = get_log_dir()
            assert result == "logs/"

    def test_正常系_環境変数からLOG_DIRを取得できる(self) -> None:
        from utils_core.settings import get_log_dir

        with patch.dict(os.environ, {"LOG_DIR": "/var/log/myapp"}, clear=True):
            result = get_log_dir()
            assert result == "/var/log/myapp"

    def test_正常系_末尾スラッシュなしでも動作する(self) -> None:
        from utils_core.settings import get_log_dir

        with patch.dict(os.environ, {"LOG_DIR": "/var/log/myapp"}, clear=True):
            result = get_log_dir()
            # 末尾スラッシュの有無は環境変数の値をそのまま返す
            assert result == "/var/log/myapp"

    def test_正常系_相対パスも受け入れる(self) -> None:
        from utils_core.settings import get_log_dir

        with patch.dict(os.environ, {"LOG_DIR": "data/logs"}, clear=True):
            result = get_log_dir()
            assert result == "data/logs"


class TestGetProjectEnv:
    """get_project_env 関数のテスト."""

    def test_正常系_デフォルト値developmentが返される(self) -> None:
        from utils_core.settings import get_project_env

        with patch.dict(os.environ, {}, clear=True):
            result = get_project_env()
            assert result == "development"

    def test_正常系_環境変数からPROJECT_ENVを取得できる(self) -> None:
        from utils_core.settings import get_project_env

        with patch.dict(os.environ, {"PROJECT_ENV": "production"}, clear=True):
            result = get_project_env()
            assert result == "production"

    def test_正常系_大文字のenvが小文字に変換される(self) -> None:
        from utils_core.settings import get_project_env

        with patch.dict(os.environ, {"PROJECT_ENV": "PRODUCTION"}, clear=True):
            result = get_project_env()
            assert result == "production"

    def test_正常系_stagingなどの任意の値も受け入れる(self) -> None:
        from utils_core.settings import get_project_env

        for env in ["development", "staging", "production", "test"]:
            settings_module._reset_cache()
            with patch.dict(os.environ, {"PROJECT_ENV": env}, clear=True):
                result = get_project_env()
                assert result == env


class TestLazyLoading:
    """遅延読み込み機能のテスト."""

    def test_正常系_初回アクセス時のみ環境変数を読み込む(self) -> None:
        from utils_core.settings import get_log_level

        # 最初の呼び出しで環境変数を読み込む
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            result = get_log_level()
            assert result == "DEBUG"

    def test_正常系_キャッシュリセット関数が存在する(self) -> None:
        # _reset_cache 関数が存在することを確認
        assert hasattr(settings_module, "_reset_cache")
        assert callable(settings_module._reset_cache)

    def test_正常系_リセット後に新しい値が読み込まれる(self) -> None:
        from utils_core.settings import get_log_level

        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}, clear=True):
            settings_module._reset_cache()
            result = get_log_level()
            assert result == "ERROR"

    def test_正常系_キャッシュが有効な間は環境変数の変更が反映されない(self) -> None:
        from utils_core.settings import get_log_level

        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            result1 = get_log_level()
            assert result1 == "DEBUG"

        # 環境変数を変更してもキャッシュが返される
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}, clear=True):
            result2 = get_log_level()
            # キャッシュされた値が返される
            assert result2 == "DEBUG"


class TestModuleExports:
    """モジュールのエクスポートに関するテスト."""

    def test_正常系_get_fred_api_keyがエクスポートされている(self) -> None:
        from utils_core.settings import get_fred_api_key

        assert callable(get_fred_api_key)

    def test_正常系_get_log_levelがエクスポートされている(self) -> None:
        from utils_core.settings import get_log_level

        assert callable(get_log_level)

    def test_正常系_get_log_formatがエクスポートされている(self) -> None:
        from utils_core.settings import get_log_format

        assert callable(get_log_format)

    def test_正常系_get_log_dirがエクスポートされている(self) -> None:
        from utils_core.settings import get_log_dir

        assert callable(get_log_dir)

    def test_正常系_get_project_envがエクスポートされている(self) -> None:
        from utils_core.settings import get_project_env

        assert callable(get_project_env)

    def test_正常系__all__に5つの関数が含まれている(self) -> None:
        expected_exports = {
            "get_fred_api_key",
            "get_log_level",
            "get_log_format",
            "get_log_dir",
            "get_project_env",
        }
        # _reset_cache はテスト用なので __all__ に含まれなくてもよい
        assert hasattr(settings_module, "__all__")
        assert expected_exports.issubset(set(settings_module.__all__))

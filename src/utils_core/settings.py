"""Environment variable settings management with lazy loading.

環境変数の取得と検証を行うモジュール。
遅延読み込みにより、初回アクセス時のみ環境変数を読み込みます。

Features
--------
- FRED_API_KEY: 必須の環境変数（未設定時はエラー）
- LOG_LEVEL: ログレベル設定（デフォルト: INFO）
- LOG_FORMAT: ログフォーマット設定（デフォルト: console）
- LOG_DIR: ログ出力ディレクトリ（デフォルト: logs/）
- PROJECT_ENV: プロジェクト環境（デフォルト: development）

Examples
--------
>>> from utils_core.settings import get_fred_api_key, get_log_level
>>> api_key = get_fred_api_key()  # 環境変数から取得
>>> log_level = get_log_level()   # "INFO" (デフォルト)
"""

import os
from typing import Final

from dotenv import load_dotenv

from .types import LogFormat, LogLevel

# 有効なログレベル
VALID_LOG_LEVELS: Final[frozenset[str]] = frozenset(
    {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
)

# 有効なログフォーマット
VALID_LOG_FORMATS: Final[frozenset[str]] = frozenset({"json", "console", "plain"})

# デフォルト値
DEFAULT_LOG_LEVEL: Final[LogLevel] = "INFO"
DEFAULT_LOG_FORMAT: Final[LogFormat] = "console"
DEFAULT_LOG_DIR: Final[str] = "logs/"
DEFAULT_PROJECT_ENV: Final[str] = "development"

# キャッシュ用の変数
_cache: dict[str, str | None] = {}
_initialized: bool = False


def _ensure_initialized() -> None:
    """環境変数の読み込みを確保する.

    初回呼び出し時のみ .env ファイルを読み込みます。
    """
    global _initialized
    if not _initialized:
        load_dotenv(override=True)
        _initialized = True


def _reset_cache() -> None:
    """キャッシュをリセットする.

    テスト用のユーティリティ関数です。
    キャッシュをクリアし、初期化フラグをリセットします。
    """
    global _initialized
    _cache.clear()
    _initialized = False


def get_fred_api_key() -> str:
    """FRED API キーを取得する.

    環境変数 FRED_API_KEY から API キーを取得します。
    必須の環境変数であり、未設定または空の場合はエラーを発生させます。

    Returns
    -------
    str
        FRED API キー

    Raises
    ------
    ValueError
        FRED_API_KEY が未設定、空文字列、または空白のみの場合

    Examples
    --------
    >>> # 環境変数に FRED_API_KEY=your-api-key を設定
    >>> api_key = get_fred_api_key()
    >>> api_key
    'your-api-key'

    Notes
    -----
    この環境変数は FRED (Federal Reserve Economic Data) API へのアクセスに必要です。
    API キーは https://fred.stlouisfed.org/docs/api/api_key.html から取得できます。
    """
    _ensure_initialized()

    if "fred_api_key" not in _cache:
        value = os.environ.get("FRED_API_KEY")
        _cache["fred_api_key"] = value

    cached_value = _cache["fred_api_key"]

    if cached_value is None or cached_value.strip() == "":
        raise ValueError(
            "FRED_API_KEY is not set or empty. "
            "Please set the FRED_API_KEY environment variable. "
            "Get your API key from https://fred.stlouisfed.org/docs/api/api_key.html"
        )

    return cached_value


def get_log_level() -> LogLevel:
    """ログレベルを取得する.

    環境変数 LOG_LEVEL からログレベルを取得します。
    未設定の場合は INFO を返します。
    無効な値が設定されている場合は ValueError を発生させます。

    Returns
    -------
    LogLevel
        ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL のいずれか）

    Raises
    ------
    ValueError
        LOG_LEVEL に無効な値が設定されている場合

    Examples
    --------
    >>> # 環境変数未設定の場合
    >>> get_log_level()
    'INFO'

    >>> # LOG_LEVEL=DEBUG を設定
    >>> get_log_level()
    'DEBUG'

    >>> # 小文字でも大文字に変換
    >>> # LOG_LEVEL=warning を設定
    >>> get_log_level()
    'WARNING'

    >>> # 無効な値の場合
    >>> # LOG_LEVEL=INVALID を設定
    >>> get_log_level()  # doctest: +SKIP
    ValueError: Invalid LOG_LEVEL: 'INVALID'. Valid values are: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    _ensure_initialized()

    if "log_level" not in _cache:
        raw_value = os.environ.get("LOG_LEVEL")
        if raw_value is None:
            # 環境変数が未設定の場合はデフォルト値を使用
            _cache["log_level"] = DEFAULT_LOG_LEVEL
        else:
            # 環境変数が設定されている場合は検証
            value = raw_value.upper()
            if value not in VALID_LOG_LEVELS:
                valid_values = ", ".join(sorted(VALID_LOG_LEVELS))
                raise ValueError(
                    f"Invalid LOG_LEVEL: '{raw_value.upper()}'. "
                    f"Valid values are: {valid_values}"
                )
            _cache["log_level"] = value

    return _cache["log_level"]  # type: ignore[return-value]


def get_log_format() -> LogFormat:
    """ログフォーマットを取得する.

    環境変数 LOG_FORMAT からログフォーマットを取得します。
    未設定の場合は console を返します。
    無効な値が設定されている場合は ValueError を発生させます。

    Returns
    -------
    LogFormat
        ログフォーマット（json, console, plain のいずれか）

    Raises
    ------
    ValueError
        LOG_FORMAT に無効な値が設定されている場合

    Examples
    --------
    >>> # 環境変数未設定の場合
    >>> get_log_format()
    'console'

    >>> # LOG_FORMAT=json を設定
    >>> get_log_format()
    'json'

    >>> # 大文字でも小文字に変換
    >>> # LOG_FORMAT=JSON を設定
    >>> get_log_format()
    'json'

    >>> # 無効な値の場合
    >>> # LOG_FORMAT=INVALID を設定
    >>> get_log_format()  # doctest: +SKIP
    ValueError: Invalid LOG_FORMAT: 'invalid'. Valid values are: console, json, plain
    """
    _ensure_initialized()

    if "log_format" not in _cache:
        raw_value = os.environ.get("LOG_FORMAT")
        if raw_value is None:
            # 環境変数が未設定の場合はデフォルト値を使用
            _cache["log_format"] = DEFAULT_LOG_FORMAT
        else:
            # 環境変数が設定されている場合は検証
            value = raw_value.lower()
            if value not in VALID_LOG_FORMATS:
                valid_values = ", ".join(sorted(VALID_LOG_FORMATS))
                raise ValueError(
                    f"Invalid LOG_FORMAT: '{value}'. Valid values are: {valid_values}"
                )
            _cache["log_format"] = value

    return _cache["log_format"]  # type: ignore[return-value]


def get_log_dir() -> str:
    """ログ出力ディレクトリを取得する.

    環境変数 LOG_DIR からログ出力ディレクトリを取得します。
    未設定の場合は logs/ を返します。

    Returns
    -------
    str
        ログ出力ディレクトリのパス

    Examples
    --------
    >>> # 環境変数未設定の場合
    >>> get_log_dir()
    'logs/'

    >>> # LOG_DIR=/var/log/myapp を設定
    >>> get_log_dir()
    '/var/log/myapp'
    """
    _ensure_initialized()

    if "log_dir" not in _cache:
        value = os.environ.get("LOG_DIR")
        _cache["log_dir"] = value if value else DEFAULT_LOG_DIR

    return _cache["log_dir"]  # type: ignore[return-value]


def get_project_env() -> str:
    """プロジェクト環境を取得する.

    環境変数 PROJECT_ENV からプロジェクト環境を取得します。
    未設定の場合は development を返します。
    値は小文字に変換されます。

    Returns
    -------
    str
        プロジェクト環境（development, staging, production など）

    Examples
    --------
    >>> # 環境変数未設定の場合
    >>> get_project_env()
    'development'

    >>> # PROJECT_ENV=production を設定
    >>> get_project_env()
    'production'

    >>> # 大文字でも小文字に変換
    >>> # PROJECT_ENV=PRODUCTION を設定
    >>> get_project_env()
    'production'
    """
    _ensure_initialized()

    if "project_env" not in _cache:
        value = os.environ.get("PROJECT_ENV")
        if value:
            _cache["project_env"] = value.lower()
        else:
            _cache["project_env"] = DEFAULT_PROJECT_ENV

    return _cache["project_env"]  # type: ignore[return-value]


__all__ = [
    "_reset_cache",
    "get_fred_api_key",
    "get_log_dir",
    "get_log_format",
    "get_log_level",
    "get_project_env",
]

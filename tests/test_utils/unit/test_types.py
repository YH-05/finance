"""Tests for utils.types module.

PEP 695 形式の型定義が正しく機能することを検証する。
"""

from typing import get_args


class TestLogFormat:
    """LogFormat 型のテスト."""

    def test_正常系_LogFormat型が定義されている(self) -> None:
        from utils.types import LogFormat

        # LogFormat が型エイリアスとして存在することを確認
        assert LogFormat is not None

    def test_正常系_LogFormatの許可値が正しい(self) -> None:
        from utils.types import LogFormat

        # PEP 695 TypeAliasType の __value__ 属性から Literal の引数を取得
        # type X = Literal[...] の場合、X.__value__ が Literal[...] になる
        allowed_values = get_args(LogFormat.__value__)
        expected = {"json", "console", "plain"}
        assert set(allowed_values) == expected

    def test_正常系_有効な値をLogFormat型として使用できる(self) -> None:
        from utils.types import LogFormat

        # 許可された値が型の許可値に含まれることを検証
        allowed = get_args(LogFormat.__value__)

        format_json = "json"
        format_console = "console"
        format_plain = "plain"

        assert format_json in allowed
        assert format_console in allowed
        assert format_plain in allowed


class TestLogLevel:
    """LogLevel 型のテスト."""

    def test_正常系_LogLevel型が定義されている(self) -> None:
        from utils.types import LogLevel

        # LogLevel が型エイリアスとして存在することを確認
        assert LogLevel is not None

    def test_正常系_LogLevelの許可値が正しい(self) -> None:
        from utils.types import LogLevel

        # PEP 695 TypeAliasType の __value__ 属性から Literal の引数を取得
        allowed_values = get_args(LogLevel.__value__)
        expected = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert set(allowed_values) == expected

    def test_正常系_有効な値をLogLevel型として使用できる(self) -> None:
        from utils.types import LogLevel

        # 許可された値が型の許可値に含まれることを検証
        allowed = get_args(LogLevel.__value__)

        level_debug = "DEBUG"
        level_info = "INFO"
        level_warning = "WARNING"
        level_error = "ERROR"
        level_critical = "CRITICAL"

        assert level_debug in allowed
        assert level_info in allowed
        assert level_warning in allowed
        assert level_error in allowed
        assert level_critical in allowed

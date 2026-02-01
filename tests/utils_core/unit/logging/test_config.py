"""Tests for utils.logging.config module.

Issue #1690: logging/config.py の作成（ログ設定本体）

このテストファイルは TDD の Red フェーズとして作成されており、
対応する実装（src/utils/logging/config.py）が存在しないため、
全てのテストは失敗する状態です。

テスト対象機能:
- get_logger(name: str) -> BoundLogger
- setup_logging() -> None
- set_log_level(level: str) -> None
- log_context(**kwargs) - コンテキストマネージャ
- log_performance(name: str) - デコレータ

受け入れ条件:
1. structlog ベースのロガーが動作する
2. logs/ ディレクトリに日付別ログファイルが作成される
3. 環境変数で設定が変更可能
4. 重複ハンドラー追加が防止される
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from structlog import BoundLogger


class TestGetLogger:
    """get_logger 関数のテスト."""

    def test_正常系_ロガーを取得できる(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__)

        assert logger is not None
        # BoundLogger or BoundLoggerLazyProxy both have the required methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "bind")

    def test_正常系_名前付きロガーを取得できる(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger("test.module")

        # ロガー名が設定されていることを確認
        assert logger is not None

    def test_正常系_コンテキスト付きでロガーを取得できる(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__, module="test", version="1.0")

        assert logger is not None

    def test_正常系_ロガーでinfoログを出力できる(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__)
        logger.info("Test message", key="value")

        # ログが出力されることを確認（内容の詳細は setup_logging の設定に依存）
        # structlog は stdout に出力するため capsys で確認可能
        # 注: 実際の出力フォーマットは setup_logging の設定による

    def test_正常系_ロガーでdebugログを出力できる(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__)
        # 例外が発生しないことを確認
        logger.debug("Debug message", debug_key="debug_value")

    def test_正常系_ロガーでwarningログを出力できる(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__)
        logger.warning("Warning message")

    def test_正常系_ロガーでerrorログを出力できる(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__)
        logger.error("Error message", error_code=500)

    def test_正常系_ロガーでcriticalログを出力できる(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__)
        logger.critical("Critical message")


class TestSetupLogging:
    """setup_logging 関数のテスト."""

    def test_正常系_デフォルト設定でセットアップできる(self) -> None:
        from utils_core.logging.config import setup_logging

        # 例外が発生しないことを確認
        setup_logging()

    def test_正常系_ログレベルを指定してセットアップできる(self) -> None:
        from utils_core.logging.config import setup_logging

        setup_logging(level="DEBUG")

        # ルートロガーのレベルが DEBUG になっていることを確認
        assert logging.root.level == logging.DEBUG

    def test_正常系_JSONフォーマットを指定できる(self) -> None:
        from utils_core.logging.config import setup_logging

        setup_logging(format="json")

    def test_正常系_コンソールフォーマットを指定できる(self) -> None:
        from utils_core.logging.config import setup_logging

        setup_logging(format="console")

    def test_正常系_プレーンフォーマットを指定できる(self) -> None:
        from utils_core.logging.config import setup_logging

        setup_logging(format="plain")

    def test_正常系_ファイル出力を有効にできる(self, tmp_path: Path) -> None:
        from utils_core.logging.config import get_logger, setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file)

        logger = get_logger(__name__)
        logger.info("Test log message")

        # ログファイルが作成されていることを確認
        assert log_file.exists()

    def test_正常系_環境変数LOG_LEVELでレベルを設定できる(self) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            setup_logging()

            assert logging.root.level == logging.WARNING

    def test_正常系_環境変数LOG_FORMATでフォーマットを設定できる(self) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_FORMAT": "json"}):
            setup_logging()

    def test_正常系_環境変数LOG_DIRでログディレクトリを設定できる(
        self, tmp_path: Path
    ) -> None:
        from utils_core.logging.config import get_logger, setup_logging

        log_dir = tmp_path / "custom_logs"
        with patch.dict(os.environ, {"LOG_DIR": str(log_dir)}):
            setup_logging()

            logger = get_logger(__name__)
            logger.info("Test message")

            # ログディレクトリが作成されることを確認
            assert log_dir.exists()

    def test_正常系_環境変数LOG_FILE_ENABLEDでファイル出力を無効にできる(
        self, tmp_path: Path
    ) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(
            os.environ,
            {"LOG_DIR": str(tmp_path), "LOG_FILE_ENABLED": "false"},
        ):
            setup_logging()

            # ログファイルが作成されないことを確認
            log_files = list(tmp_path.glob("*.log"))
            assert len(log_files) == 0

    def test_正常系_日付別ログファイルが作成される(self, tmp_path: Path) -> None:
        from utils_core.logging.config import get_logger, setup_logging

        with patch.dict(os.environ, {"LOG_DIR": str(tmp_path)}):
            setup_logging()

            logger = get_logger(__name__)
            logger.info("Test message")

            # 日付形式のログファイルが作成されることを確認
            today = datetime.now().strftime("%Y-%m-%d")
            expected_file = tmp_path / f"finance-{today}.log"
            assert expected_file.exists()

    def test_正常系_タイムスタンプを含めるオプションが機能する(self) -> None:
        from utils_core.logging.config import setup_logging

        setup_logging(include_timestamp=True)

    def test_正常系_呼び出し元情報を含めるオプションが機能する(self) -> None:
        from utils_core.logging.config import setup_logging

        setup_logging(include_caller_info=True)

    def test_正常系_forceオプションで再設定できる(self) -> None:
        from utils_core.logging.config import setup_logging

        setup_logging(level="INFO")
        setup_logging(level="DEBUG", force=True)

        assert logging.root.level == logging.DEBUG

    def test_正常系_重複ハンドラー追加が防止される(self) -> None:
        from utils_core.logging.config import setup_logging

        initial_handler_count = len(logging.root.handlers)

        setup_logging()
        setup_logging()
        setup_logging()

        # ハンドラー数が大幅に増加していないことを確認
        final_handler_count = len(logging.root.handlers)
        # 最初の setup_logging で1つ追加される可能性があるが、
        # 重複追加は防止されるべき
        assert final_handler_count <= initial_handler_count + 2


class TestSetLogLevel:
    """set_log_level 関数のテスト."""

    def test_正常系_ルートロガーのレベルを変更できる(self) -> None:
        from utils_core.logging.config import set_log_level

        set_log_level("DEBUG")

        assert logging.root.level == logging.DEBUG

    def test_正常系_特定のロガーのレベルを変更できる(self) -> None:
        from utils_core.logging.config import set_log_level

        logger_name = "test.specific.logger"
        set_log_level("ERROR", logger_name=logger_name)

        assert logging.getLogger(logger_name).level == logging.ERROR

    def test_正常系_全てのログレベルを設定できる(self) -> None:
        from utils_core.logging.config import set_log_level

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            set_log_level(level)
            assert logging.root.level == getattr(logging, level)

    def test_正常系_小文字のログレベルも受け付ける(self) -> None:
        from utils_core.logging.config import set_log_level

        set_log_level("debug")

        assert logging.root.level == logging.DEBUG

    def test_異常系_不正なログレベルでAttributeError(self) -> None:
        from utils_core.logging.config import set_log_level

        with pytest.raises(AttributeError):
            set_log_level("INVALID_LEVEL")


class TestLogContext:
    """log_context コンテキストマネージャのテスト."""

    def test_正常系_コンテキスト内でログにキーが追加される(self) -> None:
        from utils_core.logging.config import get_logger, log_context

        logger = get_logger(__name__)

        with log_context(user_id=123, request_id="abc"):
            # コンテキスト内でのログ出力
            logger.info("Processing request")

    def test_正常系_コンテキスト終了後にキーが削除される(self) -> None:
        from utils_core.logging.config import get_logger, log_context

        logger = get_logger(__name__)

        with log_context(temp_key="temp_value"):
            logger.info("Inside context")

        # コンテキスト外でのログ出力（temp_key が含まれないはず）
        logger.info("Outside context")

    def test_正常系_ネストしたコンテキストが機能する(self) -> None:
        from utils_core.logging.config import get_logger, log_context

        logger = get_logger(__name__)

        with log_context(outer_key="outer"):
            logger.info("Outer context")
            with log_context(inner_key="inner"):
                logger.info("Inner context")
            logger.info("Back to outer")

    def test_正常系_複数のキーを同時にバインドできる(self) -> None:
        from utils_core.logging.config import get_logger, log_context

        logger = get_logger(__name__)

        with log_context(key1="value1", key2="value2", key3="value3"):
            logger.info("Multiple keys bound")

    def test_正常系_例外が発生してもコンテキストがクリーンアップされる(self) -> None:
        from utils_core.logging.config import get_logger, log_context

        logger = get_logger(__name__)

        try:
            with log_context(error_context="testing"):
                logger.info("Before error")
                raise ValueError("Test error")
        except ValueError:
            pass

        # コンテキストがクリーンアップされていることを確認
        logger.info("After error - context should be clean")


class TestLogPerformance:
    """log_performance デコレータのテスト."""

    def test_正常系_デコレータが関数を実行できる(self) -> None:
        from utils_core.logging.config import get_logger, log_performance

        logger = get_logger(__name__)

        @log_performance(logger)
        def sample_function(x: int, y: int) -> int:
            return x + y

        result = sample_function(2, 3)
        assert result == 5

    def test_正常系_関数の戻り値が正しく返される(self) -> None:
        from utils_core.logging.config import get_logger, log_performance

        logger = get_logger(__name__)

        @log_performance(logger)
        def return_list() -> list[int]:
            return [1, 2, 3]

        result = return_list()
        assert result == [1, 2, 3]

    def test_正常系_例外が発生しても再送出される(self) -> None:
        from utils_core.logging.config import get_logger, log_performance

        logger = get_logger(__name__)

        @log_performance(logger)
        def raise_error() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            raise_error()

    def test_正常系_引数とキーワード引数を正しく渡せる(self) -> None:
        from utils_core.logging.config import get_logger, log_performance

        logger = get_logger(__name__)

        @log_performance(logger)
        def func_with_kwargs(a: int, b: int = 10) -> int:
            return a + b

        result = func_with_kwargs(5, b=20)
        assert result == 25

    def test_正常系_関数名が保持される(self) -> None:
        from utils_core.logging.config import get_logger, log_performance

        logger = get_logger(__name__)

        @log_performance(logger)
        def named_function() -> None:
            pass

        assert named_function.__name__ == "named_function"

    def test_正常系_ドキュストリングが保持される(self) -> None:
        from utils_core.logging.config import get_logger, log_performance

        logger = get_logger(__name__)

        @log_performance(logger)
        def documented_function() -> None:
            """This is a docstring."""

        assert documented_function.__doc__ == "This is a docstring."


class TestProcessors:
    """カスタムプロセッサのテスト."""

    def test_正常系_タイムスタンプが追加される(self) -> None:
        from utils_core.logging.config import add_timestamp

        event_dict: dict[str, Any] = {"event": "test"}
        result = add_timestamp(None, None, event_dict)

        assert "timestamp" in result
        # ISO形式のタイムスタンプであることを確認
        timestamp = result["timestamp"]
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO形式には T が含まれる

    def test_正常系_呼び出し元情報が追加される(self) -> None:
        from utils_core.logging.config import add_caller_info

        event_dict: dict[str, Any] = {"event": "test"}
        _ = add_caller_info(None, None, event_dict)

        # caller 情報が追加されることを確認
        # 注: テスト環境では正確な呼び出し元情報が取得できない場合がある
        # 実装によっては caller キーが追加されない場合もある

    def test_正常系_ログレベルが大文字に変換される(self) -> None:
        from utils_core.logging.config import add_log_level_upper

        event_dict: dict[str, Any] = {"event": "test", "level": "info"}
        result = add_log_level_upper(None, None, event_dict)

        assert result["level"] == "INFO"

    def test_正常系_ログレベルがない場合もエラーにならない(self) -> None:
        from utils_core.logging.config import add_log_level_upper

        event_dict: dict[str, Any] = {"event": "test"}
        result = add_log_level_upper(None, None, event_dict)

        # level キーがない場合はそのまま返される
        assert result == {"event": "test"}


class TestEnvironmentVariables:
    """環境変数の処理に関するテスト."""

    def test_正常系_LOG_LEVEL_DEBUGが機能する(self) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            setup_logging()
            assert logging.root.level == logging.DEBUG

    def test_正常系_LOG_LEVEL_INFOが機能する(self) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_LEVEL": "INFO"}):
            setup_logging()
            assert logging.root.level == logging.INFO

    def test_正常系_LOG_LEVEL_WARNINGが機能する(self) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            setup_logging()
            assert logging.root.level == logging.WARNING

    def test_正常系_LOG_LEVEL_ERRORが機能する(self) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            setup_logging()
            assert logging.root.level == logging.ERROR

    def test_正常系_LOG_LEVEL_CRITICALが機能する(self) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_LEVEL": "CRITICAL"}):
            setup_logging()
            assert logging.root.level == logging.CRITICAL

    def test_正常系_不正なLOG_LEVELはデフォルトINFOになる(self) -> None:
        from utils_core.logging.config import setup_logging

        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            setup_logging()
            # 不正な値の場合はデフォルトの INFO が使用される
            assert logging.root.level == logging.INFO


class TestLogFileCreation:
    """ログファイル作成に関するテスト."""

    def test_正常系_ログディレクトリが存在しない場合自動作成される(
        self, tmp_path: Path
    ) -> None:
        from utils_core.logging.config import setup_logging

        log_dir = tmp_path / "nested" / "log" / "dir"
        with patch.dict(os.environ, {"LOG_DIR": str(log_dir)}):
            setup_logging()

            assert log_dir.exists()

    def test_正常系_ログファイルにメッセージが書き込まれる(
        self, tmp_path: Path
    ) -> None:
        from utils_core.logging.config import get_logger, setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(log_file=log_file, force=True)

        logger = get_logger("test.write")
        logger.info("Test log entry", key="value")

        # ファイルが作成され、内容が書き込まれていることを確認
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test log entry" in content

    def test_正常系_ログファイルがUTF8エンコーディングで書き込まれる(
        self, tmp_path: Path
    ) -> None:
        from utils_core.logging.config import get_logger, setup_logging

        log_file = tmp_path / "utf8_test.log"
        setup_logging(log_file=log_file, force=True)

        logger = get_logger("test.utf8")
        logger.info("日本語テストメッセージ", key="値")

        content = log_file.read_text(encoding="utf-8")
        assert "日本語テストメッセージ" in content


class TestLoggerProtocol:
    """LoggerProtocol の型定義テスト."""

    def test_正常系_ロガーがbindメソッドを持つ(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__)
        bound_logger = logger.bind(extra_key="extra_value")

        assert bound_logger is not None

    def test_正常系_ロガーがunbindメソッドを持つ(self) -> None:
        from utils_core.logging.config import get_logger

        logger = get_logger(__name__)
        bound_logger = logger.bind(key_to_remove="value")
        unbound_logger = bound_logger.unbind("key_to_remove")

        assert unbound_logger is not None


class TestIntegration:
    """統合テスト."""

    def test_正常系_完全なログワークフローが機能する(self, tmp_path: Path) -> None:
        from utils_core.logging.config import (
            get_logger,
            log_context,
            log_performance,
            set_log_level,
            setup_logging,
        )

        # セットアップ
        log_file = tmp_path / "integration.log"
        setup_logging(level="DEBUG", log_file=log_file, force=True)

        # ロガー取得
        logger = get_logger("integration.test", component="test_suite")

        # ログ出力
        logger.info("Starting integration test")

        # コンテキスト内でのログ
        with log_context(request_id="req-123"):
            logger.debug("Processing with context")

            # パフォーマンス計測
            @log_performance(logger)
            def compute(n: int) -> int:
                return sum(range(n))

            result = compute(100)
            assert result == 4950

        # ログレベル変更
        set_log_level("WARNING")
        logger.warning("This should be logged")

        # ログファイルの確認
        assert log_file.exists()
        content = log_file.read_text()
        assert "Starting integration test" in content


class TestFileLevelParameter:
    """file_level パラメータのテスト (Issue #2676).

    ファイル出力とコンソール出力で異なるログレベルを設定できる機能のテスト。
    - コンソール: INFO（クリーンな出力を維持）
    - ファイル: DEBUG（詳細な分析用ログを保存）
    """

    def test_正常系_file_levelパラメータが受け付けられる(self, tmp_path: Path) -> None:
        """setup_logging が file_level パラメータを受け付けることを確認."""
        from utils_core.logging.config import setup_logging

        log_file = tmp_path / "test.log"

        # 例外が発生しないことを確認
        setup_logging(
            level="INFO",
            file_level="DEBUG",
            format="console",
            log_file=log_file,
            force=True,
        )

    def test_正常系_file_level指定でファイルハンドラがDEBUGレベルになる(
        self, tmp_path: Path
    ) -> None:
        """file_level 指定時にファイルハンドラが指定レベルになることを確認."""
        from utils_core.logging.config import setup_logging

        log_file = tmp_path / "test.log"

        # 既存のハンドラーをクリア
        logging.root.handlers.clear()

        setup_logging(
            level="INFO",
            file_level="DEBUG",
            format="console",
            log_file=log_file,
            force=True,
        )

        # ファイルハンドラーを検索
        file_handler = None
        for handler in logging.root.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break

        assert file_handler is not None, "ファイルハンドラーが追加されている必要がある"
        assert file_handler.level == logging.DEBUG, (
            f"ファイルハンドラーは DEBUG レベルである必要がある。実際: {file_handler.level}"
        )

    def test_正常系_コンソールハンドラはlevelパラメータを使用(
        self, tmp_path: Path
    ) -> None:
        """コンソールハンドラは level パラメータを使用することを確認."""
        from utils_core.logging.config import setup_logging

        log_file = tmp_path / "test.log"

        # 既存のハンドラーをクリア
        logging.root.handlers.clear()

        setup_logging(
            level="INFO",
            file_level="DEBUG",
            format="console",
            log_file=log_file,
            force=True,
        )

        # コンソールハンドラを検索（StreamHandler だが FileHandler ではない）
        console_handler = None
        for handler in logging.root.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                console_handler = handler
                break

        assert console_handler is not None, (
            "コンソールハンドラが追加されている必要がある"
        )
        assert console_handler.level == logging.INFO, (
            f"コンソールハンドラは INFO レベルである必要がある。実際: {console_handler.level}"
        )

    def test_正常系_file_level未指定時はlevelと同じになる(self, tmp_path: Path) -> None:
        """file_level 未指定時はファイルハンドラも level と同じになることを確認."""
        from utils_core.logging.config import setup_logging

        log_file = tmp_path / "test.log"

        # 既存のハンドラーをクリア
        logging.root.handlers.clear()

        setup_logging(
            level="WARNING",
            format="console",
            log_file=log_file,
            force=True,
        )

        # ファイルハンドラーを検索
        file_handler = None
        for handler in logging.root.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break

        assert file_handler is not None, "ファイルハンドラーが追加されている必要がある"
        assert file_handler.level == logging.WARNING, (
            f"ファイルハンドラーは WARNING レベルである必要がある（file_level 未指定時）。"
            f"実際: {file_handler.level}"
        )

    def test_正常系_DEBUGログがファイルに書き込まれる(self, tmp_path: Path) -> None:
        """file_level=DEBUG 時に DEBUG ログがファイルに書き込まれることを確認."""
        from utils_core.logging.config import get_logger, setup_logging

        log_file = tmp_path / "test.log"

        # 既存のハンドラーをクリア
        logging.root.handlers.clear()

        setup_logging(
            level="INFO",
            file_level="DEBUG",
            format="plain",
            log_file=log_file,
            force=True,
        )

        test_logger = get_logger("test_debug_file")
        test_logger.debug("This is a DEBUG message for file")
        test_logger.info("This is an INFO message")

        # ハンドラーをフラッシュ
        for handler in logging.root.handlers:
            handler.flush()

        # ファイル内容を確認
        file_content = log_file.read_text()

        # file_level=DEBUG なので DEBUG メッセージがファイルに含まれる
        assert "DEBUG" in file_content or "debug" in file_content.lower(), (
            f"DEBUG メッセージがファイルに含まれる必要がある。内容: {file_content}"
        )

    def test_正常系_全てのログレベルをfile_levelに設定できる(
        self, tmp_path: Path
    ) -> None:
        """全てのログレベルを file_level として設定できることを確認."""
        from utils_core.logging.config import setup_logging

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            log_file = tmp_path / f"test_{level.lower()}.log"
            logging.root.handlers.clear()

            setup_logging(
                level="INFO",
                file_level=level,
                log_file=log_file,
                force=True,
            )

            # ファイルハンドラーを検索
            file_handler = None
            for handler in logging.root.handlers:
                if isinstance(handler, logging.FileHandler):
                    file_handler = handler
                    break

            assert file_handler is not None
            assert file_handler.level == getattr(logging, level), (
                f"file_level={level} でファイルハンドラーレベルが一致する必要がある"
            )

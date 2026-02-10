"""Tests for log file permission settings (CWE-732).

Issue #3453: ログファイルパーミッション設定

ログファイルが所有者のみ読み書き可能（0o600）で作成されること、
既存ログファイルのパーミッションも起動時に修正されることを検証する。
"""

import logging
import stat
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="os.chmod の動作が Windows では異なるためスキップ",
)


class TestLogFilePermissions:
    """ログファイルパーミッション設定のテスト."""

    def test_正常系_ログファイルが0o600で作成される(self, tmp_path: Path) -> None:
        """setup_logging 後にファイルのパーミッションが 0o600 であること."""
        from utils_core.logging.config import get_logger, setup_logging

        log_file = tmp_path / "test_perm.log"
        setup_logging(log_file=log_file, force=True)

        logger = get_logger("test.permissions")
        logger.info("Permission test message")

        # ハンドラーをフラッシュ
        for handler in logging.root.handlers:
            handler.flush()

        assert log_file.exists(), "ログファイルが作成されている必要がある"

        file_mode = stat.S_IMODE(log_file.stat().st_mode)
        assert file_mode == 0o600, (
            f"ログファイルのパーミッションは 0o600 である必要がある。実際: {oct(file_mode)}"
        )

    def test_正常系_既存ログファイルのパーミッションが修正される(
        self, tmp_path: Path
    ) -> None:
        """0o644 で作成された既存ファイルが setup_logging で 0o600 に修正されること."""
        from utils_core.logging.config import setup_logging

        log_file = tmp_path / "existing.log"

        # 0o644 でファイルを事前作成
        log_file.write_text("existing log content")
        log_file.chmod(0o644)

        pre_mode = stat.S_IMODE(log_file.stat().st_mode)
        assert pre_mode == 0o644, "事前条件: ファイルが 0o644 で存在する"

        # setup_logging で既存ファイルのパーミッションが修正される
        setup_logging(log_file=log_file, force=True)

        post_mode = stat.S_IMODE(log_file.stat().st_mode)
        assert post_mode == 0o600, (
            f"既存ファイルのパーミッションが 0o600 に修正される必要がある。実際: {oct(post_mode)}"
        )

    def test_正常系_セキュアファイル関数が存在しないパスでエラーにならない(
        self, tmp_path: Path
    ) -> None:
        """存在しないパスを渡してもエラーにならないこと."""
        from utils_core.logging.config import _secure_log_file

        nonexistent_path = tmp_path / "nonexistent" / "test.log"

        # 例外が発生しないことを確認
        _secure_log_file(nonexistent_path)

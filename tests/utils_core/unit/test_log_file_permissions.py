"""Tests for log file permission settings (CWE-732).

Issue #3453: ログファイルパーミッション設定
Issue #3468: TOCTOU対策（os.open原子的作成）

ログファイルが所有者のみ読み書き可能（0o600）で作成されること、
既存ログファイルのパーミッションも起動時に修正されることを検証する。
TOCTOU（Time-of-check to Time-of-use）問題の解消を検証する。
"""

import logging
import os
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
        """存在しないパスを渡してもエラーにならないこと（親ディレクトリが存在しない場合）."""
        from utils_core.logging.config import _create_secure_log_file

        nonexistent_path = tmp_path / "nonexistent" / "test.log"

        # 例外が発生しないことを確認（親ディレクトリも作成される）
        _create_secure_log_file(nonexistent_path)


class TestTOCTOUPrevention:
    """TOCTOU（Time-of-check to Time-of-use）対策のテスト（Issue #3468）."""

    def test_正常系_新規ファイルがos_openで原子的に0o600で作成される(
        self, tmp_path: Path
    ) -> None:
        """新規ファイル作成時に os.open() で原子的に 0o600 パーミッションが設定されること."""
        from utils_core.logging.config import _create_secure_log_file

        log_file = tmp_path / "atomic_test.log"
        assert not log_file.exists(), "事前条件: ファイルが存在しない"

        _create_secure_log_file(log_file)

        # ファイルが作成されていること
        assert log_file.exists(), "ファイルが作成されている必要がある"

        # 作成直後のパーミッションが 0o600 であること（TOCTOU窓なし）
        file_mode = stat.S_IMODE(log_file.stat().st_mode)
        assert file_mode == 0o600, (
            f"新規ファイルのパーミッションは作成時点で 0o600 である必要がある。"
            f"実際: {oct(file_mode)}"
        )

    def test_正常系_既存ファイルのパーミッションがchmodで修正される(
        self, tmp_path: Path
    ) -> None:
        """既存ファイルに対しては chmod(0o600) でパーミッションが修正されること."""
        from utils_core.logging.config import _create_secure_log_file

        log_file = tmp_path / "existing_chmod.log"

        # 0o644 でファイルを事前作成
        log_file.write_text("pre-existing content")
        log_file.chmod(0o644)

        pre_mode = stat.S_IMODE(log_file.stat().st_mode)
        assert pre_mode == 0o644, "事前条件: ファイルが 0o644 で存在する"

        _create_secure_log_file(log_file)

        post_mode = stat.S_IMODE(log_file.stat().st_mode)
        assert post_mode == 0o600, (
            f"既存ファイルのパーミッションが 0o600 に修正される必要がある。"
            f"実際: {oct(post_mode)}"
        )

    def test_正常系_親ディレクトリが自動作成される(self, tmp_path: Path) -> None:
        """親ディレクトリが存在しない場合に自動作成されること."""
        from utils_core.logging.config import _create_secure_log_file

        log_file = tmp_path / "nested" / "deep" / "dir" / "test.log"
        assert not log_file.parent.exists(), "事前条件: 親ディレクトリが存在しない"

        _create_secure_log_file(log_file)

        assert log_file.parent.exists(), "親ディレクトリが作成されている必要がある"
        assert log_file.exists(), "ファイルが作成されている必要がある"

        file_mode = stat.S_IMODE(log_file.stat().st_mode)
        assert file_mode == 0o600, (
            f"新規ファイルのパーミッションは 0o600 である必要がある。実際: {oct(file_mode)}"
        )

    def test_正常系_setup_loggingがFileHandler作成前にセキュアファイルを作成(
        self, tmp_path: Path
    ) -> None:
        """setup_logging が FileHandler 作成前にファイルを安全に作成すること."""
        from utils_core.logging.config import setup_logging

        log_file = tmp_path / "pre_handler.log"
        assert not log_file.exists(), "事前条件: ファイルが存在しない"

        setup_logging(log_file=log_file, force=True)

        # ファイルが存在し、パーミッションが 0o600 であること
        assert log_file.exists(), "ログファイルが作成されている必要がある"

        file_mode = stat.S_IMODE(log_file.stat().st_mode)
        assert file_mode == 0o600, (
            f"setup_logging 後のパーミッションは 0o600 である必要がある。"
            f"実際: {oct(file_mode)}"
        )

    def test_正常系_既存ファイルの内容が保持される(self, tmp_path: Path) -> None:
        """既存ファイルに対して _create_secure_log_file を呼んでも内容が失われないこと."""
        from utils_core.logging.config import _create_secure_log_file

        log_file = tmp_path / "content_preserved.log"
        original_content = "既存のログ内容\n"
        log_file.write_text(original_content)
        log_file.chmod(0o644)

        _create_secure_log_file(log_file)

        # 内容が保持されていること
        assert log_file.read_text() == original_content, (
            "既存ファイルの内容が保持される必要がある"
        )

    def test_正常系_新規ファイルが空で作成される(self, tmp_path: Path) -> None:
        """新規ファイルが空の状態で作成されること."""
        from utils_core.logging.config import _create_secure_log_file

        log_file = tmp_path / "empty_new.log"

        _create_secure_log_file(log_file)

        assert log_file.read_text() == "", "新規ファイルは空である必要がある"

    def test_正常系_os_openフラグが正しく設定される(self, tmp_path: Path) -> None:
        """os.open() の O_CREAT | O_WRONLY | O_APPEND フラグで作成されること."""
        from unittest.mock import patch

        from utils_core.logging.config import _create_secure_log_file

        log_file = tmp_path / "flag_test.log"

        with patch("utils_core.logging.config.os.open", wraps=os.open) as mock_open:
            _create_secure_log_file(log_file)

            mock_open.assert_called_once()
            call_args = mock_open.call_args
            flags = call_args[0][1]
            mode = call_args[0][2]

            # フラグの検証
            assert flags & os.O_CREAT, "O_CREAT フラグが設定されている必要がある"
            assert flags & os.O_WRONLY, "O_WRONLY フラグが設定されている必要がある"
            assert flags & os.O_APPEND, "O_APPEND フラグが設定されている必要がある"

            # モードの検証
            assert mode == (stat.S_IRUSR | stat.S_IWUSR), (
                f"モードは S_IRUSR | S_IWUSR (0o600) である必要がある。実際: {oct(mode)}"
            )

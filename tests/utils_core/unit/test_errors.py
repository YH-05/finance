"""Tests for utils_core.errors module.

Issue #3452: エラーハンドリングパターン共通化（DRY原則）

テスト対象機能:
- log_and_reraise コンテキストマネージャ
  - 例外発生時にログを出力して再送出
  - reraise_as 指定時に例外を変換
  - コンテキスト情報の付与
  - 例外未発生時のパススルー
"""

from unittest.mock import MagicMock

import pytest


class TestLogAndReraise:
    """log_and_reraise コンテキストマネージャのテスト."""

    def test_正常系_例外が発生しなければ何もしない(self) -> None:
        from utils_core.errors import log_and_reraise
        from utils_core.logging import get_logger

        logger = get_logger(__name__)

        with log_and_reraise(logger, "test operation"):
            result = 1 + 1

        assert result == 2

    def test_正常系_例外発生時にログ出力して再送出(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with (
            pytest.raises(ValueError, match="test error"),
            log_and_reraise(mock_logger, "test operation"),
        ):
            raise ValueError("test error")

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "test operation failed" in call_args[0][0]

    def test_正常系_コンテキスト情報がログに含まれる(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()
        context = {"filing_id": "abc-123", "operation": "cache_get"}

        with (
            pytest.raises(RuntimeError),
            log_and_reraise(mock_logger, "cache lookup", context=context),
        ):
            raise RuntimeError("db error")

        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs["filing_id"] == "abc-123"
        assert call_kwargs["operation"] == "cache_get"

    def test_正常系_reraise_asで例外型を変換(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with (
            pytest.raises(OSError, match="data fetch failed"),
            log_and_reraise(
                mock_logger,
                "data fetch",
                reraise_as=OSError,
            ),
        ):
            raise ValueError("connection timeout")

    def test_正常系_reraise_as使用時に元例外がチェーンされる(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with (
            pytest.raises(OSError) as exc_info,
            log_and_reraise(
                mock_logger,
                "data fetch",
                reraise_as=OSError,
            ),
        ):
            raise ValueError("original error")

        assert isinstance(exc_info.value.__cause__, ValueError)
        assert str(exc_info.value.__cause__) == "original error"

    def test_正常系_reraise_asなしで元の例外型が保持される(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with pytest.raises(KeyError), log_and_reraise(mock_logger, "key lookup"):
            raise KeyError("missing_key")

    def test_正常系_exc_infoがログに含まれる(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with pytest.raises(ValueError), log_and_reraise(mock_logger, "test op"):
            raise ValueError("test")

        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs["exc_info"] is True

    def test_正常系_error文字列がログに含まれる(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with pytest.raises(ValueError), log_and_reraise(mock_logger, "test op"):
            raise ValueError("detailed error message")

        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs["error"] == "detailed error message"

    def test_正常系_コンテキストなしでも動作する(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with pytest.raises(TypeError), log_and_reraise(mock_logger, "null check"):
            raise TypeError("None is not valid")

        mock_logger.error.assert_called_once()

    def test_正常系_log_levelをwarningに変更できる(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with (
            pytest.raises(ValueError),
            log_and_reraise(mock_logger, "test op", log_level="warning"),
        ):
            raise ValueError("test")

        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_not_called()

    def test_正常系_skip_types指定で特定例外をスキップ(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with (
            pytest.raises(ValueError, match="pass through"),
            log_and_reraise(
                mock_logger,
                "test op",
                skip_types=(ValueError,),
            ),
        ):
            raise ValueError("pass through")

        # skip_types に含まれる例外はログ出力されない
        mock_logger.error.assert_not_called()

    def test_正常系_skip_types以外の例外はログ出力される(self) -> None:
        from utils_core.errors import log_and_reraise

        mock_logger = MagicMock()

        with (
            pytest.raises(TypeError),
            log_and_reraise(
                mock_logger,
                "test op",
                skip_types=(ValueError,),
            ),
        ):
            raise TypeError("not skipped")

        mock_logger.error.assert_called_once()


class TestLogAndReturn:
    """log_and_return コンテキストマネージャのテスト."""

    def test_正常系_例外発生時にログ出力してデフォルト値を返す(self) -> None:
        from utils_core.errors import log_and_return

        mock_logger = MagicMock()

        with log_and_return(mock_logger, "test operation", default=None) as ctx:
            raise ValueError("test error")

        assert ctx.value is None
        mock_logger.error.assert_called_once()

    def test_正常系_例外未発生時はyield値を使用(self) -> None:
        from utils_core.errors import log_and_return

        mock_logger = MagicMock()

        with log_and_return(mock_logger, "test operation", default=None) as ctx:
            ctx.value = "success"

        assert ctx.value == "success"
        mock_logger.error.assert_not_called()

    def test_正常系_コンテキスト情報がログに含まれる(self) -> None:
        from utils_core.errors import log_and_return

        mock_logger = MagicMock()
        context = {"url": "https://example.com"}

        with log_and_return(
            mock_logger, "fetch page", default=None, context=context
        ) as ctx:
            raise RuntimeError("network error")

        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs["url"] == "https://example.com"

    def test_正常系_特定の例外型のみキャッチ(self) -> None:
        from utils_core.errors import log_and_return

        mock_logger = MagicMock()

        with (
            pytest.raises(TypeError),
            log_and_return(
                mock_logger,
                "test op",
                default=None,
                catch=(ValueError, KeyError),
            ),
        ):
            raise TypeError("uncaught")

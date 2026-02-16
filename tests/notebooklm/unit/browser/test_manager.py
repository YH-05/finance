"""Unit tests for notebooklm.browser.manager module."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestNotebookLMBrowserManagerInit:
    """Tests for NotebookLMBrowserManager initialization."""

    def test_正常系_デフォルト設定で生成できる(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        assert manager._browser is None
        assert manager._playwright is None
        assert manager._context is None
        assert manager.headless is True

    def test_正常系_headedモードで生成できる(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager(headless=False)
        assert manager.headless is False

    def test_正常系_カスタムセッションファイルで生成できる(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager(session_file="custom-session.json")
        assert manager.session_file == "custom-session.json"

    def test_正常系_デフォルトセッションファイルが設定される(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        assert manager.session_file == ".notebooklm-session.json"


class TestNotebookLMBrowserManagerLazyInit:
    """Tests for lazy initialization of Playwright browser."""

    @pytest.mark.asyncio
    async def test_正常系_ensure_browserで遅延初期化される(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()

        mock_playwright = MagicMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.add_init_script = AsyncMock()

        with patch(
            "notebooklm.browser.manager._async_playwright_factory"
        ) as mock_factory:
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_cm

            await manager._ensure_browser()

            assert manager._browser is mock_browser
            assert manager._context is mock_context
            assert manager._playwright is mock_playwright

        # Clean up
        manager._browser = None
        manager._context = None
        manager._playwright = None

    @pytest.mark.asyncio
    async def test_正常系_二重初期化しない(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        manager._browser = mock_browser
        manager._context = mock_context
        manager._playwright = MagicMock()

        # Should not reinitialize
        await manager._ensure_browser()
        assert manager._browser is mock_browser


class TestNotebookLMBrowserManagerClose:
    """Tests for browser close functionality."""

    @pytest.mark.asyncio
    async def test_正常系_closeでリソースが解放される(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_pw_cm = AsyncMock()

        manager._context = mock_context
        manager._browser = mock_browser
        manager._pw_context_manager = mock_pw_cm

        await manager.close()

        mock_context.close.assert_awaited_once()
        mock_browser.close.assert_awaited_once()
        mock_pw_cm.__aexit__.assert_awaited_once()
        assert manager._context is None
        assert manager._browser is None
        assert manager._playwright is None

    @pytest.mark.asyncio
    async def test_正常系_未初期化でcloseしてもエラーにならない(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        # Should not raise
        await manager.close()


class TestNotebookLMBrowserManagerContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    async def test_正常系_async_context_managerとして動作する(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()

        mock_playwright = MagicMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.add_init_script = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        with patch(
            "notebooklm.browser.manager._async_playwright_factory"
        ) as mock_factory:
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_cm

            async with manager as mgr:
                assert mgr is manager
                assert mgr._browser is not None

        # After exit, resources should be cleaned up
        assert manager._browser is None
        assert manager._context is None


class TestNotebookLMBrowserManagerSession:
    """Tests for session save/restore."""

    @pytest.mark.asyncio
    async def test_正常系_セッション保存が動作する(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager(session_file="test-session.json")
        mock_context = AsyncMock()
        mock_context.storage_state = AsyncMock(return_value=None)
        manager._context = mock_context

        await manager.save_session()

        mock_context.storage_state.assert_awaited_once_with(path="test-session.json")

    @pytest.mark.asyncio
    async def test_異常系_コンテキスト未初期化でセッション保存するとエラー(
        self,
    ) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        with pytest.raises(RuntimeError, match="Browser context not initialized"):
            await manager.save_session()

    def test_正常系_セッションファイル存在確認(self, tmp_path: Path) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        session_file = str(tmp_path / "session.json")
        manager = NotebookLMBrowserManager(session_file=session_file)
        assert not manager.has_session()

        # Create a dummy session file
        Path(session_file).write_text("{}")
        assert manager.has_session()


class TestNotebookLMBrowserManagerStealth:
    """Tests for stealth browser configuration."""

    @pytest.mark.asyncio
    async def test_正常系_stealth設定がコンテキストに適用される(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager
        from notebooklm.constants import (
            STEALTH_LOCALE,
            STEALTH_TIMEZONE,
            STEALTH_USER_AGENT,
            STEALTH_VIEWPORT,
        )

        manager = NotebookLMBrowserManager()

        mock_playwright = MagicMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.add_init_script = AsyncMock()

        with patch(
            "notebooklm.browser.manager._async_playwright_factory"
        ) as mock_factory:
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_cm

            await manager._ensure_browser()

            # Verify stealth settings were applied to new_context
            call_kwargs = mock_browser.new_context.call_args[1]
            assert call_kwargs["viewport"] == STEALTH_VIEWPORT
            assert call_kwargs["user_agent"] == STEALTH_USER_AGENT
            assert call_kwargs["locale"] == STEALTH_LOCALE
            assert call_kwargs["timezone_id"] == STEALTH_TIMEZONE

            # Verify init script was added
            mock_context.add_init_script.assert_awaited_once()

        # Clean up
        manager._browser = None
        manager._context = None
        manager._playwright = None


class TestNotebookLMBrowserManagerSessionRestore:
    """Tests for session restoration from storage state."""

    @pytest.mark.asyncio
    async def test_正常系_セッションファイルがある場合復元される(
        self, tmp_path: Path
    ) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        session_file = str(tmp_path / "session.json")
        Path(session_file).write_text('{"cookies": []}')

        manager = NotebookLMBrowserManager(session_file=session_file)

        mock_playwright = MagicMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.add_init_script = AsyncMock()

        with patch(
            "notebooklm.browser.manager._async_playwright_factory"
        ) as mock_factory:
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_playwright)
            mock_cm.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_cm

            await manager._ensure_browser()

            # Verify storage_state was passed to new_context
            call_kwargs = mock_browser.new_context.call_args[1]
            assert call_kwargs["storage_state"] == session_file

        # Clean up
        manager._browser = None
        manager._context = None
        manager._playwright = None


class TestNotebookLMBrowserManagerNewPage:
    """Tests for new_page functionality."""

    @pytest.mark.asyncio
    async def test_正常系_新しいページを作成できる(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        manager._context = mock_context
        manager._browser = AsyncMock()
        manager._playwright = MagicMock()

        page = await manager.new_page()
        assert page is mock_page
        mock_context.new_page.assert_awaited_once()


class TestNotebookLMBrowserManagerSessionExpiry:
    """Tests for session expiry detection."""

    @pytest.mark.asyncio
    async def test_正常系_セッション有効時にTrueを返す(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.goto = AsyncMock()
        mock_page.close = AsyncMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        manager._context = mock_context
        manager._browser = AsyncMock()
        manager._playwright = MagicMock()

        result = await manager.is_session_valid()
        assert result is True

    @pytest.mark.asyncio
    async def test_正常系_セッション期限切れ時にFalseを返す(self) -> None:
        from notebooklm.browser.manager import NotebookLMBrowserManager

        manager = NotebookLMBrowserManager()
        mock_page = AsyncMock()
        mock_page.url = "https://accounts.google.com/signin"
        mock_page.goto = AsyncMock()
        mock_page.close = AsyncMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        manager._context = mock_context
        manager._browser = AsyncMock()
        manager._playwright = MagicMock()

        result = await manager.is_session_valid()
        assert result is False

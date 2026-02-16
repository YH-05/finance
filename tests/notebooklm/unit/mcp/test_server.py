"""Unit tests for the NotebookLM MCP server module.

Tests cover:
- FastMCP server configuration (name, instructions, lifespan).
- Lifespan context manager (BrowserManager lifecycle).
- Tool registration (5 Phase 1 tools).
- Entry point functions (serve, main).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMCPServerConfiguration:
    """Tests for the FastMCP server instance configuration."""

    def test_正常系_サーバー名がNotebookLMである(self) -> None:
        """サーバー名が 'NotebookLM' に設定されていること。"""
        from notebooklm.mcp.server import mcp

        assert mcp.name == "NotebookLM"

    def test_正常系_サーバーにinstructionsが設定されている(self) -> None:
        """サーバーにinstructionsが設定されていること。"""
        from notebooklm.mcp.server import mcp

        assert mcp.instructions is not None
        assert "NotebookLM" in mcp.instructions


class TestLifespan:
    """Tests for the notebooklm_lifespan context manager."""

    @pytest.mark.asyncio
    async def test_正常系_lifespanがbrowser_managerをyieldする(self) -> None:
        """lifespan がコンテキストに browser_manager を含むこと。"""
        from notebooklm.mcp.server import notebooklm_lifespan

        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.close = AsyncMock()
        mock_manager.headless = True
        mock_manager.has_session = MagicMock(return_value=False)

        with patch(
            "notebooklm.browser.manager.NotebookLMBrowserManager",
            return_value=mock_manager,
        ):
            async with notebooklm_lifespan(None) as context:
                assert "browser_manager" in context
                assert context["browser_manager"] is mock_manager

    @pytest.mark.asyncio
    async def test_正常系_lifespanがBrowserManagerを初期化する(self) -> None:
        """lifespan が BrowserManager を __aenter__ で初期化すること。"""
        from notebooklm.mcp.server import notebooklm_lifespan

        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.close = AsyncMock()
        mock_manager.headless = True
        mock_manager.has_session = MagicMock(return_value=False)

        with patch(
            "notebooklm.browser.manager.NotebookLMBrowserManager",
            return_value=mock_manager,
        ):
            async with notebooklm_lifespan(None):
                mock_manager.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_lifespanがBrowserManagerをcloseする(self) -> None:
        """lifespan 終了時に BrowserManager が close されること。"""
        from notebooklm.mcp.server import notebooklm_lifespan

        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.close = AsyncMock()
        mock_manager.headless = True
        mock_manager.has_session = MagicMock(return_value=False)

        with patch(
            "notebooklm.browser.manager.NotebookLMBrowserManager",
            return_value=mock_manager,
        ):
            async with notebooklm_lifespan(None):
                pass

        mock_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_正常系_lifespan中に例外が発生してもcloseが呼ばれる(self) -> None:
        """lifespan 中に例外が発生しても BrowserManager が close されること。"""
        from notebooklm.mcp.server import notebooklm_lifespan

        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.close = AsyncMock()
        mock_manager.headless = True
        mock_manager.has_session = MagicMock(return_value=False)

        with (
            patch(
                "notebooklm.browser.manager.NotebookLMBrowserManager",
                return_value=mock_manager,
            ),
            pytest.raises(RuntimeError, match="test error"),
        ):
            async with notebooklm_lifespan(None):
                raise RuntimeError("test error")

        mock_manager.close.assert_called_once()


class TestToolRegistration:
    """Tests for MCP tool registration."""

    def test_正常系_5つのツールが登録されている(self) -> None:
        """Phase 1 の 5 つのツールがサーバーに登録されていること。"""
        from notebooklm.mcp.server import mcp

        tool_manager = mcp._tool_manager
        tools = tool_manager._tools

        expected_tools = {
            "notebooklm_create_notebook",
            "notebooklm_list_notebooks",
            "notebooklm_get_notebook_summary",
            "notebooklm_add_text_source",
            "notebooklm_list_sources",
        }

        registered_names = set(tools.keys())
        assert expected_tools.issubset(registered_names), (
            f"Missing tools: {expected_tools - registered_names}"
        )

    def test_正常系_ノートブック管理ツールが3つ登録されている(self) -> None:
        """ノートブック管理ツールが 3 つ登録されていること。"""
        from notebooklm.mcp.server import mcp

        tool_manager = mcp._tool_manager
        tools = tool_manager._tools

        notebook_tools = [
            name
            for name in tools
            if name.startswith("notebooklm_")
            and "notebook" in name
            and "source" not in name
        ]
        assert len(notebook_tools) == 3

    def test_正常系_ソース管理ツールが2つ登録されている(self) -> None:
        """ソース管理ツールが 2 つ登録されていること。"""
        from notebooklm.mcp.server import mcp

        tool_manager = mcp._tool_manager
        tools = tool_manager._tools

        source_tools = [
            name
            for name in tools
            if name.startswith("notebooklm_") and "source" in name
        ]
        assert len(source_tools) == 2


class TestEntryPoints:
    """Tests for server entry point functions."""

    def test_正常系_serve関数がmcpのrunを呼ぶ(self) -> None:
        """serve() が mcp.run(transport='stdio') を呼ぶこと。"""
        from notebooklm.mcp.server import serve

        with patch("notebooklm.mcp.server.mcp") as mock_mcp:
            serve()
            mock_mcp.run.assert_called_once_with(transport="stdio")

    def test_正常系_main関数がserveを呼ぶ(self) -> None:
        """main() が serve() を呼ぶこと。"""
        from notebooklm.mcp.server import main

        with patch("notebooklm.mcp.server.serve") as mock_serve:
            main()
            mock_serve.assert_called_once()


class TestModuleExports:
    """Tests for module exports."""

    def test_正常系_mcp_initからmcpをインポートできる(self) -> None:
        """mcp/__init__.py から mcp インスタンスをインポートできること。"""
        from notebooklm.mcp import mcp

        assert mcp is not None

    def test_正常系_mcp_initからserveをインポートできる(self) -> None:
        """mcp/__init__.py から serve 関数をインポートできること。"""
        from notebooklm.mcp import serve

        assert callable(serve)

    def test_正常系_mcp_initからmainをインポートできる(self) -> None:
        """mcp/__init__.py から main 関数をインポートできること。"""
        from notebooklm.mcp import main

        assert callable(main)

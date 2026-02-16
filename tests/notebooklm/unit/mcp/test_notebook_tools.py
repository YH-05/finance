"""Unit tests for NotebookLM MCP notebook tools.

Tests cover:
- notebooklm_create_notebook: Success, validation error, NotebookLMError.
- notebooklm_list_notebooks: Success, NotebookLMError.
- notebooklm_get_notebook_summary: Success, validation error, NotebookLMError.
- notebooklm_delete_notebook: Success, validation error, NotebookLMError.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.errors import ElementNotFoundError, SessionExpiredError
from notebooklm.types import NotebookInfo, NotebookSummary


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create a mocked FastMCP Context with lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"browser_manager": MagicMock()}
    return ctx


class TestCreateNotebook:
    """Tests for notebooklm_create_notebook tool."""

    @pytest.mark.asyncio
    async def test_正常系_ノートブックを作成してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にノートブックを作成し、dict形式で結果を返すこと。"""
        expected_notebook = NotebookInfo(
            notebook_id="abc-123",
            title="Test Notebook",
            source_count=0,
        )

        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.create_notebook = AsyncMock(return_value=expected_notebook)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_create_notebook"]
            result = await tool.fn(title="Test Notebook", ctx=mock_ctx)

        assert result["notebook_id"] == "abc-123"
        assert result["title"] == "Test Notebook"
        assert result["source_count"] == 0

    @pytest.mark.asyncio
    async def test_異常系_空タイトルでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空のタイトルで ValueError のエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.create_notebook = AsyncMock(
                side_effect=ValueError("title must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_create_notebook"]
            result = await tool.fn(title="", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_NotebookLMErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """NotebookLMError 発生時にエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.create_notebook = AsyncMock(
                side_effect=ElementNotFoundError(
                    "Create button not found",
                    context={"selector": "button.create"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_create_notebook"]
            result = await tool.fn(title="Test", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ElementNotFoundError"
        assert result["context"] == {"selector": "button.create"}


class TestListNotebooks:
    """Tests for notebooklm_list_notebooks tool."""

    @pytest.mark.asyncio
    async def test_正常系_ノートブック一覧をdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にノートブック一覧を返すこと。"""
        notebooks = [
            NotebookInfo(notebook_id="nb-1", title="Notebook 1", source_count=3),
            NotebookInfo(notebook_id="nb-2", title="Notebook 2", source_count=1),
        ]

        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_notebooks = AsyncMock(return_value=notebooks)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_notebooks"]
            result = await tool.fn(ctx=mock_ctx)

        assert result["total"] == 2
        assert len(result["notebooks"]) == 2
        assert result["notebooks"][0]["notebook_id"] == "nb-1"
        assert result["notebooks"][1]["title"] == "Notebook 2"

    @pytest.mark.asyncio
    async def test_正常系_ノートブックがない場合は空リスト(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """ノートブックが存在しない場合、空リストを返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_notebooks = AsyncMock(return_value=[])

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_notebooks"]
            result = await tool.fn(ctx=mock_ctx)

        assert result["total"] == 0
        assert result["notebooks"] == []

    @pytest.mark.asyncio
    async def test_異常系_NotebookLMErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """NotebookLMError 発生時にエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_notebooks = AsyncMock(
                side_effect=SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".notebooklm-session.json"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_notebooks"]
            result = await tool.fn(ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "SessionExpiredError"


class TestGetNotebookSummary:
    """Tests for notebooklm_get_notebook_summary tool."""

    @pytest.mark.asyncio
    async def test_正常系_ノートブック概要をdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にノートブック概要を返すこと。"""
        expected_summary = NotebookSummary(
            notebook_id="abc-123",
            summary_text="This notebook covers AI research...",
            suggested_questions=[
                "What are the key findings?",
                "How does this compare?",
            ],
        )

        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_notebook_summary = AsyncMock(return_value=expected_summary)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_notebook_summary"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert result["notebook_id"] == "abc-123"
        assert result["summary_text"] == "This notebook covers AI research..."
        assert len(result["suggested_questions"]) == 2

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_notebook_summary = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_notebook_summary"]
            result = await tool.fn(notebook_id="", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_NotebookLMErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """NotebookLMError 発生時にエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_notebook_summary = AsyncMock(
                side_effect=SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".notebooklm-session.json"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_notebook_summary"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "SessionExpiredError"


class TestDeleteNotebook:
    """Tests for notebooklm_delete_notebook tool."""

    @pytest.mark.asyncio
    async def test_正常系_ノートブックを削除してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にノートブックを削除し、dict形式で結果を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_notebook = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_notebook"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert result["deleted"] is True
        assert result["notebook_id"] == "abc-123"

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_notebook = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_notebook"]
            result = await tool.fn(notebook_id="", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_NotebookLMErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """NotebookLMError 発生時にエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.notebook_tools.NotebookService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_notebook = AsyncMock(
                side_effect=ElementNotFoundError(
                    "Notebook not found",
                    context={"notebook_id": "abc-123"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_notebook"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ElementNotFoundError"
        assert result["context"] == {"notebook_id": "abc-123"}

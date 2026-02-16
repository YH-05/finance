"""Unit tests for NotebookLM MCP source tools.

Tests cover:
- notebooklm_add_text_source: Success, validation error, SourceAddError.
- notebooklm_list_sources: Success, validation error, NotebookLMError.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.errors import SessionExpiredError, SourceAddError
from notebooklm.types import SourceInfo


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create a mocked FastMCP Context with lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"browser_manager": MagicMock()}
    return ctx


class TestAddTextSource:
    """Tests for notebooklm_add_text_source tool."""

    @pytest.mark.asyncio
    async def test_正常系_テキストソースを追加してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にテキストソースを追加し、dict形式で結果を返すこと。"""
        expected_source = SourceInfo(
            source_id="src-abc12345",
            title="Research Notes",
            source_type="text",
        )

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_text_source = AsyncMock(return_value=expected_source)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_text_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                text="Some research content...",
                ctx=mock_ctx,
                title="Research Notes",
            )

        assert result["source_id"] == "src-abc12345"
        assert result["title"] == "Research Notes"
        assert result["source_type"] == "text"

    @pytest.mark.asyncio
    async def test_正常系_タイトル省略でテキストソースを追加(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """タイトルを省略してテキストソースを追加できること。"""
        expected_source = SourceInfo(
            source_id="src-def67890",
            title="Pasted text",
            source_type="text",
        )

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_text_source = AsyncMock(return_value=expected_source)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_text_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                text="Some content...",
                ctx=mock_ctx,
            )

        assert result["title"] == "Pasted text"
        mock_service.add_text_source.assert_called_once_with(
            notebook_id="nb-123",
            text="Some content...",
            title=None,
        )

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_text_source = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_text_source"]
            result = await tool.fn(
                notebook_id="",
                text="content",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_空のtextでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の text で ValueError のエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_text_source = AsyncMock(
                side_effect=ValueError("text must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_text_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                text="",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_SourceAddErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """SourceAddError 発生時にエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_text_source = AsyncMock(
                side_effect=SourceAddError(
                    "Failed to add text source",
                    context={
                        "notebook_id": "nb-123",
                        "source_type": "text",
                        "text_length": 100,
                    },
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_text_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                text="x" * 100,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "SourceAddError"
        assert result["context"]["notebook_id"] == "nb-123"


class TestListSources:
    """Tests for notebooklm_list_sources tool."""

    @pytest.mark.asyncio
    async def test_正常系_ソース一覧をdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にソース一覧を返すこと。"""
        sources = [
            SourceInfo(source_id="src-001", title="Paper 1", source_type="url"),
            SourceInfo(source_id="src-002", title="Notes", source_type="text"),
        ]

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_sources = AsyncMock(return_value=sources)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_sources"]
            result = await tool.fn(notebook_id="nb-123", ctx=mock_ctx)

        assert result["total"] == 2
        assert result["notebook_id"] == "nb-123"
        assert len(result["sources"]) == 2
        assert result["sources"][0]["source_id"] == "src-001"
        assert result["sources"][1]["source_type"] == "text"

    @pytest.mark.asyncio
    async def test_正常系_ソースがない場合は空リスト(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """ソースが存在しない場合、空リストを返すこと。"""
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_sources = AsyncMock(return_value=[])

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_sources"]
            result = await tool.fn(notebook_id="nb-123", ctx=mock_ctx)

        assert result["total"] == 0
        assert result["sources"] == []
        assert result["notebook_id"] == "nb-123"

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_sources = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_sources"]
            result = await tool.fn(notebook_id="", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_SessionExpiredErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """SessionExpiredError 発生時にエラー dict を返すこと。"""
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_sources = AsyncMock(
                side_effect=SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".notebooklm-session.json"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_sources"]
            result = await tool.fn(notebook_id="nb-123", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "SessionExpiredError"

"""Unit tests for NotebookLM MCP source tools.

Tests cover:
Phase 1:
- notebooklm_add_text_source: Success, validation error, SourceAddError.
- notebooklm_list_sources: Success, validation error, NotebookLMError.

Phase 2:
- notebooklm_add_url_source: Success, validation error, SourceAddError.
- notebooklm_add_file_source: Success, validation error, FileNotFoundError.
- notebooklm_get_source_details: Success, validation error, SourceAddError.
- notebooklm_delete_source: Success, validation error, SourceAddError.
- notebooklm_rename_source: Success, validation error, SourceAddError.
- notebooklm_toggle_source_selection: Success, validation error.
- notebooklm_web_research: Success, validation error, invalid mode.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.errors import SessionExpiredError, SourceAddError
from notebooklm.types import SearchResult, SourceDetails, SourceInfo


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create a mocked FastMCP Context with lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"browser_manager": MagicMock()}
    ctx.report_progress = AsyncMock(return_value=None)
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


# ---------------------------------------------------------------------------
# Phase 2 MCP tool tests
# ---------------------------------------------------------------------------


class TestAddUrlSource:
    """Tests for notebooklm_add_url_source tool."""

    @pytest.mark.asyncio
    async def test_正常系_URLソースを追加してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        expected_source = SourceInfo(
            source_id="src-abc12345",
            title="https://example.com/article",
            source_type="url",
        )

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_url_source = AsyncMock(return_value=expected_source)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_url_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                url="https://example.com/article",
                ctx=mock_ctx,
            )

        assert result["source_id"] == "src-abc12345"
        assert result["source_type"] == "url"

    @pytest.mark.asyncio
    async def test_異常系_空のurlでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_url_source = AsyncMock(
                side_effect=ValueError("url must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_url_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                url="",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_SourceAddErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_url_source = AsyncMock(
                side_effect=SourceAddError(
                    "Failed to add URL source",
                    context={"notebook_id": "nb-123", "source_type": "url"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_url_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                url="https://example.com",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "SourceAddError"


class TestAddFileSource:
    """Tests for notebooklm_add_file_source tool."""

    @pytest.mark.asyncio
    async def test_正常系_ファイルソースを追加してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        expected_source = SourceInfo(
            source_id="src-file001",
            title="report.pdf",
            source_type="file",
        )

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_file_source = AsyncMock(return_value=expected_source)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_file_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                file_path="/path/to/report.pdf",
                ctx=mock_ctx,
            )

        assert result["source_id"] == "src-file001"
        assert result["source_type"] == "file"
        assert result["title"] == "report.pdf"

    @pytest.mark.asyncio
    async def test_異常系_FileNotFoundErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.add_file_source = AsyncMock(
                side_effect=FileNotFoundError("File not found: /nonexistent.pdf"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_add_file_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                file_path="/nonexistent.pdf",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "FileNotFoundError"


class TestGetSourceDetails:
    """Tests for notebooklm_get_source_details tool."""

    @pytest.mark.asyncio
    async def test_正常系_ソース詳細をdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        expected_details = SourceDetails(
            source_id="src-001",
            title="Research Paper",
            source_type="url",
            source_url="https://example.com/paper",
            content_summary="This paper discusses AI trends.",
        )

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_source_details = AsyncMock(return_value=expected_details)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_source_details"]
            result = await tool.fn(
                notebook_id="nb-123",
                source_index=0,
                ctx=mock_ctx,
            )

        assert result["source_id"] == "src-001"
        assert result["title"] == "Research Paper"
        assert result["source_url"] == "https://example.com/paper"
        assert result["content_summary"] == "This paper discusses AI trends."

    @pytest.mark.asyncio
    async def test_異常系_負のsource_indexでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_source_details = AsyncMock(
                side_effect=ValueError("source_index must be non-negative"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_source_details"]
            result = await tool.fn(
                notebook_id="nb-123",
                source_index=-1,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"


class TestDeleteSourceTool:
    """Tests for notebooklm_delete_source tool."""

    @pytest.mark.asyncio
    async def test_正常系_ソースを削除してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_source = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                source_index=0,
                ctx=mock_ctx,
            )

        assert result["deleted"] is True
        assert result["notebook_id"] == "nb-123"
        assert result["source_index"] == 0

    @pytest.mark.asyncio
    async def test_異常系_SourceAddErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_source = AsyncMock(
                side_effect=SourceAddError(
                    "Failed to delete source",
                    context={"notebook_id": "nb-123"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                source_index=0,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "SourceAddError"


class TestRenameSourceTool:
    """Tests for notebooklm_rename_source tool."""

    @pytest.mark.asyncio
    async def test_正常系_ソースをリネームしてdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        expected_source = SourceInfo(
            source_id="src-001",
            title="Updated Name",
            source_type="text",
        )

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.rename_source = AsyncMock(return_value=expected_source)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_rename_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                source_index=0,
                new_name="Updated Name",
                ctx=mock_ctx,
            )

        assert result["title"] == "Updated Name"
        assert result["source_id"] == "src-001"

    @pytest.mark.asyncio
    async def test_異常系_空のnew_nameでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.rename_source = AsyncMock(
                side_effect=ValueError("new_name must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_rename_source"]
            result = await tool.fn(
                notebook_id="nb-123",
                source_index=0,
                new_name="",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"


class TestToggleSourceSelectionTool:
    """Tests for notebooklm_toggle_source_selection tool."""

    @pytest.mark.asyncio
    async def test_正常系_ソース選択をトグルしてdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.toggle_source_selection = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_toggle_source_selection"]
            result = await tool.fn(
                notebook_id="nb-123",
                source_index=0,
                ctx=mock_ctx,
            )

        assert result["toggled"] is True
        assert result["notebook_id"] == "nb-123"
        assert result["source_index"] == 0

    @pytest.mark.asyncio
    async def test_正常系_select_allでトグルしてdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.toggle_source_selection = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_toggle_source_selection"]
            result = await tool.fn(
                notebook_id="nb-123",
                select_all=True,
                ctx=mock_ctx,
            )

        assert result["toggled"] is True
        assert result["select_all"] is True


class TestWebResearchTool:
    """Tests for notebooklm_web_research tool."""

    @pytest.mark.asyncio
    async def test_正常系_fastリサーチでdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        expected_results = [
            SearchResult(
                title="AI Trends 2026",
                url="https://example.com/ai-trends",
                summary="Summary of AI trends",
                source_type="web",
                selected=True,
            ),
        ]

        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.web_research = AsyncMock(return_value=expected_results)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_web_research"]
            result = await tool.fn(
                notebook_id="nb-123",
                query="AI investment trends",
                mode="fast",
                ctx=mock_ctx,
            )

        assert result["total"] == 1
        assert result["mode"] == "fast"
        assert result["results"][0]["title"] == "AI Trends 2026"

    @pytest.mark.asyncio
    async def test_異常系_無効なmodeでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        from notebooklm.mcp.server import mcp

        tool = mcp._tool_manager._tools["notebooklm_web_research"]
        result = await tool.fn(
            notebook_id="nb-123",
            query="AI trends",
            mode="invalid",
            ctx=mock_ctx,
        )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_空のqueryでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch(
            "notebooklm.mcp.tools.source_tools.SourceService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.web_research = AsyncMock(
                side_effect=ValueError("query must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_web_research"]
            result = await tool.fn(
                notebook_id="nb-123",
                query="",
                mode="fast",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

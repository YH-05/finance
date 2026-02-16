"""Unit tests for NotebookLM MCP note tools.

Tests cover:
- notebooklm_create_note: Success, validation error, NotebookLMError.
- notebooklm_list_notes: Success, empty list, validation error, NotebookLMError.
- notebooklm_get_note: Success, validation error, NotebookLMError.
- notebooklm_delete_note: Success, validation error, NotebookLMError.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.errors import NotebookLMError, SessionExpiredError
from notebooklm.types import NoteContent, NoteInfo


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create a mocked FastMCP Context with lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"browser_manager": MagicMock()}
    return ctx


# ---------------------------------------------------------------------------
# notebooklm_create_note tests
# ---------------------------------------------------------------------------


class TestCreateNote:
    """Tests for notebooklm_create_note tool."""

    @pytest.mark.asyncio
    async def test_正常系_ノートを作成してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にノートを作成し、dict形式で結果を返すこと。"""
        expected_note = NoteInfo(
            note_id="note-abc12345",
            title="Research Notes",
        )

        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.create_note = AsyncMock(return_value=expected_note)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_create_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                content="Key observations from research.",
                ctx=mock_ctx,
                title="Research Notes",
            )

        assert result["note_id"] == "note-abc12345"
        assert result["title"] == "Research Notes"

    @pytest.mark.asyncio
    async def test_正常系_タイトルなしでノートを作成(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """タイトル指定なしでノートを作成できること。"""
        expected_note = NoteInfo(
            note_id="note-def67890",
            title="Untitled Note",
        )

        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.create_note = AsyncMock(return_value=expected_note)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_create_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                content="Some content here.",
                ctx=mock_ctx,
            )

        assert result["note_id"] == "note-def67890"
        assert result["title"] == "Untitled Note"

        # Verify title=None was passed to service
        mock_service.create_note.assert_awaited_once_with(
            "nb-001",
            "Some content here.",
            title=None,
        )

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.create_note = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_create_note"]
            result = await tool.fn(
                notebook_id="",
                content="Content",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_空のcontentでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の content で ValueError のエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.create_note = AsyncMock(
                side_effect=ValueError("content must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_create_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                content="",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_NotebookLMErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """NotebookLMError 発生時にエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.create_note = AsyncMock(
                side_effect=NotebookLMError(
                    "Failed to create note",
                    context={"notebook_id": "nb-001"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_create_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                content="Content",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "NotebookLMError"
        assert result["context"]["notebook_id"] == "nb-001"


# ---------------------------------------------------------------------------
# notebooklm_list_notes tests
# ---------------------------------------------------------------------------


class TestListNotes:
    """Tests for notebooklm_list_notes tool."""

    @pytest.mark.asyncio
    async def test_正常系_ノート一覧をdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にノート一覧を返すこと。"""
        notes = [
            NoteInfo(note_id="note-000", title="Note One"),
            NoteInfo(note_id="note-001", title="Note Two"),
        ]

        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_notes = AsyncMock(return_value=notes)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_notes"]
            result = await tool.fn(notebook_id="nb-001", ctx=mock_ctx)

        assert result["total"] == 2
        assert len(result["notes"]) == 2
        assert result["notes"][0]["note_id"] == "note-000"
        assert result["notes"][1]["title"] == "Note Two"

    @pytest.mark.asyncio
    async def test_正常系_ノートがない場合は空リスト(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """ノートが存在しない場合、空リストを返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_notes = AsyncMock(return_value=[])

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_notes"]
            result = await tool.fn(notebook_id="nb-001", ctx=mock_ctx)

        assert result["total"] == 0
        assert result["notes"] == []

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_notes = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_notes"]
            result = await tool.fn(notebook_id="", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_SessionExpiredErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """SessionExpiredError 発生時にエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_notes = AsyncMock(
                side_effect=SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".notebooklm-session.json"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_list_notes"]
            result = await tool.fn(notebook_id="nb-001", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "SessionExpiredError"


# ---------------------------------------------------------------------------
# notebooklm_get_note tests
# ---------------------------------------------------------------------------


class TestGetNote:
    """Tests for notebooklm_get_note tool."""

    @pytest.mark.asyncio
    async def test_正常系_ノート全文をdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にノート全文を返すこと。"""
        expected_note = NoteContent(
            note_id="note-000",
            title="Research Notes",
            content="Key observations from the research paper...",
        )

        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_note = AsyncMock(return_value=expected_note)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                note_index=0,
                ctx=mock_ctx,
            )

        assert result["note_id"] == "note-000"
        assert result["title"] == "Research Notes"
        assert result["content"] == "Key observations from the research paper..."

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_note = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_note"]
            result = await tool.fn(
                notebook_id="",
                note_index=0,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_範囲外のnote_indexでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """範囲外の note_index で ValueError のエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_note = AsyncMock(
                side_effect=ValueError("note_index 5 out of range"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                note_index=5,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_NotebookLMErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """NotebookLMError 発生時にエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_note = AsyncMock(
                side_effect=NotebookLMError(
                    "Failed to get note",
                    context={"notebook_id": "nb-001", "note_index": 0},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                note_index=0,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "NotebookLMError"


# ---------------------------------------------------------------------------
# notebooklm_delete_note tests
# ---------------------------------------------------------------------------


class TestDeleteNote:
    """Tests for notebooklm_delete_note tool."""

    @pytest.mark.asyncio
    async def test_正常系_ノートを削除してdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にノートを削除し、dict形式で結果を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_note = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                note_index=0,
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "nb-001"
        assert result["note_index"] == 0
        assert result["deleted"] is True

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空の notebook_id で ValueError のエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_note = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_note"]
            result = await tool.fn(
                notebook_id="",
                note_index=0,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_負のnote_indexでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """負の note_index で ValueError のエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_note = AsyncMock(
                side_effect=ValueError("note_index must be non-negative"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                note_index=-1,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_NotebookLMErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """NotebookLMError 発生時にエラー dict を返すこと。"""
        with patch("notebooklm.mcp.tools.note_tools.NoteService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.delete_note = AsyncMock(
                side_effect=NotebookLMError(
                    "Failed to delete note",
                    context={"notebook_id": "nb-001", "note_index": 0},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_delete_note"]
            result = await tool.fn(
                notebook_id="nb-001",
                note_index=0,
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "NotebookLMError"

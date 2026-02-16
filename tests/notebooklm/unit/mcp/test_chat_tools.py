"""Unit tests for NotebookLM MCP chat tools.

Tests cover:
- notebooklm_chat: Success, validation error, NotebookLMError.
- notebooklm_get_chat_history: Success, validation error, NotebookLMError.
- notebooklm_clear_chat_history: Success, validation error, NotebookLMError.
- notebooklm_configure_chat: Success, validation error, NotebookLMError.
- notebooklm_save_chat_to_note: Success, validation error, NotebookLMError.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.errors import ChatError, SessionExpiredError
from notebooklm.types import ChatHistory, ChatResponse


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create a mocked FastMCP Context with lifespan_context."""
    ctx = MagicMock()
    ctx.lifespan_context = {"browser_manager": MagicMock()}
    return ctx


# ---------------------------------------------------------------------------
# notebooklm_chat tests
# ---------------------------------------------------------------------------


class TestChat:
    """Tests for notebooklm_chat tool."""

    @pytest.mark.asyncio
    async def test_正常系_チャットレスポンスをdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にチャットレスポンスをdict形式で返すこと。"""
        expected_response = ChatResponse(
            notebook_id="abc-123",
            question="What are the key findings?",
            answer="The key findings include...",
            citations=["Source 1"],
            suggested_followups=["How does this compare?"],
        )

        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.chat = AsyncMock(return_value=expected_response)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_chat"]
            result = await tool.fn(
                notebook_id="abc-123",
                question="What are the key findings?",
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "abc-123"
        assert result["question"] == "What are the key findings?"
        assert result["answer"] == "The key findings include..."
        assert result["citations"] == ["Source 1"]
        assert result["suggested_followups"] == ["How does this compare?"]

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """空のnotebook_idでValueErrorのエラーdictを返すこと。"""
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.chat = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_chat"]
            result = await tool.fn(
                notebook_id="",
                question="Q",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_ChatErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """ChatError発生時にエラーdictを返すこと。"""
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.chat = AsyncMock(
                side_effect=ChatError(
                    "Chat interaction failed",
                    context={"notebook_id": "abc-123"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_chat"]
            result = await tool.fn(
                notebook_id="abc-123",
                question="Q",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ChatError"
        assert result["context"] == {"notebook_id": "abc-123"}


# ---------------------------------------------------------------------------
# notebooklm_get_chat_history tests
# ---------------------------------------------------------------------------


class TestGetChatHistory:
    """Tests for notebooklm_get_chat_history tool."""

    @pytest.mark.asyncio
    async def test_正常系_チャット履歴をdictで返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """正常にチャット履歴をdict形式で返すこと。"""
        expected_history = ChatHistory(
            notebook_id="abc-123",
            messages=[],
            total_messages=5,
        )

        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_chat_history = AsyncMock(return_value=expected_history)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_chat_history"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert result["notebook_id"] == "abc-123"
        assert result["total_messages"] == 5

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_chat_history = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_chat_history"]
            result = await tool.fn(notebook_id="", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_NotebookLMErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.get_chat_history = AsyncMock(
                side_effect=SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".notebooklm-session.json"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_get_chat_history"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "SessionExpiredError"


# ---------------------------------------------------------------------------
# notebooklm_clear_chat_history tests
# ---------------------------------------------------------------------------


class TestClearChatHistory:
    """Tests for notebooklm_clear_chat_history tool."""

    @pytest.mark.asyncio
    async def test_正常系_チャット履歴クリア成功(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.clear_chat_history = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_clear_chat_history"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert result["notebook_id"] == "abc-123"
        assert result["cleared"] is True

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.clear_chat_history = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_clear_chat_history"]
            result = await tool.fn(notebook_id="", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_ChatErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.clear_chat_history = AsyncMock(
                side_effect=ChatError(
                    "Failed to clear chat history",
                    context={"notebook_id": "abc-123"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_clear_chat_history"]
            result = await tool.fn(notebook_id="abc-123", ctx=mock_ctx)

        assert "error" in result
        assert result["error_type"] == "ChatError"


# ---------------------------------------------------------------------------
# notebooklm_configure_chat tests
# ---------------------------------------------------------------------------


class TestConfigureChat:
    """Tests for notebooklm_configure_chat tool."""

    @pytest.mark.asyncio
    async def test_正常系_チャット設定保存成功(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.configure_chat = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_configure_chat"]
            result = await tool.fn(
                notebook_id="abc-123",
                system_prompt="Be concise",
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "abc-123"
        assert result["configured"] is True

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.configure_chat = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_configure_chat"]
            result = await tool.fn(
                notebook_id="",
                system_prompt="Prompt",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_ChatErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.configure_chat = AsyncMock(
                side_effect=ChatError(
                    "Failed to configure chat",
                    context={"notebook_id": "abc-123"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_configure_chat"]
            result = await tool.fn(
                notebook_id="abc-123",
                system_prompt="Prompt",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ChatError"


# ---------------------------------------------------------------------------
# notebooklm_save_chat_to_note tests
# ---------------------------------------------------------------------------


class TestSaveChatToNote:
    """Tests for notebooklm_save_chat_to_note tool."""

    @pytest.mark.asyncio
    async def test_正常系_メモ保存成功(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.save_response_to_note = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_save_chat_to_note"]
            result = await tool.fn(
                notebook_id="abc-123",
                question="Summarize this",
                ctx=mock_ctx,
            )

        assert result["notebook_id"] == "abc-123"
        assert result["question"] == "Summarize this"
        assert result["saved"] is True

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.save_response_to_note = AsyncMock(
                side_effect=ValueError("notebook_id must not be empty"),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_save_chat_to_note"]
            result = await tool.fn(
                notebook_id="",
                question="Q",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_異常系_ChatErrorでエラーdictを返す(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.save_response_to_note = AsyncMock(
                side_effect=ChatError(
                    "Failed to save response to note",
                    context={"notebook_id": "abc-123"},
                ),
            )

            from notebooklm.mcp.server import mcp

            tool = mcp._tool_manager._tools["notebooklm_save_chat_to_note"]
            result = await tool.fn(
                notebook_id="abc-123",
                question="Q",
                ctx=mock_ctx,
            )

        assert "error" in result
        assert result["error_type"] == "ChatError"

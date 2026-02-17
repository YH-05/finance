"""Integration tests for the NotebookLM chat workflow.

Tests verify the end-to-end workflow of configuring chat settings,
sending questions, receiving AI responses, checking chat history,
saving responses to notes, and clearing chat history through the
MCP tool layer.

All tests are marked with ``@pytest.mark.playwright`` since the underlying
services use Playwright browser automation. In these integration tests,
the services are mocked to validate the coordination between MCP tools
and services without requiring a real browser.

Notes
-----
These tests are marked with ``@pytest.mark.playwright`` and require:

- Playwright to be installed: ``uv add playwright && playwright install chromium``
- CI runs should install Playwright before running these tests

Tests will be skipped automatically if:

- Playwright is not installed
- Chromium browser is not installed
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
    ctx.report_progress = AsyncMock()
    return ctx


@pytest.mark.integration
@pytest.mark.playwright
class TestChatWorkflow:
    """Integration tests for the full chat lifecycle workflow.

    Tests the sequence: configure chat -> send question -> get response
    -> save to note, verifying that all MCP chat tools work together
    correctly through the service layer.
    """

    @pytest.mark.asyncio
    async def test_正常系_チャット設定から質問回答メモ保存までの完全ワークフロー(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """チャット設定 -> 質問 -> 回答取得 -> メモ保存の完全ワークフロー。"""
        chat_response = ChatResponse(
            notebook_id="wf-chat-001",
            question="What are the key findings?",
            answer="The key findings include three major trends...",
            citations=["Source 1: Research Paper"],
            suggested_followups=["What are the implications?"],
        )

        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_chat_svc_cls:
            mock_chat_svc = mock_chat_svc_cls.return_value
            mock_chat_svc.configure_chat = AsyncMock(return_value=True)
            mock_chat_svc.chat = AsyncMock(return_value=chat_response)
            mock_chat_svc.save_response_to_note = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            # Step 1: Configure chat settings
            configure_tool = mcp._tool_manager._tools["notebooklm_configure_chat"]
            configure_result = await configure_tool.fn(
                notebook_id="wf-chat-001",
                system_prompt="Answer concisely in Japanese",
                ctx=mock_ctx,
            )

            assert configure_result["notebook_id"] == "wf-chat-001"
            assert configure_result["configured"] is True

            # Step 2: Send a chat question
            chat_tool = mcp._tool_manager._tools["notebooklm_chat"]
            chat_result = await chat_tool.fn(
                notebook_id="wf-chat-001",
                question="What are the key findings?",
                ctx=mock_ctx,
            )

            assert chat_result["notebook_id"] == "wf-chat-001"
            assert chat_result["question"] == "What are the key findings?"
            assert (
                chat_result["answer"]
                == "The key findings include three major trends..."
            )
            assert chat_result["citations"] == ["Source 1: Research Paper"]
            assert len(chat_result["suggested_followups"]) == 1

            # Step 3: Save a follow-up response to a note
            save_tool = mcp._tool_manager._tools["notebooklm_save_chat_to_note"]
            save_result = await save_tool.fn(
                notebook_id="wf-chat-001",
                question="What are the implications?",
                ctx=mock_ctx,
            )

            assert save_result["notebook_id"] == "wf-chat-001"
            assert save_result["saved"] is True

    @pytest.mark.asyncio
    async def test_正常系_質問から履歴確認までのワークフロー(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """質問 -> 回答取得 -> 履歴確認のワークフロー。"""
        chat_response = ChatResponse(
            notebook_id="wf-chat-002",
            question="Summarize the document",
            answer="The document discusses AI applications in finance...",
            citations=[],
            suggested_followups=[],
        )
        history_after_chat = ChatHistory(
            notebook_id="wf-chat-002",
            messages=[],
            total_messages=1,
        )

        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_chat_svc_cls:
            mock_chat_svc = mock_chat_svc_cls.return_value
            mock_chat_svc.chat = AsyncMock(return_value=chat_response)
            mock_chat_svc.get_chat_history = AsyncMock(
                return_value=history_after_chat,
            )

            from notebooklm.mcp.server import mcp

            # Step 1: Send a chat question
            chat_tool = mcp._tool_manager._tools["notebooklm_chat"]
            chat_result = await chat_tool.fn(
                notebook_id="wf-chat-002",
                question="Summarize the document",
                ctx=mock_ctx,
            )

            assert chat_result["notebook_id"] == "wf-chat-002"
            assert "AI applications" in chat_result["answer"]

            # Step 2: Check chat history
            history_tool = mcp._tool_manager._tools["notebooklm_get_chat_history"]
            history_result = await history_tool.fn(
                notebook_id="wf-chat-002",
                ctx=mock_ctx,
            )

            assert history_result["notebook_id"] == "wf-chat-002"
            assert history_result["total_messages"] == 1

    @pytest.mark.asyncio
    async def test_正常系_複数質問と履歴クリアのワークフロー(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """複数質問 -> 履歴確認 -> 履歴クリア -> 履歴再確認のワークフロー。"""
        response_1 = ChatResponse(
            notebook_id="wf-chat-003",
            question="What is AI?",
            answer="AI stands for Artificial Intelligence...",
            citations=[],
            suggested_followups=["What are AI applications?"],
        )
        response_2 = ChatResponse(
            notebook_id="wf-chat-003",
            question="What are AI applications?",
            answer="AI applications include healthcare, finance...",
            citations=["Source 2"],
            suggested_followups=[],
        )
        history_after_two = ChatHistory(
            notebook_id="wf-chat-003",
            messages=[],
            total_messages=2,
        )
        history_after_clear = ChatHistory(
            notebook_id="wf-chat-003",
            messages=[],
            total_messages=0,
        )

        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_chat_svc_cls:
            mock_chat_svc = mock_chat_svc_cls.return_value
            mock_chat_svc.chat = AsyncMock(
                side_effect=[response_1, response_2],
            )
            mock_chat_svc.get_chat_history = AsyncMock(
                side_effect=[history_after_two, history_after_clear],
            )
            mock_chat_svc.clear_chat_history = AsyncMock(return_value=True)

            from notebooklm.mcp.server import mcp

            chat_tool = mcp._tool_manager._tools["notebooklm_chat"]

            # Step 1: Send first question
            result_1 = await chat_tool.fn(
                notebook_id="wf-chat-003",
                question="What is AI?",
                ctx=mock_ctx,
            )
            assert result_1["answer"] == "AI stands for Artificial Intelligence..."

            # Step 2: Send follow-up question
            result_2 = await chat_tool.fn(
                notebook_id="wf-chat-003",
                question="What are AI applications?",
                ctx=mock_ctx,
            )
            assert (
                result_2["answer"] == "AI applications include healthcare, finance..."
            )

            # Step 3: Check history has 2 messages
            history_tool = mcp._tool_manager._tools["notebooklm_get_chat_history"]
            history_result = await history_tool.fn(
                notebook_id="wf-chat-003",
                ctx=mock_ctx,
            )
            assert history_result["total_messages"] == 2

            # Step 4: Clear chat history
            clear_tool = mcp._tool_manager._tools["notebooklm_clear_chat_history"]
            clear_result = await clear_tool.fn(
                notebook_id="wf-chat-003",
                ctx=mock_ctx,
            )
            assert clear_result["cleared"] is True

            # Step 5: Verify history is empty
            history_result_2 = await history_tool.fn(
                notebook_id="wf-chat-003",
                ctx=mock_ctx,
            )
            assert history_result_2["total_messages"] == 0


@pytest.mark.integration
@pytest.mark.playwright
class TestChatLifespanIntegration:
    """Integration tests for lifespan and ChatService coordination."""

    @pytest.mark.asyncio
    async def test_正常系_lifespanコンテキストからChatService初期化まで(
        self,
    ) -> None:
        """lifespan から browser_manager 取得 -> ChatService 初期化の連携を検証。"""
        from notebooklm.mcp.server import notebooklm_lifespan
        from notebooklm.services.chat import ChatService

        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_manager)
        mock_manager.close = AsyncMock()
        mock_manager.headless = True
        mock_manager.has_session = MagicMock(return_value=True)

        with patch(
            "notebooklm.browser.manager.NotebookLMBrowserManager",
            return_value=mock_manager,
        ):
            async with notebooklm_lifespan(None) as context:
                browser_manager = context["browser_manager"]

                # Verify ChatService can be instantiated with the browser manager
                chat_service = ChatService(browser_manager)

                assert chat_service._browser_manager is browser_manager

        # Verify cleanup
        mock_manager.close.assert_called_once()


@pytest.mark.integration
@pytest.mark.playwright
class TestChatErrorPropagation:
    """Integration tests for error propagation across chat tool boundaries."""

    @pytest.mark.asyncio
    async def test_異常系_セッション期限切れ時にチャットワークフロー全体がエラー返却(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """セッション期限切れ時、チャット各ステップでエラーが返却されること。"""
        session_error = SessionExpiredError(
            "Session expired, re-authentication required",
            context={
                "session_file": ".notebooklm-session.json",
                "last_used": "2026-02-15T10:00:00Z",
            },
        )

        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_chat_svc_cls:
            mock_chat_svc = mock_chat_svc_cls.return_value
            mock_chat_svc.chat = AsyncMock(side_effect=session_error)
            mock_chat_svc.configure_chat = AsyncMock(side_effect=session_error)
            mock_chat_svc.get_chat_history = AsyncMock(side_effect=session_error)

            from notebooklm.mcp.server import mcp

            # Chat should fail
            chat_tool = mcp._tool_manager._tools["notebooklm_chat"]
            chat_result = await chat_tool.fn(
                notebook_id="wf-chat-err",
                question="Test question",
                ctx=mock_ctx,
            )

            assert "error" in chat_result
            assert chat_result["error_type"] == "SessionExpiredError"

            # Configure should also fail
            configure_tool = mcp._tool_manager._tools["notebooklm_configure_chat"]
            configure_result = await configure_tool.fn(
                notebook_id="wf-chat-err",
                system_prompt="Test prompt",
                ctx=mock_ctx,
            )

            assert "error" in configure_result
            assert configure_result["error_type"] == "SessionExpiredError"

            # History should also fail
            history_tool = mcp._tool_manager._tools["notebooklm_get_chat_history"]
            history_result = await history_tool.fn(
                notebook_id="wf-chat-err",
                ctx=mock_ctx,
            )

            assert "error" in history_result
            assert history_result["error_type"] == "SessionExpiredError"

    @pytest.mark.asyncio
    async def test_異常系_チャット設定成功後にチャット送信失敗(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """チャット設定成功後、チャット送信でChatErrorが発生するケース。"""
        chat_error = ChatError(
            "AI response not received within timeout",
            context={
                "notebook_id": "wf-chat-partial",
                "question": "Complex question",
                "timeout_ms": 30000,
            },
        )

        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_chat_svc_cls:
            mock_chat_svc = mock_chat_svc_cls.return_value
            mock_chat_svc.configure_chat = AsyncMock(return_value=True)
            mock_chat_svc.chat = AsyncMock(side_effect=chat_error)

            from notebooklm.mcp.server import mcp

            # Step 1: Configure succeeds
            configure_tool = mcp._tool_manager._tools["notebooklm_configure_chat"]
            configure_result = await configure_tool.fn(
                notebook_id="wf-chat-partial",
                system_prompt="Be concise",
                ctx=mock_ctx,
            )

            assert configure_result["configured"] is True
            assert "error" not in configure_result

            # Step 2: Chat fails with timeout
            chat_tool = mcp._tool_manager._tools["notebooklm_chat"]
            chat_result = await chat_tool.fn(
                notebook_id="wf-chat-partial",
                question="Complex question",
                ctx=mock_ctx,
            )

            assert "error" in chat_result
            assert chat_result["error_type"] == "ChatError"
            assert chat_result["context"]["notebook_id"] == "wf-chat-partial"
            assert chat_result["context"]["timeout_ms"] == 30000

    @pytest.mark.asyncio
    async def test_異常系_メモ保存失敗時にチャット応答は成功済み(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """チャット応答取得成功後、メモ保存で失敗するケース。"""
        chat_response = ChatResponse(
            notebook_id="wf-chat-note-fail",
            question="Summarize findings",
            answer="The main findings are...",
            citations=[],
            suggested_followups=[],
        )
        save_error = ChatError(
            "Failed to save response to note: save button not found",
            context={
                "notebook_id": "wf-chat-note-fail",
                "question": "Summarize findings",
            },
        )

        with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_chat_svc_cls:
            mock_chat_svc = mock_chat_svc_cls.return_value
            mock_chat_svc.chat = AsyncMock(return_value=chat_response)
            mock_chat_svc.save_response_to_note = AsyncMock(side_effect=save_error)

            from notebooklm.mcp.server import mcp

            # Step 1: Chat succeeds
            chat_tool = mcp._tool_manager._tools["notebooklm_chat"]
            chat_result = await chat_tool.fn(
                notebook_id="wf-chat-note-fail",
                question="Summarize findings",
                ctx=mock_ctx,
            )

            assert chat_result["answer"] == "The main findings are..."
            assert "error" not in chat_result

            # Step 2: Save to note fails
            save_tool = mcp._tool_manager._tools["notebooklm_save_chat_to_note"]
            save_result = await save_tool.fn(
                notebook_id="wf-chat-note-fail",
                question="Summarize findings",
                ctx=mock_ctx,
            )

            assert "error" in save_result
            assert save_result["error_type"] == "ChatError"
            assert save_result["context"]["notebook_id"] == "wf-chat-note-fail"

    @pytest.mark.asyncio
    async def test_正常系_各チャットツールのエラー型が正しくdict化される(
        self,
        mock_ctx: MagicMock,
    ) -> None:
        """異なるエラー型が各チャットツールで正しく dict に変換されること。"""
        from notebooklm.mcp.server import mcp

        error_cases = [
            (
                "notebooklm_chat",
                {"notebook_id": "nb-1", "question": "Q", "ctx": mock_ctx},
                "chat",
                ChatError(
                    "Chat interaction failed",
                    context={"notebook_id": "nb-1"},
                ),
                "ChatError",
            ),
            (
                "notebooklm_get_chat_history",
                {"notebook_id": "nb-1", "ctx": mock_ctx},
                "get_chat_history",
                SessionExpiredError(
                    "Session expired",
                    context={"session_file": ".session.json"},
                ),
                "SessionExpiredError",
            ),
            (
                "notebooklm_clear_chat_history",
                {"notebook_id": "nb-1", "ctx": mock_ctx},
                "clear_chat_history",
                ChatError(
                    "Failed to clear chat",
                    context={"notebook_id": "nb-1"},
                ),
                "ChatError",
            ),
            (
                "notebooklm_configure_chat",
                {
                    "notebook_id": "nb-1",
                    "system_prompt": "Be concise",
                    "ctx": mock_ctx,
                },
                "configure_chat",
                ChatError(
                    "Failed to configure",
                    context={"notebook_id": "nb-1"},
                ),
                "ChatError",
            ),
            (
                "notebooklm_save_chat_to_note",
                {"notebook_id": "nb-1", "question": "Q", "ctx": mock_ctx},
                "save_response_to_note",
                ChatError(
                    "Failed to save to note",
                    context={"notebook_id": "nb-1"},
                ),
                "ChatError",
            ),
        ]

        for (
            tool_name,
            tool_kwargs,
            method_name,
            error,
            expected_error_type,
        ) in error_cases:
            with patch("notebooklm.mcp.tools.chat_tools.ChatService") as mock_svc_cls:
                mock_svc = mock_svc_cls.return_value
                setattr(
                    mock_svc,
                    method_name,
                    AsyncMock(side_effect=error),
                )

                tool = mcp._tool_manager._tools[tool_name]
                result = await tool.fn(**tool_kwargs)

                assert "error" in result, f"Tool {tool_name} did not return error dict"
                assert result["error_type"] == expected_error_type, (
                    f"Tool {tool_name}: expected {expected_error_type}, "
                    f"got {result['error_type']}"
                )

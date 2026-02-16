"""Unit tests for ChatService.

Tests cover:
- chat: Sends a question and retrieves the AI response via clipboard.
- get_chat_history: Gets chat history for a notebook.
- clear_chat_history: Clears chat history via options menu.
- configure_chat: Configures chat settings (system prompt).
- save_response_to_note: Sends a question and saves the response to a note.
- DI: Service receives BrowserManager via constructor injection.
- Error paths: empty notebook_id, empty question, ChatError wrapping.
- Private helpers: _wait_for_response, _copy_response_via_clipboard.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.browser.manager import NotebookLMBrowserManager
from notebooklm.errors import ChatError, ElementNotFoundError
from notebooklm.services.chat import ChatService
from notebooklm.types import ChatHistory, ChatResponse

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create a mocked Playwright Page with locator support."""
    page = AsyncMock()
    page.url = "https://notebooklm.google.com/notebook/nb-001"
    page.goto = AsyncMock(return_value=None)
    page.wait_for_load_state = AsyncMock(return_value=None)
    page.close = AsyncMock(return_value=None)
    page.evaluate = AsyncMock(return_value="AI response text in Markdown format")
    return page


@pytest.fixture
def mock_manager(mock_page: AsyncMock) -> MagicMock:
    """Create a mocked NotebookLMBrowserManager."""
    manager = MagicMock(spec=NotebookLMBrowserManager)
    manager.new_page = AsyncMock(return_value=mock_page)
    manager.headless = True
    manager.session_file = ".notebooklm-session.json"
    return manager


@pytest.fixture
def chat_service(mock_manager: MagicMock) -> ChatService:
    """Create a ChatService with mocked BrowserManager."""
    return ChatService(mock_manager)


def _make_interactive_locator(
    count: int = 1,
    *,
    inner_text: str = "",
) -> AsyncMock:
    """Create a mock locator with standard interactive methods."""
    locator = AsyncMock()
    locator.wait_for = AsyncMock(return_value=None)
    locator.count = AsyncMock(return_value=count)
    locator.first = locator
    locator.click = AsyncMock(return_value=None)
    locator.fill = AsyncMock(return_value=None)
    locator.inner_text = AsyncMock(return_value=inner_text)
    locator.all = AsyncMock(return_value=[])

    # Support nth() for indexed access
    def nth_fn(idx: int) -> AsyncMock:
        nth_locator = AsyncMock()
        nth_locator.click = AsyncMock(return_value=None)
        nth_locator.inner_text = AsyncMock(return_value=inner_text)
        return nth_locator

    locator.nth = MagicMock(side_effect=nth_fn)
    return locator


# ---------------------------------------------------------------------------
# DI tests
# ---------------------------------------------------------------------------


class TestChatServiceInit:
    """Test ChatService initialization and DI."""

    def test_正常系_BrowserManagerをDIで受け取る(self, mock_manager: MagicMock) -> None:
        service = ChatService(mock_manager)
        assert service._browser_manager is mock_manager

    def test_正常系_SelectorManagerが初期化される(
        self, chat_service: ChatService
    ) -> None:
        assert chat_service._selectors is not None


# ---------------------------------------------------------------------------
# chat tests
# ---------------------------------------------------------------------------


class TestChat:
    """Test ChatService.chat()."""

    @pytest.mark.asyncio
    async def test_正常系_質問を送信してChatResponseを返す(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Set up locators for chat flow
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)
        mock_page.evaluate = AsyncMock(return_value="The key findings include...")

        # Act
        result = await chat_service.chat("nb-001", "What are the key findings?")

        # Assert
        assert isinstance(result, ChatResponse)
        assert result.notebook_id == "nb-001"
        assert result.question == "What are the key findings?"
        assert result.answer == "The key findings include..."

    @pytest.mark.asyncio
    async def test_正常系_クリップボードから回答テキストを取得(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        """Response text is retrieved via clipboard copy button."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)
        mock_page.evaluate = AsyncMock(return_value="# Heading\n\nMarkdown response")

        result = await chat_service.chat("nb-001", "Summarize")

        assert "Markdown response" in result.answer
        # Verify clipboard read was called
        mock_page.evaluate.assert_awaited()

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.chat("", "What is this?")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.chat("   ", "What is this?")

    @pytest.mark.asyncio
    async def test_異常系_空のquestionでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="question must not be empty"):
            await chat_service.chat("nb-001", "")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのquestionでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="question must not be empty"):
            await chat_service.chat("nb-001", "   ")

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でChatError(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        """Non-ValueError exceptions are wrapped as ChatError."""
        with (
            patch(
                "notebooklm.services.chat.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "textbox"},
                ),
            ),
            pytest.raises(ChatError, match="Chat interaction failed"),
        ):
            await chat_service.chat("nb-001", "What is this?")

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)
        mock_page.evaluate = AsyncMock(return_value="Response text")

        await chat_service.chat("nb-001", "Question")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_エラー発生時もページがcloseされる(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        """Page is closed even when an error occurs during chat."""
        with (
            patch(
                "notebooklm.services.chat.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "textbox"},
                ),
            ),
            pytest.raises(ChatError),
        ):
            await chat_service.chat("nb-001", "Question")

        mock_page.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_chat_history tests
# ---------------------------------------------------------------------------


class TestGetChatHistory:
    """Test ChatService.get_chat_history()."""

    @pytest.mark.asyncio
    async def test_正常系_チャット履歴を取得(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: copy buttons indicate 3 messages in history
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=3)
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Act
        result = await chat_service.get_chat_history("nb-001")

        # Assert
        assert isinstance(result, ChatHistory)
        assert result.notebook_id == "nb-001"
        assert result.total_messages == 3

    @pytest.mark.asyncio
    async def test_正常系_履歴がない場合はゼロ件(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=0)
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await chat_service.get_chat_history("nb-001")

        assert result.total_messages == 0

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.get_chat_history("")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.get_chat_history("   ")

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=0)
        mock_page.locator = MagicMock(return_value=mock_locator)

        await chat_service.get_chat_history("nb-001")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でChatError(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        with (
            patch(
                "notebooklm.services.chat.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(ChatError, match="Failed to get chat history"),
        ):
            await chat_service.get_chat_history("nb-001")


# ---------------------------------------------------------------------------
# clear_chat_history tests
# ---------------------------------------------------------------------------


class TestClearChatHistory:
    """Test ChatService.clear_chat_history()."""

    @pytest.mark.asyncio
    async def test_正常系_チャット履歴をクリア(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await chat_service.clear_chat_history("nb-001")

        assert result is True

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.clear_chat_history("")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.clear_chat_history("   ")

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        await chat_service.clear_chat_history("nb-001")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でChatError(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        with (
            patch(
                "notebooklm.services.chat.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(ChatError, match="Failed to clear chat history"),
        ):
            await chat_service.clear_chat_history("nb-001")


# ---------------------------------------------------------------------------
# configure_chat tests
# ---------------------------------------------------------------------------


class TestConfigureChat:
    """Test ChatService.configure_chat()."""

    @pytest.mark.asyncio
    async def test_正常系_チャット設定を保存(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await chat_service.configure_chat(
            "nb-001", "Answer concisely in Japanese"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.configure_chat("", "Some prompt")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.configure_chat("   ", "Some prompt")

    @pytest.mark.asyncio
    async def test_異常系_空のsystem_promptでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="system_prompt must not be empty"):
            await chat_service.configure_chat("nb-001", "")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのsystem_promptでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="system_prompt must not be empty"):
            await chat_service.configure_chat("nb-001", "   ")

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        await chat_service.configure_chat("nb-001", "Be concise")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でChatError(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        with (
            patch(
                "notebooklm.services.chat.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(ChatError, match="Failed to configure chat"),
        ):
            await chat_service.configure_chat("nb-001", "Some prompt")


# ---------------------------------------------------------------------------
# save_response_to_note tests
# ---------------------------------------------------------------------------


class TestSaveResponseToNote:
    """Test ChatService.save_response_to_note()."""

    @pytest.mark.asyncio
    async def test_正常系_回答をメモに保存(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: mock locator with save button
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await chat_service.save_response_to_note("nb-001", "Summarize this")

        assert result is True

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.save_response_to_note("", "Question")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await chat_service.save_response_to_note("   ", "Question")

    @pytest.mark.asyncio
    async def test_異常系_空のquestionでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="question must not be empty"):
            await chat_service.save_response_to_note("nb-001", "")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのquestionでValueError(
        self,
        chat_service: ChatService,
    ) -> None:
        with pytest.raises(ValueError, match="question must not be empty"):
            await chat_service.save_response_to_note("nb-001", "   ")

    @pytest.mark.asyncio
    async def test_正常系_保存ボタンがない場合はFalseを返す(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        """When no save button is found, returns False."""
        # Mock: copy button exists (response received), but save button count=0
        call_count = 0

        def locator_dispatch(selector: str) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            if "メモに保存" in selector:
                return _make_interactive_locator(count=0)
            return _make_interactive_locator(count=1)

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        result = await chat_service.save_response_to_note("nb-001", "Summarize")

        assert result is False

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        await chat_service.save_response_to_note("nb-001", "Question")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でChatError(
        self,
        chat_service: ChatService,
        mock_page: AsyncMock,
    ) -> None:
        with (
            patch(
                "notebooklm.services.chat.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(ChatError, match="Failed to save response to note"),
        ):
            await chat_service.save_response_to_note("nb-001", "Question")


# ---------------------------------------------------------------------------
# _wait_for_response tests
# ---------------------------------------------------------------------------


class TestWaitForResponse:
    """Test ChatService._wait_for_response() private method."""

    @pytest.mark.asyncio
    async def test_正常系_コピーボタン検出で完了(
        self,
        chat_service: ChatService,
    ) -> None:
        """Response detection completes when copy button appears."""
        page = AsyncMock()
        copy_locator = AsyncMock()
        copy_locator.count = AsyncMock(return_value=1)
        page.locator = MagicMock(return_value=copy_locator)

        # Should complete without error
        await chat_service._wait_for_response(page)

    @pytest.mark.asyncio
    async def test_異常系_タイムアウトでChatError(
        self,
        chat_service: ChatService,
    ) -> None:
        """Timeout when no copy button appears raises ChatError."""
        page = AsyncMock()
        copy_locator = AsyncMock()
        copy_locator.count = AsyncMock(return_value=0)
        page.locator = MagicMock(return_value=copy_locator)

        # Override timeout to make test fast
        with (
            patch("notebooklm.services.chat.CHAT_RESPONSE_TIMEOUT_MS", 100),
            patch("notebooklm.services.chat.GENERATION_POLL_INTERVAL_SECONDS", 0.01),
            pytest.raises(ChatError, match="AI response not received"),
        ):
            await chat_service._wait_for_response(page)


# ---------------------------------------------------------------------------
# _copy_response_via_clipboard tests
# ---------------------------------------------------------------------------


class TestCopyResponseViaClipboard:
    """Test ChatService._copy_response_via_clipboard() private method."""

    @pytest.mark.asyncio
    async def test_正常系_クリップボードからテキストを取得(
        self,
        chat_service: ChatService,
    ) -> None:
        """Clipboard content is returned when available."""
        page = AsyncMock()
        copy_locator = AsyncMock()
        copy_locator.count = AsyncMock(return_value=1)
        copy_locator.nth = MagicMock(
            return_value=AsyncMock(click=AsyncMock(return_value=None))
        )
        page.locator = MagicMock(return_value=copy_locator)
        page.evaluate = AsyncMock(return_value="Clipboard text content")

        result = await chat_service._copy_response_via_clipboard(page)

        assert result == "Clipboard text content"

    @pytest.mark.asyncio
    async def test_正常系_コピーボタンがない場合は空文字(
        self,
        chat_service: ChatService,
    ) -> None:
        """Empty string returned when no copy button is found."""
        page = AsyncMock()
        copy_locator = AsyncMock()
        copy_locator.count = AsyncMock(return_value=0)
        page.locator = MagicMock(return_value=copy_locator)

        result = await chat_service._copy_response_via_clipboard(page)

        assert result == ""

    @pytest.mark.asyncio
    async def test_正常系_クリップボード読み取り失敗でDOMフォールバック(
        self,
        chat_service: ChatService,
    ) -> None:
        """Falls back to DOM extraction when clipboard read fails."""
        page = AsyncMock()
        copy_locator = AsyncMock()
        copy_locator.count = AsyncMock(return_value=1)
        copy_locator.nth = MagicMock(
            return_value=AsyncMock(click=AsyncMock(return_value=None))
        )
        page.locator = MagicMock(return_value=copy_locator)
        page.evaluate = AsyncMock(side_effect=RuntimeError("Clipboard denied"))

        # DOM fallback also returns the locator
        dom_locator = AsyncMock()
        dom_locator.count = AsyncMock(return_value=1)
        dom_locator.nth = MagicMock(
            return_value=AsyncMock(
                inner_text=AsyncMock(return_value="DOM extracted text")
            )
        )

        call_count = 0

        def locator_dispatch(selector: str) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            if "chat-message" in selector or "response-content" in selector:
                return dom_locator
            return copy_locator

        page.locator = MagicMock(side_effect=locator_dispatch)

        result = await chat_service._copy_response_via_clipboard(page)

        assert result == "DOM extracted text"

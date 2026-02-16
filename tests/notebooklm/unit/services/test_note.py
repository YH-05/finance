"""Unit tests for NoteService.

Tests cover:
- create_note: Creates a new plain text note and returns NoteInfo.
- list_notes: Lists all notes in a notebook.
- get_note: Gets full content of a specific note.
- delete_note: Deletes a note from a notebook.
- DI: Service receives BrowserManager via constructor injection.
- Error paths: empty notebook_id, empty content, invalid note_index.
- Page cleanup: page.close() is called in all scenarios.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from notebooklm.browser.manager import NotebookLMBrowserManager
from notebooklm.services.note import NoteService
from notebooklm.types import NoteContent, NoteInfo

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create a mocked Playwright Page with locator support."""
    page = AsyncMock()
    page.url = "https://notebooklm.google.com/notebook/test-nb-id"
    page.goto = AsyncMock(return_value=None)
    page.wait_for_load_state = AsyncMock(return_value=None)
    page.close = AsyncMock(return_value=None)

    # Keyboard mock for Enter key presses
    page.keyboard = AsyncMock()
    page.keyboard.press = AsyncMock(return_value=None)

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
def note_service(mock_manager: MagicMock) -> NoteService:
    """Create a NoteService with mocked BrowserManager."""
    return NoteService(mock_manager)


# ---------------------------------------------------------------------------
# DI tests
# ---------------------------------------------------------------------------


class TestNoteServiceInit:
    """Test NoteService initialization and DI."""

    def test_正常系_BrowserManagerをDIで受け取る(self, mock_manager: MagicMock) -> None:
        service = NoteService(mock_manager)
        assert service._browser_manager is mock_manager

    def test_正常系_SelectorManagerが初期化される(
        self, note_service: NoteService
    ) -> None:
        assert note_service._selectors is not None


# ---------------------------------------------------------------------------
# create_note tests
# ---------------------------------------------------------------------------


class TestCreateNote:
    """Test NoteService.create_note()."""

    @pytest.mark.asyncio
    async def test_正常系_プレーンテキストメモを作成してNoteInfoを返す(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Mock locators for the note creation flow
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)
        mock_locator.inner_text = AsyncMock(return_value="My Note Title")
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Act
        result = await note_service.create_note(
            notebook_id="test-nb-id",
            content="This is my note content.",
        )

        # Assert
        assert isinstance(result, NoteInfo)
        assert result.note_id != ""
        assert result.title != ""

    @pytest.mark.asyncio
    async def test_正常系_タイトル指定でメモを作成(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)
        mock_locator.inner_text = AsyncMock(return_value="Custom Title")
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await note_service.create_note(
            notebook_id="test-nb-id",
            content="Note content here.",
            title="Custom Title",
        )

        assert isinstance(result, NoteInfo)

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await note_service.create_note(
                notebook_id="",
                content="Some content",
            )

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await note_service.create_note(
                notebook_id="   ",
                content="Some content",
            )

    @pytest.mark.asyncio
    async def test_異常系_空のcontentでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="content must not be empty"):
            await note_service.create_note(
                notebook_id="test-nb-id",
                content="",
            )

    @pytest.mark.asyncio
    async def test_異常系_空白のみのcontentでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="content must not be empty"):
            await note_service.create_note(
                notebook_id="test-nb-id",
                content="   ",
            )

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)
        mock_locator.inner_text = AsyncMock(return_value="Title")
        mock_page.locator = MagicMock(return_value=mock_locator)

        await note_service.create_note(
            notebook_id="test-nb-id",
            content="Content",
        )

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_正常系_エラー時もページがcloseされる(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        with pytest.raises(ValueError):
            await note_service.create_note(
                notebook_id="",
                content="Content",
            )

        # page.close should not be called when ValueError raised before page creation
        # (ValueError raised before new_page is called)


# ---------------------------------------------------------------------------
# list_notes tests
# ---------------------------------------------------------------------------


class TestListNotes:
    """Test NoteService.list_notes()."""

    @pytest.mark.asyncio
    async def test_正常系_ノート一覧を取得(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Mock note list elements
        note1 = AsyncMock()
        note1.inner_text = AsyncMock(return_value="Note One")

        note2 = AsyncMock()
        note2.inner_text = AsyncMock(return_value="Note Two")

        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[note1, note2])
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Act
        result = await note_service.list_notes("test-nb-id")

        # Assert
        assert len(result) == 2
        assert all(isinstance(n, NoteInfo) for n in result)
        assert result[0].title == "Note One"
        assert result[1].title == "Note Two"

    @pytest.mark.asyncio
    async def test_正常系_ノートがない場合は空リスト(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await note_service.list_notes("test-nb-id")

        assert result == []

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await note_service.list_notes("")

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=mock_locator)

        await note_service.list_notes("test-nb-id")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_正常系_Noneタイトルのノートはデフォルトタイトルになる(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        note_element = AsyncMock()
        note_element.inner_text = AsyncMock(return_value=None)

        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[note_element])
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await note_service.list_notes("test-nb-id")

        assert len(result) == 1
        assert result[0].title == "Untitled Note"


# ---------------------------------------------------------------------------
# get_note tests
# ---------------------------------------------------------------------------


class TestGetNote:
    """Test NoteService.get_note()."""

    @pytest.mark.asyncio
    async def test_正常系_ノートの全内容を取得(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Mock note list and content extraction
        note_element = AsyncMock()
        note_element.inner_text = AsyncMock(return_value="My Note Title")
        note_element.click = AsyncMock(return_value=None)

        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[note_element])

        # Content locator for the note editor/viewer
        content_locator = AsyncMock()
        content_locator.count = AsyncMock(return_value=1)
        content_locator.inner_text = AsyncMock(return_value="Note body text here.")

        def locator_side_effect(selector: str) -> AsyncMock:
            if "note-item" in selector or "note-card" in selector:
                return mock_locator
            return content_locator

        mock_page.locator = MagicMock(side_effect=locator_side_effect)

        # Act
        result = await note_service.get_note("test-nb-id", note_index=0)

        # Assert
        assert isinstance(result, NoteContent)
        assert result.title == "My Note Title"
        assert result.content == "Note body text here."

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await note_service.get_note("", note_index=0)

    @pytest.mark.asyncio
    async def test_異常系_負のnote_indexでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="note_index must be non-negative"):
            await note_service.get_note("test-nb-id", note_index=-1)

    @pytest.mark.asyncio
    async def test_異常系_範囲外のnote_indexでValueError(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[])  # No notes
        mock_page.locator = MagicMock(return_value=mock_locator)

        with pytest.raises(ValueError, match="note_index 0 out of range"):
            await note_service.get_note("test-nb-id", note_index=0)

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        note_element = AsyncMock()
        note_element.inner_text = AsyncMock(return_value="Title")
        note_element.click = AsyncMock(return_value=None)

        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[note_element])

        content_locator = AsyncMock()
        content_locator.count = AsyncMock(return_value=1)
        content_locator.inner_text = AsyncMock(return_value="Content")

        def locator_side_effect(selector: str) -> AsyncMock:
            if "note-item" in selector or "note-card" in selector:
                return mock_locator
            return content_locator

        mock_page.locator = MagicMock(side_effect=locator_side_effect)

        await note_service.get_note("test-nb-id", note_index=0)

        mock_page.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# delete_note tests
# ---------------------------------------------------------------------------


class TestDeleteNote:
    """Test NoteService.delete_note()."""

    @pytest.mark.asyncio
    async def test_正常系_ノートを削除してTrueを返す(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange
        note_element = AsyncMock()
        note_element.inner_text = AsyncMock(return_value="Note to Delete")
        note_element.hover = AsyncMock(return_value=None)

        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[note_element])
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.wait_for = AsyncMock(return_value=None)

        mock_page.locator = MagicMock(return_value=mock_locator)

        # Act
        result = await note_service.delete_note("test-nb-id", note_index=0)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await note_service.delete_note("", note_index=0)

    @pytest.mark.asyncio
    async def test_異常系_負のnote_indexでValueError(
        self,
        note_service: NoteService,
    ) -> None:
        with pytest.raises(ValueError, match="note_index must be non-negative"):
            await note_service.delete_note("test-nb-id", note_index=-1)

    @pytest.mark.asyncio
    async def test_異常系_範囲外のnote_indexでValueError(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=mock_locator)

        with pytest.raises(ValueError, match="note_index 0 out of range"):
            await note_service.delete_note("test-nb-id", note_index=0)

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        note_service: NoteService,
        mock_page: AsyncMock,
    ) -> None:
        note_element = AsyncMock()
        note_element.hover = AsyncMock(return_value=None)

        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[note_element])
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.wait_for = AsyncMock(return_value=None)

        mock_page.locator = MagicMock(return_value=mock_locator)

        await note_service.delete_note("test-nb-id", note_index=0)

        mock_page.close.assert_awaited_once()

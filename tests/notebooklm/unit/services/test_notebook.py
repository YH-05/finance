"""Unit tests for NotebookService.

Tests cover:
- create_notebook: Creates a new notebook and returns NotebookInfo.
- list_notebooks: Lists all notebooks from the home page.
- get_notebook_summary: Gets AI-generated summary for a notebook.
- DI: Service receives BrowserManager via constructor injection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.browser.manager import NotebookLMBrowserManager
from notebooklm.services.notebook import NotebookService
from notebooklm.types import NotebookInfo, NotebookSummary

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create a mocked Playwright Page with locator support."""
    page = AsyncMock()
    page.url = "https://notebooklm.google.com"
    page.goto = AsyncMock(return_value=None)
    page.wait_for_load_state = AsyncMock(return_value=None)
    page.close = AsyncMock(return_value=None)
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
def notebook_service(mock_manager: MagicMock) -> NotebookService:
    """Create a NotebookService with mocked BrowserManager."""
    return NotebookService(mock_manager)


# ---------------------------------------------------------------------------
# DI tests
# ---------------------------------------------------------------------------


class TestNotebookServiceInit:
    """Test NotebookService initialization and DI."""

    def test_正常系_BrowserManagerをDIで受け取る(self, mock_manager: MagicMock) -> None:
        service = NotebookService(mock_manager)
        assert service._browser_manager is mock_manager

    def test_正常系_SelectorManagerが初期化される(
        self, notebook_service: NotebookService
    ) -> None:
        assert notebook_service._selectors is not None


# ---------------------------------------------------------------------------
# create_notebook tests
# ---------------------------------------------------------------------------


class TestCreateNotebook:
    """Test NotebookService.create_notebook()."""

    @pytest.mark.asyncio
    async def test_正常系_ノートブックを作成してNotebookInfoを返す(
        self,
        notebook_service: NotebookService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Set up page to simulate notebook creation flow
        # After clicking create, URL changes to new notebook page
        mock_page.url = (
            "https://notebooklm.google.com/notebook/"
            "c9354f3f-f55b-4f90-a5c4-219e582945cf"
        )

        # Mock locator for create button
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Mock wait_for_url for navigation after creation
        mock_page.wait_for_url = AsyncMock(return_value=None)

        # Act
        result = await notebook_service.create_notebook("AI Research Notes")

        # Assert
        assert isinstance(result, NotebookInfo)
        assert result.title == "AI Research Notes"
        assert result.notebook_id == "c9354f3f-f55b-4f90-a5c4-219e582945cf"
        assert result.source_count == 0

    @pytest.mark.asyncio
    async def test_正常系_タイトルがNotebookInfoに設定される(
        self,
        notebook_service: NotebookService,
        mock_page: AsyncMock,
    ) -> None:
        mock_page.url = "https://notebooklm.google.com/notebook/test-id-123"

        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)
        mock_page.locator = MagicMock(return_value=mock_locator)
        mock_page.wait_for_url = AsyncMock(return_value=None)

        result = await notebook_service.create_notebook("My Custom Title")

        assert result.title == "My Custom Title"

    @pytest.mark.asyncio
    async def test_異常系_空タイトルでValueError(
        self,
        notebook_service: NotebookService,
    ) -> None:
        with pytest.raises(ValueError, match="title must not be empty"):
            await notebook_service.create_notebook("")

    @pytest.mark.asyncio
    async def test_異常系_ページ作成後にcloseが呼ばれる(
        self,
        notebook_service: NotebookService,
        mock_page: AsyncMock,
    ) -> None:
        mock_page.url = "https://notebooklm.google.com/notebook/test-id"

        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_page.locator = MagicMock(return_value=mock_locator)
        mock_page.wait_for_url = AsyncMock(return_value=None)

        await notebook_service.create_notebook("Test")

        mock_page.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# list_notebooks tests
# ---------------------------------------------------------------------------


class TestListNotebooks:
    """Test NotebookService.list_notebooks()."""

    @pytest.mark.asyncio
    async def test_正常系_ノートブック一覧を取得(
        self,
        notebook_service: NotebookService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Simulate notebook list page with links
        link1 = AsyncMock()
        link1.get_attribute = AsyncMock(return_value="/notebook/id-001")
        link1.inner_text = AsyncMock(return_value="Notebook One")

        link2 = AsyncMock()
        link2.get_attribute = AsyncMock(return_value="/notebook/id-002")
        link2.inner_text = AsyncMock(return_value="Notebook Two")

        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[link1, link2])
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Act
        result = await notebook_service.list_notebooks()

        # Assert
        assert len(result) == 2
        assert all(isinstance(nb, NotebookInfo) for nb in result)
        assert result[0].notebook_id == "id-001"
        assert result[0].title == "Notebook One"
        assert result[1].notebook_id == "id-002"
        assert result[1].title == "Notebook Two"

    @pytest.mark.asyncio
    async def test_正常系_ノートブックがない場合は空リスト(
        self,
        notebook_service: NotebookService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await notebook_service.list_notebooks()

        assert result == []

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        notebook_service: NotebookService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=mock_locator)

        await notebook_service.list_notebooks()

        mock_page.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_notebook_summary tests
# ---------------------------------------------------------------------------


class TestGetNotebookSummary:
    """Test NotebookService.get_notebook_summary()."""

    @pytest.mark.asyncio
    async def test_正常系_ノートブック概要を取得(
        self,
        notebook_service: NotebookService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Navigate to notebook and extract summary
        mock_page.url = "https://notebooklm.google.com/notebook/nb-id-123"

        # Mock summary text extraction
        summary_locator = AsyncMock()
        summary_locator.count = AsyncMock(return_value=1)
        summary_locator.inner_text = AsyncMock(
            return_value="This notebook covers AI research topics."
        )

        # Mock suggested questions
        question_elements = [
            AsyncMock(inner_text=AsyncMock(return_value="What are the key findings?")),
            AsyncMock(inner_text=AsyncMock(return_value="How does this compare?")),
        ]

        def locator_side_effect(selector: str) -> AsyncMock:
            if "summary" in selector.lower() or "概要" in selector:
                return summary_locator
            mock = AsyncMock()
            mock.count = AsyncMock(return_value=0)
            mock.all = AsyncMock(return_value=question_elements)
            return mock

        mock_page.locator = MagicMock(side_effect=locator_side_effect)
        mock_page.wait_for_load_state = AsyncMock(return_value=None)

        # Act
        result = await notebook_service.get_notebook_summary("nb-id-123")

        # Assert
        assert isinstance(result, NotebookSummary)
        assert result.notebook_id == "nb-id-123"
        assert "AI research" in result.summary_text

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        notebook_service: NotebookService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await notebook_service.get_notebook_summary("")

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        notebook_service: NotebookService,
        mock_page: AsyncMock,
    ) -> None:
        mock_page.url = "https://notebooklm.google.com/notebook/nb-id-123"

        summary_locator = AsyncMock()
        summary_locator.count = AsyncMock(return_value=1)
        summary_locator.inner_text = AsyncMock(return_value="Summary text")

        mock_page.locator = MagicMock(return_value=summary_locator)
        mock_page.wait_for_load_state = AsyncMock(return_value=None)

        # Mock for suggested questions (empty)
        question_locator = AsyncMock()
        question_locator.all = AsyncMock(return_value=[])

        call_count = 0

        def locator_dispatch(selector: str) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return summary_locator
            return question_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        await notebook_service.get_notebook_summary("nb-id-123")

        mock_page.close.assert_awaited_once()

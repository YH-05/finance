"""Unit tests for SourceService.

Tests cover:
- add_text_source: Adds pasted text as a source to a notebook.
- list_sources: Lists all sources in a notebook.
- DI: Service receives BrowserManager via constructor injection.
- Error paths: SourceAddError wrapping, page close on exception.
- Private helpers: _detect_source_type, _wait_for_source_processing.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.browser.manager import NotebookLMBrowserManager
from notebooklm.errors import ElementNotFoundError, SourceAddError
from notebooklm.services.source import SourceService
from notebooklm.types import SourceInfo

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
def source_service(mock_manager: MagicMock) -> SourceService:
    """Create a SourceService with mocked BrowserManager."""
    return SourceService(mock_manager)


# ---------------------------------------------------------------------------
# DI tests
# ---------------------------------------------------------------------------


class TestSourceServiceInit:
    """Test SourceService initialization and DI."""

    def test_正常系_BrowserManagerをDIで受け取る(self, mock_manager: MagicMock) -> None:
        service = SourceService(mock_manager)
        assert service._browser_manager is mock_manager

    def test_正常系_SelectorManagerが初期化される(
        self, source_service: SourceService
    ) -> None:
        assert source_service._selectors is not None


# ---------------------------------------------------------------------------
# add_text_source tests
# ---------------------------------------------------------------------------


class TestAddTextSource:
    """Test SourceService.add_text_source()."""

    @pytest.mark.asyncio
    async def test_正常系_テキストソースを追加してSourceInfoを返す(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Set up locators for the text source addition flow
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Mock loading progress bar disappearing
        progress_locator = AsyncMock()
        progress_locator.count = AsyncMock(return_value=0)

        source_item_locator = AsyncMock()
        source_item_text = AsyncMock()
        source_item_text.inner_text = AsyncMock(return_value="Pasted text")
        source_item_locator.all = AsyncMock(return_value=[source_item_text])
        source_item_locator.count = AsyncMock(return_value=1)

        call_count = 0

        def locator_dispatch(selector: str) -> AsyncMock:
            nonlocal call_count
            call_count += 1
            if "progressbar" in selector:
                return progress_locator
            return mock_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        # Act
        result = await source_service.add_text_source(
            notebook_id="nb-001",
            text="This is sample text for testing.",
            title="Test Source",
        )

        # Assert
        assert isinstance(result, SourceInfo)
        assert result.source_type == "text"
        assert result.title == "Test Source"

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.add_text_source(
                notebook_id="",
                text="Some text",
            )

    @pytest.mark.asyncio
    async def test_異常系_空のtextでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="text must not be empty"):
            await source_service.add_text_source(
                notebook_id="nb-001",
                text="",
            )

    @pytest.mark.asyncio
    async def test_正常系_titleが省略された場合はPasted_textが使用される(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await source_service.add_text_source(
            notebook_id="nb-001",
            text="Test content here.",
        )

        assert isinstance(result, SourceInfo)
        assert result.source_type == "text"

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)
        mock_page.locator = MagicMock(return_value=mock_locator)

        await source_service.add_text_source(
            notebook_id="nb-001",
            text="Test text.",
        )

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でSourceAddError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        """Non-ValueError exceptions are wrapped as SourceAddError."""
        # Arrange: navigate_to_notebook raises ElementNotFoundError
        with (
            patch(
                "notebooklm.services.source.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(SourceAddError, match="Failed to add text source"),
        ):
            await source_service.add_text_source(
                notebook_id="nb-001",
                text="Some text content.",
            )

    @pytest.mark.asyncio
    async def test_異常系_エラー発生時もページがcloseされる(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        """Page is closed even when an error occurs during add_text_source."""
        with (
            patch(
                "notebooklm.services.source.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(SourceAddError),
        ):
            await source_service.add_text_source(
                notebook_id="nb-001",
                text="Some text.",
            )

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.add_text_source(
                notebook_id="   ",
                text="Some text",
            )

    @pytest.mark.asyncio
    async def test_異常系_空白のみのtextでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="text must not be empty"):
            await source_service.add_text_source(
                notebook_id="nb-001",
                text="   ",
            )


# ---------------------------------------------------------------------------
# list_sources tests
# ---------------------------------------------------------------------------


class TestListSources:
    """Test SourceService.list_sources()."""

    @pytest.mark.asyncio
    async def test_正常系_ソース一覧を取得(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        # Arrange: Simulate source list in the notebook page
        source1 = AsyncMock()
        source1.inner_text = AsyncMock(return_value="Machine Learning Overview")
        source1.get_attribute = AsyncMock(return_value=None)
        source1.inner_html = AsyncMock(
            return_value="<div>Machine Learning Overview</div>"
        )

        source2 = AsyncMock()
        source2.inner_text = AsyncMock(return_value="Deep Learning Paper")
        source2.get_attribute = AsyncMock(return_value=None)
        source2.inner_html = AsyncMock(
            return_value='<div class="url">Deep Learning Paper</div>'
        )

        source_list_locator = AsyncMock()
        source_list_locator.all = AsyncMock(return_value=[source1, source2])

        # Source count indicator
        count_locator = AsyncMock()
        count_locator.count = AsyncMock(return_value=1)
        count_locator.inner_text = AsyncMock(return_value="2 / 300")

        def locator_dispatch(selector: str) -> AsyncMock:
            if "source-item" in selector or "checkbox" in selector:
                return source_list_locator
            if "300" in selector:
                return count_locator
            return source_list_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        # Act
        result = await source_service.list_sources("nb-001")

        # Assert
        assert len(result) == 2
        assert all(isinstance(src, SourceInfo) for src in result)

    @pytest.mark.asyncio
    async def test_正常系_ソースがない場合は空リスト(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        empty_locator = AsyncMock()
        empty_locator.all = AsyncMock(return_value=[])
        empty_locator.count = AsyncMock(return_value=0)
        mock_page.locator = MagicMock(return_value=empty_locator)

        result = await source_service.list_sources("nb-001")

        assert result == []

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.list_sources("")

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        empty_locator = AsyncMock()
        empty_locator.all = AsyncMock(return_value=[])
        empty_locator.count = AsyncMock(return_value=0)
        mock_page.locator = MagicMock(return_value=empty_locator)

        await source_service.list_sources("nb-001")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.list_sources("   ")


# ---------------------------------------------------------------------------
# _detect_source_type tests
# ---------------------------------------------------------------------------


class TestDetectSourceType:
    """Test SourceService._detect_source_type() static method."""

    @pytest.mark.asyncio
    async def test_正常系_data属性からtextを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value="text")
        element.inner_html = AsyncMock(return_value="<div>text</div>")

        result = await SourceService._detect_source_type(element)
        assert result == "text"

    @pytest.mark.asyncio
    async def test_正常系_data属性からurlを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value="url")
        element.inner_html = AsyncMock(return_value="<div>url</div>")

        result = await SourceService._detect_source_type(element)
        assert result == "url"

    @pytest.mark.asyncio
    async def test_正常系_data属性からfileを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value="file")
        element.inner_html = AsyncMock(return_value="<div>file</div>")

        result = await SourceService._detect_source_type(element)
        assert result == "file"

    @pytest.mark.asyncio
    async def test_正常系_data属性からgoogle_driveを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value="google_drive")
        element.inner_html = AsyncMock(return_value="<div>drive</div>")

        result = await SourceService._detect_source_type(element)
        assert result == "google_drive"

    @pytest.mark.asyncio
    async def test_正常系_data属性からyoutubeを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value="youtube")
        element.inner_html = AsyncMock(return_value="<div>youtube</div>")

        result = await SourceService._detect_source_type(element)
        assert result == "youtube"

    @pytest.mark.asyncio
    async def test_正常系_innerHTMLからurlを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value=None)
        element.inner_html = AsyncMock(
            return_value='<div class="url-icon">Article Link</div>'
        )

        result = await SourceService._detect_source_type(element)
        assert result == "url"

    @pytest.mark.asyncio
    async def test_正常系_innerHTMLからfileを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value=None)
        element.inner_html = AsyncMock(
            return_value='<div class="file-upload">Document</div>'
        )

        result = await SourceService._detect_source_type(element)
        assert result == "file"

    @pytest.mark.asyncio
    async def test_正常系_innerHTMLからdriveを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value=None)
        element.inner_html = AsyncMock(
            return_value='<div class="drive-icon">Google Drive Document</div>'
        )

        result = await SourceService._detect_source_type(element)
        assert result == "google_drive"

    @pytest.mark.asyncio
    async def test_正常系_innerHTMLからyoutubeを検出(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value=None)
        element.inner_html = AsyncMock(
            return_value='<div class="youtube-icon">YouTube Video</div>'
        )

        result = await SourceService._detect_source_type(element)
        assert result == "youtube"

    @pytest.mark.asyncio
    async def test_正常系_不明なタイプはtextがデフォルト(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value=None)
        element.inner_html = AsyncMock(return_value="<div>Unknown content</div>")

        result = await SourceService._detect_source_type(element)
        assert result == "text"

    @pytest.mark.asyncio
    async def test_正常系_無効なdata属性はinnerHTMLにフォールバック(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(return_value="invalid_type")
        element.inner_html = AsyncMock(
            return_value='<div class="link-icon">URL Source</div>'
        )

        result = await SourceService._detect_source_type(element)
        assert result == "url"

    @pytest.mark.asyncio
    async def test_正常系_例外発生時はtextがデフォルト(self) -> None:
        element = AsyncMock()
        element.get_attribute = AsyncMock(side_effect=RuntimeError("DOM error"))

        result = await SourceService._detect_source_type(element)
        assert result == "text"


# ---------------------------------------------------------------------------
# _wait_for_source_processing tests
# ---------------------------------------------------------------------------


class TestWaitForSourceProcessing:
    """Test SourceService._wait_for_source_processing() method."""

    @pytest.mark.asyncio
    async def test_正常系_プログレスバーが非表示になるまで待機(
        self,
        source_service: SourceService,
    ) -> None:
        """When progress bar exists and then hides, method completes."""
        mock_page = AsyncMock()
        progress_locator = AsyncMock()
        progress_locator.count = AsyncMock(return_value=1)
        progress_locator.wait_for = AsyncMock(return_value=None)
        mock_page.locator = MagicMock(return_value=progress_locator)

        # Should complete without error
        await source_service._wait_for_source_processing(mock_page)

    @pytest.mark.asyncio
    async def test_正常系_プログレスバーが存在しない場合スキップ(
        self,
        source_service: SourceService,
    ) -> None:
        """When progress bar is not found, method waits briefly and returns."""
        mock_page = AsyncMock()
        progress_locator = AsyncMock()
        progress_locator.count = AsyncMock(return_value=0)
        mock_page.locator = MagicMock(return_value=progress_locator)

        # Should complete without error
        await source_service._wait_for_source_processing(mock_page)

    @pytest.mark.asyncio
    async def test_正常系_タイムアウトしても例外にならない(
        self,
        source_service: SourceService,
    ) -> None:
        """Timeout during processing wait is caught and logged, not raised."""
        mock_page = AsyncMock()
        progress_locator = AsyncMock()
        progress_locator.count = AsyncMock(return_value=1)
        progress_locator.wait_for = AsyncMock(side_effect=TimeoutError("timeout"))
        mock_page.locator = MagicMock(return_value=progress_locator)

        # Should not raise - timeout is caught internally
        await source_service._wait_for_source_processing(mock_page)

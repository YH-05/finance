"""Unit tests for SourceService.

Tests cover:
- add_text_source: Adds pasted text as a source to a notebook.
- add_url_source: Adds a URL/website as a source.
- add_file_source: Uploads a file as a source.
- get_source_details: Gets detailed information about a source.
- delete_source: Deletes a source from a notebook.
- rename_source: Renames a source in a notebook.
- toggle_source_selection: Selects/deselects a source.
- web_research: Runs Fast or Deep web research.
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
from notebooklm.types import SourceDetails, SourceInfo

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


# ---------------------------------------------------------------------------
# add_url_source tests
# ---------------------------------------------------------------------------


class TestAddUrlSource:
    """Test SourceService.add_url_source()."""

    @pytest.mark.asyncio
    async def test_正常系_URLソースを追加してSourceInfoを返す(
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

        progress_locator = AsyncMock()
        progress_locator.count = AsyncMock(return_value=0)

        def locator_dispatch(selector: str) -> AsyncMock:
            if "progressbar" in selector:
                return progress_locator
            return mock_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        result = await source_service.add_url_source(
            notebook_id="nb-001",
            url="https://example.com/article",
        )

        assert isinstance(result, SourceInfo)
        assert result.source_type == "url"
        assert result.title == "https://example.com/article"

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.add_url_source(
                notebook_id="",
                url="https://example.com",
            )

    @pytest.mark.asyncio
    async def test_異常系_空のurlでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="url must not be empty"):
            await source_service.add_url_source(
                notebook_id="nb-001",
                url="",
            )

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でSourceAddError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        with (
            patch(
                "notebooklm.services.source.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(SourceAddError, match="Failed to add URL source"),
        ):
            await source_service.add_url_source(
                notebook_id="nb-001",
                url="https://example.com",
            )

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

        await source_service.add_url_source(
            notebook_id="nb-001",
            url="https://example.com",
        )

        mock_page.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# add_file_source tests
# ---------------------------------------------------------------------------


class TestAddFileSource:
    """Test SourceService.add_file_source()."""

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.add_file_source(
                notebook_id="",
                file_path="/tmp/test.pdf",
            )

    @pytest.mark.asyncio
    async def test_異常系_空のfile_pathでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="file_path must not be empty"):
            await source_service.add_file_source(
                notebook_id="nb-001",
                file_path="",
            )

    @pytest.mark.asyncio
    async def test_異常系_存在しないファイルでFileNotFoundError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(FileNotFoundError, match="File not found"):
            await source_service.add_file_source(
                notebook_id="nb-001",
                file_path="/nonexistent/path/file.pdf",
            )

    @pytest.mark.asyncio
    async def test_正常系_ファイルソースを追加してSourceInfoを返す(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
        tmp_path: Any,
    ) -> None:
        # Create a temporary test file
        test_file = tmp_path / "test_document.pdf"
        test_file.write_text("test content")

        mock_locator = AsyncMock()
        mock_locator.wait_for = AsyncMock(return_value=None)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)

        progress_locator = AsyncMock()
        progress_locator.count = AsyncMock(return_value=0)

        # Mock file chooser
        mock_file_chooser = MagicMock()
        mock_file_chooser.set_files = AsyncMock(return_value=None)

        # Playwright's expect_file_chooser returns an async context manager.
        # __aenter__ returns an EventInfo whose .value is awaitable (coroutine).
        # `await fc_info.value` resolves to the FileChooser object.

        async def _file_chooser_value() -> MagicMock:
            return mock_file_chooser

        fc_event_info = MagicMock()
        fc_event_info.value = _file_chooser_value()

        fc_context = AsyncMock()
        fc_context.__aenter__ = AsyncMock(return_value=fc_event_info)
        fc_context.__aexit__ = AsyncMock(return_value=False)

        def locator_dispatch(selector: str) -> AsyncMock:
            if "progressbar" in selector:
                return progress_locator
            return mock_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)
        mock_page.expect_file_chooser = MagicMock(return_value=fc_context)

        result = await source_service.add_file_source(
            notebook_id="nb-001",
            file_path=str(test_file),
        )

        assert isinstance(result, SourceInfo)
        assert result.source_type == "file"
        assert result.title == "test_document.pdf"

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でSourceAddError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
        tmp_path: Any,
    ) -> None:
        test_file = tmp_path / "test.pdf"
        test_file.write_text("content")

        with (
            patch(
                "notebooklm.services.source.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(SourceAddError, match="Failed to add file source"),
        ):
            await source_service.add_file_source(
                notebook_id="nb-001",
                file_path=str(test_file),
            )


# ---------------------------------------------------------------------------
# get_source_details tests
# ---------------------------------------------------------------------------


class TestGetSourceDetails:
    """Test SourceService.get_source_details()."""

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.get_source_details(
                notebook_id="",
                source_index=0,
            )

    @pytest.mark.asyncio
    async def test_異常系_負のsource_indexでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="source_index must be non-negative"):
            await source_service.get_source_details(
                notebook_id="nb-001",
                source_index=-1,
            )

    @pytest.mark.asyncio
    async def test_正常系_ソース詳細を取得してSourceDetailsを返す(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        # Set up source elements
        source_element = AsyncMock()
        source_element.inner_text = AsyncMock(return_value="Research Paper")
        source_element.get_attribute = AsyncMock(return_value="url")
        source_element.inner_html = AsyncMock(return_value="<div>url</div>")
        source_element.click = AsyncMock(return_value=None)

        source_list_locator = AsyncMock()
        source_list_locator.all = AsyncMock(return_value=[source_element])

        # Mock for summary extraction
        summary_locator = AsyncMock()
        summary_locator.count = AsyncMock(return_value=1)
        summary_locator.inner_text = AsyncMock(return_value="This paper discusses...")

        # Mock for URL extraction
        url_locator = AsyncMock()
        url_locator.count = AsyncMock(return_value=0)

        def locator_dispatch(selector: str) -> AsyncMock:
            if "source-item" in selector:
                return source_list_locator
            if "source-detail-url" in selector or "source-link" in selector:
                return url_locator
            if "source-detail-summary" in selector or "source-summary" in selector:
                return summary_locator
            return summary_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        result = await source_service.get_source_details(
            notebook_id="nb-001",
            source_index=0,
        )

        assert isinstance(result, SourceDetails)
        assert result.title == "Research Paper"
        assert result.source_type == "url"

    @pytest.mark.asyncio
    async def test_異常系_範囲外のsource_indexでValueError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        empty_locator = AsyncMock()
        empty_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=empty_locator)

        with pytest.raises(ValueError, match="source_index 0 out of range"):
            await source_service.get_source_details(
                notebook_id="nb-001",
                source_index=0,
            )

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        empty_locator = AsyncMock()
        empty_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=empty_locator)

        with pytest.raises(ValueError):
            await source_service.get_source_details(
                notebook_id="nb-001",
                source_index=0,
            )

        mock_page.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# delete_source tests
# ---------------------------------------------------------------------------


class TestDeleteSource:
    """Test SourceService.delete_source()."""

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.delete_source(
                notebook_id="",
                source_index=0,
            )

    @pytest.mark.asyncio
    async def test_異常系_負のsource_indexでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="source_index must be non-negative"):
            await source_service.delete_source(
                notebook_id="nb-001",
                source_index=-1,
            )

    @pytest.mark.asyncio
    async def test_正常系_ソースを削除してTrueを返す(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        source_element = AsyncMock()
        source_element.hover = AsyncMock(return_value=None)

        source_list_locator = AsyncMock()
        source_list_locator.all = AsyncMock(return_value=[source_element])

        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.click = AsyncMock(return_value=None)

        def locator_dispatch(selector: str) -> AsyncMock:
            if "source-item" in selector:
                return source_list_locator
            return mock_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        result = await source_service.delete_source(
            notebook_id="nb-001",
            source_index=0,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_異常系_範囲外のsource_indexでValueError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        empty_locator = AsyncMock()
        empty_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=empty_locator)

        with pytest.raises(ValueError, match="source_index 0 out of range"):
            await source_service.delete_source(
                notebook_id="nb-001",
                source_index=0,
            )

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でSourceAddError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        with (
            patch(
                "notebooklm.services.source.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(SourceAddError, match="Failed to delete source"),
        ):
            await source_service.delete_source(
                notebook_id="nb-001",
                source_index=0,
            )


# ---------------------------------------------------------------------------
# rename_source tests
# ---------------------------------------------------------------------------


class TestRenameSource:
    """Test SourceService.rename_source()."""

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.rename_source(
                notebook_id="",
                source_index=0,
                new_name="New Name",
            )

    @pytest.mark.asyncio
    async def test_異常系_負のsource_indexでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="source_index must be non-negative"):
            await source_service.rename_source(
                notebook_id="nb-001",
                source_index=-1,
                new_name="New Name",
            )

    @pytest.mark.asyncio
    async def test_異常系_空のnew_nameでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="new_name must not be empty"):
            await source_service.rename_source(
                notebook_id="nb-001",
                source_index=0,
                new_name="",
            )

    @pytest.mark.asyncio
    async def test_正常系_ソースをリネームしてSourceInfoを返す(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        source_element = AsyncMock()
        source_element.hover = AsyncMock(return_value=None)

        source_list_locator = AsyncMock()
        source_list_locator.all = AsyncMock(return_value=[source_element])

        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.first = mock_locator
        mock_locator.click = AsyncMock(return_value=None)
        mock_locator.fill = AsyncMock(return_value=None)
        mock_locator.wait_for = AsyncMock(return_value=None)

        mock_keyboard = AsyncMock()
        mock_keyboard.press = AsyncMock(return_value=None)
        mock_page.keyboard = mock_keyboard

        def locator_dispatch(selector: str) -> AsyncMock:
            if "source-item" in selector:
                return source_list_locator
            return mock_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        result = await source_service.rename_source(
            notebook_id="nb-001",
            source_index=0,
            new_name="Updated Name",
        )

        assert isinstance(result, SourceInfo)
        assert result.title == "Updated Name"

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でSourceAddError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        with (
            patch(
                "notebooklm.services.source.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(SourceAddError, match="Failed to rename source"),
        ):
            await source_service.rename_source(
                notebook_id="nb-001",
                source_index=0,
                new_name="New Name",
            )


# ---------------------------------------------------------------------------
# toggle_source_selection tests
# ---------------------------------------------------------------------------


class TestToggleSourceSelection:
    """Test SourceService.toggle_source_selection()."""

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.toggle_source_selection(
                notebook_id="",
                source_index=0,
            )

    @pytest.mark.asyncio
    async def test_異常系_source_indexもselect_allもないでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="Either source_index or select_all=True must be specified",
        ):
            await source_service.toggle_source_selection(
                notebook_id="nb-001",
            )

    @pytest.mark.asyncio
    async def test_異常系_負のsource_indexでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="source_index must be non-negative"):
            await source_service.toggle_source_selection(
                notebook_id="nb-001",
                source_index=-1,
            )

    @pytest.mark.asyncio
    async def test_正常系_select_allでTrueを返す(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.click = AsyncMock(return_value=None)
        mock_page.locator = MagicMock(return_value=mock_locator)

        result = await source_service.toggle_source_selection(
            notebook_id="nb-001",
            select_all=True,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_正常系_個別ソースをトグルしてTrueを返す(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        # Set up source element with checkbox
        checkbox_locator = AsyncMock()
        checkbox_locator.count = AsyncMock(return_value=1)
        checkbox_locator.click = AsyncMock(return_value=None)

        source_element = AsyncMock()
        source_element.locator = MagicMock(return_value=checkbox_locator)

        source_list_locator = AsyncMock()
        source_list_locator.all = AsyncMock(return_value=[source_element])

        def locator_dispatch(selector: str) -> AsyncMock:
            if "source-item" in selector:
                return source_list_locator
            return AsyncMock(count=AsyncMock(return_value=1))

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        result = await source_service.toggle_source_selection(
            notebook_id="nb-001",
            source_index=0,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_異常系_範囲外のsource_indexでValueError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        empty_locator = AsyncMock()
        empty_locator.all = AsyncMock(return_value=[])
        mock_page.locator = MagicMock(return_value=empty_locator)

        with pytest.raises(ValueError, match="source_index 0 out of range"):
            await source_service.toggle_source_selection(
                notebook_id="nb-001",
                source_index=0,
            )


# ---------------------------------------------------------------------------
# web_research tests
# ---------------------------------------------------------------------------


class TestWebResearch:
    """Test SourceService.web_research()."""

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await source_service.web_research(
                notebook_id="",
                query="AI trends",
            )

    @pytest.mark.asyncio
    async def test_異常系_空のqueryでValueError(
        self,
        source_service: SourceService,
    ) -> None:
        with pytest.raises(ValueError, match="query must not be empty"):
            await source_service.web_research(
                notebook_id="nb-001",
                query="",
            )

    @pytest.mark.asyncio
    async def test_正常系_fastリサーチで結果を返す(
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

        # Mock search result elements (empty results for simplicity)
        result_locator = AsyncMock()
        result_locator.all = AsyncMock(return_value=[])

        mock_keyboard = AsyncMock()
        mock_keyboard.press = AsyncMock(return_value=None)
        mock_page.keyboard = mock_keyboard

        def locator_dispatch(selector: str) -> AsyncMock:
            if "search-result" in selector or "research-result" in selector:
                return result_locator
            return mock_locator

        mock_page.locator = MagicMock(side_effect=locator_dispatch)

        result = await source_service.web_research(
            notebook_id="nb-001",
            query="AI investment trends",
            mode="fast",
        )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_異常系_ブラウザ操作失敗でSourceAddError(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
        with (
            patch(
                "notebooklm.services.source.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(SourceAddError, match="Failed to run web research"),
        ):
            await source_service.web_research(
                notebook_id="nb-001",
                query="AI trends",
            )

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        source_service: SourceService,
        mock_page: AsyncMock,
    ) -> None:
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
            await source_service.web_research(
                notebook_id="nb-001",
                query="AI trends",
            )

        mock_page.close.assert_awaited_once()

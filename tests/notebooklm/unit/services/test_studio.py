"""Unit tests for StudioService.

Tests cover:
- DI: Service receives BrowserManager via constructor injection.
- Validation: Empty notebook_id raises ValueError.
- generate_content: 4 content types (report, infographic, slides, data_table).
- Report: DOM scraping for Markdown conversion via clipboard copy.
- Data Table: HTML table extraction to structured data (list[list[str]]).
- Infographic/Slides: Download via Playwright download handler.
- Polling: content_type-specific completion detection.
- Report format: Optional format parameter for reports.
- Error handling: Browser failures wrapped as StudioGenerationError.
- Page cleanup: Page is always closed in finally block.
- Timing: generation_time_seconds is recorded in the result.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.browser.manager import NotebookLMBrowserManager
from notebooklm.errors import ElementNotFoundError, StudioGenerationError
from notebooklm.services.studio import StudioService
from notebooklm.types import StudioContentResult

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
    page.evaluate = AsyncMock(return_value="# Report Title\n\nContent here")
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
def studio_service(mock_manager: MagicMock) -> StudioService:
    """Create a StudioService with mocked BrowserManager."""
    return StudioService(mock_manager)


def _make_interactive_locator(
    count: int = 1,
    *,
    inner_text: str = "",
    inner_html: str = "",
) -> AsyncMock:
    """Create a mock locator with standard interactive methods."""
    locator = AsyncMock()
    locator.wait_for = AsyncMock(return_value=None)
    locator.count = AsyncMock(return_value=count)
    locator.first = locator
    locator.click = AsyncMock(return_value=None)
    locator.fill = AsyncMock(return_value=None)
    locator.inner_text = AsyncMock(return_value=inner_text)
    locator.inner_html = AsyncMock(return_value=inner_html)
    locator.all = AsyncMock(return_value=[])
    locator.all_inner_texts = AsyncMock(return_value=[])
    locator.locator = MagicMock(return_value=locator)

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


class TestStudioServiceInit:
    """Test StudioService initialization and DI."""

    def test_正常系_BrowserManagerをDIで受け取る(self, mock_manager: MagicMock) -> None:
        service = StudioService(mock_manager)
        assert service._browser_manager is mock_manager

    def test_正常系_SelectorManagerが初期化される(
        self, studio_service: StudioService
    ) -> None:
        assert studio_service._selectors is not None


# ---------------------------------------------------------------------------
# generate_content: Report tests
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Test StudioService.generate_content() for report type."""

    @pytest.mark.asyncio
    async def test_正常系_レポートを生成してStudioContentResultを返す(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Report generation completes and returns StudioContentResult."""
        mock_locator = _make_interactive_locator(count=1, inner_text="Report Title")
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.studio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await studio_service.generate_content("nb-001", "report")

        assert isinstance(result, StudioContentResult)
        assert result.notebook_id == "nb-001"
        assert result.content_type == "report"

    @pytest.mark.asyncio
    async def test_正常系_レポートのtext_contentが設定される(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Report text_content is extracted from clipboard."""
        mock_locator = _make_interactive_locator(count=1, inner_text="Report Title")
        mock_page.locator = MagicMock(return_value=mock_locator)
        mock_page.evaluate = AsyncMock(return_value="# Report Title\n\nContent here")

        with patch(
            "notebooklm.services.studio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await studio_service.generate_content("nb-001", "report")

        assert result.text_content is not None
        assert len(result.text_content) > 0

    @pytest.mark.asyncio
    async def test_正常系_レポートフォーマットを指定して生成(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Report format option (briefing_doc) is supported."""
        mock_locator = _make_interactive_locator(count=1, inner_text="Report Title")
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.studio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await studio_service.generate_content(
                "nb-001", "report", report_format="briefing_doc"
            )

        assert isinstance(result, StudioContentResult)
        assert result.content_type == "report"

    @pytest.mark.asyncio
    async def test_正常系_生成時間が記録される(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Generation time is recorded in the result."""
        mock_locator = _make_interactive_locator(count=1, inner_text="Report Title")
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.studio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await studio_service.generate_content("nb-001", "report")

        assert result.generation_time_seconds >= 0.0


# ---------------------------------------------------------------------------
# generate_content: Data Table tests
# ---------------------------------------------------------------------------


class TestGenerateDataTable:
    """Test StudioService.generate_content() for data_table type."""

    @pytest.mark.asyncio
    async def test_正常系_DataTableを生成してtable_dataが設定される(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Data table generation extracts structured data."""
        mock_locator = _make_interactive_locator(count=1, inner_text="Data Table")

        # Set up table extraction mock
        table_rows = [
            AsyncMock(
                locator=MagicMock(
                    return_value=AsyncMock(
                        all_inner_texts=AsyncMock(return_value=["Header1", "Header2"])
                    )
                )
            ),
            AsyncMock(
                locator=MagicMock(
                    return_value=AsyncMock(
                        all_inner_texts=AsyncMock(return_value=["Value1", "Value2"])
                    )
                )
            ),
        ]

        def locator_side_effect(selector: str) -> AsyncMock:
            loc = _make_interactive_locator(count=1, inner_text="Data Table")
            if selector == "tr":
                loc.all = AsyncMock(return_value=table_rows)
            return loc

        mock_locator.locator = MagicMock(side_effect=locator_side_effect)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with (
            patch(
                "notebooklm.services.studio.poll_until",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "notebooklm.services.studio.extract_table_data",
                new_callable=AsyncMock,
                return_value=[["Header1", "Header2"], ["Value1", "Value2"]],
            ),
        ):
            result = await studio_service.generate_content("nb-001", "data_table")

        assert isinstance(result, StudioContentResult)
        assert result.content_type == "data_table"
        assert result.table_data is not None
        assert len(result.table_data) == 2
        assert result.table_data[0] == ["Header1", "Header2"]
        assert result.table_data[1] == ["Value1", "Value2"]


# ---------------------------------------------------------------------------
# generate_content: Infographic tests
# ---------------------------------------------------------------------------


class TestGenerateInfographic:
    """Test StudioService.generate_content() for infographic type."""

    @pytest.mark.asyncio
    async def test_正常系_インフォグラフィックを生成する(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Infographic generation returns StudioContentResult."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.studio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await studio_service.generate_content("nb-001", "infographic")

        assert isinstance(result, StudioContentResult)
        assert result.content_type == "infographic"
        assert result.notebook_id == "nb-001"


# ---------------------------------------------------------------------------
# generate_content: Slides tests
# ---------------------------------------------------------------------------


class TestGenerateSlides:
    """Test StudioService.generate_content() for slides type."""

    @pytest.mark.asyncio
    async def test_正常系_スライドを生成する(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Slides generation returns StudioContentResult."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.studio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await studio_service.generate_content("nb-001", "slides")

        assert isinstance(result, StudioContentResult)
        assert result.content_type == "slides"


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestGenerateContentValidation:
    """Test input validation for generate_content."""

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        studio_service: StudioService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await studio_service.generate_content("", "report")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        studio_service: StudioService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await studio_service.generate_content("   ", "report")


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestGenerateContentErrorHandling:
    """Test error handling in generate_content."""

    @pytest.mark.asyncio
    async def test_異常系_ポーリングタイムアウトでStudioGenerationError(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """StudioGenerationError when polling times out."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with (
            patch(
                "notebooklm.services.studio.poll_until",
                new_callable=AsyncMock,
                side_effect=StudioGenerationError(
                    "Generation timed out",
                    context={"content_type": "report"},
                ),
            ),
            pytest.raises(StudioGenerationError, match="Generation timed out"),
        ):
            await studio_service.generate_content("nb-001", "report")

    @pytest.mark.asyncio
    async def test_異常系_要素が見つからない場合StudioGenerationError(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """ElementNotFoundError is wrapped as StudioGenerationError."""
        with (
            patch(
                "notebooklm.services.studio.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "studio_report_button"},
                ),
            ),
            pytest.raises(
                StudioGenerationError,
                match="Studio content generation failed",
            ),
        ):
            await studio_service.generate_content("nb-001", "report")


# ---------------------------------------------------------------------------
# Page cleanup tests
# ---------------------------------------------------------------------------


class TestGenerateContentPageCleanup:
    """Test page lifecycle management."""

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.studio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            await studio_service.generate_content("nb-001", "report")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_エラー発生時もページがcloseされる(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Page is closed even when an error occurs."""
        with (
            patch(
                "notebooklm.services.studio.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(StudioGenerationError),
        ):
            await studio_service.generate_content("nb-001", "report")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_正常系_poll_untilにoperation_nameを渡す(
        self,
        studio_service: StudioService,
        mock_page: AsyncMock,
    ) -> None:
        """poll_until is called with operation_name containing content_type."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.studio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_poll:
            await studio_service.generate_content("nb-001", "report")

        mock_poll.assert_awaited_once()
        call_kwargs = mock_poll.call_args.kwargs
        assert "timeout_seconds" in call_kwargs
        assert "interval_seconds" in call_kwargs
        assert "operation_name" in call_kwargs
        assert "report" in call_kwargs["operation_name"]

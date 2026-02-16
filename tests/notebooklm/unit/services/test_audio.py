"""Unit tests for AudioService.

Tests cover:
- generate_audio_overview: Starts audio generation and polls for completion.
- DI: Service receives BrowserManager via constructor injection.
- Validation: Empty notebook_id raises ValueError.
- Exponential backoff: Polling uses poll_until with backoff.
- Error handling: Browser failures wrapped as BrowserTimeoutError.
- Page cleanup: Page is always closed in finally block.
- Customization: Optional prompt parameter for audio customization.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from notebooklm.browser.manager import NotebookLMBrowserManager
from notebooklm.errors import BrowserTimeoutError, ElementNotFoundError
from notebooklm.services.audio import AudioService
from notebooklm.types import AudioOverviewResult

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
def audio_service(mock_manager: MagicMock) -> AudioService:
    """Create an AudioService with mocked BrowserManager."""
    return AudioService(mock_manager)


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


class TestAudioServiceInit:
    """Test AudioService initialization and DI."""

    def test_正常系_BrowserManagerをDIで受け取る(self, mock_manager: MagicMock) -> None:
        service = AudioService(mock_manager)
        assert service._browser_manager is mock_manager

    def test_正常系_SelectorManagerが初期化される(
        self, audio_service: AudioService
    ) -> None:
        assert audio_service._selectors is not None


# ---------------------------------------------------------------------------
# generate_audio_overview tests
# ---------------------------------------------------------------------------


class TestGenerateAudioOverview:
    """Test AudioService.generate_audio_overview()."""

    @pytest.mark.asyncio
    async def test_正常系_Audio_Overviewを生成してAudioOverviewResultを返す(
        self,
        audio_service: AudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Audio generation completes and returns AudioOverviewResult."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.audio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await audio_service.generate_audio_overview("nb-001")

        assert isinstance(result, AudioOverviewResult)
        assert result.notebook_id == "nb-001"
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_正常系_生成時間が記録される(
        self,
        audio_service: AudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Generation time is recorded in the result."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.audio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await audio_service.generate_audio_overview("nb-001")

        assert result.generation_time_seconds is not None
        assert result.generation_time_seconds >= 0.0

    @pytest.mark.asyncio
    async def test_正常系_カスタマイズプロンプトを指定して生成(
        self,
        audio_service: AudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Customization prompt is filled when provided."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.audio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await audio_service.generate_audio_overview(
                "nb-001",
                customize_prompt="Focus on technical details",
            )

        assert isinstance(result, AudioOverviewResult)
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_異常系_空のnotebook_idでValueError(
        self,
        audio_service: AudioService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await audio_service.generate_audio_overview("")

    @pytest.mark.asyncio
    async def test_異常系_空白のみのnotebook_idでValueError(
        self,
        audio_service: AudioService,
    ) -> None:
        with pytest.raises(ValueError, match="notebook_id must not be empty"):
            await audio_service.generate_audio_overview("   ")

    @pytest.mark.asyncio
    async def test_異常系_ポーリングタイムアウトでBrowserTimeoutError(
        self,
        audio_service: AudioService,
        mock_page: AsyncMock,
    ) -> None:
        """BrowserTimeoutError when polling times out."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with (
            patch(
                "notebooklm.services.audio.poll_until",
                new_callable=AsyncMock,
                side_effect=BrowserTimeoutError(
                    "Polling timed out",
                    context={"operation": "audio_overview_generation"},
                ),
            ),
            pytest.raises(BrowserTimeoutError, match="Polling timed out"),
        ):
            await audio_service.generate_audio_overview("nb-001")

    @pytest.mark.asyncio
    async def test_異常系_要素が見つからない場合BrowserTimeoutError(
        self,
        audio_service: AudioService,
        mock_page: AsyncMock,
    ) -> None:
        """ElementNotFoundError is wrapped as BrowserTimeoutError."""
        with (
            patch(
                "notebooklm.services.audio.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "audio_overview_button"},
                ),
            ),
            pytest.raises(
                BrowserTimeoutError,
                match="Audio Overview generation failed",
            ),
        ):
            await audio_service.generate_audio_overview("nb-001")

    @pytest.mark.asyncio
    async def test_正常系_ページがcloseされる(
        self,
        audio_service: AudioService,
        mock_page: AsyncMock,
    ) -> None:
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.audio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ):
            await audio_service.generate_audio_overview("nb-001")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_異常系_エラー発生時もページがcloseされる(
        self,
        audio_service: AudioService,
        mock_page: AsyncMock,
    ) -> None:
        """Page is closed even when an error occurs."""
        with (
            patch(
                "notebooklm.services.audio.navigate_to_notebook",
                side_effect=ElementNotFoundError(
                    "Element not found",
                    context={"selector": "button"},
                ),
            ),
            pytest.raises(BrowserTimeoutError),
        ):
            await audio_service.generate_audio_overview("nb-001")

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_正常系_poll_untilにexponential_backoffパラメータを渡す(
        self,
        audio_service: AudioService,
        mock_page: AsyncMock,
    ) -> None:
        """poll_until is called with exponential backoff parameters."""
        mock_locator = _make_interactive_locator(count=1)
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch(
            "notebooklm.services.audio.poll_until",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_poll:
            await audio_service.generate_audio_overview("nb-001")

        mock_poll.assert_awaited_once()
        call_kwargs = mock_poll.call_args.kwargs
        assert "timeout_seconds" in call_kwargs
        assert "interval_seconds" in call_kwargs
        assert "operation_name" in call_kwargs
        assert call_kwargs["operation_name"] == "audio_overview_generation"

"""AudioService for NotebookLM Audio Overview generation.

This module provides ``AudioService``, which orchestrates Playwright
browser operations for generating Audio Overview (podcast-style audio)
from NotebookLM notebooks.

Architecture
------------
The service receives a ``NotebookLMBrowserManager`` via dependency injection
and uses ``SelectorManager`` for resilient element lookup with fallback
selector chains.

The generation workflow:
1. Navigates to the target notebook page.
2. Clicks the "Audio Overview" button to initiate generation.
3. Optionally fills a customization prompt.
4. Polls for completion using exponential backoff via ``poll_until``.
5. Returns ``AudioOverviewResult`` with status and timing metadata.

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services.audio import AudioService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     service = AudioService(manager)
...     result = await service.generate_audio_overview("abc-123")
...     print(result.status, result.generation_time_seconds)

See Also
--------
notebooklm.browser.manager : Browser lifecycle management.
notebooklm.browser.helpers : Page operation helpers including poll_until.
notebooklm.selectors : CSS selector management.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from notebooklm.browser.helpers import (
    click_with_fallback,
    navigate_to_notebook,
    poll_until,
    wait_for_element,
)
from notebooklm.constants import (
    AUDIO_OVERVIEW_TIMEOUT_MS,
    DEFAULT_ELEMENT_TIMEOUT_MS,
    GENERATION_POLL_INTERVAL_SECONDS,
)
from notebooklm.decorators import handle_browser_operation
from notebooklm.errors import BrowserTimeoutError
from notebooklm.selectors import SelectorManager
from notebooklm.types import AudioOverviewResult
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from notebooklm.browser.manager import NotebookLMBrowserManager

logger = get_logger(__name__)


class AudioService:
    """Service for NotebookLM Audio Overview generation.

    Provides methods for generating Audio Overview (podcast-style audio)
    from notebook sources via Playwright browser automation.

    Parameters
    ----------
    browser_manager : NotebookLMBrowserManager
        Initialized browser manager for page creation.

    Attributes
    ----------
    _browser_manager : NotebookLMBrowserManager
        The injected browser manager.
    _selectors : SelectorManager
        Selector registry for UI element lookup.

    Examples
    --------
    >>> async with NotebookLMBrowserManager() as manager:
    ...     service = AudioService(manager)
    ...     result = await service.generate_audio_overview("abc-123")
    ...     print(result.status)
    'completed'
    """

    def __init__(self, browser_manager: NotebookLMBrowserManager) -> None:
        self._browser_manager = browser_manager
        self._selectors = SelectorManager()

        logger.debug("AudioService initialized")

    @handle_browser_operation(error_class=BrowserTimeoutError)
    async def generate_audio_overview(
        self,
        notebook_id: str,
        customize_prompt: str | None = None,
    ) -> AudioOverviewResult:
        """Generate an Audio Overview for a notebook.

        Navigates to the notebook page, clicks the Audio Overview button,
        optionally fills a customization prompt, and polls for generation
        completion using exponential backoff.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        customize_prompt : str | None
            Optional prompt to customize the audio generation.
            If provided, the text is entered into the customization
            input field before starting generation.

        Returns
        -------
        AudioOverviewResult
            Result containing notebook_id, status, and generation time.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty.
        BrowserTimeoutError
            If the audio generation times out or a browser operation fails.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> result = await service.generate_audio_overview("abc-123")
        >>> print(result.status, result.generation_time_seconds)
        'completed' 45.0

        >>> result = await service.generate_audio_overview(
        ...     "abc-123",
        ...     customize_prompt="Focus on technical details",
        ... )
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        logger.info(
            "Starting Audio Overview generation",
            notebook_id=notebook_id,
            has_customization=customize_prompt is not None,
        )

        start_time = time.monotonic()

        async with self._browser_manager.managed_page() as page:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Fill customization prompt if provided
            if customize_prompt:
                await self._fill_customize_prompt(page, customize_prompt)

            # Click the Audio Overview button to start generation
            audio_button_selectors = self._selectors.get_selector_strings(
                "audio_overview_button"
            )
            await click_with_fallback(
                page,
                audio_button_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Small delay for generation to start
            await asyncio.sleep(1.0)

            # Poll for completion using exponential backoff
            timeout_seconds = AUDIO_OVERVIEW_TIMEOUT_MS / 1000.0

            async def check_audio_complete() -> bool:
                return await self._is_generation_complete(page)

            await poll_until(
                check_fn=check_audio_complete,
                timeout_seconds=timeout_seconds,
                interval_seconds=GENERATION_POLL_INTERVAL_SECONDS,
                operation_name="audio_overview_generation",
            )

            elapsed = time.monotonic() - start_time

            logger.info(
                "Audio Overview generation completed",
                notebook_id=notebook_id,
                generation_time_seconds=round(elapsed, 2),
            )

            return AudioOverviewResult(
                notebook_id=notebook_id,
                status="completed",
                generation_time_seconds=round(elapsed, 2),
            )

    # ---- Private helpers ----

    async def _fill_customize_prompt(
        self,
        page: Any,
        prompt: str,
    ) -> None:
        """Fill the Audio Overview customization input field.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.
        prompt : str
            Customization prompt text to enter.
        """
        customize_selectors = self._selectors.get_selector_strings(
            "audio_customize_input"
        )
        try:
            customize_input = await wait_for_element(
                page,
                customize_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )
            await customize_input.fill(prompt)
            logger.debug(
                "Customization prompt filled",
                prompt_length=len(prompt),
            )
        except Exception as e:
            logger.warning(
                "Failed to fill customization prompt, proceeding without it",
                error=str(e),
            )

    async def _is_generation_complete(self, page: Any) -> bool:
        """Check whether Audio Overview generation has completed.

        Looks for indicators that generation is finished, such as
        the appearance of a play button or the disappearance of
        a progress indicator.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.

        Returns
        -------
        bool
            True if generation is complete, False otherwise.
        """
        # Check for play button appearance (indicates audio is ready)
        play_locator = page.locator(
            'button[aria-label="再生"], [role="button"]:has-text("再生"), audio[src]'
        )
        count = await play_locator.count()
        if count > 0:
            logger.debug("Audio generation complete: play button detected")
            return True

        return False


__all__ = [
    "AudioService",
]

"""SourceService for NotebookLM source management operations.

This module provides ``SourceService``, which orchestrates Playwright
browser operations for adding and listing sources in NotebookLM notebooks.

Architecture
------------
The service receives a ``NotebookLMBrowserManager`` via dependency injection
and uses ``SelectorManager`` for resilient element lookup with fallback
selector chains.

Phase 1 implements:
- ``add_text_source``: Add pasted text as a source.
- ``list_sources``: List all sources in a notebook.

Future phases will add:
- ``add_url_source``: Add a URL source.
- ``add_file_source``: Upload a file source.
- ``delete_source``: Remove a source.

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services.source import SourceService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     service = SourceService(manager)
...     source = await service.add_text_source(
...         notebook_id="abc-123",
...         text="Research findings...",
...         title="Research Notes",
...     )
...     print(source.source_id)

See Also
--------
notebooklm.browser.manager : Browser lifecycle management.
notebooklm.browser.helpers : Page operation helpers.
notebooklm.selectors : CSS selector management.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING, Any

from notebooklm.browser.helpers import (
    click_with_fallback,
    navigate_to_notebook,
    wait_for_element,
)
from notebooklm.constants import (
    DEFAULT_ELEMENT_TIMEOUT_MS,
    SOURCE_ADD_TIMEOUT_MS,
)
from notebooklm.errors import SourceAddError
from notebooklm.selectors import SelectorManager
from notebooklm.types import SourceInfo, SourceType
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from notebooklm.browser.manager import NotebookLMBrowserManager

logger = get_logger(__name__)


class SourceService:
    """Service for NotebookLM source management operations.

    Provides methods for adding and listing sources in NotebookLM
    notebooks via Playwright browser automation.

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
    ...     service = SourceService(manager)
    ...     sources = await service.list_sources("abc-123")
    ...     for src in sources:
    ...         print(f"{src.title}: {src.source_type}")
    """

    def __init__(self, browser_manager: NotebookLMBrowserManager) -> None:
        self._browser_manager = browser_manager
        self._selectors = SelectorManager()

        logger.debug("SourceService initialized")

    async def add_text_source(
        self,
        notebook_id: str,
        text: str,
        title: str | None = None,
    ) -> SourceInfo:
        """Add pasted text as a source to a notebook.

        Navigates to the notebook page, opens the source addition dialog,
        selects the "Copied text" option, pastes the text, and submits.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        text : str
            Text content to add as a source. Must not be empty.
        title : str | None
            Optional display title for the source.
            If None, defaults to "Pasted text".

        Returns
        -------
        SourceInfo
            Metadata for the newly added source.

        Raises
        ------
        ValueError
            If ``notebook_id`` or ``text`` is empty.
        SourceAddError
            If the text source cannot be added.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> source = await service.add_text_source(
        ...     notebook_id="abc-123",
        ...     text="Research findings about AI...",
        ...     title="AI Research Notes",
        ... )
        >>> print(source.source_id)
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not text.strip():
            raise ValueError("text must not be empty")

        effective_title = title or "Pasted text"

        logger.info(
            "Adding text source",
            notebook_id=notebook_id,
            title=effective_title,
            text_length=len(text),
        )

        page = await self._browser_manager.new_page()
        try:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Click "Add source" button
            add_source_selectors = self._selectors.get_selector_strings(
                "source_add_button"
            )
            await click_with_fallback(
                page,
                add_source_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Small delay for dialog animation
            await asyncio.sleep(0.5)

            # Click "Copied text" button
            text_button_selectors = self._selectors.get_selector_strings(
                "source_text_button"
            )
            await click_with_fallback(
                page,
                text_button_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Fill the text input area
            text_input_selectors = self._selectors.get_selector_strings(
                "source_text_input"
            )
            text_element = await wait_for_element(
                page,
                text_input_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )
            await text_element.fill(text)

            # Click insert/submit button
            insert_selectors = self._selectors.get_selector_strings(
                "source_insert_button"
            )
            await click_with_fallback(
                page,
                insert_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for source to be processed (progress bar disappears)
            await self._wait_for_source_processing(page)

            # Generate a source ID (NotebookLM doesn't expose IDs easily)
            source_id = f"src-{uuid.uuid4().hex[:8]}"

            logger.info(
                "Text source added",
                notebook_id=notebook_id,
                source_id=source_id,
                title=effective_title,
            )

            return SourceInfo(
                source_id=source_id,
                title=effective_title,
                source_type="text",
            )

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise SourceAddError(
                f"Failed to add text source: {e}",
                context={
                    "notebook_id": notebook_id,
                    "source_type": "text",
                    "text_length": len(text),
                    "error": str(e),
                },
            ) from e
        finally:
            await page.close()

    async def list_sources(
        self,
        notebook_id: str,
    ) -> list[SourceInfo]:
        """List all sources in a notebook.

        Navigates to the notebook page and scrapes the source list
        panel to extract metadata for each source.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.

        Returns
        -------
        list[SourceInfo]
            List of source metadata, ordered as displayed on the page.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> sources = await service.list_sources("abc-123")
        >>> for src in sources:
        ...     print(f"{src.title} ({src.source_type})")
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        logger.info("Listing sources", notebook_id=notebook_id)

        page = await self._browser_manager.new_page()
        try:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Wait for source panel to load
            await page.wait_for_load_state("networkidle")

            # Find source items in the source panel
            source_elements = await page.locator(
                ".source-item, [data-type='source-item'], .source-list-item"
            ).all()

            sources: list[SourceInfo] = []
            for idx, element in enumerate(source_elements):
                title = await element.inner_text()
                title = title.strip() if title else f"Source {idx + 1}"

                # Try to get source type from element attributes
                source_type = await self._detect_source_type(element)

                source_id = f"src-{idx:03d}"

                sources.append(
                    SourceInfo(
                        source_id=source_id,
                        title=title,
                        source_type=source_type,
                    )
                )

            logger.info(
                "Sources listed",
                notebook_id=notebook_id,
                count=len(sources),
            )
            return sources

        finally:
            await page.close()

    # ---- Private helpers ----

    async def _wait_for_source_processing(self, page: Any) -> None:
        """Wait for source processing to complete.

        Monitors the progress bar and waits for it to disappear,
        indicating that the source has been processed.

        Parameters
        ----------
        page : Any
            Playwright page object.
        """
        progress_selectors = self._selectors.get_selector_strings("search_progress_bar")

        if not progress_selectors:
            # If no progress bar selector, just wait a fixed time
            await asyncio.sleep(3.0)
            return

        try:
            progress_locator = page.locator(progress_selectors[0])
            # Wait up to SOURCE_ADD_TIMEOUT_MS for progress bar to appear and disappear
            await asyncio.sleep(1.0)

            # Check if progress bar is present
            count = await progress_locator.count()
            if count > 0:
                # Wait for it to disappear
                await progress_locator.wait_for(
                    state="hidden",
                    timeout=SOURCE_ADD_TIMEOUT_MS,
                )
        except (TimeoutError, Exception) as e:
            logger.warning(
                "Source processing wait timed out or failed",
                error=str(e),
            )
            # Continue anyway - the source may have been added successfully

    @staticmethod
    async def _detect_source_type(element: Any) -> SourceType:
        """Detect the source type from a source list element.

        Parameters
        ----------
        element : Any
            Playwright locator for a source list item.

        Returns
        -------
        SourceType
            Detected source type. Defaults to "text" if unknown.
        """
        valid_types: set[SourceType] = {
            "text",
            "url",
            "file",
            "google_drive",
            "youtube",
            "web_research",
        }

        try:
            # Try to get data attribute or icon class for type detection
            data_type = await element.get_attribute("data-source-type")
            if data_type and data_type in valid_types:
                return data_type

            # Check for type indicators in inner HTML
            inner_html = await element.inner_html()
            inner_lower = inner_html.lower() if inner_html else ""

            if "url" in inner_lower or "link" in inner_lower:
                return "url"
            if "file" in inner_lower or "upload" in inner_lower:
                return "file"
            if "drive" in inner_lower:
                return "google_drive"
            if "youtube" in inner_lower:
                return "youtube"

        except Exception:
            logger.debug("Failed to detect source type, defaulting to text")

        return "text"


__all__ = [
    "SourceService",
]

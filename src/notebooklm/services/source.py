"""SourceService for NotebookLM source management operations.

This module provides ``SourceService``, which orchestrates Playwright
browser operations for managing sources in NotebookLM notebooks.

Architecture
------------
The service receives a ``NotebookLMBrowserManager`` via dependency injection
and uses ``SelectorManager`` for resilient element lookup with fallback
selector chains.

Phase 1 (implemented):
- ``add_text_source``: Add pasted text as a source.
- ``list_sources``: List all sources in a notebook.

Phase 2 (implemented):
- ``add_url_source``: Add a URL/website source.
- ``add_file_source``: Upload a file source.
- ``get_source_details``: Get detailed information about a source.
- ``delete_source``: Remove a source from a notebook.
- ``rename_source``: Rename a source.
- ``toggle_source_selection``: Select or deselect a source.
- ``web_research``: Run Fast or Deep web research.

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services.source import SourceService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     service = SourceService(manager)
...     source = await service.add_url_source(
...         notebook_id="abc-123",
...         url="https://example.com/article",
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
from pathlib import Path
from typing import TYPE_CHECKING, Any

from notebooklm.browser.helpers import (
    click_with_fallback,
    extract_text,
    navigate_to_notebook,
    poll_until,
    wait_for_element,
)
from notebooklm.constants import (
    DEEP_RESEARCH_POLL_INTERVAL_SECONDS,
    DEEP_RESEARCH_TIMEOUT_MS,
    DEFAULT_ELEMENT_TIMEOUT_MS,
    FAST_RESEARCH_TIMEOUT_MS,
    FILE_UPLOAD_TIMEOUT_MS,
    SOURCE_ADD_TIMEOUT_MS,
)
from notebooklm.decorators import handle_browser_operation
from notebooklm.errors import SourceAddError
from notebooklm.selectors import SelectorManager
from notebooklm.types import (
    ResearchMode,
    SearchResult,
    SourceDetails,
    SourceInfo,
    SourceType,
)
from notebooklm.validation import (
    validate_file_path,
    validate_text_input,
    validate_url_input,
)
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

    @handle_browser_operation(error_class=SourceAddError)
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

        # SEC-002: Validate text input for XSS and injection attacks
        validate_text_input(text)

        effective_title = title or "Pasted text"

        logger.info(
            "Adding text source",
            notebook_id=notebook_id,
            title=effective_title,
            text_length=len(text),
        )

        async with self._browser_manager.managed_page() as page:
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

    @handle_browser_operation(error_class=SourceAddError)
    async def add_url_source(
        self,
        notebook_id: str,
        url: str,
    ) -> SourceInfo:
        """Add a URL/website as a source to a notebook.

        Navigates to the notebook page, opens the source addition dialog,
        selects the "Website" option, pastes the URL, and submits.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        url : str
            URL of the website to add as a source. Must not be empty.

        Returns
        -------
        SourceInfo
            Metadata for the newly added source.

        Raises
        ------
        ValueError
            If ``notebook_id`` or ``url`` is empty.
        SourceAddError
            If the URL source cannot be added.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> source = await service.add_url_source(
        ...     notebook_id="abc-123",
        ...     url="https://example.com/article",
        ... )
        >>> print(source.source_id)
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not url.strip():
            raise ValueError("url must not be empty")

        # SEC-003: Validate URL input for SSRF attacks
        validate_url_input(url)

        logger.info(
            "Adding URL source",
            notebook_id=notebook_id,
            url=url,
        )

        async with self._browser_manager.managed_page() as page:
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

            await asyncio.sleep(0.5)

            # Click "Website" button
            url_button_selectors = self._selectors.get_selector_strings(
                "source_url_button"
            )
            await click_with_fallback(
                page,
                url_button_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Fill the URL input
            url_input_selectors = self._selectors.get_selector_strings(
                "source_url_input"
            )
            url_element = await wait_for_element(
                page,
                url_input_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )
            await url_element.fill(url)

            # Click insert/submit button
            insert_selectors = self._selectors.get_selector_strings(
                "source_insert_button"
            )
            await click_with_fallback(
                page,
                insert_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for source to be processed
            await self._wait_for_source_processing(page)

            source_id = f"src-{uuid.uuid4().hex[:8]}"

            logger.info(
                "URL source added",
                notebook_id=notebook_id,
                source_id=source_id,
                url=url,
            )

            return SourceInfo(
                source_id=source_id,
                title=url,
                source_type="url",
            )

    @handle_browser_operation(error_class=SourceAddError)
    async def add_file_source(
        self,
        notebook_id: str,
        file_path: str,
    ) -> SourceInfo:
        """Upload a file as a source to a notebook.

        Navigates to the notebook page, opens the source addition dialog,
        and uploads the specified file using the file chooser.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        file_path : str
            Local file path to upload. Must not be empty and file must exist.

        Returns
        -------
        SourceInfo
            Metadata for the newly added source.

        Raises
        ------
        ValueError
            If ``notebook_id`` or ``file_path`` is empty.
        FileNotFoundError
            If the specified file does not exist.
        SourceAddError
            If the file source cannot be added.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> source = await service.add_file_source(
        ...     notebook_id="abc-123",
        ...     file_path="/path/to/document.pdf",
        ... )
        >>> print(source.source_id)
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not file_path.strip():
            raise ValueError("file_path must not be empty")

        # SEC-004: Validate file path for path traversal attacks
        resolved_path = validate_file_path(file_path)

        logger.info(
            "Adding file source",
            notebook_id=notebook_id,
            file_path=file_path,
        )

        async with self._browser_manager.managed_page() as page:
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

            await asyncio.sleep(0.5)

            # Set up file chooser handler and click upload button
            upload_button_selectors = self._selectors.get_selector_strings(
                "source_file_upload_button"
            )

            async with page.expect_file_chooser(
                timeout=FILE_UPLOAD_TIMEOUT_MS,
            ) as fc_info:
                await click_with_fallback(
                    page,
                    upload_button_selectors,
                    timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
                )

            file_chooser = await fc_info.value
            await file_chooser.set_files(str(resolved_path))

            # Wait for source to be processed
            await self._wait_for_source_processing(page)

            source_id = f"src-{uuid.uuid4().hex[:8]}"
            file_title = resolved_path.name

            logger.info(
                "File source added",
                notebook_id=notebook_id,
                source_id=source_id,
                file_path=file_path,
            )

            return SourceInfo(
                source_id=source_id,
                title=file_title,
                source_type="file",
            )

    @handle_browser_operation(error_class=SourceAddError)
    async def get_source_details(
        self,
        notebook_id: str,
        source_index: int,
    ) -> SourceDetails:
        """Get detailed information about a specific source.

        Navigates to the notebook page, clicks on the source at the
        given index to open its detail panel, and extracts metadata
        including content summary and URL.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        source_index : int
            Zero-based index of the source in the source list.
            Must be non-negative.

        Returns
        -------
        SourceDetails
            Detailed source information including content summary.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty or ``source_index`` is negative.
        SourceAddError
            If the source details cannot be retrieved.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> details = await service.get_source_details(
        ...     notebook_id="abc-123",
        ...     source_index=0,
        ... )
        >>> print(details.content_summary)
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if source_index < 0:
            raise ValueError("source_index must be non-negative")

        logger.info(
            "Getting source details",
            notebook_id=notebook_id,
            source_index=source_index,
        )

        async with self._browser_manager.managed_page() as page:
            await navigate_to_notebook(page, notebook_id)
            await page.wait_for_load_state("networkidle")

            # Find source items
            source_elements = await page.locator(
                ".source-item, [data-type='source-item'], .source-list-item"
            ).all()

            if source_index >= len(source_elements):
                raise ValueError(
                    f"source_index {source_index} out of range "
                    f"(notebook has {len(source_elements)} sources)"
                )

            # Click on the source to open detail panel
            source_element = source_elements[source_index]
            await source_element.click()
            await asyncio.sleep(1.0)

            # Extract title
            title = await source_element.inner_text()
            title = title.strip() if title else f"Source {source_index + 1}"

            # Detect source type
            source_type = await self._detect_source_type(source_element)

            # Try to extract content summary from detail panel
            content_summary = await extract_text(
                page,
                ".source-detail-summary, .source-summary, [data-type='source-summary']",
            )

            # Try to extract source URL if present
            source_url = await self._extract_source_url(page)

            source_id = f"src-{source_index:03d}"

            logger.info(
                "Source details retrieved",
                notebook_id=notebook_id,
                source_id=source_id,
                title=title,
                source_type=source_type,
            )

            return SourceDetails(
                source_id=source_id,
                title=title,
                source_type=source_type,
                source_url=source_url,
                content_summary=content_summary,
            )

    @handle_browser_operation(error_class=SourceAddError)
    async def delete_source(
        self,
        notebook_id: str,
        source_index: int,
    ) -> bool:
        """Delete a source from a notebook.

        Navigates to the notebook page, locates the source at the given
        index, opens its context menu, and clicks delete.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        source_index : int
            Zero-based index of the source to delete.
            Must be non-negative.

        Returns
        -------
        bool
            True if the source was deleted successfully.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty or ``source_index`` is negative.
        SourceAddError
            If the source cannot be deleted.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> deleted = await service.delete_source(
        ...     notebook_id="abc-123",
        ...     source_index=0,
        ... )
        >>> print(deleted)
        True
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if source_index < 0:
            raise ValueError("source_index must be non-negative")

        logger.info(
            "Deleting source",
            notebook_id=notebook_id,
            source_index=source_index,
        )

        async with self._browser_manager.managed_page() as page:
            await navigate_to_notebook(page, notebook_id)
            await page.wait_for_load_state("networkidle")

            # Find source items
            source_elements = await page.locator(
                ".source-item, [data-type='source-item'], .source-list-item"
            ).all()

            if source_index >= len(source_elements):
                raise ValueError(
                    f"source_index {source_index} out of range "
                    f"(notebook has {len(source_elements)} sources)"
                )

            # Hover over the source to reveal menu button
            source_element = source_elements[source_index]
            await source_element.hover()
            await asyncio.sleep(0.3)

            # Click "More options" menu button
            more_menu_selectors = self._selectors.get_selector_strings(
                "source_more_menu_button"
            )
            await click_with_fallback(
                page,
                more_menu_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            await asyncio.sleep(0.3)

            # Click "Delete source" menu item
            delete_selectors = self._selectors.get_selector_strings(
                "source_delete_menuitem"
            )
            await click_with_fallback(
                page,
                delete_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            await asyncio.sleep(1.0)

            logger.info(
                "Source deleted",
                notebook_id=notebook_id,
                source_index=source_index,
            )

            return True

    @handle_browser_operation(error_class=SourceAddError)
    async def rename_source(
        self,
        notebook_id: str,
        source_index: int,
        new_name: str,
    ) -> SourceInfo:
        """Rename a source in a notebook.

        Navigates to the notebook page, locates the source at the given
        index, opens its context menu, clicks rename, and types the new name.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        source_index : int
            Zero-based index of the source to rename.
            Must be non-negative.
        new_name : str
            New name for the source. Must not be empty.

        Returns
        -------
        SourceInfo
            Updated source metadata with the new name.

        Raises
        ------
        ValueError
            If ``notebook_id`` or ``new_name`` is empty,
            or ``source_index`` is negative.
        SourceAddError
            If the source cannot be renamed.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> source = await service.rename_source(
        ...     notebook_id="abc-123",
        ...     source_index=0,
        ...     new_name="Updated Research Notes",
        ... )
        >>> print(source.title)
        'Updated Research Notes'
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if source_index < 0:
            raise ValueError("source_index must be non-negative")
        if not new_name.strip():
            raise ValueError("new_name must not be empty")

        logger.info(
            "Renaming source",
            notebook_id=notebook_id,
            source_index=source_index,
            new_name=new_name,
        )

        async with self._browser_manager.managed_page() as page:
            await navigate_to_notebook(page, notebook_id)
            await page.wait_for_load_state("networkidle")

            # Find source items
            source_elements = await page.locator(
                ".source-item, [data-type='source-item'], .source-list-item"
            ).all()

            if source_index >= len(source_elements):
                raise ValueError(
                    f"source_index {source_index} out of range "
                    f"(notebook has {len(source_elements)} sources)"
                )

            # Hover over the source to reveal menu button
            source_element = source_elements[source_index]
            await source_element.hover()
            await asyncio.sleep(0.3)

            # Click "More options" menu button
            more_menu_selectors = self._selectors.get_selector_strings(
                "source_more_menu_button"
            )
            await click_with_fallback(
                page,
                more_menu_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            await asyncio.sleep(0.3)

            # Click "Rename source" menu item
            rename_selectors = self._selectors.get_selector_strings(
                "source_rename_menuitem"
            )
            await click_with_fallback(
                page,
                rename_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            await asyncio.sleep(0.3)

            # Find and fill the rename input (usually an inline input)
            rename_input = await wait_for_element(
                page,
                ['input[type="text"]', '[contenteditable="true"]'],
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Clear existing text and type new name
            await rename_input.fill("")
            await rename_input.fill(new_name)
            await page.keyboard.press("Enter")

            await asyncio.sleep(0.5)

            source_id = f"src-{source_index:03d}"

            logger.info(
                "Source renamed",
                notebook_id=notebook_id,
                source_index=source_index,
                new_name=new_name,
            )

            return SourceInfo(
                source_id=source_id,
                title=new_name,
                source_type="text",
            )

    @handle_browser_operation(error_class=SourceAddError)
    async def toggle_source_selection(
        self,
        notebook_id: str,
        source_index: int | None = None,
        *,
        select_all: bool = False,
    ) -> bool:
        """Select or deselect a source (or all sources) in a notebook.

        When ``select_all`` is True, toggles the "Select all" checkbox.
        When ``source_index`` is provided, clicks the checkbox for
        that specific source.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        source_index : int | None
            Zero-based index of the source to toggle.
            Required if ``select_all`` is False.
        select_all : bool
            If True, toggles the select-all checkbox.
            Defaults to False.

        Returns
        -------
        bool
            True if the toggle operation completed.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty, or neither ``source_index``
            nor ``select_all`` is specified.
        SourceAddError
            If the toggle operation fails.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> # Toggle a specific source
        >>> await service.toggle_source_selection("abc-123", source_index=0)
        True
        >>> # Toggle all sources
        >>> await service.toggle_source_selection("abc-123", select_all=True)
        True
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not select_all and source_index is None:
            raise ValueError("Either source_index or select_all=True must be specified")
        if source_index is not None and source_index < 0:
            raise ValueError("source_index must be non-negative")

        logger.info(
            "Toggling source selection",
            notebook_id=notebook_id,
            source_index=source_index,
            select_all=select_all,
        )

        async with self._browser_manager.managed_page() as page:
            await navigate_to_notebook(page, notebook_id)
            await page.wait_for_load_state("networkidle")

            if select_all:
                # Click the "Select all" checkbox
                select_all_selectors = self._selectors.get_selector_strings(
                    "source_select_all_checkbox"
                )
                await click_with_fallback(
                    page,
                    select_all_selectors,
                    timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
                )
            else:
                # Find source items
                source_elements = await page.locator(
                    ".source-item, [data-type='source-item'], .source-list-item"
                ).all()

                assert source_index is not None  # guaranteed by validation above
                if source_index >= len(source_elements):
                    raise ValueError(
                        f"source_index {source_index} out of range "
                        f"(notebook has {len(source_elements)} sources)"
                    )

                # Click the checkbox for the specific source
                source_element = source_elements[source_index]
                checkbox = source_element.locator(
                    '[role="checkbox"], input[type="checkbox"]'
                )
                count = await checkbox.count()
                if count > 0:
                    await checkbox.click()
                else:
                    # Fall back to clicking the source element itself
                    await source_element.click()

            await asyncio.sleep(0.3)

            logger.info(
                "Source selection toggled",
                notebook_id=notebook_id,
                source_index=source_index,
                select_all=select_all,
            )

            return True

    @handle_browser_operation(error_class=SourceAddError)
    async def web_research(
        self,
        notebook_id: str,
        query: str,
        mode: ResearchMode = "fast",
    ) -> list[SearchResult]:
        """Run web research to discover and add sources.

        Navigates to the notebook page, opens the source addition dialog,
        selects the research mode (Fast or Deep), enters the query,
        and waits for results.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        query : str
            Search query for source discovery. Must not be empty.
        mode : ResearchMode
            Research mode: "fast" for quick results or "deep" for
            comprehensive research. Defaults to "fast".

        Returns
        -------
        list[SearchResult]
            List of discovered sources from the research.

        Raises
        ------
        ValueError
            If ``notebook_id`` or ``query`` is empty.
        SourceAddError
            If the web research operation fails.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> results = await service.web_research(
        ...     notebook_id="abc-123",
        ...     query="AI investment trends 2026",
        ...     mode="fast",
        ... )
        >>> for r in results:
        ...     print(f"{r.title}: {r.url}")
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not query.strip():
            raise ValueError("query must not be empty")

        logger.info(
            "Starting web research",
            notebook_id=notebook_id,
            query=query,
            mode=mode,
        )

        async with self._browser_manager.managed_page() as page:
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

            await asyncio.sleep(0.5)

            # Select research mode
            if mode == "deep":
                mode_selectors = self._selectors.get_selector_strings(
                    "search_mode_deep"
                )
            else:
                mode_selectors = self._selectors.get_selector_strings(
                    "search_mode_fast"
                )

            if mode_selectors:
                await click_with_fallback(
                    page,
                    mode_selectors,
                    timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
                )
                await asyncio.sleep(0.3)

            # Enter search query
            query_input_selectors = self._selectors.get_selector_strings(
                "search_query_input"
            )
            query_element = await wait_for_element(
                page,
                query_input_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )
            await query_element.fill(query)
            await page.keyboard.press("Enter")

            # Wait for research to complete
            timeout_ms = (
                DEEP_RESEARCH_TIMEOUT_MS if mode == "deep" else FAST_RESEARCH_TIMEOUT_MS
            )
            complete_selector = (
                "search_deep_complete" if mode == "deep" else "search_fast_complete"
            )

            complete_selectors = self._selectors.get_selector_strings(complete_selector)

            if complete_selectors:

                async def _check_complete() -> bool:
                    locator = page.locator(complete_selectors[0])
                    count = await locator.count()
                    return count > 0

                poll_interval = (
                    DEEP_RESEARCH_POLL_INTERVAL_SECONDS if mode == "deep" else 2.0
                )

                await poll_until(
                    _check_complete,
                    timeout_seconds=timeout_ms / 1000.0,
                    interval_seconds=poll_interval,
                    operation_name=f"{mode}_research",
                )
            else:
                # Fallback: wait a fixed time
                wait_time = 30.0 if mode == "deep" else 10.0
                await asyncio.sleep(wait_time)

            # Extract search results
            results = await self._extract_search_results(page)

            logger.info(
                "Web research completed",
                notebook_id=notebook_id,
                query=query,
                mode=mode,
                result_count=len(results),
            )

            return results

    @handle_browser_operation(error_class=SourceAddError)
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

        async with self._browser_manager.managed_page() as page:
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

    # ---- Private helpers ----

    async def _wait_for_source_processing(self, page: Any) -> None:
        """Wait for source processing via UI state polling.

        Polls for progress indicator disappearance instead of fixed sleep.
        This adapts to actual processing time (typically 0.5-5s).

        Parameters
        ----------
        page : Any
            Playwright page object.
        """
        progress_selectors = self._selectors.get_selector_strings("search_progress_bar")

        # Build the list of selectors to check for active processing
        poll_selectors = list(progress_selectors) if progress_selectors else []
        # Add generic progress indicators as fallback
        poll_selectors.extend(
            [
                'div[role="progressbar"]',
                '[aria-busy="true"]',
            ]
        )

        async def _is_processing_complete() -> bool:
            """Check if all progress indicators have disappeared."""
            for selector in poll_selectors:
                try:
                    locator = page.locator(selector)
                    count = await locator.count()
                    if count > 0:
                        return False
                except Exception:  # nosec B112
                    continue  # Intentional: try next selector in fallback chain
            return True

        try:
            await poll_until(
                _is_processing_complete,
                timeout_seconds=SOURCE_ADD_TIMEOUT_MS / 1000.0,
                interval_seconds=0.5,
                backoff_factor=1.0,
                operation_name="source_processing",
            )
        except Exception as e:
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

    @staticmethod
    async def _extract_source_url(page: Any) -> str | None:
        """Extract the source URL from the detail panel.

        Parameters
        ----------
        page : Any
            Playwright page object with a source detail panel open.

        Returns
        -------
        str | None
            The source URL if found, or None.
        """
        try:
            link_locator = page.locator(
                ".source-detail-url a, [data-type='source-url'] a, .source-link a"
            )
            count = await link_locator.count()
            if count > 0:
                href = await link_locator.first.get_attribute("href")
                return href
        except Exception:
            logger.debug("Failed to extract source URL")

        return None

    async def _extract_search_results(self, page: Any) -> list[SearchResult]:
        """Extract search results from the research results panel.

        Parameters
        ----------
        page : Any
            Playwright page object with research results displayed.

        Returns
        -------
        list[SearchResult]
            List of discovered search results.
        """
        results: list[SearchResult] = []

        try:
            # Look for search result items
            result_elements = await page.locator(
                ".search-result-item, [data-type='search-result'], .research-result"
            ).all()

            for element in result_elements:
                title = await element.inner_text()
                title = title.strip() if title else "Untitled"

                # Try to extract URL
                url = ""
                link = element.locator("a")
                link_count = await link.count()
                if link_count > 0:
                    href = await link.first.get_attribute("href")
                    url = href or ""

                # Try to extract summary
                summary_el = element.locator(".result-summary, .result-description")
                summary_count = await summary_el.count()
                summary = ""
                if summary_count > 0:
                    summary_text = await summary_el.first.inner_text()
                    summary = summary_text.strip() if summary_text else ""

                if url:
                    results.append(
                        SearchResult(
                            title=title,
                            url=url,
                            summary=summary,
                            source_type="web",
                            selected=True,
                        )
                    )

        except Exception as e:
            logger.warning(
                "Failed to extract search results",
                error=str(e),
            )

        return results


__all__ = [
    "SourceService",
]

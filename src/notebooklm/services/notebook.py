"""NotebookService for NotebookLM notebook CRUD operations.

This module provides ``NotebookService``, which orchestrates Playwright
browser operations for creating, listing, summarizing, and deleting
NotebookLM notebooks.

Architecture
------------
The service receives a ``NotebookLMBrowserManager`` via dependency injection
and uses ``SelectorManager`` for resilient element lookup with fallback
selector chains.

Each operation:
1. Creates a new browser page from the shared context.
2. Performs navigation and UI interaction.
3. Extracts data from the page DOM.
4. Returns typed Pydantic models.
5. Closes the page in a ``finally`` block.

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services.notebook import NotebookService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     service = NotebookService(manager)
...     notebooks = await service.list_notebooks()
...     for nb in notebooks:
...         print(f"{nb.title} ({nb.notebook_id})")

See Also
--------
notebooklm.browser.manager : Browser lifecycle management.
notebooklm.browser.helpers : Page operation helpers.
notebooklm.selectors : CSS selector management.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from notebooklm.browser.helpers import (
    click_with_fallback,
    extract_text,
    navigate_to_notebook,
    wait_for_element,
)
from notebooklm.constants import (
    DEFAULT_ELEMENT_TIMEOUT_MS,
    DEFAULT_NAVIGATION_TIMEOUT_MS,
    NOTEBOOKLM_BASE_URL,
)
from notebooklm.decorators import handle_browser_operation
from notebooklm.errors import ElementNotFoundError, NotebookLMError
from notebooklm.selectors import SelectorManager
from notebooklm.types import NotebookInfo, NotebookSummary
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from notebooklm.browser.manager import NotebookLMBrowserManager

logger = get_logger(__name__)

# Regex to extract notebook ID from URL path
_NOTEBOOK_ID_PATTERN = re.compile(r"/notebook/([^/?#]+)")


class NotebookService:
    """Service for NotebookLM notebook CRUD operations.

    Provides methods for creating, listing, and retrieving summaries
    of NotebookLM notebooks via Playwright browser automation.

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
    ...     service = NotebookService(manager)
    ...     nb = await service.create_notebook("My Notebook")
    ...     print(nb.notebook_id)
    """

    def __init__(self, browser_manager: NotebookLMBrowserManager) -> None:
        self._browser_manager = browser_manager
        self._selectors = SelectorManager()

        logger.debug("NotebookService initialized")

    @handle_browser_operation(error_class=NotebookLMError)
    async def create_notebook(self, title: str) -> NotebookInfo:
        """Create a new NotebookLM notebook.

        Navigates to the NotebookLM home page, clicks the create button,
        and returns the new notebook's metadata.

        Parameters
        ----------
        title : str
            Display title for the new notebook. Must not be empty.

        Returns
        -------
        NotebookInfo
            Metadata for the newly created notebook.

        Raises
        ------
        ValueError
            If ``title`` is empty.
        ElementNotFoundError
            If the create button cannot be found.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> nb = await service.create_notebook("AI Research Notes")
        >>> print(nb.notebook_id)
        'c9354f3f-f55b-4f90-a5c4-219e582945cf'
        """
        if not title.strip():
            raise ValueError("title must not be empty")

        logger.info("Creating notebook", title=title)

        async with self._browser_manager.managed_page() as page:
            # Navigate to NotebookLM home page
            await page.goto(
                NOTEBOOKLM_BASE_URL,
                timeout=DEFAULT_NAVIGATION_TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            await page.wait_for_load_state("networkidle")

            # Click create notebook button
            create_selectors = self._selectors.get_selector_strings(
                "create_notebook_button"
            )
            await click_with_fallback(
                page,
                create_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for navigation to the new notebook page
            await page.wait_for_url(
                re.compile(r".*/notebook/.*"),
                timeout=DEFAULT_NAVIGATION_TIMEOUT_MS,
            )

            # Extract notebook ID from URL
            notebook_id = self._extract_notebook_id(page.url)

            logger.info(
                "Notebook created",
                notebook_id=notebook_id,
                title=title,
            )

            return NotebookInfo(
                notebook_id=notebook_id,
                title=title,
                source_count=0,
            )

    @handle_browser_operation(error_class=NotebookLMError)
    async def list_notebooks(self) -> list[NotebookInfo]:
        """List all NotebookLM notebooks.

        Navigates to the NotebookLM home page and scrapes the
        notebook list to extract metadata for each notebook.

        Returns
        -------
        list[NotebookInfo]
            List of notebook metadata, ordered as displayed on the page.

        Raises
        ------
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> notebooks = await service.list_notebooks()
        >>> for nb in notebooks:
        ...     print(f"{nb.title}: {nb.notebook_id}")
        """
        logger.info("Listing notebooks")

        async with self._browser_manager.managed_page() as page:
            # Navigate to NotebookLM home page
            await page.goto(
                NOTEBOOKLM_BASE_URL,
                timeout=DEFAULT_NAVIGATION_TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            await page.wait_for_load_state("networkidle")

            # Get notebook list items using selector
            notebook_link_selectors = self._selectors.get_selector_strings(
                "notebook_list_item"
            )
            selector = (
                notebook_link_selectors[0]
                if notebook_link_selectors
                else 'a[href*="/notebook/"]'
            )

            links = await page.locator(selector).all()

            notebooks: list[NotebookInfo] = []
            for link in links:
                href = await link.get_attribute("href")
                if href is None:
                    continue

                notebook_id = self._extract_notebook_id_from_path(href)
                if not notebook_id:
                    continue

                title = await link.inner_text()
                title = title.strip() if title else "Untitled"

                notebooks.append(
                    NotebookInfo(
                        notebook_id=notebook_id,
                        title=title,
                        source_count=0,
                    )
                )

            logger.info("Notebooks listed", count=len(notebooks))
            return notebooks

    @handle_browser_operation(error_class=NotebookLMError)
    async def get_notebook_summary(
        self,
        notebook_id: str,
    ) -> NotebookSummary:
        """Get the AI-generated summary of a notebook.

        Navigates to the notebook page and extracts the auto-generated
        summary text and suggested questions.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.

        Returns
        -------
        NotebookSummary
            AI-generated summary and suggested questions.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> summary = await service.get_notebook_summary("abc-123")
        >>> print(summary.summary_text)
        'This notebook covers...'
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        logger.info("Getting notebook summary", notebook_id=notebook_id)

        async with self._browser_manager.managed_page() as page:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Wait for content to load
            await page.wait_for_load_state("networkidle")

            # Extract summary text using the summary copy button area
            summary_text = await self._extract_summary_text(page)

            # Extract suggested questions
            suggested_questions = await self._extract_suggested_questions(page)

            logger.info(
                "Notebook summary retrieved",
                notebook_id=notebook_id,
                summary_length=len(summary_text),
                question_count=len(suggested_questions),
            )

            return NotebookSummary(
                notebook_id=notebook_id,
                summary_text=summary_text,
                suggested_questions=suggested_questions,
            )

    @handle_browser_operation(error_class=NotebookLMError)
    async def delete_notebook(self, notebook_id: str) -> bool:
        """Delete a NotebookLM notebook.

        Navigates to the NotebookLM home page, locates the notebook
        by its ID, opens the settings menu, and clicks the delete option.
        Handles the confirmation dialog.

        Parameters
        ----------
        notebook_id : str
            UUID of the notebook to delete. Must not be empty.

        Returns
        -------
        bool
            True if the notebook was deleted successfully.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty.
        ElementNotFoundError
            If the notebook or delete menu cannot be found.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> deleted = await service.delete_notebook("c9354f3f-f55b-4f90-a5c4-219e582945cf")
        >>> print(deleted)
        True
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        logger.info("Deleting notebook", notebook_id=notebook_id)

        async with self._browser_manager.managed_page() as page:
            # Navigate to NotebookLM home page
            await page.goto(
                NOTEBOOKLM_BASE_URL,
                timeout=DEFAULT_NAVIGATION_TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            await page.wait_for_load_state("networkidle")

            # Find the notebook link element by its href
            notebook_link = page.locator(f'a[href*="/notebook/{notebook_id}"]')
            link_count = await notebook_link.count()
            if link_count == 0:
                raise ElementNotFoundError(
                    f"Notebook not found: {notebook_id}",
                    context={
                        "notebook_id": notebook_id,
                        "page_url": page.url,
                    },
                )

            # Hover over the notebook to reveal the settings menu button
            await notebook_link.first.hover()

            # Click the settings/more menu button
            settings_selectors = self._selectors.get_selector_strings(
                "notebook_settings_menu"
            )
            await click_with_fallback(
                page,
                settings_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Click the delete menu item
            delete_selectors = self._selectors.get_selector_strings(
                "notebook_delete_menuitem"
            )
            await click_with_fallback(
                page,
                delete_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Handle confirmation dialog
            confirm_selectors = self._selectors.get_selector_strings(
                "notebook_delete_confirm_button"
            )
            await click_with_fallback(
                page,
                confirm_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for the page to reflect the deletion
            await page.wait_for_load_state("networkidle")

            logger.info(
                "Notebook deleted",
                notebook_id=notebook_id,
            )

            return True

    # ---- Private helpers ----

    @staticmethod
    def _extract_notebook_id(url: str) -> str:
        """Extract notebook ID from a full URL.

        Parameters
        ----------
        url : str
            Full NotebookLM URL containing a notebook ID.

        Returns
        -------
        str
            The extracted notebook ID.

        Raises
        ------
        ValueError
            If no notebook ID is found in the URL.
        """
        match = _NOTEBOOK_ID_PATTERN.search(url)
        if not match:
            raise ValueError(f"No notebook ID found in URL: {url}")
        return match.group(1)

    @staticmethod
    def _extract_notebook_id_from_path(path: str) -> str | None:
        """Extract notebook ID from a URL path segment.

        Parameters
        ----------
        path : str
            URL path like ``/notebook/abc-123``.

        Returns
        -------
        str | None
            The extracted notebook ID, or None if not found.
        """
        match = _NOTEBOOK_ID_PATTERN.search(path)
        return match.group(1) if match else None

    async def _extract_summary_text(self, page: Any) -> str:
        """Extract notebook summary text from the page.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.

        Returns
        -------
        str
            The summary text, or empty string if not found.
        """
        # Look for summary text in the notebook guide section
        summary = await extract_text(page, ".notebook-guide-content")
        if summary:
            return summary

        # Fallback: try to extract from first content section
        summary = await extract_text(page, "[data-content-type='summary']")
        if summary:
            return summary

        # Second fallback: extract from any available text area
        locator = page.locator(".notebook-guide-content, .guide-content, .summary-text")
        count = await locator.count()
        if count > 0:
            text = await locator.inner_text()
            return text.strip() if text else ""

        logger.warning(
            "Summary text not found",
            page_url=getattr(page, "url", "unknown"),
        )
        return ""

    async def _extract_suggested_questions(self, page: Any) -> list[str]:
        """Extract suggested questions from the notebook page.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.

        Returns
        -------
        list[str]
            List of suggested question strings.
        """
        # Suggested questions are typically displayed as clickable chips
        question_locator = page.locator(
            ".suggested-question, [data-type='suggested-question'], .guide-chip"
        )

        elements = await question_locator.all()
        questions: list[str] = []

        for element in elements:
            text = await element.inner_text()
            text = text.strip() if text else ""
            if text:
                questions.append(text)

        return questions


__all__ = [
    "NotebookService",
]

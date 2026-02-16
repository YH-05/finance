"""StudioService for NotebookLM Studio content generation.

This module provides ``StudioService``, which orchestrates Playwright
browser operations for generating Studio content (reports, infographics,
slides, and data tables) from NotebookLM notebooks.

Architecture
------------
The service receives a ``NotebookLMBrowserManager`` via dependency injection
and uses ``SelectorManager`` for resilient element lookup with fallback
selector chains.

The generation workflow:
1. Navigates to the target notebook page.
2. Clicks the appropriate Studio content button (report, infographic, etc.).
3. Optionally selects a report format (briefing_doc, study_guide, blog_post).
4. Polls for generation completion using exponential backoff via ``poll_until``.
5. Extracts the generated content (text, table data, or download path).
6. Returns ``StudioContentResult`` with content and timing metadata.

Content Type Extraction Strategies
-----------------------------------
- **Report**: Copies formatted text via the clipboard copy button, then
  reads clipboard content as Markdown.
- **Data Table**: Scrapes HTML ``<table>`` rows/cells into a 2D list of strings
  using ``extract_table_data``.
- **Infographic / Slides**: Visual content types that are available in the
  viewer; no automatic download is performed (download_path is None).

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services.studio import StudioService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     service = StudioService(manager)
...     result = await service.generate_content("abc-123", "report")
...     print(result.text_content)

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
    extract_table_data,
    navigate_to_notebook,
    poll_until,
    wait_for_element,
)
from notebooklm.constants import (
    DEFAULT_ELEMENT_TIMEOUT_MS,
    GENERATION_POLL_INTERVAL_SECONDS,
    STUDIO_GENERATION_TIMEOUT_MS,
)
from notebooklm.errors import StudioGenerationError
from notebooklm.selectors import SelectorManager
from notebooklm.types import ReportFormat, StudioContentResult, StudioContentType
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from notebooklm.browser.manager import NotebookLMBrowserManager

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Content type to selector name mapping
# ---------------------------------------------------------------------------

_CONTENT_TYPE_BUTTON_MAP: dict[str, str] = {
    "report": "studio_report_button",
    "infographic": "studio_infographic_button",
    "slides": "studio_slides_button",
    "data_table": "studio_data_table_button",
}
"""Mapping from content type to the selector group name for the generate button."""

_REPORT_FORMAT_SELECTOR_MAP: dict[str, str] = {
    "briefing_doc": "studio_report_format_briefing",
    "study_guide": "studio_report_format_study_guide",
    "blog_post": "studio_report_format_blog",
}
"""Mapping from report format to the selector group name for the format button."""

_CONTENT_TYPE_VIEWER_CLOSE_MAP: dict[str, str] = {
    "report": "studio_close_viewer_report",
    "slides": "studio_close_viewer_slides",
    "data_table": "studio_close_viewer_table",
}
"""Mapping from content type to the selector group name for the viewer close button."""


class StudioService:
    """Service for NotebookLM Studio content generation.

    Provides a unified interface for generating 4 types of Studio content
    (reports, infographics, slides, data tables) via Playwright browser
    automation.

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
    ...     service = StudioService(manager)
    ...     result = await service.generate_content("abc-123", "report")
    ...     print(result.content_type, result.generation_time_seconds)
    'report' 15.3
    """

    def __init__(self, browser_manager: NotebookLMBrowserManager) -> None:
        self._browser_manager = browser_manager
        self._selectors = SelectorManager()

        logger.debug("StudioService initialized")

    async def generate_content(
        self,
        notebook_id: str,
        content_type: StudioContentType,
        *,
        report_format: ReportFormat | None = None,
    ) -> StudioContentResult:
        """Generate Studio content for a notebook.

        Navigates to the notebook page, clicks the appropriate Studio
        content button, optionally selects a report format, polls for
        generation completion, and extracts the generated content.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        content_type : StudioContentType
            Type of Studio content to generate. One of:
            ``"report"``, ``"infographic"``, ``"slides"``, ``"data_table"``.
        report_format : ReportFormat | None
            Optional report format. Only applicable when ``content_type``
            is ``"report"``. One of: ``"custom"``, ``"briefing_doc"``,
            ``"study_guide"``, ``"blog_post"``. Defaults to None (custom).

        Returns
        -------
        StudioContentResult
            Result containing notebook_id, content_type, extracted content,
            and generation time.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty.
        StudioGenerationError
            If the content generation fails or times out.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> result = await service.generate_content("abc-123", "report")
        >>> print(result.text_content)
        '# Report Title\\n\\nContent...'

        >>> result = await service.generate_content(
        ...     "abc-123",
        ...     "report",
        ...     report_format="briefing_doc",
        ... )

        >>> result = await service.generate_content("abc-123", "data_table")
        >>> print(result.table_data)
        [['Header1', 'Header2'], ['Value1', 'Value2']]
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        logger.info(
            "Starting Studio content generation",
            notebook_id=notebook_id,
            content_type=content_type,
            report_format=report_format,
        )

        start_time = time.monotonic()

        page = await self._browser_manager.new_page()
        try:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Click the content type button
            await self._click_content_button(page, content_type)

            # Select report format if specified
            if content_type == "report" and report_format is not None:
                await self._select_report_format(page, report_format)

            # Small delay for generation to start
            await asyncio.sleep(1.0)

            # Poll for completion
            timeout_seconds = STUDIO_GENERATION_TIMEOUT_MS / 1000.0

            async def check_generation_complete() -> bool:
                return await self._is_generation_complete(page, content_type)

            await poll_until(
                check_fn=check_generation_complete,
                timeout_seconds=timeout_seconds,
                interval_seconds=GENERATION_POLL_INTERVAL_SECONDS,
                operation_name=f"studio_{content_type}_generation",
            )

            # Extract content based on type
            text_content: str | None = None
            table_data: list[list[str]] | None = None
            title = ""

            if content_type == "report":
                text_content = await self._extract_report_content(page)
                title = self._extract_title_from_text(text_content)
            elif content_type == "data_table":
                table_data = await self._extract_table_content(page)
                title = "Data Table"
            else:
                title = content_type.replace("_", " ").title()

            elapsed = time.monotonic() - start_time

            logger.info(
                "Studio content generation completed",
                notebook_id=notebook_id,
                content_type=content_type,
                generation_time_seconds=round(elapsed, 2),
            )

            return StudioContentResult(
                notebook_id=notebook_id,
                content_type=content_type,
                title=title,
                text_content=text_content,
                table_data=table_data,
                generation_time_seconds=round(elapsed, 2),
            )

        except (ValueError, StudioGenerationError):
            raise
        except Exception as e:
            raise StudioGenerationError(
                f"Studio content generation failed: {e}",
                context={
                    "notebook_id": notebook_id,
                    "content_type": content_type,
                    "error": str(e),
                },
            ) from e
        finally:
            await page.close()

    # ---- Private helpers ----

    async def _click_content_button(
        self,
        page: Any,
        content_type: StudioContentType,
    ) -> None:
        """Click the Studio content generation button for the given type.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.
        content_type : StudioContentType
            Type of content to generate.

        Raises
        ------
        StudioGenerationError
            If the content type button cannot be found.
        """
        selector_name = _CONTENT_TYPE_BUTTON_MAP.get(content_type)
        if selector_name is None:
            raise StudioGenerationError(
                f"Unsupported content type: {content_type}",
                context={"content_type": content_type},
            )

        button_selectors = self._selectors.get_selector_strings(selector_name)
        await click_with_fallback(
            page,
            button_selectors,
            timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
        )

        logger.debug(
            "Content type button clicked",
            content_type=content_type,
        )

    async def _select_report_format(
        self,
        page: Any,
        report_format: ReportFormat,
    ) -> None:
        """Select a report format option.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.
        report_format : ReportFormat
            Report format to select.
        """
        if report_format == "custom":
            # Custom format is the default; no action needed
            return

        selector_name = _REPORT_FORMAT_SELECTOR_MAP.get(report_format)
        if selector_name is None:
            logger.warning(
                "Unknown report format, using default",
                report_format=report_format,
            )
            return

        format_selectors = self._selectors.get_selector_strings(selector_name)
        try:
            await click_with_fallback(
                page,
                format_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )
            logger.debug(
                "Report format selected",
                report_format=report_format,
            )
        except Exception as e:
            logger.warning(
                "Failed to select report format, proceeding with default",
                report_format=report_format,
                error=str(e),
            )

    async def _is_generation_complete(
        self,
        page: Any,
        content_type: StudioContentType,
    ) -> bool:
        """Check whether Studio content generation has completed.

        Detection strategy varies by content type:
        - Report: Check for the report viewer element.
        - Data Table: Check for table element appearance.
        - Infographic / Slides: Check for viewer/download button.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.
        content_type : StudioContentType
            Type of content being generated.

        Returns
        -------
        bool
            True if generation is complete, False otherwise.
        """
        if content_type == "report":
            # Check for report viewer element
            viewer_selectors = self._selectors.get_selector_strings(
                "studio_report_viewer"
            )
            for selector in viewer_selectors:
                locator = page.locator(selector)
                count = await locator.count()
                if count > 0:
                    logger.debug("Report generation complete: viewer detected")
                    return True

        elif content_type == "data_table":
            # Check for table element
            close_selectors = self._selectors.get_selector_strings(
                "studio_close_viewer_table"
            )
            for selector in close_selectors:
                locator = page.locator(selector)
                count = await locator.count()
                if count > 0:
                    logger.debug(
                        "Data Table generation complete: close button detected"
                    )
                    return True

        else:
            # Infographic / Slides: check for more options button in viewer
            more_selectors = self._selectors.get_selector_strings(
                "studio_more_options_button"
            )
            for selector in more_selectors:
                locator = page.locator(selector)
                count = await locator.count()
                if count > 0:
                    logger.debug(
                        f"{content_type} generation complete: options button detected"
                    )
                    return True

        return False

    async def _extract_report_content(self, page: Any) -> str:
        """Extract report content as Markdown via clipboard copy.

        Clicks the copy button on the report viewer and reads the
        clipboard content via ``page.evaluate()``.

        Parameters
        ----------
        page : Any
            Playwright page object with report viewer visible.

        Returns
        -------
        str
            Report content in Markdown format.
        """
        # Click the copy report button
        copy_selectors = self._selectors.get_selector_strings(
            "studio_copy_report_button"
        )
        try:
            await click_with_fallback(
                page,
                copy_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Small delay for clipboard write
            await asyncio.sleep(0.5)

            # Read clipboard content
            clipboard_text: str = await page.evaluate("navigator.clipboard.readText()")
            content = clipboard_text.strip() if clipboard_text else ""

            logger.debug(
                "Report content extracted via clipboard",
                content_length=len(content),
            )
            return content

        except Exception as e:
            logger.warning(
                "Clipboard copy failed, falling back to DOM extraction",
                error=str(e),
            )
            return await self._extract_report_from_dom(page)

    async def _extract_report_from_dom(self, page: Any) -> str:
        """Extract report content directly from the DOM.

        Fallback method when clipboard access is unavailable.

        Parameters
        ----------
        page : Any
            Playwright page object with report viewer visible.

        Returns
        -------
        str
            Extracted report text, or empty string if not found.
        """
        viewer_selectors = self._selectors.get_selector_strings("studio_report_viewer")
        for selector in viewer_selectors:
            locator = page.locator(selector)
            count = await locator.count()
            if count > 0:
                text = await locator.inner_text()
                content = text.strip() if text else ""
                logger.debug(
                    "Report content extracted from DOM",
                    content_length=len(content),
                )
                return content

        logger.warning("No report viewer element found in DOM")
        return ""

    async def _extract_table_content(self, page: Any) -> list[list[str]]:
        """Extract Data Table content as structured data.

        Scrapes HTML table rows and cells into a 2D list of strings
        using ``extract_table_data``.

        Parameters
        ----------
        page : Any
            Playwright page object with data table viewer visible.

        Returns
        -------
        list[list[str]]
            2D list of cell text values. Empty list if table not found.
        """
        # Try to find the table element
        table_data = await extract_table_data(page, "table")

        if table_data:
            logger.debug(
                "Table data extracted",
                rows=len(table_data),
                cols=len(table_data[0]) if table_data else 0,
            )
        else:
            logger.warning("No table data found in viewer")

        return table_data

    @staticmethod
    def _extract_title_from_text(text: str | None) -> str:
        """Extract a title from Markdown text content.

        Looks for the first Markdown heading (``# Title``) in the text.
        Falls back to ``"Report"`` if no heading is found.

        Parameters
        ----------
        text : str | None
            Markdown text to extract the title from.

        Returns
        -------
        str
            Extracted title string.
        """
        if not text:
            return "Report"

        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()

        return "Report"


__all__ = [
    "StudioService",
]

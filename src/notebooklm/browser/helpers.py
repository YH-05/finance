"""Page operation helpers for NotebookLM Playwright automation.

This module provides helper functions for common browser operations:

- Element waiting with selector fallback chains
- Text extraction from page elements
- Click operations with fallback selectors
- Polling with exponential backoff for long-running operations
- File download waiting
- Navigation with session expiry detection
- DOM scraping (table data extraction)

All helpers are designed to work with Playwright page objects
and use the NotebookLM error hierarchy for consistent error handling.

Examples
--------
>>> from notebooklm.browser.helpers import wait_for_element, poll_until
>>>
>>> element = await wait_for_element(
...     page,
...     ['button[aria-label="Send"]', 'button.send-btn'],
...     timeout_ms=5000,
... )
>>>
>>> await poll_until(
...     check_fn=lambda: is_generation_complete(page),
...     timeout_seconds=600.0,
...     interval_seconds=2.0,
... )

See Also
--------
notebooklm.selectors : CSS selector management with fallback support.
notebooklm.browser.manager : Browser lifecycle management.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable

from notebooklm.constants import (
    DEFAULT_ELEMENT_TIMEOUT_MS,
    DEFAULT_NAVIGATION_TIMEOUT_MS,
    GOOGLE_LOGIN_URL,
    NOTEBOOK_URL_TEMPLATE,
)
from notebooklm.errors import (
    BrowserTimeoutError,
    ElementNotFoundError,
    SessionExpiredError,
)
from utils_core.logging import get_logger

logger = get_logger(__name__)


async def wait_for_element(
    page: Any,
    selectors: list[str],
    *,
    timeout_ms: int = DEFAULT_ELEMENT_TIMEOUT_MS,
) -> Any:
    """Wait for an element using a fallback chain of selectors.

    Tries each selector in order and returns the first match.
    Uses Playwright's ``locator().wait_for()`` for each candidate.

    Parameters
    ----------
    page : Any
        Playwright page object.
    selectors : list[str]
        Ordered list of CSS selectors to try (highest priority first).
    timeout_ms : int
        Timeout per selector attempt in milliseconds.

    Returns
    -------
    Any
        The first matching Playwright locator element.

    Raises
    ------
    ElementNotFoundError
        If no selector matches within the timeout.

    Examples
    --------
    >>> element = await wait_for_element(
    ...     page,
    ...     ['button[aria-label="Send"]', 'button.fallback'],
    ...     timeout_ms=5000,
    ... )
    """
    tried_selectors: list[str] = []

    for selector in selectors:
        try:
            locator = page.locator(selector)
            await locator.wait_for(timeout=timeout_ms, state="visible")

            count = await locator.count()
            if count > 0:
                logger.debug(
                    "Element found",
                    selector=selector,
                    count=count,
                )
                return locator.first

        except (TimeoutError, Exception) as e:
            tried_selectors.append(selector)
            logger.debug(
                "Selector did not match",
                selector=selector,
                error=str(e),
            )
            continue

    raise ElementNotFoundError(
        f"No element found for any selector: {tried_selectors}",
        context={
            "selectors": tried_selectors,
            "timeout_ms": timeout_ms,
            "page_url": getattr(page, "url", "unknown"),
        },
    )


async def extract_text(
    page: Any,
    selector: str,
) -> str | None:
    """Extract inner text from an element on the page.

    Parameters
    ----------
    page : Any
        Playwright page object.
    selector : str
        CSS selector for the target element.

    Returns
    -------
    str | None
        Stripped text content, or None if the element is not found.

    Examples
    --------
    >>> text = await extract_text(page, "div.summary")
    >>> if text:
    ...     print(text)
    """
    locator = page.locator(selector)
    count = await locator.count()

    if count == 0:
        logger.debug("Element not found for text extraction", selector=selector)
        return None

    text = await locator.inner_text()
    stripped = text.strip() if text else None

    logger.debug(
        "Text extracted",
        selector=selector,
        text_length=len(stripped) if stripped else 0,
    )

    return stripped


async def poll_until(
    check_fn: Callable[[], Awaitable[bool]],
    *,
    timeout_seconds: float,
    interval_seconds: float,
    backoff_factor: float = 1.5,
    max_interval_seconds: float = 30.0,
    operation_name: str = "polling",
) -> bool:
    """Poll a condition function with exponential backoff.

    Repeatedly calls ``check_fn`` until it returns True or
    the timeout expires. Uses exponential backoff to reduce
    polling frequency over time.

    Parameters
    ----------
    check_fn : Callable[[], Awaitable[bool]]
        Async function that returns True when the condition is met.
    timeout_seconds : float
        Maximum time to wait in seconds.
    interval_seconds : float
        Initial polling interval in seconds.
    backoff_factor : float
        Multiplier for exponential backoff. Default is 1.5.
    max_interval_seconds : float
        Maximum polling interval in seconds. Default is 30.0.
    operation_name : str
        Name of the operation for logging and error messages.

    Returns
    -------
    bool
        True when the condition is met.

    Raises
    ------
    BrowserTimeoutError
        If the condition is not met within the timeout.

    Examples
    --------
    >>> async def is_complete() -> bool:
    ...     return await check_generation_status(page)
    >>>
    >>> await poll_until(
    ...     is_complete,
    ...     timeout_seconds=600.0,
    ...     interval_seconds=2.0,
    ... )
    """
    start_time = time.monotonic()
    current_interval = interval_seconds
    attempt = 0

    while True:
        attempt += 1

        result = await check_fn()
        if result:
            elapsed = time.monotonic() - start_time
            logger.debug(
                "Poll condition met",
                operation=operation_name,
                attempts=attempt,
                elapsed_seconds=round(elapsed, 2),
            )
            return True

        elapsed = time.monotonic() - start_time
        if elapsed >= timeout_seconds:
            raise BrowserTimeoutError(
                f"Polling timed out after {timeout_seconds}s "
                f"({attempt} attempts) for operation: {operation_name}",
                context={
                    "operation": operation_name,
                    "timeout_seconds": timeout_seconds,
                    "attempts": attempt,
                    "elapsed_seconds": round(elapsed, 2),
                },
            )

        logger.debug(
            "Poll condition not met, waiting",
            operation=operation_name,
            attempt=attempt,
            interval=round(current_interval, 2),
        )

        await asyncio.sleep(current_interval)
        current_interval = min(
            current_interval * backoff_factor,
            max_interval_seconds,
        )


async def wait_for_download(page: Any) -> Any:
    """Wait for a file download to complete.

    Uses Playwright's ``expect_download`` to capture the download event.

    Parameters
    ----------
    page : Any
        Playwright page object.

    Returns
    -------
    Any
        Playwright Download object with path and filename.

    Examples
    --------
    >>> download = await wait_for_download(page)
    >>> path = await download.path()
    >>> filename = download.suggested_filename
    """
    async with page.expect_download() as download_info:
        pass
    download = download_info.value

    logger.info(
        "Download completed",
        filename=download.suggested_filename,
    )

    return download


async def click_with_fallback(
    page: Any,
    selectors: list[str],
    *,
    timeout_ms: int = DEFAULT_ELEMENT_TIMEOUT_MS,
) -> None:
    """Click an element using a fallback chain of selectors.

    Tries each selector in order and clicks the first visible match.

    Parameters
    ----------
    page : Any
        Playwright page object.
    selectors : list[str]
        Ordered list of CSS selectors to try.
    timeout_ms : int
        Timeout for waiting per selector in milliseconds.

    Raises
    ------
    ElementNotFoundError
        If no selector matches a clickable element.

    Examples
    --------
    >>> await click_with_fallback(
    ...     page,
    ...     ['button[aria-label="Send"]', 'button.send-btn'],
    ...     timeout_ms=5000,
    ... )
    """
    tried_selectors: list[str] = []

    for selector in selectors:
        locator = page.locator(selector)
        count = await locator.count()

        if count > 0:
            await locator.click()
            logger.debug("Clicked element", selector=selector)
            return

        tried_selectors.append(selector)
        logger.debug("Selector not clickable", selector=selector)

    raise ElementNotFoundError(
        f"No clickable element found for any selector: {tried_selectors}",
        context={
            "selectors": tried_selectors,
            "timeout_ms": timeout_ms,
            "page_url": getattr(page, "url", "unknown"),
        },
    )


async def navigate_to_notebook(
    page: Any,
    notebook_id: str,
    *,
    timeout_ms: int = DEFAULT_NAVIGATION_TIMEOUT_MS,
) -> None:
    """Navigate to a specific NotebookLM notebook page.

    Navigates to the notebook URL and checks for session expiry
    by detecting redirects to the Google login page.

    Parameters
    ----------
    page : Any
        Playwright page object.
    notebook_id : str
        UUID of the target notebook.
    timeout_ms : int
        Navigation timeout in milliseconds.

    Raises
    ------
    SessionExpiredError
        If the browser is redirected to the Google login page.
    NavigationError
        If the navigation fails for other reasons.

    Examples
    --------
    >>> await navigate_to_notebook(page, "c9354f3f-f55b-4f90-a5c4-219e582945cf")
    """
    target_url = NOTEBOOK_URL_TEMPLATE.format(notebook_id=notebook_id)

    logger.debug(
        "Navigating to notebook",
        notebook_id=notebook_id,
        target_url=target_url,
    )

    await page.goto(target_url, timeout=timeout_ms, wait_until="domcontentloaded")
    await page.wait_for_load_state("networkidle", timeout=timeout_ms)

    current_url = page.url
    if current_url.startswith(GOOGLE_LOGIN_URL):
        raise SessionExpiredError(
            "Session expired, redirected to Google login",
            context={
                "notebook_id": notebook_id,
                "target_url": target_url,
                "redirect_url": current_url,
            },
        )

    logger.info(
        "Navigated to notebook",
        notebook_id=notebook_id,
        current_url=current_url,
    )


async def extract_table_data(
    page: Any,
    selector: str,
) -> list[list[str]]:
    """Extract table data from a page element.

    Scrapes rows and cells from a table element into a 2D list.

    Parameters
    ----------
    page : Any
        Playwright page object.
    selector : str
        CSS selector for the table element.

    Returns
    -------
    list[list[str]]
        2D list of cell text values. Empty list if table not found.

    Examples
    --------
    >>> data = await extract_table_data(page, "table.report-data")
    >>> for row in data:
    ...     print(row)
    ['Header1', 'Header2']
    ['Value1', 'Value2']
    """
    table_locator = page.locator(selector)
    count = await table_locator.count()

    if count == 0:
        logger.debug("Table not found", selector=selector)
        return []

    rows = await table_locator.locator("tr").all()
    result: list[list[str]] = []

    for row in rows:
        cells = await row.locator("td, th").all_inner_texts()
        result.append(cells)

    logger.debug(
        "Table data extracted",
        selector=selector,
        rows=len(result),
    )

    return result


__all__ = [
    "click_with_fallback",
    "extract_table_data",
    "extract_text",
    "navigate_to_notebook",
    "poll_until",
    "wait_for_download",
    "wait_for_element",
]

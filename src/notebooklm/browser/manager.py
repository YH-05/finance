"""Playwright browser lifecycle manager for NotebookLM automation.

This module provides ``NotebookLMBrowserManager``, which handles:

- Lazy initialization of Playwright browser and context
- ``storage_state()`` session persistence (save/restore)
- Headed/headless mode switching
- Stealth browser configuration (viewport, user agent, init scripts)
- Async context manager pattern for resource management
- Session validity checking (redirect-based expiry detection)

Architecture
------------
The manager creates a single Playwright browser instance and a
browser context with stealth settings applied. Pages are created
from this shared context to inherit cookies and session state.

Examples
--------
>>> from notebooklm.browser.manager import NotebookLMBrowserManager
>>>
>>> async with NotebookLMBrowserManager(headless=False) as manager:
...     page = await manager.new_page()
...     await page.goto("https://notebooklm.google.com")
...     await manager.save_session()

See Also
--------
news.extractors.playwright : Similar Playwright browser pattern.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from notebooklm.constants import (
    DEFAULT_NAVIGATION_TIMEOUT_MS,
    DEFAULT_SESSION_FILE,
    GOOGLE_LOGIN_URL,
    SESSION_CHECK_URL,
    STEALTH_INIT_SCRIPT,
    STEALTH_LOCALE,
    STEALTH_TIMEZONE,
    STEALTH_USER_AGENT,
    STEALTH_VIEWPORT,
)
from utils_core.logging import get_logger

logger = get_logger(__name__)


def _async_playwright_factory() -> Any:
    """Create and return an async_playwright context manager.

    Returns
    -------
    Any
        The async_playwright context manager from playwright.

    Raises
    ------
    ImportError
        If playwright is not installed.
    """
    try:
        from playwright.async_api import (  # type: ignore[import-not-found]
            async_playwright,
        )

        return async_playwright()
    except ImportError as e:
        raise ImportError(
            "playwright is not installed. "
            "Install with: uv add playwright && playwright install chromium"
        ) from e


class NotebookLMBrowserManager:
    """Playwright browser lifecycle manager for NotebookLM automation.

    Manages a single browser instance with stealth configuration,
    session persistence, and automatic resource cleanup.

    Parameters
    ----------
    headless : bool
        Whether to run the browser in headless mode. Default is True.
    session_file : str
        Path to the session state file for cookie persistence.
        Default is ".notebooklm-session.json".

    Attributes
    ----------
    headless : bool
        Whether the browser runs in headless mode.
    session_file : str
        Path to the session state file.

    Examples
    --------
    >>> manager = NotebookLMBrowserManager(headless=False)
    >>> async with manager:
    ...     page = await manager.new_page()
    ...     await page.goto("https://notebooklm.google.com")
    ...     await manager.save_session()
    """

    def __init__(
        self,
        headless: bool = True,
        session_file: str = DEFAULT_SESSION_FILE,
    ) -> None:
        self.headless = headless
        self.session_file = session_file
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._pw_context_manager: Any = None

        logger.debug(
            "NotebookLMBrowserManager created",
            headless=headless,
            session_file=session_file,
        )

    # ---- Async context manager ----

    async def __aenter__(self) -> NotebookLMBrowserManager:
        """Start the async context manager and initialize the browser.

        Returns
        -------
        NotebookLMBrowserManager
            Self for use in ``async with`` statement.
        """
        await self._ensure_browser()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the async context manager and release resources.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if raised.
        exc_val : BaseException | None
            Exception value if raised.
        exc_tb : Any
            Exception traceback if raised.
        """
        await self.close()

    # ---- Browser initialization ----

    async def _ensure_browser(self) -> None:
        """Initialize browser and context if not already started.

        Creates a Playwright browser instance with stealth settings
        and applies session state if a session file exists.

        Raises
        ------
        ImportError
            If playwright is not installed.
        """
        if self._browser is not None:
            return

        logger.debug("Initializing Playwright browser")

        self._pw_context_manager = _async_playwright_factory()
        self._playwright = await self._pw_context_manager.__aenter__()

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )

        # Build context kwargs with stealth settings
        context_kwargs: dict[str, Any] = {
            "viewport": STEALTH_VIEWPORT,
            "user_agent": STEALTH_USER_AGENT,
            "locale": STEALTH_LOCALE,
            "timezone_id": STEALTH_TIMEZONE,
        }

        # Restore session if file exists
        if self.has_session():
            context_kwargs["storage_state"] = self.session_file
            logger.info(
                "Restoring session from file",
                session_file=self.session_file,
            )

        self._context = await self._browser.new_context(**context_kwargs)

        # Apply stealth init script
        await self._context.add_init_script(STEALTH_INIT_SCRIPT)

        logger.info(
            "Playwright browser initialized",
            headless=self.headless,
            session_restored=self.has_session(),
        )

    # ---- Resource cleanup ----

    async def close(self) -> None:
        """Close browser, context, and Playwright resources.

        Safely releases all resources. Can be called multiple times.
        """
        if self._context is not None:
            await self._context.close()
            self._context = None

        if self._browser is not None:
            await self._browser.close()
            self._browser = None

        if self._pw_context_manager is not None:
            await self._pw_context_manager.__aexit__(None, None, None)
            self._pw_context_manager = None

        self._playwright = None

        logger.debug("Playwright browser closed")

    # ---- Page management ----

    async def new_page(self) -> Any:
        """Create a new browser page in the current context.

        The page inherits all cookies and session state from the context.

        Returns
        -------
        Any
            A Playwright Page object.

        Raises
        ------
        RuntimeError
            If the browser context is not initialized.
        """
        await self._ensure_browser()
        page = await self._context.new_page()
        logger.debug("New page created")
        return page

    @asynccontextmanager
    async def managed_page(self) -> AsyncIterator[Any]:
        """Context manager for automatic page lifecycle management.

        Creates a new page, yields it for use, and ensures it is closed
        in the finally block regardless of success or failure.

        Yields
        ------
        Any
            Playwright page instance.

        Examples
        --------
        >>> async with browser_manager.managed_page() as page:
        ...     await page.goto("https://example.com")
        ...     # Page is automatically closed after this block
        """
        page = await self.new_page()
        try:
            yield page
        finally:
            await page.close()

    # ---- Session management ----

    async def save_session(self) -> None:
        """Save the current browser session state to disk.

        Persists cookies and local storage to the session file
        for later restoration. On Unix-like systems, the file
        permissions are restricted to owner-only read/write (0600).

        Raises
        ------
        RuntimeError
            If the browser context is not initialized.
        """
        if self._context is None:
            raise RuntimeError(
                "Browser context not initialized. "
                "Call _ensure_browser() or use async context manager first."
            )

        await self._context.storage_state(path=self.session_file)

        # SEC-006: Restrict session file to owner-only read/write (0600)
        import platform
        import stat
        from pathlib import Path

        if platform.system() != "Windows":
            Path(self.session_file).chmod(stat.S_IRUSR | stat.S_IWUSR)
            logger.info(
                "Session saved with secure permissions",
                session_file=self.session_file,
                permissions="0600",
            )
        else:
            logger.warning(
                "Session saved (Windows does not support Unix permissions)",
                session_file=self.session_file,
            )

    def has_session(self) -> bool:
        """Check whether a session file exists on disk.

        Returns
        -------
        bool
            True if the session file exists, False otherwise.
        """
        return Path(self.session_file).exists()

    async def is_session_valid(self) -> bool:
        """Check whether the current session is still valid.

        Navigates to the NotebookLM check URL and verifies that
        the browser is not redirected to the Google login page.

        Returns
        -------
        bool
            True if the session is valid, False if expired.
        """
        await self._ensure_browser()
        page = await self._context.new_page()

        try:
            await page.goto(
                SESSION_CHECK_URL,
                timeout=DEFAULT_NAVIGATION_TIMEOUT_MS,
                wait_until="domcontentloaded",
            )

            current_url = page.url
            is_valid = not current_url.startswith(GOOGLE_LOGIN_URL)

            logger.debug(
                "Session validity checked",
                current_url=current_url,
                is_valid=is_valid,
            )

            return is_valid
        finally:
            await page.close()


__all__ = [
    "NotebookLMBrowserManager",
]

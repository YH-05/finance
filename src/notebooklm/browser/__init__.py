"""Browser automation layer for NotebookLM.

This sub-package provides Playwright-based browser lifecycle management
and page operation helpers for automating Google NotebookLM.

Modules
-------
manager
    NotebookLMBrowserManager singleton for browser lifecycle management.
helpers
    Page operation helper functions (element wait, text extraction, polling).

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> async with NotebookLMBrowserManager() as manager:
...     page = await manager.new_page()
...     await page.goto("https://notebooklm.google.com")
"""

from notebooklm.browser.manager import NotebookLMBrowserManager

__all__ = [
    "NotebookLMBrowserManager",
]

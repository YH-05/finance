"""NotebookLM MCP server package.

Provides Playwright-based browser automation for Google NotebookLM,
exposing notebook management, source management, AI chat, Audio Overview,
Studio content generation, note management, and batch processing
as MCP tools for Claude Code integration.

Main Components
---------------
NotebookService
    CRUD operations for NotebookLM notebooks.
SourceService
    Source management operations (add, list, delete).
ChatService
    AI chat operations (chat, history, settings).
NotebookLMBrowserManager
    Playwright browser lifecycle management.
SelectorManager
    CSS selector fallback registry.

Examples
--------
>>> from notebooklm import ChatService, NotebookService, SourceService
>>> from notebooklm.browser import NotebookLMBrowserManager
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     notebook_svc = NotebookService(manager)
...     source_svc = SourceService(manager)
...     chat_svc = ChatService(manager)
...     notebooks = await notebook_svc.list_notebooks()
"""

from notebooklm.browser.manager import NotebookLMBrowserManager
from notebooklm.selectors import SelectorManager
from notebooklm.services.chat import ChatService
from notebooklm.services.notebook import NotebookService
from notebooklm.services.source import SourceService

__all__ = [
    "ChatService",
    "NotebookLMBrowserManager",
    "NotebookService",
    "SelectorManager",
    "SourceService",
]

__version__ = "0.1.0"

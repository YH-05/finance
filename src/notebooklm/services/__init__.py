"""Service layer for NotebookLM browser automation.

This module provides high-level service classes that orchestrate
Playwright browser operations for NotebookLM notebook and source
management.

Services
--------
NotebookService
    CRUD operations for NotebookLM notebooks.
SourceService
    Source management operations (add, list, delete).

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services import NotebookService, SourceService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     notebook_svc = NotebookService(manager)
...     source_svc = SourceService(manager)
...     notebooks = await notebook_svc.list_notebooks()
"""

from notebooklm.services.notebook import NotebookService
from notebooklm.services.source import SourceService

__all__ = [
    "NotebookService",
    "SourceService",
]

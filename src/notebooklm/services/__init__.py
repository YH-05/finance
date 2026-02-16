"""Service layer for NotebookLM browser automation.

This module provides high-level service classes that orchestrate
Playwright browser operations for NotebookLM notebook, source,
chat, audio, and batch management.

Services
--------
NotebookService
    CRUD operations for NotebookLM notebooks.
SourceService
    Source management operations (add, list, delete).
ChatService
    AI chat operations (chat, history, settings).
AudioService
    Audio Overview generation operations.
BatchService
    Batch operations (batch add sources, batch chat).

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services import AudioService, BatchService, ChatService, NotebookService, SourceService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     notebook_svc = NotebookService(manager)
...     source_svc = SourceService(manager)
...     chat_svc = ChatService(manager)
...     audio_svc = AudioService(manager)
...     batch_svc = BatchService(source_svc, chat_svc)
...     notebooks = await notebook_svc.list_notebooks()
"""

from notebooklm.services.audio import AudioService
from notebooklm.services.batch import BatchService
from notebooklm.services.chat import ChatService
from notebooklm.services.notebook import NotebookService
from notebooklm.services.source import SourceService

__all__ = [
    "AudioService",
    "BatchService",
    "ChatService",
    "NotebookService",
    "SourceService",
]

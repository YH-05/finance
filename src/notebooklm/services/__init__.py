"""Service layer for NotebookLM browser automation.

This module provides high-level service classes that orchestrate
Playwright browser operations for NotebookLM notebook, source,
chat, audio, studio, note, and batch management.

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
StudioService
    Studio content generation (reports, infographics, slides, data tables).
NoteService
    Note (memo) CRUD operations (create, list, get, delete).
BatchService
    Batch operations (batch add sources, batch chat).

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services import (
...     AudioService, BatchService, ChatService, NoteService,
...     NotebookService, SourceService, StudioService,
... )
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     notebook_svc = NotebookService(manager)
...     source_svc = SourceService(manager)
...     chat_svc = ChatService(manager)
...     audio_svc = AudioService(manager)
...     studio_svc = StudioService(manager)
...     note_svc = NoteService(manager)
...     batch_svc = BatchService(source_svc, chat_svc)
...     notebooks = await notebook_svc.list_notebooks()
"""

from notebooklm.services.audio import AudioService
from notebooklm.services.batch import BatchService
from notebooklm.services.chat import ChatService
from notebooklm.services.note import NoteService
from notebooklm.services.notebook import NotebookService
from notebooklm.services.source import SourceService
from notebooklm.services.studio import StudioService

__all__ = [
    "AudioService",
    "BatchService",
    "ChatService",
    "NoteService",
    "NotebookService",
    "SourceService",
    "StudioService",
]

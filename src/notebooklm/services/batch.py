"""BatchService for NotebookLM batch operations.

This module provides ``BatchService``, which orchestrates sequential
batch operations by delegating to ``SourceService`` and ``ChatService``.

Architecture
------------
The service receives ``SourceService`` and ``ChatService`` via dependency
injection and uses them to perform sequential batch operations. Each item
in the batch is processed independently, and failures do not halt the
remaining items.

Batch Operations:
1. ``batch_add_sources``: Add multiple sources sequentially to a notebook.
2. ``batch_chat``: Send multiple questions sequentially to a notebook.

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services.batch import BatchService
>>> from notebooklm.services.chat import ChatService
>>> from notebooklm.services.source import SourceService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     source_svc = SourceService(manager)
...     chat_svc = ChatService(manager)
...     batch_svc = BatchService(source_svc, chat_svc)
...     result = await batch_svc.batch_add_sources(
...         "abc-123",
...         [{"type": "text", "text": "content", "title": "Source 1"}],
...     )
...     print(result.succeeded, result.failed)

See Also
--------
notebooklm.services.source : SourceService implementation.
notebooklm.services.chat : ChatService implementation.
notebooklm.types : BatchResult data model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from notebooklm.types import BatchResult
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from notebooklm.services.chat import ChatService
    from notebooklm.services.source import SourceService

logger = get_logger(__name__)


class BatchService:
    """Service for NotebookLM batch operations.

    Provides methods for performing sequential batch operations
    on NotebookLM notebooks, including adding multiple sources
    and sending multiple chat questions.

    Parameters
    ----------
    source_service : SourceService
        Initialized source service for source operations.
    chat_service : ChatService
        Initialized chat service for chat operations.

    Attributes
    ----------
    _source_service : SourceService
        The injected source service.
    _chat_service : ChatService
        The injected chat service.

    Examples
    --------
    >>> batch_svc = BatchService(source_svc, chat_svc)
    >>> result = await batch_svc.batch_chat("abc-123", ["Q1", "Q2"])
    >>> print(result.succeeded)
    2
    """

    def __init__(
        self,
        source_service: SourceService,
        chat_service: ChatService,
    ) -> None:
        self._source_service = source_service
        self._chat_service = chat_service

        logger.debug("BatchService initialized")

    async def batch_add_sources(
        self,
        notebook_id: str,
        sources: list[dict[str, Any]],
    ) -> BatchResult:
        """Add multiple sources sequentially to a notebook.

        Processes each source definition one at a time, delegating
        to the appropriate ``SourceService`` method based on the
        source type. Failures on individual sources do not stop
        the remaining sources from being processed.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        sources : list[dict[str, Any]]
            List of source definitions. Each must contain a ``type``
            key (``"text"`` or ``"url"``) and type-specific fields:
            - For ``"text"``: ``text`` (str), optional ``title`` (str).
            - For ``"url"``: ``url`` (str).

        Returns
        -------
        BatchResult
            Result containing total, succeeded, failed counts and
            per-item results.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty or ``sources`` is empty.

        Examples
        --------
        >>> result = await batch_svc.batch_add_sources(
        ...     "abc-123",
        ...     [
        ...         {"type": "text", "text": "content", "title": "S1"},
        ...         {"type": "url", "url": "https://example.com"},
        ...     ],
        ... )
        >>> print(result.succeeded)
        2
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not sources:
            raise ValueError("sources must not be empty")

        logger.info(
            "Starting batch add sources",
            notebook_id=notebook_id,
            source_count=len(sources),
        )

        results: list[dict[str, str]] = []
        succeeded = 0
        failed = 0

        for idx, source_def in enumerate(sources):
            source_type = source_def.get("type", "")

            try:
                if source_type == "text":
                    source_info = await self._source_service.add_text_source(
                        notebook_id=notebook_id,
                        text=source_def.get("text", ""),
                        title=source_def.get("title"),
                    )
                    results.append(
                        {
                            "index": str(idx),
                            "source_id": source_info.source_id,
                            "title": source_info.title,
                            "status": "success",
                        }
                    )
                    succeeded += 1

                elif source_type == "url":
                    source_info = await self._source_service.add_url_source(
                        notebook_id=notebook_id,
                        url=source_def.get("url", ""),
                    )
                    results.append(
                        {
                            "index": str(idx),
                            "source_id": source_info.source_id,
                            "title": source_info.title,
                            "status": "success",
                        }
                    )
                    succeeded += 1

                else:
                    results.append(
                        {
                            "index": str(idx),
                            "status": f"failed: unsupported source type '{source_type}'",
                        }
                    )
                    failed += 1
                    logger.warning(
                        "Unsupported source type in batch",
                        index=idx,
                        source_type=source_type,
                    )

            except Exception as e:
                results.append(
                    {
                        "index": str(idx),
                        "status": f"failed: {e}",
                    }
                )
                failed += 1
                logger.error(
                    "Batch source addition failed",
                    index=idx,
                    source_type=source_type,
                    error=str(e),
                )

        logger.info(
            "Batch add sources completed",
            notebook_id=notebook_id,
            total=len(sources),
            succeeded=succeeded,
            failed=failed,
        )

        return BatchResult(
            total=len(sources),
            succeeded=succeeded,
            failed=failed,
            results=results,
        )

    async def batch_chat(
        self,
        notebook_id: str,
        questions: list[str],
    ) -> BatchResult:
        """Send multiple chat questions sequentially to a notebook.

        Processes each question one at a time, delegating to
        ``ChatService.chat()``. Failures on individual questions
        do not stop the remaining questions from being processed.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        questions : list[str]
            List of questions to ask. Must not be empty.

        Returns
        -------
        BatchResult
            Result containing total, succeeded, failed counts and
            per-item results with question and answer text.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty or ``questions`` is empty.

        Examples
        --------
        >>> result = await batch_svc.batch_chat(
        ...     "abc-123",
        ...     ["What is AI?", "How does ML work?"],
        ... )
        >>> print(result.succeeded)
        2
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not questions:
            raise ValueError("questions must not be empty")

        logger.info(
            "Starting batch chat",
            notebook_id=notebook_id,
            question_count=len(questions),
        )

        results: list[dict[str, str]] = []
        succeeded = 0
        failed = 0

        for idx, question in enumerate(questions):
            try:
                response = await self._chat_service.chat(
                    notebook_id=notebook_id,
                    question=question,
                )
                results.append(
                    {
                        "index": str(idx),
                        "question": question,
                        "answer": response.answer,
                        "status": "success",
                    }
                )
                succeeded += 1

            except Exception as e:
                results.append(
                    {
                        "index": str(idx),
                        "question": question,
                        "status": f"failed: {e}",
                    }
                )
                failed += 1
                logger.error(
                    "Batch chat failed for question",
                    index=idx,
                    question_length=len(question),
                    error=str(e),
                )

        logger.info(
            "Batch chat completed",
            notebook_id=notebook_id,
            total=len(questions),
            succeeded=succeeded,
            failed=failed,
        )

        return BatchResult(
            total=len(questions),
            succeeded=succeeded,
            failed=failed,
            results=results,
        )


__all__ = [
    "BatchService",
]

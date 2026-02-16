"""BatchService for NotebookLM batch operations.

This module provides ``BatchService``, which orchestrates sequential
batch operations by delegating to ``SourceService``, ``ChatService``,
and optionally ``StudioService``.

Architecture
------------
The service receives ``SourceService`` and ``ChatService`` via dependency
injection (with optional ``StudioService``) and uses them to perform
sequential batch operations. Each item in the batch is processed
independently, and failures do not halt the remaining items.

Batch Operations:
1. ``batch_add_sources``: Add multiple sources sequentially to a notebook.
2. ``batch_chat``: Send multiple questions sequentially to a notebook.

Workflow Operations:
3. ``workflow_research``: Orchestrate a complete research workflow
   (add sources -> chat questions -> generate studio content).

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services.batch import BatchService
>>> from notebooklm.services.chat import ChatService
>>> from notebooklm.services.source import SourceService
>>> from notebooklm.services.studio import StudioService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     source_svc = SourceService(manager)
...     chat_svc = ChatService(manager)
...     studio_svc = StudioService(manager)
...     batch_svc = BatchService(source_svc, chat_svc, studio_svc)
...     result = await batch_svc.workflow_research(
...         "abc-123",
...         sources=[{"type": "text", "text": "content", "title": "Source 1"}],
...         questions=["What are the key findings?"],
...     )
...     print(result.status, result.steps_completed)

See Also
--------
notebooklm.services.source : SourceService implementation.
notebooklm.services.chat : ChatService implementation.
notebooklm.services.studio : StudioService implementation.
notebooklm.types : BatchResult, WorkflowResult data models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from notebooklm.types import BatchResult, StudioContentType, WorkflowResult
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from notebooklm.services.chat import ChatService
    from notebooklm.services.source import SourceService
    from notebooklm.services.studio import StudioService

logger = get_logger(__name__)


class BatchService:
    """Service for NotebookLM batch operations.

    Provides methods for performing sequential batch operations
    on NotebookLM notebooks, including adding multiple sources,
    sending multiple chat questions, and orchestrating multi-step
    research workflows.

    Parameters
    ----------
    source_service : SourceService
        Initialized source service for source operations.
    chat_service : ChatService
        Initialized chat service for chat operations.
    studio_service : StudioService | None
        Optional initialized studio service for content generation.
        Required for ``workflow_research()``.

    Attributes
    ----------
    _source_service : SourceService
        The injected source service.
    _chat_service : ChatService
        The injected chat service.
    _studio_service : StudioService | None
        The optional injected studio service.

    Examples
    --------
    >>> batch_svc = BatchService(source_svc, chat_svc, studio_svc)
    >>> result = await batch_svc.workflow_research(
    ...     "abc-123",
    ...     sources=[{"type": "text", "text": "content"}],
    ...     questions=["What is the key insight?"],
    ... )
    >>> print(result.status)
    'completed'
    """

    def __init__(
        self,
        source_service: SourceService,
        chat_service: ChatService,
        studio_service: StudioService | None = None,
    ) -> None:
        self._source_service = source_service
        self._chat_service = chat_service
        self._studio_service = studio_service

        logger.debug(
            "BatchService initialized",
            has_studio_service=studio_service is not None,
        )

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

    async def workflow_research(
        self,
        notebook_id: str,
        sources: list[dict[str, Any]],
        questions: list[str],
        *,
        content_type: StudioContentType = "report",
    ) -> WorkflowResult:
        """Orchestrate a complete research workflow.

        Executes a 3-step pipeline:
        1. Add sources to the notebook via ``batch_add_sources``.
        2. Send research questions via ``batch_chat``.
        3. Generate Studio content (e.g., report) via ``StudioService``.

        Each step is executed independently: failures in one step do not
        prevent subsequent steps from running. The overall status reflects
        how many steps completed successfully.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        sources : list[dict[str, Any]]
            List of source definitions to add. Must not be empty.
            Each must contain a ``type`` key (``"text"`` or ``"url"``).
        questions : list[str]
            List of research questions to ask. Must not be empty.
        content_type : StudioContentType
            Type of Studio content to generate. Defaults to ``"report"``.

        Returns
        -------
        WorkflowResult
            Result containing workflow name, status, step counts,
            outputs (notebook_id, source/chat counts, content_type),
            and any error messages.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty, ``sources`` is empty,
            ``questions`` is empty, or ``studio_service`` is not set.

        Examples
        --------
        >>> result = await batch_svc.workflow_research(
        ...     "abc-123",
        ...     sources=[{"type": "text", "text": "AI paper content"}],
        ...     questions=["What are the key findings?"],
        ... )
        >>> print(result.status)
        'completed'
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not sources:
            raise ValueError("sources must not be empty")
        if not questions:
            raise ValueError("questions must not be empty")
        if self._studio_service is None:
            raise ValueError(
                "studio_service is required for workflow_research. "
                "Pass studio_service to BatchService constructor."
            )

        logger.info(
            "Starting research workflow",
            notebook_id=notebook_id,
            source_count=len(sources),
            question_count=len(questions),
            content_type=content_type,
        )

        steps_total = 3
        steps_completed = 0
        errors: list[str] = []
        outputs: dict[str, str] = {"notebook_id": notebook_id}

        # Step 1: Add sources
        try:
            source_result = await self.batch_add_sources(notebook_id, sources)
            outputs["sources_succeeded"] = str(source_result.succeeded)
            outputs["sources_failed"] = str(source_result.failed)

            if source_result.failed == source_result.total:
                errors.append(f"All {source_result.total} sources failed to add")
            else:
                steps_completed += 1
                if source_result.failed > 0:
                    logger.warning(
                        "Some sources failed in workflow",
                        succeeded=source_result.succeeded,
                        failed=source_result.failed,
                    )
        except Exception as e:
            errors.append(f"Source addition failed: {e}")
            outputs["sources_succeeded"] = "0"
            outputs["sources_failed"] = str(len(sources))
            logger.error(
                "Workflow source step failed",
                error=str(e),
            )

        # Step 2: Send chat questions
        try:
            chat_result = await self.batch_chat(notebook_id, questions)
            outputs["chat_succeeded"] = str(chat_result.succeeded)
            outputs["chat_failed"] = str(chat_result.failed)

            if chat_result.failed == chat_result.total:
                errors.append(f"All {chat_result.total} chat questions failed")
            else:
                steps_completed += 1
                if chat_result.failed > 0:
                    logger.warning(
                        "Some chat questions failed in workflow",
                        succeeded=chat_result.succeeded,
                        failed=chat_result.failed,
                    )
        except Exception as e:
            errors.append(f"Chat step failed: {e}")
            outputs["chat_succeeded"] = "0"
            outputs["chat_failed"] = str(len(questions))
            logger.error(
                "Workflow chat step failed",
                error=str(e),
            )

        # Step 3: Generate Studio content
        try:
            studio_result = await self._studio_service.generate_content(
                notebook_id=notebook_id,
                content_type=content_type,
            )
            outputs["content_type"] = studio_result.content_type
            outputs["content_title"] = studio_result.title
            outputs["generation_time_seconds"] = str(
                studio_result.generation_time_seconds
            )
            steps_completed += 1
        except Exception as e:
            errors.append(f"Studio content generation failed: {e}")
            logger.error(
                "Workflow studio step failed",
                content_type=content_type,
                error=str(e),
            )

        # Determine overall status
        if steps_completed == steps_total:
            status = "completed"
        elif steps_completed == 0:
            status = "failed"
        else:
            status = "partial"

        logger.info(
            "Research workflow finished",
            notebook_id=notebook_id,
            status=status,
            steps_completed=steps_completed,
            steps_total=steps_total,
            error_count=len(errors),
        )

        return WorkflowResult(
            workflow_name="research",
            status=status,
            steps_completed=steps_completed,
            steps_total=steps_total,
            outputs=outputs,
            errors=errors,
        )


__all__ = [
    "BatchService",
]

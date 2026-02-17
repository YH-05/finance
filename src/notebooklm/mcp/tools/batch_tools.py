"""MCP tools for NotebookLM batch and workflow operations.

This module provides three MCP tools:

- ``notebooklm_batch_add_sources``: Add multiple sources sequentially.
- ``notebooklm_batch_chat``: Send multiple questions sequentially.
- ``notebooklm_workflow_research``: Orchestrate a complete research workflow
  (add sources -> chat questions -> generate studio content).

Each tool retrieves the ``NotebookLMBrowserManager`` from the lifespan
context via ``ctx.lifespan_context["browser_manager"]`` and instantiates
the required services for the operation.

See Also
--------
notebooklm.services.batch : BatchService implementation.
notebooklm.mcp.server : Server setup with lifespan.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context
from mcp.server.fastmcp import FastMCP

from notebooklm.decorators import mcp_tool_handler
from notebooklm.services.batch import BatchService
from notebooklm.services.chat import ChatService
from notebooklm.services.source import SourceService
from notebooklm.services.studio import StudioService
from notebooklm.types import StudioContentType  # noqa: TC001  # runtime: FastMCP schema


def register_batch_tools(mcp: FastMCP) -> None:
    """Register batch operation MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    @mcp_tool_handler("notebooklm_batch_add_sources")
    async def notebooklm_batch_add_sources(
        notebook_id: str,
        sources: list[dict[str, Any]],
        ctx: Context,
    ) -> dict[str, Any]:
        """Add multiple sources sequentially to a NotebookLM notebook.

        Processes each source definition one at a time. Each source
        must contain a ``type`` key (``"text"`` or ``"url"``) and
        type-specific fields. Failures on individual sources do not
        stop the remaining sources from being processed.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        sources : list[dict[str, Any]]
            List of source definitions. Each must have a ``type`` key:
            - ``"text"``: requires ``text`` (str), optional ``title`` (str).
            - ``"url"``: requires ``url`` (str).
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - total: Total number of sources processed.
            - succeeded: Number of successfully added sources.
            - failed: Number of failed source additions.
            - results: Per-item results with status and source info.
        """
        browser_manager = ctx.lifespan_context["browser_manager"]
        source_service = SourceService(browser_manager)
        chat_service = ChatService(browser_manager)
        batch_service = BatchService(
            source_service=source_service,
            chat_service=chat_service,
        )
        result = await batch_service.batch_add_sources(notebook_id, sources)
        return result.model_dump()

    @mcp.tool()
    @mcp_tool_handler("notebooklm_batch_chat")
    async def notebooklm_batch_chat(
        notebook_id: str,
        questions: list[str],
        ctx: Context,
    ) -> dict[str, Any]:
        """Send multiple chat questions sequentially to a NotebookLM notebook.

        Processes each question one at a time. Failures on individual
        questions do not stop the remaining questions from being processed.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        questions : list[str]
            List of questions to ask. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - total: Total number of questions processed.
            - succeeded: Number of successfully answered questions.
            - failed: Number of failed questions.
            - results: Per-item results with question, answer, and status.
        """
        browser_manager = ctx.lifespan_context["browser_manager"]
        source_service = SourceService(browser_manager)
        chat_service = ChatService(browser_manager)
        batch_service = BatchService(
            source_service=source_service,
            chat_service=chat_service,
        )
        result = await batch_service.batch_chat(notebook_id, questions)
        return result.model_dump()

    @mcp.tool()
    @mcp_tool_handler("notebooklm_workflow_research")
    async def notebooklm_workflow_research(
        notebook_id: str,
        sources: list[dict[str, Any]],
        questions: list[str],
        ctx: Context,
        content_type: StudioContentType = "report",
    ) -> dict[str, Any]:
        """Run a complete research workflow on a NotebookLM notebook.

        Orchestrates a 3-step pipeline:
        1. Add sources (text/URL) to the notebook.
        2. Send research questions to the AI chat.
        3. Generate Studio content (report, data table, etc.).

        Each step runs independently; failures in one step do not
        prevent subsequent steps from executing. The ``status`` field
        indicates overall success: ``"completed"`` (all steps passed),
        ``"partial"`` (some steps failed), or ``"failed"`` (all failed).

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        sources : list[dict[str, Any]]
            List of source definitions. Each must have a ``type`` key:
            - ``"text"``: requires ``text`` (str), optional ``title`` (str).
            - ``"url"``: requires ``url`` (str).
        questions : list[str]
            List of research questions to ask. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.
        content_type : StudioContentType
            Type of Studio content to generate. Defaults to ``"report"``.
            Options: ``"report"``, ``"infographic"``, ``"slides"``,
            ``"data_table"``.

        Returns
        -------
        dict
            JSON object containing:
            - workflow_name: Always ``"research"``.
            - status: ``"completed"``, ``"partial"``, or ``"failed"``.
            - steps_completed: Number of steps completed (0-3).
            - steps_total: Always 3.
            - outputs: Key-value pairs including notebook_id, source/chat
              counts, content metadata.
            - errors: List of error messages from failed steps.
        """
        browser_manager = ctx.lifespan_context["browser_manager"]
        source_service = SourceService(browser_manager)
        chat_service = ChatService(browser_manager)
        studio_service = StudioService(browser_manager)
        batch_service = BatchService(
            source_service=source_service,
            chat_service=chat_service,
            studio_service=studio_service,
        )
        result = await batch_service.workflow_research(
            notebook_id=notebook_id,
            sources=sources,
            questions=questions,
            content_type=content_type,
        )
        return result.model_dump()

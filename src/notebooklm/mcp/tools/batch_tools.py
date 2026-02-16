"""MCP tools for NotebookLM batch operations.

This module provides two MCP tools for batch operations:

- ``notebooklm_batch_add_sources``: Add multiple sources sequentially.
- ``notebooklm_batch_chat``: Send multiple questions sequentially.

Each tool retrieves the ``NotebookLMBrowserManager`` from the lifespan
context via ``ctx.lifespan_context["browser_manager"]`` and instantiates
``SourceService``, ``ChatService``, and ``BatchService`` for the operation.

See Also
--------
notebooklm.services.batch : BatchService implementation.
notebooklm.mcp.server : Server setup with lifespan.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context
from mcp.server.fastmcp import FastMCP

from notebooklm.errors import NotebookLMError
from notebooklm.services.batch import BatchService
from notebooklm.services.chat import ChatService
from notebooklm.services.source import SourceService
from utils_core.logging import get_logger

logger = get_logger(__name__)


def register_batch_tools(mcp: FastMCP) -> None:
    """Register batch operation MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
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
        logger.info(
            "MCP tool called: notebooklm_batch_add_sources",
            notebook_id=notebook_id,
            source_count=len(sources),
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            source_service = SourceService(browser_manager)
            chat_service = ChatService(browser_manager)
            batch_service = BatchService(
                source_service=source_service,
                chat_service=chat_service,
            )

            result = await batch_service.batch_add_sources(notebook_id, sources)

            result_dict = result.model_dump()

            logger.info(
                "notebooklm_batch_add_sources completed",
                notebook_id=notebook_id,
                total=result.total,
                succeeded=result.succeeded,
                failed=result.failed,
            )
            return result_dict

        except ValueError as e:
            logger.error(
                "notebooklm_batch_add_sources failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_batch_add_sources failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
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
        logger.info(
            "MCP tool called: notebooklm_batch_chat",
            notebook_id=notebook_id,
            question_count=len(questions),
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            source_service = SourceService(browser_manager)
            chat_service = ChatService(browser_manager)
            batch_service = BatchService(
                source_service=source_service,
                chat_service=chat_service,
            )

            result = await batch_service.batch_chat(notebook_id, questions)

            result_dict = result.model_dump()

            logger.info(
                "notebooklm_batch_chat completed",
                notebook_id=notebook_id,
                total=result.total,
                succeeded=result.succeeded,
                failed=result.failed,
            )
            return result_dict

        except ValueError as e:
            logger.error(
                "notebooklm_batch_chat failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_batch_chat failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

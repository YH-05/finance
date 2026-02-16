"""MCP tools for NotebookLM notebook management.

This module provides three MCP tools for notebook operations:

- ``notebooklm_create_notebook``: Create a new notebook.
- ``notebooklm_list_notebooks``: List all notebooks.
- ``notebooklm_get_notebook_summary``: Get AI-generated summary.

Each tool retrieves the ``NotebookLMBrowserManager`` from the lifespan
context via ``ctx.lifespan_context["browser_manager"]`` and instantiates
a ``NotebookService`` for the operation.

See Also
--------
notebooklm.services.notebook : NotebookService implementation.
notebooklm.mcp.server : Server setup with lifespan.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context
from mcp.server.fastmcp import FastMCP

from notebooklm.errors import NotebookLMError
from notebooklm.services.notebook import NotebookService
from utils_core.logging import get_logger

logger = get_logger(__name__)


def register_notebook_tools(mcp: FastMCP) -> None:
    """Register notebook management MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    async def notebooklm_create_notebook(
        title: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Create a new NotebookLM notebook.

        Creates a new notebook with the given title by navigating to
        the NotebookLM home page and clicking the create button.

        Parameters
        ----------
        title : str
            Display title for the new notebook. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: Unique identifier for the created notebook.
            - title: Display title of the notebook.
            - source_count: Number of sources (always 0 for new notebooks).
        """
        logger.info("MCP tool called: notebooklm_create_notebook", title=title)

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = NotebookService(browser_manager)
            notebook = await service.create_notebook(title)

            result = notebook.model_dump()

            logger.info(
                "notebooklm_create_notebook completed",
                notebook_id=notebook.notebook_id,
                title=title,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_create_notebook failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_create_notebook failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_list_notebooks(
        ctx: Context,
    ) -> dict[str, Any]:
        """List all NotebookLM notebooks.

        Navigates to the NotebookLM home page and scrapes the
        notebook list to extract metadata for each notebook.

        Parameters
        ----------
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - notebooks: List of notebook objects with notebook_id, title,
              updated_at, and source_count.
            - total: Total number of notebooks found.
        """
        logger.info("MCP tool called: notebooklm_list_notebooks")

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = NotebookService(browser_manager)
            notebooks = await service.list_notebooks()

            result = {
                "notebooks": [nb.model_dump() for nb in notebooks],
                "total": len(notebooks),
            }

            logger.info(
                "notebooklm_list_notebooks completed",
                total=len(notebooks),
            )
            return result

        except NotebookLMError as e:
            logger.error(
                "notebooklm_list_notebooks failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_get_notebook_summary(
        notebook_id: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Get the AI-generated summary of a notebook.

        Navigates to the notebook page and extracts the auto-generated
        summary text and suggested questions.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: UUID of the notebook.
            - summary_text: AI-generated overview of the notebook contents.
            - suggested_questions: List of AI-generated follow-up questions.
        """
        logger.info(
            "MCP tool called: notebooklm_get_notebook_summary",
            notebook_id=notebook_id,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = NotebookService(browser_manager)
            summary = await service.get_notebook_summary(notebook_id)

            result = summary.model_dump()

            logger.info(
                "notebooklm_get_notebook_summary completed",
                notebook_id=notebook_id,
                summary_length=len(summary.summary_text),
                question_count=len(summary.suggested_questions),
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_get_notebook_summary failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_get_notebook_summary failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

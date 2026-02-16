"""MCP tools for NotebookLM source management (Phase 1).

This module provides two MCP tools for source operations:

- ``notebooklm_add_text_source``: Add pasted text as a source.
- ``notebooklm_list_sources``: List all sources in a notebook.

Each tool retrieves the ``NotebookLMBrowserManager`` from the lifespan
context via ``ctx.lifespan_context["browser_manager"]`` and instantiates
a ``SourceService`` for the operation.

See Also
--------
notebooklm.services.source : SourceService implementation.
notebooklm.mcp.server : Server setup with lifespan.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context
from mcp.server.fastmcp import FastMCP

from notebooklm.errors import NotebookLMError
from notebooklm.services.source import SourceService
from utils_core.logging import get_logger

logger = get_logger(__name__)


def register_source_tools(mcp: FastMCP) -> None:
    """Register source management MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    async def notebooklm_add_text_source(
        notebook_id: str,
        text: str,
        ctx: Context,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Add pasted text as a source to a notebook.

        Navigates to the notebook page, opens the source addition dialog,
        selects the "Copied text" option, pastes the text, and submits.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        text : str
            Text content to add as a source. Must not be empty.
        title : str | None
            Optional display title for the source. Defaults to "Pasted text".
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - source_id: Identifier for the newly added source.
            - title: Display title of the source.
            - source_type: Type of the source (always "text").
        """
        logger.info(
            "MCP tool called: notebooklm_add_text_source",
            notebook_id=notebook_id,
            title=title,
            text_length=len(text),
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            source = await service.add_text_source(
                notebook_id=notebook_id,
                text=text,
                title=title,
            )

            result = source.model_dump()

            logger.info(
                "notebooklm_add_text_source completed",
                notebook_id=notebook_id,
                source_id=source.source_id,
                title=source.title,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_add_text_source failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_add_text_source failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_list_sources(
        notebook_id: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """List all sources in a NotebookLM notebook.

        Navigates to the notebook page and scrapes the source list
        panel to extract metadata for each source.

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
            - sources: List of source objects with source_id, title,
              source_type, and added_at.
            - total: Total number of sources found.
            - notebook_id: The notebook ID queried.
        """
        logger.info(
            "MCP tool called: notebooklm_list_sources",
            notebook_id=notebook_id,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            sources = await service.list_sources(notebook_id)

            result = {
                "sources": [src.model_dump() for src in sources],
                "total": len(sources),
                "notebook_id": notebook_id,
            }

            logger.info(
                "notebooklm_list_sources completed",
                notebook_id=notebook_id,
                total=len(sources),
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_list_sources failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_list_sources failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

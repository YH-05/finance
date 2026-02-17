"""MCP tools for NotebookLM notebook management.

This module provides four MCP tools for notebook operations:

- ``notebooklm_create_notebook``: Create a new notebook.
- ``notebooklm_list_notebooks``: List all notebooks.
- ``notebooklm_get_notebook_summary``: Get AI-generated summary.
- ``notebooklm_delete_notebook``: Delete a notebook.

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

from notebooklm.decorators import mcp_tool_handler
from notebooklm.services.notebook import NotebookService


def register_notebook_tools(mcp: FastMCP) -> None:
    """Register notebook management MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    @mcp_tool_handler("notebooklm_create_notebook")
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
        browser_manager = ctx.lifespan_context["browser_manager"]
        service = NotebookService(browser_manager)
        notebook = await service.create_notebook(title)
        return notebook.model_dump()

    @mcp.tool()
    @mcp_tool_handler("notebooklm_list_notebooks")
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
        browser_manager = ctx.lifespan_context["browser_manager"]
        service = NotebookService(browser_manager)
        notebooks = await service.list_notebooks()
        return {
            "notebooks": [nb.model_dump() for nb in notebooks],
            "total": len(notebooks),
        }

    @mcp.tool()
    @mcp_tool_handler("notebooklm_get_notebook_summary")
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
        browser_manager = ctx.lifespan_context["browser_manager"]
        service = NotebookService(browser_manager)
        summary = await service.get_notebook_summary(notebook_id)
        return summary.model_dump()

    @mcp.tool()
    @mcp_tool_handler("notebooklm_delete_notebook")
    async def notebooklm_delete_notebook(
        notebook_id: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Delete a NotebookLM notebook.

        Navigates to the NotebookLM home page, locates the notebook,
        opens the settings menu, and clicks delete with confirmation.

        Parameters
        ----------
        notebook_id : str
            UUID of the notebook to delete. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - deleted: Whether the notebook was deleted (bool).
            - notebook_id: UUID of the deleted notebook.
        """
        browser_manager = ctx.lifespan_context["browser_manager"]
        service = NotebookService(browser_manager)
        deleted = await service.delete_notebook(notebook_id)
        return {
            "deleted": deleted,
            "notebook_id": notebook_id,
        }

"""MCP tools for NotebookLM source management.

This module provides MCP tools for source operations:

Phase 1:
- ``notebooklm_add_text_source``: Add pasted text as a source.
- ``notebooklm_list_sources``: List all sources in a notebook.

Phase 2:
- ``notebooklm_add_url_source``: Add a URL/website as a source.
- ``notebooklm_add_file_source``: Upload a file as a source.
- ``notebooklm_get_source_details``: Get detailed source information.
- ``notebooklm_delete_source``: Delete a source.
- ``notebooklm_rename_source``: Rename a source.
- ``notebooklm_toggle_source_selection``: Select/deselect a source.
- ``notebooklm_web_research``: Run Fast or Deep web research.

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

    # ------------------------------------------------------------------
    # Phase 2 tools
    # ------------------------------------------------------------------

    @mcp.tool()
    async def notebooklm_add_url_source(
        notebook_id: str,
        url: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Add a URL/website as a source to a notebook.

        Navigates to the notebook page, opens the source addition dialog,
        selects the "Website" option, pastes the URL, and submits.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        url : str
            URL of the website to add. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing source_id, title, and source_type.
        """
        logger.info(
            "MCP tool called: notebooklm_add_url_source",
            notebook_id=notebook_id,
            url=url,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            source = await service.add_url_source(
                notebook_id=notebook_id,
                url=url,
            )

            result = source.model_dump()

            logger.info(
                "notebooklm_add_url_source completed",
                notebook_id=notebook_id,
                source_id=source.source_id,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_add_url_source failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_add_url_source failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_add_file_source(
        notebook_id: str,
        file_path: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Upload a file as a source to a notebook.

        Supports PDF, TXT, and other document formats.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        file_path : str
            Local file path to upload. Must not be empty
            and file must exist.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing source_id, title, and source_type.
        """
        logger.info(
            "MCP tool called: notebooklm_add_file_source",
            notebook_id=notebook_id,
            file_path=file_path,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            source = await service.add_file_source(
                notebook_id=notebook_id,
                file_path=file_path,
            )

            result = source.model_dump()

            logger.info(
                "notebooklm_add_file_source completed",
                notebook_id=notebook_id,
                source_id=source.source_id,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_add_file_source failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except FileNotFoundError as e:
            logger.error(
                "notebooklm_add_file_source failed: file not found",
                error=str(e),
            )
            return {"error": str(e), "error_type": "FileNotFoundError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_add_file_source failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_get_source_details(
        notebook_id: str,
        source_index: int,
        ctx: Context,
    ) -> dict[str, Any]:
        """Get detailed information about a specific source.

        Opens the source detail panel and extracts metadata
        including content summary and URL.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        source_index : int
            Zero-based index of the source in the source list.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing source_id, title, source_type,
            source_url, and content_summary.
        """
        logger.info(
            "MCP tool called: notebooklm_get_source_details",
            notebook_id=notebook_id,
            source_index=source_index,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            details = await service.get_source_details(
                notebook_id=notebook_id,
                source_index=source_index,
            )

            result = details.model_dump()

            logger.info(
                "notebooklm_get_source_details completed",
                notebook_id=notebook_id,
                source_id=details.source_id,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_get_source_details failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_get_source_details failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_delete_source(
        notebook_id: str,
        source_index: int,
        ctx: Context,
    ) -> dict[str, Any]:
        """Delete a source from a notebook.

        Opens the source context menu and clicks delete.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        source_index : int
            Zero-based index of the source to delete.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing deleted (bool) and notebook_id.
        """
        logger.info(
            "MCP tool called: notebooklm_delete_source",
            notebook_id=notebook_id,
            source_index=source_index,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            deleted = await service.delete_source(
                notebook_id=notebook_id,
                source_index=source_index,
            )

            result = {
                "deleted": deleted,
                "notebook_id": notebook_id,
                "source_index": source_index,
            }

            logger.info(
                "notebooklm_delete_source completed",
                notebook_id=notebook_id,
                source_index=source_index,
                deleted=deleted,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_delete_source failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_delete_source failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_rename_source(
        notebook_id: str,
        source_index: int,
        new_name: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Rename a source in a notebook.

        Opens the source context menu, clicks rename, and types
        the new name.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        source_index : int
            Zero-based index of the source to rename.
        new_name : str
            New name for the source. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing source_id, title, and source_type.
        """
        logger.info(
            "MCP tool called: notebooklm_rename_source",
            notebook_id=notebook_id,
            source_index=source_index,
            new_name=new_name,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            source = await service.rename_source(
                notebook_id=notebook_id,
                source_index=source_index,
                new_name=new_name,
            )

            result = source.model_dump()

            logger.info(
                "notebooklm_rename_source completed",
                notebook_id=notebook_id,
                source_index=source_index,
                new_name=new_name,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_rename_source failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_rename_source failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_toggle_source_selection(
        notebook_id: str,
        ctx: Context,
        source_index: int | None = None,
        select_all: bool = False,
    ) -> dict[str, Any]:
        """Select or deselect a source (or all sources) in a notebook.

        When select_all is True, toggles the "Select all" checkbox.
        When source_index is provided, toggles that specific source.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.
        source_index : int | None
            Zero-based index of the source to toggle.
            Required if select_all is False.
        select_all : bool
            If True, toggles the select-all checkbox.

        Returns
        -------
        dict
            JSON object containing toggled (bool), notebook_id,
            source_index, and select_all.
        """
        logger.info(
            "MCP tool called: notebooklm_toggle_source_selection",
            notebook_id=notebook_id,
            source_index=source_index,
            select_all=select_all,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            toggled = await service.toggle_source_selection(
                notebook_id=notebook_id,
                source_index=source_index,
                select_all=select_all,
            )

            result = {
                "toggled": toggled,
                "notebook_id": notebook_id,
                "source_index": source_index,
                "select_all": select_all,
            }

            logger.info(
                "notebooklm_toggle_source_selection completed",
                notebook_id=notebook_id,
                toggled=toggled,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_toggle_source_selection failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_toggle_source_selection failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_web_research(
        notebook_id: str,
        query: str,
        ctx: Context,
        mode: str = "fast",
    ) -> dict[str, Any]:
        """Run web research to discover and add sources.

        Runs Fast Research (quick results) or Deep Research
        (comprehensive, multi-step research) to find relevant
        web sources for the notebook.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        query : str
            Search query for source discovery. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.
        mode : str
            Research mode: "fast" or "deep". Defaults to "fast".

        Returns
        -------
        dict
            JSON object containing results list, total count,
            notebook_id, query, and mode.
        """
        logger.info(
            "MCP tool called: notebooklm_web_research",
            notebook_id=notebook_id,
            query=query,
            mode=mode,
        )

        try:
            # Validate mode
            if mode not in ("fast", "deep"):
                return {
                    "error": f"Invalid mode: {mode}. Must be 'fast' or 'deep'.",
                    "error_type": "ValueError",
                }

            browser_manager = ctx.lifespan_context["browser_manager"]
            service = SourceService(browser_manager)
            results = await service.web_research(
                notebook_id=notebook_id,
                query=query,
                mode=mode,  # type: ignore[arg-type]
            )

            result = {
                "results": [r.model_dump() for r in results],
                "total": len(results),
                "notebook_id": notebook_id,
                "query": query,
                "mode": mode,
            }

            logger.info(
                "notebooklm_web_research completed",
                notebook_id=notebook_id,
                query=query,
                mode=mode,
                total=len(results),
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_web_research failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_web_research failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

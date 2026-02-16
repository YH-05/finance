"""MCP tools for NotebookLM Studio content generation.

This module provides an MCP tool for Studio content generation:

- ``notebooklm_generate_studio_content``: Generate Studio content
  (report, infographic, slides, data_table).

The tool retrieves the ``NotebookLMBrowserManager`` from the lifespan
context via ``ctx.lifespan_context["browser_manager"]`` and instantiates
a ``StudioService`` for the operation.

See Also
--------
notebooklm.services.studio : StudioService implementation.
notebooklm.mcp.server : Server setup with lifespan.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context
from mcp.server.fastmcp import FastMCP

from notebooklm.errors import NotebookLMError
from notebooklm.services.studio import StudioService
from notebooklm.types import (  # noqa: TC001  # runtime: FastMCP schema
    ReportFormat,
    StudioContentType,
)
from utils_core.logging import get_logger

logger = get_logger(__name__)


def register_studio_tools(mcp: FastMCP) -> None:
    """Register Studio content generation MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    async def notebooklm_generate_studio_content(
        notebook_id: str,
        content_type: StudioContentType,
        ctx: Context,
        report_format: ReportFormat | None = None,
    ) -> dict[str, Any]:
        """Generate Studio content for a NotebookLM notebook.

        Generates one of 4 types of Studio content: report, infographic,
        slides, or data_table. For reports, an optional format can be
        specified (briefing_doc, study_guide, blog_post).

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        content_type : StudioContentType
            Type of Studio content to generate. One of:
            ``"report"``, ``"infographic"``, ``"slides"``, ``"data_table"``.
        ctx : Context
            MCP context providing access to lifespan resources.
        report_format : ReportFormat | None
            Optional report format. Only applicable when ``content_type``
            is ``"report"``. One of: ``"custom"``, ``"briefing_doc"``,
            ``"study_guide"``, ``"blog_post"``. Defaults to None.

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: UUID of the notebook.
            - content_type: Type of content generated.
            - title: Title of the generated content.
            - text_content: Extracted text (for reports, None for others).
            - table_data: Structured table data (for data_table, None for others).
            - generation_time_seconds: Time taken for generation.
        """
        logger.info(
            "MCP tool called: notebooklm_generate_studio_content",
            notebook_id=notebook_id,
            content_type=content_type,
            report_format=report_format,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = StudioService(browser_manager)
            result = await service.generate_content(
                notebook_id,
                content_type,
                report_format=report_format,
            )

            result_dict = result.model_dump()

            logger.info(
                "notebooklm_generate_studio_content completed",
                notebook_id=notebook_id,
                content_type=content_type,
                generation_time_seconds=result.generation_time_seconds,
            )
            return result_dict

        except ValueError as e:
            logger.error(
                "notebooklm_generate_studio_content failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_generate_studio_content failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

"""MCP tools for NotebookLM Audio Overview operations.

This module provides an MCP tool for audio generation:

- ``notebooklm_generate_audio_overview``: Generate Audio Overview (podcast).

The tool retrieves the ``NotebookLMBrowserManager`` from the lifespan
context via ``ctx.lifespan_context["browser_manager"]`` and instantiates
an ``AudioService`` for the operation. Progress is reported via
``ctx.report_progress()`` during the polling phase.

See Also
--------
notebooklm.services.audio : AudioService implementation.
notebooklm.mcp.server : Server setup with lifespan.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context
from mcp.server.fastmcp import FastMCP

from notebooklm.errors import NotebookLMError
from notebooklm.services.audio import AudioService
from utils_core.logging import get_logger

logger = get_logger(__name__)


def register_audio_tools(mcp: FastMCP) -> None:
    """Register audio management MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    async def notebooklm_generate_audio_overview(
        notebook_id: str,
        ctx: Context,
        customize_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Generate an Audio Overview (podcast) for a NotebookLM notebook.

        Initiates Audio Overview generation, which creates a podcast-style
        audio summary of the notebook's sources. Generation typically takes
        1-10 minutes depending on content length.

        Progress is reported via ctx.report_progress() during polling.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.
        customize_prompt : str | None
            Optional prompt to customize the audio generation.
            For example: "Focus on technical details" or
            "Use a casual conversational tone".

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: UUID of the notebook.
            - status: Generation status ("completed", "in_progress", "failed").
            - audio_url: URL to the generated audio (if available).
            - duration_seconds: Duration of the audio (if available).
            - generation_time_seconds: Time taken for generation.
        """
        logger.info(
            "MCP tool called: notebooklm_generate_audio_overview",
            notebook_id=notebook_id,
            has_customization=customize_prompt is not None,
        )

        try:
            await ctx.report_progress(
                progress=0.0,
                total=1.0,
            )

            browser_manager = ctx.lifespan_context["browser_manager"]
            service = AudioService(browser_manager)

            await ctx.report_progress(
                progress=0.1,
                total=1.0,
            )

            result = await service.generate_audio_overview(
                notebook_id,
                customize_prompt=customize_prompt,
            )

            await ctx.report_progress(
                progress=1.0,
                total=1.0,
            )

            result_dict = result.model_dump()

            logger.info(
                "notebooklm_generate_audio_overview completed",
                notebook_id=notebook_id,
                status=result.status,
                generation_time_seconds=result.generation_time_seconds,
            )
            return result_dict

        except ValueError as e:
            logger.error(
                "notebooklm_generate_audio_overview failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_generate_audio_overview failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

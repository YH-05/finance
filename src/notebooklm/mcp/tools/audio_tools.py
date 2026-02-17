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

from notebooklm.decorators import mcp_tool_handler
from notebooklm.services.audio import AudioService


def register_audio_tools(mcp: FastMCP) -> None:
    """Register audio management MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    @mcp_tool_handler("notebooklm_generate_audio_overview")
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
        browser_manager = ctx.lifespan_context["browser_manager"]
        service = AudioService(browser_manager)
        result = await service.generate_audio_overview(
            notebook_id,
            customize_prompt=customize_prompt,
        )
        return result.model_dump()

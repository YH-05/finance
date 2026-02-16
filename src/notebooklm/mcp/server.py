"""FastMCP server for NotebookLM browser automation.

This module provides an MCP (Model Context Protocol) server that exposes
NotebookLM notebook and source management operations as MCP tools
for Claude Code integration.

The server uses a lifespan context manager to manage the
``NotebookLMBrowserManager`` lifecycle, ensuring the browser is
initialized on startup and properly closed on shutdown.

Phase 1 Tools (5 total)
-----------------------
Notebook tools:
- ``notebooklm_create_notebook``: Create a new notebook.
- ``notebooklm_list_notebooks``: List all notebooks.
- ``notebooklm_get_notebook_summary``: Get AI-generated summary.

Source tools:
- ``notebooklm_add_text_source``: Add pasted text as a source.
- ``notebooklm_list_sources``: List all sources in a notebook.

Phase 2 Chat Tools (5 total)
-----------------------------
- ``notebooklm_chat``: Send a question and get an AI response.
- ``notebooklm_get_chat_history``: Get chat conversation history.
- ``notebooklm_clear_chat_history``: Clear chat history.
- ``notebooklm_configure_chat``: Configure chat settings.
- ``notebooklm_save_chat_to_note``: Send a question and save response to note.

Phase 3 Audio Tools (1 total)
------------------------------
- ``notebooklm_generate_audio_overview``: Generate Audio Overview (podcast).

Batch & Workflow Tools (3 total)
---------------------------------
- ``notebooklm_batch_add_sources``: Add multiple sources sequentially.
- ``notebooklm_batch_chat``: Send multiple questions sequentially.
- ``notebooklm_workflow_research``: Orchestrate a complete research workflow.

Usage
-----
Run as a command::

    $ notebooklm-mcp

Or add to Claude Code::

    $ claude mcp add notebooklm -- uvx notebooklm-mcp

Or configure in .mcp.json::

    {
      "mcpServers": {
        "notebooklm": {
          "command": "uvx",
          "args": ["notebooklm-mcp"]
        }
      }
    }

See Also
--------
rss.mcp.server : Similar FastMCP server pattern.
notebooklm.browser.manager : Browser lifecycle management.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = get_logger(__name__)


@asynccontextmanager
async def notebooklm_lifespan(server: Any) -> AsyncIterator[dict[str, Any]]:
    """Manage the NotebookLMBrowserManager lifecycle.

    Initializes the browser manager on server startup and ensures
    proper cleanup on shutdown.

    Parameters
    ----------
    server : Any
        The FastMCP server instance (unused but required by lifespan protocol).

    Yields
    ------
    dict[str, Any]
        Context dictionary containing:
        - ``browser_manager``: The initialized ``NotebookLMBrowserManager``.
    """
    from notebooklm.browser.manager import NotebookLMBrowserManager

    logger.info("Starting NotebookLM MCP server lifespan")

    manager = NotebookLMBrowserManager()
    try:
        await manager.__aenter__()
        logger.info(
            "BrowserManager initialized",
            headless=manager.headless,
            session_restored=manager.has_session(),
        )
        yield {"browser_manager": manager}
    finally:
        await manager.close()
        logger.info("BrowserManager closed")


# Create MCP server with lifespan
mcp = FastMCP(
    name="NotebookLM",
    instructions=(
        "MCP server for Google NotebookLM browser automation. "
        "Provides notebook management, source management, and AI-powered "
        "content operations via Playwright browser automation."
    ),
    lifespan=notebooklm_lifespan,
)

# Register Phase 1 tools
# Register Phase 2 tools
# Register Phase 3 tools
from notebooklm.mcp.tools.audio_tools import register_audio_tools  # noqa: E402
from notebooklm.mcp.tools.batch_tools import register_batch_tools  # noqa: E402
from notebooklm.mcp.tools.chat_tools import register_chat_tools  # noqa: E402
from notebooklm.mcp.tools.notebook_tools import register_notebook_tools  # noqa: E402
from notebooklm.mcp.tools.source_tools import register_source_tools  # noqa: E402

register_notebook_tools(mcp)
register_source_tools(mcp)
register_chat_tools(mcp)
register_audio_tools(mcp)
register_batch_tools(mcp)


def serve() -> None:
    """Run the MCP server with stdio transport.

    This function starts the MCP server using stdio transport,
    which is the standard way to communicate with Claude Code.
    """
    logger.info("Starting NotebookLM MCP server")
    mcp.run(transport="stdio")


def main() -> None:
    """Entry point for the notebooklm-mcp command.

    This function is called when running ``notebooklm-mcp``
    from the command line.
    """
    serve()


if __name__ == "__main__":
    main()

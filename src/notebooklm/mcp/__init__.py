"""MCP (Model Context Protocol) server module for NotebookLM.

This module provides the FastMCP server and tool implementations
for exposing NotebookLM operations as MCP tools for Claude Code integration.

Phase 1 Tools
-------------
- ``notebooklm_create_notebook``: Create a new notebook.
- ``notebooklm_list_notebooks``: List all notebooks.
- ``notebooklm_get_notebook_summary``: Get AI-generated summary.
- ``notebooklm_add_text_source``: Add pasted text as a source.
- ``notebooklm_list_sources``: List all sources in a notebook.

See Also
--------
notebooklm.mcp.server : FastMCP server implementation.
notebooklm.mcp.tools : Tool registration modules.
"""

from notebooklm.mcp.server import main, mcp, serve

__all__ = [
    "main",
    "mcp",
    "serve",
]

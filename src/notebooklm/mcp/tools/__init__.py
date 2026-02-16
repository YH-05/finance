"""MCP tool modules for NotebookLM operations.

This package contains tool registration functions organized by domain:

- ``notebook_tools``: Notebook CRUD operations (create, list, get summary).
- ``source_tools``: Source management operations (add text, list sources).
- ``chat_tools``: AI chat operations (chat, history, settings, save to note).
- ``audio_tools``: Audio Overview generation operations.

Each module provides a ``register_*_tools(mcp)`` function that registers
tools on the given FastMCP server instance using ``@mcp.tool()`` decorators.

See Also
--------
notebooklm.mcp.server : FastMCP server that imports and registers these tools.
"""

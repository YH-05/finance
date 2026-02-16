"""MCP tool modules for NotebookLM operations.

This package contains tool registration functions organized by domain:

- ``notebook_tools``: Notebook CRUD operations (create, list, get summary).
- ``source_tools``: Source management operations (add text, list sources).
- ``chat_tools``: AI chat operations (chat, history, settings, save to note).
- ``audio_tools``: Audio Overview generation operations.
- ``studio_tools``: Studio content generation operations (report, infographic,
  slides, data_table).
- ``note_tools``: Note CRUD operations (create, list, get, delete).
- ``batch_tools``: Batch and workflow operations (batch add sources,
  batch chat, workflow research).

Each module provides a ``register_*_tools(mcp)`` function that registers
tools on the given FastMCP server instance using ``@mcp.tool()`` decorators.

See Also
--------
notebooklm.mcp.server : FastMCP server that imports and registers these tools.
"""

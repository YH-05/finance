"""MCP server module for RSS feed management.

This module provides an MCP (Model Context Protocol) server that allows
AI agents like Claude Code to interact with RSS feed management functionality.
"""

from .server import main, serve

__all__ = ["main", "serve"]

"""MCP server for RSS feed management.

This module provides an MCP (Model Context Protocol) server that allows
AI agents like Claude Code to interact with RSS feed management functionality.

The server exposes 7 tools:
- rss_list_feeds: List all registered feeds
- rss_get_items: Get items from a specific feed
- rss_search_items: Search items by keyword
- rss_add_feed: Add a new feed
- rss_update_feed: Update feed information
- rss_remove_feed: Remove a feed
- rss_fetch_feed: Fetch items from a feed immediately

Usage
-----
Run as a command:
    $ rss-mcp

Or add to Claude Code:
    $ claude mcp add rss -- uvx rss-mcp

Or configure in .mcp.json:
    {
      "mcpServers": {
        "rss": {
          "command": "uvx",
          "args": ["rss-mcp"],
          "env": {
            "RSS_DATA_DIR": "./data/raw/rss"
          }
        }
      }
    }
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP  # type: ignore[import-untyped]

from ..exceptions import (
    FeedAlreadyExistsError,
    FeedFetchError,
    FeedNotFoundError,
    FeedParseError,
    InvalidURLError,
    RSSError,
)
from ..services.feed_fetcher import FeedFetcher
from ..services.feed_manager import FeedManager
from ..services.feed_reader import FeedReader
from ..types import FetchInterval


def _get_logger() -> Any:
    """Get logger with lazy initialization to avoid circular imports."""
    try:
        from ..utils.logging_config import get_logger

        return get_logger(__name__, module="mcp_server")
    except ImportError:
        import logging

        return logging.getLogger(__name__)


logger: Any = _get_logger()

# Default data directory
DEFAULT_DATA_DIR = Path("data/raw/rss")

# Create MCP server
mcp = FastMCP(
    name="RSS Feed Manager",
    instructions="MCP server for managing RSS feeds - list, add, update, remove, fetch feeds and search items",
)


def _get_data_dir() -> Path:
    """Get the RSS data directory, creating it if necessary.

    Returns
    -------
    Path
        The RSS data directory path
    """
    data_dir = Path(os.environ.get("RSS_DATA_DIR", str(DEFAULT_DATA_DIR)))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _feed_to_dict(feed: Any) -> dict[str, Any]:
    """Convert a Feed dataclass to a dictionary for JSON serialization.

    Parameters
    ----------
    feed : Feed
        The feed object to convert

    Returns
    -------
    dict[str, Any]
        Dictionary representation of the feed
    """
    return {
        "feed_id": feed.feed_id,
        "url": feed.url,
        "title": feed.title,
        "category": feed.category,
        "fetch_interval": (
            feed.fetch_interval.value
            if hasattr(feed.fetch_interval, "value")
            else feed.fetch_interval
        ),
        "created_at": feed.created_at,
        "updated_at": feed.updated_at,
        "last_fetched": feed.last_fetched,
        "last_status": (
            feed.last_status.value
            if hasattr(feed.last_status, "value")
            else feed.last_status
        ),
        "enabled": feed.enabled,
    }


def _item_to_dict(item: Any) -> dict[str, Any]:
    """Convert a FeedItem dataclass to a dictionary for JSON serialization.

    Parameters
    ----------
    item : FeedItem
        The feed item object to convert

    Returns
    -------
    dict[str, Any]
        Dictionary representation of the feed item
    """
    return {
        "item_id": item.item_id,
        "title": item.title,
        "link": item.link,
        "published": item.published,
        "summary": item.summary,
        "content": item.content,
        "author": item.author,
        "fetched_at": item.fetched_at,
    }


def _parse_fetch_interval(interval_str: str) -> FetchInterval:
    """Parse a fetch interval string to FetchInterval enum.

    Parameters
    ----------
    interval_str : str
        Interval string: "daily", "weekly", or "manual"

    Returns
    -------
    FetchInterval
        Corresponding FetchInterval enum value
    """
    interval_map = {
        "daily": FetchInterval.DAILY,
        "weekly": FetchInterval.WEEKLY,
        "manual": FetchInterval.MANUAL,
    }
    return interval_map.get(interval_str.lower(), FetchInterval.DAILY)


@mcp.tool()
def rss_list_feeds(
    category: str | None = None,
    enabled_only: bool = False,
) -> dict[str, Any]:
    """List all registered RSS feeds.

    Parameters
    ----------
    category : str | None
        Filter feeds by category (optional)
    enabled_only : bool
        If True, only return enabled feeds (default: False)

    Returns
    -------
    dict
        JSON object containing:
        - feeds: List of feed objects
        - total: Total number of feeds returned
    """
    logger.info(
        "MCP tool called: rss_list_feeds",
        category=category,
        enabled_only=enabled_only,
    )

    try:
        data_dir = _get_data_dir()
        manager = FeedManager(data_dir)
        feeds = manager.list_feeds(category=category, enabled_only=enabled_only)

        result = {
            "feeds": [_feed_to_dict(feed) for feed in feeds],
            "total": len(feeds),
        }

        logger.info("rss_list_feeds completed", total=len(feeds))
        return result

    except RSSError as e:
        logger.error("rss_list_feeds failed", error=str(e))
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def rss_get_items(
    feed_id: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    """Get items from RSS feeds.

    Parameters
    ----------
    feed_id : str | None
        Feed ID to get items from (optional, if None returns items from all feeds)
    limit : int
        Maximum number of items to return (default: 10)
    offset : int
        Number of items to skip for pagination (default: 0)

    Returns
    -------
    dict
        JSON object containing:
        - items: List of feed item objects
        - total: Total number of items returned
    """
    logger.info(
        "MCP tool called: rss_get_items",
        feed_id=feed_id,
        limit=limit,
        offset=offset,
    )

    try:
        data_dir = _get_data_dir()
        reader = FeedReader(data_dir)
        items = reader.get_items(feed_id=feed_id, limit=limit, offset=offset)

        result = {
            "items": [_item_to_dict(item) for item in items],
            "total": len(items),
        }

        logger.info("rss_get_items completed", total=len(items))
        return result

    except RSSError as e:
        logger.error("rss_get_items failed", error=str(e))
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def rss_search_items(
    query: str,
    category: str | None = None,
    fields: list[str] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search feed items by keyword.

    Performs case-insensitive partial matching on specified fields.

    Parameters
    ----------
    query : str
        Search query string
    category : str | None
        Filter by feed category (optional)
    fields : list[str] | None
        Fields to search in (optional, defaults to ["title", "summary", "content"])
    limit : int
        Maximum number of results to return (default: 50)

    Returns
    -------
    dict
        JSON object containing:
        - items: List of matching feed item objects
        - total: Total number of matches found
        - query: The search query used
    """
    logger.info(
        "MCP tool called: rss_search_items",
        query=query,
        category=category,
        fields=fields,
        limit=limit,
    )

    try:
        data_dir = _get_data_dir()
        reader = FeedReader(data_dir)
        items = reader.search_items(
            query=query,
            category=category,
            fields=fields,
            limit=limit,
        )

        result = {
            "items": [_item_to_dict(item) for item in items],
            "total": len(items),
            "query": query,
        }

        logger.info("rss_search_items completed", total=len(items), query=query)
        return result

    except RSSError as e:
        logger.error("rss_search_items failed", error=str(e))
        return {"error": str(e), "error_type": type(e).__name__}


@mcp.tool()
def rss_add_feed(
    url: str,
    title: str,
    category: str,
    fetch_interval: str = "daily",
    validate_url: bool = False,
    enabled: bool = True,
) -> dict[str, Any]:
    """Add a new RSS feed.

    Parameters
    ----------
    url : str
        Feed URL (HTTP/HTTPS only)
    title : str
        Feed title (1-200 characters)
    category : str
        Feed category (1-50 characters)
    fetch_interval : str
        Fetch interval: "daily", "weekly", or "manual" (default: "daily")
    validate_url : bool
        Whether to check URL reachability before adding (default: False)
    enabled : bool
        Whether the feed is enabled (default: True)

    Returns
    -------
    dict
        JSON object containing:
        - feed: The newly created feed object
        - success: True if feed was added successfully
    """
    logger.info(
        "MCP tool called: rss_add_feed",
        url=url,
        title=title,
        category=category,
        fetch_interval=fetch_interval,
        validate_url=validate_url,
        enabled=enabled,
    )

    try:
        data_dir = _get_data_dir()
        manager = FeedManager(data_dir)
        interval = _parse_fetch_interval(fetch_interval)

        feed = manager.add_feed(
            url=url,
            title=title,
            category=category,
            fetch_interval=interval,
            validate_url=validate_url,
            enabled=enabled,
        )

        result = {
            "feed": _feed_to_dict(feed),
            "success": True,
        }

        logger.info("rss_add_feed completed", feed_id=feed.feed_id, title=title)
        return result

    except FeedAlreadyExistsError as e:
        logger.error("rss_add_feed failed: feed already exists", error=str(e))
        return {
            "error": str(e),
            "error_type": "FeedAlreadyExistsError",
            "success": False,
        }

    except InvalidURLError as e:
        logger.error("rss_add_feed failed: invalid URL", error=str(e))
        return {"error": str(e), "error_type": "InvalidURLError", "success": False}

    except FeedFetchError as e:
        logger.error("rss_add_feed failed: URL validation failed", error=str(e))
        return {"error": str(e), "error_type": "FeedFetchError", "success": False}

    except RSSError as e:
        logger.error("rss_add_feed failed", error=str(e))
        return {"error": str(e), "error_type": type(e).__name__, "success": False}


@mcp.tool()
def rss_update_feed(
    feed_id: str,
    title: str | None = None,
    category: str | None = None,
    fetch_interval: str | None = None,
    enabled: bool | None = None,
) -> dict[str, Any]:
    """Update an existing RSS feed.

    Parameters
    ----------
    feed_id : str
        The ID of the feed to update
    title : str | None
        New title (optional, 1-200 characters)
    category : str | None
        New category (optional, 1-50 characters)
    fetch_interval : str | None
        New fetch interval: "daily", "weekly", or "manual" (optional)
    enabled : bool | None
        New enabled status (optional)

    Returns
    -------
    dict
        JSON object containing:
        - feed: The updated feed object
        - success: True if feed was updated successfully
    """
    logger.info(
        "MCP tool called: rss_update_feed",
        feed_id=feed_id,
        title=title,
        category=category,
        fetch_interval=fetch_interval,
        enabled=enabled,
    )

    try:
        data_dir = _get_data_dir()
        manager = FeedManager(data_dir)
        interval = (
            _parse_fetch_interval(fetch_interval)
            if fetch_interval is not None
            else None
        )

        feed = manager.update_feed(
            feed_id=feed_id,
            title=title,
            category=category,
            fetch_interval=interval,
            enabled=enabled,
        )

        result = {
            "feed": _feed_to_dict(feed),
            "success": True,
        }

        logger.info("rss_update_feed completed", feed_id=feed_id)
        return result

    except FeedNotFoundError as e:
        logger.error("rss_update_feed failed: feed not found", error=str(e))
        return {"error": str(e), "error_type": "FeedNotFoundError", "success": False}

    except RSSError as e:
        logger.error("rss_update_feed failed", error=str(e))
        return {"error": str(e), "error_type": type(e).__name__, "success": False}


@mcp.tool()
def rss_remove_feed(feed_id: str) -> dict[str, Any]:
    """Remove an RSS feed and its associated items.

    Parameters
    ----------
    feed_id : str
        The ID of the feed to remove

    Returns
    -------
    dict
        JSON object containing:
        - feed_id: The ID of the removed feed
        - success: True if feed was removed successfully
    """
    logger.info("MCP tool called: rss_remove_feed", feed_id=feed_id)

    try:
        data_dir = _get_data_dir()
        manager = FeedManager(data_dir)
        manager.remove_feed(feed_id)

        result = {
            "feed_id": feed_id,
            "success": True,
        }

        logger.info("rss_remove_feed completed", feed_id=feed_id)
        return result

    except FeedNotFoundError as e:
        logger.error("rss_remove_feed failed: feed not found", error=str(e))
        return {"error": str(e), "error_type": "FeedNotFoundError", "success": False}

    except RSSError as e:
        logger.error("rss_remove_feed failed", error=str(e))
        return {"error": str(e), "error_type": type(e).__name__, "success": False}


@mcp.tool()
async def rss_fetch_feed(feed_id: str) -> dict[str, Any]:
    """Fetch items from a specific RSS feed immediately.

    This tool fetches the latest items from the specified feed, parses them,
    detects new items (diff detection), and saves them to storage.

    Parameters
    ----------
    feed_id : str
        The ID of the feed to fetch

    Returns
    -------
    dict
        JSON object containing:
        - feed_id: The feed ID
        - success: True if fetch was successful
        - items_count: Total number of items after fetch
        - new_items: Number of new items found
        - error_message: Error message if fetch failed (only present on failure)
    """
    logger.info("MCP tool called: rss_fetch_feed", feed_id=feed_id)

    try:
        data_dir = _get_data_dir()
        fetcher = FeedFetcher(data_dir)
        result = await fetcher.fetch_feed(feed_id)

        response = {
            "feed_id": result.feed_id,
            "success": result.success,
            "items_count": result.items_count,
            "new_items": result.new_items,
        }

        if result.error_message:
            response["error_message"] = result.error_message

        logger.info(
            "rss_fetch_feed completed",
            feed_id=feed_id,
            success=result.success,
            items_count=result.items_count,
            new_items=result.new_items,
        )
        return response

    except FeedNotFoundError as e:
        logger.error("rss_fetch_feed failed: feed not found", error=str(e))
        return {
            "feed_id": feed_id,
            "success": False,
            "items_count": 0,
            "new_items": 0,
            "error_message": str(e),
            "error_type": "FeedNotFoundError",
        }

    except FeedFetchError as e:
        logger.error("rss_fetch_feed failed: fetch error", error=str(e))
        return {
            "feed_id": feed_id,
            "success": False,
            "items_count": 0,
            "new_items": 0,
            "error_message": str(e),
            "error_type": "FeedFetchError",
        }

    except FeedParseError as e:
        logger.error("rss_fetch_feed failed: parse error", error=str(e))
        return {
            "feed_id": feed_id,
            "success": False,
            "items_count": 0,
            "new_items": 0,
            "error_message": str(e),
            "error_type": "FeedParseError",
        }

    except RSSError as e:
        logger.error("rss_fetch_feed failed", error=str(e))
        return {
            "feed_id": feed_id,
            "success": False,
            "items_count": 0,
            "new_items": 0,
            "error_message": str(e),
            "error_type": type(e).__name__,
        }


def serve() -> None:
    """Run the MCP server with stdio transport.

    This function starts the MCP server using stdio transport,
    which is the standard way to communicate with Claude Code.
    """
    data_dir = _get_data_dir()
    logger.info("Starting RSS MCP server", data_dir=str(data_dir))
    mcp.run(transport="stdio")


def main() -> None:
    """Entry point for the rss-mcp command.

    This function is called when running `rss-mcp` from the command line.
    """
    serve()


if __name__ == "__main__":
    main()

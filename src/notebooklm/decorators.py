"""Browser operation and MCP tool decorators for error handling and logging.

Provides two decorators for standardizing error handling across the package:

- ``handle_browser_operation``: For service methods that interact with the browser.
  Passes through ``ValueError`` and ``NotebookLMError``, wraps generic exceptions.
- ``mcp_tool_handler``: For MCP tool functions. Adds automatic progress reporting
  and returns standardized error dictionaries instead of raising exceptions.

Examples
--------
>>> from notebooklm.decorators import handle_browser_operation, mcp_tool_handler
>>> from notebooklm.errors import SourceAddError
>>>
>>> @handle_browser_operation(error_class=SourceAddError)
... async def add_source(self, url: str) -> dict:
...     # browser operations here
...     ...
>>>
>>> @mcp_tool_handler("add_source")
... async def tool_add_source(url: str, ctx=None) -> dict:
...     # MCP tool logic here
...     ...
"""

import functools
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from notebooklm.errors import NotebookLMError
from utils_core.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def handle_browser_operation(
    error_class: type[NotebookLMError] = NotebookLMError,
) -> Callable[[F], F]:
    """Decorate service methods to standardize error handling.

    Wraps an async function so that:

    - ``ValueError`` and ``NotebookLMError`` (including subclasses)
      are passed through unchanged.
    - All other exceptions are wrapped in the specified ``error_class``
      with contextual information attached.

    Parameters
    ----------
    error_class : type[NotebookLMError]
        Exception class to wrap generic errors. Defaults to ``NotebookLMError``.

    Returns
    -------
    Callable
        Decorator that wraps an async function.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation_name = func.__name__
            logger.debug("Operation started", operation=operation_name)

            try:
                result = await func(*args, **kwargs)
                logger.debug("Operation completed", operation=operation_name)
                return result

            except (ValueError, NotebookLMError):
                raise

            except Exception as e:
                context: dict[str, Any] = {
                    "operation": operation_name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }

                logger.error(
                    "Operation failed",
                    operation=operation_name,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

                raise error_class(
                    f"{operation_name} failed: {e}",
                    context=context,
                ) from e

        return wrapper  # type: ignore[return-value]

    return decorator


def mcp_tool_handler(tool_name: str) -> Callable[[F], F]:
    """Decorate MCP tool functions with progress reporting and error handling.

    Wraps an async function so that:

    - ``ctx.report_progress(0.0, 1.0)`` is called at start (if ctx available).
    - ``ctx.report_progress(1.0, 1.0)`` is called at end (if ctx available).
    - ``ValueError`` is caught and returned as an error dictionary.
    - ``NotebookLMError`` is caught and returned as an error dictionary
      with context.
    - All other exceptions are caught and returned as an error dictionary.

    Parameters
    ----------
    tool_name : str
        Name of the MCP tool for logging and error reporting.

    Returns
    -------
    Callable
        Decorator that wraps an async function.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            ctx = kwargs.get("ctx")
            if ctx is None:
                for arg in args:
                    if hasattr(arg, "report_progress"):
                        ctx = arg
                        break

            logger.info("MCP tool called", tool=tool_name)

            try:
                if ctx:
                    await ctx.report_progress(0.0, 1.0)

                result = await func(*args, **kwargs)

                if ctx:
                    await ctx.report_progress(1.0, 1.0)

                logger.info("MCP tool completed", tool=tool_name)
                return result

            except ValueError as e:
                logger.error(
                    "MCP tool validation error",
                    tool=tool_name,
                    error=str(e),
                )
                return {
                    "error": str(e),
                    "error_type": "ValueError",
                    "tool": tool_name,
                }

            except NotebookLMError as e:
                logger.error(
                    "MCP tool business error",
                    tool=tool_name,
                    error=str(e),
                    exc_info=True,
                )
                return {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "tool": tool_name,
                    "context": e.context,
                }

            except Exception as e:
                logger.error(
                    "MCP tool unexpected error",
                    tool=tool_name,
                    error=str(e),
                    exc_info=True,
                )
                return {
                    "error": f"Unexpected error: {e}",
                    "error_type": type(e).__name__,
                    "tool": tool_name,
                }

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = [
    "handle_browser_operation",
    "mcp_tool_handler",
]

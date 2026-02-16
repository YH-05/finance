"""MCP tools for NotebookLM AI chat operations.

This module provides five MCP tools for chat operations:

- ``notebooklm_chat``: Send a question and get an AI response.
- ``notebooklm_get_chat_history``: Get chat conversation history.
- ``notebooklm_clear_chat_history``: Clear chat history for a notebook.
- ``notebooklm_configure_chat``: Configure chat settings (system prompt).
- ``notebooklm_save_chat_to_note``: Send a question and save the response to a note.

Each tool retrieves the ``NotebookLMBrowserManager`` from the lifespan
context via ``ctx.lifespan_context["browser_manager"]`` and instantiates
a ``ChatService`` for the operation.

See Also
--------
notebooklm.services.chat : ChatService implementation.
notebooklm.mcp.server : Server setup with lifespan.
"""

from __future__ import annotations

from typing import Any

from fastmcp import Context
from mcp.server.fastmcp import FastMCP

from notebooklm.errors import NotebookLMError
from notebooklm.services.chat import ChatService
from utils_core.logging import get_logger

logger = get_logger(__name__)


def register_chat_tools(mcp: FastMCP) -> None:
    """Register chat management MCP tools on the server.

    Parameters
    ----------
    mcp : FastMCP
        The FastMCP server instance to register tools on.
    """

    @mcp.tool()
    async def notebooklm_chat(
        notebook_id: str,
        question: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Send a chat question to a NotebookLM notebook and get an AI response.

        Types the question into the chat input, sends it, waits for
        the AI to generate a response, and copies the response text
        via the clipboard copy button for reliable Markdown extraction.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        question : str
            The question to ask the AI. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: UUID of the notebook.
            - question: The original question asked.
            - answer: AI-generated answer text (Markdown format).
            - citations: Source citations referenced in the answer.
            - suggested_followups: AI-suggested follow-up questions.
        """
        logger.info(
            "MCP tool called: notebooklm_chat",
            notebook_id=notebook_id,
            question_length=len(question),
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = ChatService(browser_manager)
            response = await service.chat(notebook_id, question)

            result = response.model_dump()

            logger.info(
                "notebooklm_chat completed",
                notebook_id=notebook_id,
                answer_length=len(response.answer),
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_chat failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_chat failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_get_chat_history(
        notebook_id: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Get the chat conversation history for a notebook.

        Navigates to the notebook page and counts the visible
        chat messages in the conversation panel.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: UUID of the notebook.
            - messages: List of chat message objects (empty for count-only).
            - total_messages: Total number of messages in the history.
        """
        logger.info(
            "MCP tool called: notebooklm_get_chat_history",
            notebook_id=notebook_id,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = ChatService(browser_manager)
            history = await service.get_chat_history(notebook_id)

            result = history.model_dump()

            logger.info(
                "notebooklm_get_chat_history completed",
                notebook_id=notebook_id,
                total_messages=history.total_messages,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_get_chat_history failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_get_chat_history failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_clear_chat_history(
        notebook_id: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Clear the chat history for a notebook.

        Opens the chat options menu and clicks the "Clear chat history"
        menu item to remove all previous conversations.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: UUID of the notebook.
            - cleared: Whether the history was cleared successfully.
        """
        logger.info(
            "MCP tool called: notebooklm_clear_chat_history",
            notebook_id=notebook_id,
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = ChatService(browser_manager)
            cleared = await service.clear_chat_history(notebook_id)

            result = {
                "notebook_id": notebook_id,
                "cleared": cleared,
            }

            logger.info(
                "notebooklm_clear_chat_history completed",
                notebook_id=notebook_id,
                cleared=cleared,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_clear_chat_history failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_clear_chat_history failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_configure_chat(
        notebook_id: str,
        system_prompt: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Configure chat settings for a notebook.

        Opens the chat settings dialog, enters the system prompt,
        and saves the configuration. The system prompt controls
        how the AI responds to subsequent queries.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        system_prompt : str
            System prompt to configure. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: UUID of the notebook.
            - configured: Whether the settings were saved successfully.
        """
        logger.info(
            "MCP tool called: notebooklm_configure_chat",
            notebook_id=notebook_id,
            prompt_length=len(system_prompt),
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = ChatService(browser_manager)
            configured = await service.configure_chat(notebook_id, system_prompt)

            result = {
                "notebook_id": notebook_id,
                "configured": configured,
            }

            logger.info(
                "notebooklm_configure_chat completed",
                notebook_id=notebook_id,
                configured=configured,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_configure_chat failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_configure_chat failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

    @mcp.tool()
    async def notebooklm_save_chat_to_note(
        notebook_id: str,
        question: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """Send a chat question and save the AI response to a note.

        Types the question, sends it, waits for the AI response,
        then clicks the "Save to note" button to create a note
        from the response content.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        question : str
            The question to ask the AI. Must not be empty.
        ctx : Context
            MCP context providing access to lifespan resources.

        Returns
        -------
        dict
            JSON object containing:
            - notebook_id: UUID of the notebook.
            - question: The original question asked.
            - saved: Whether the response was saved to a note.
        """
        logger.info(
            "MCP tool called: notebooklm_save_chat_to_note",
            notebook_id=notebook_id,
            question_length=len(question),
        )

        try:
            browser_manager = ctx.lifespan_context["browser_manager"]
            service = ChatService(browser_manager)
            saved = await service.save_response_to_note(notebook_id, question)

            result = {
                "notebook_id": notebook_id,
                "question": question,
                "saved": saved,
            }

            logger.info(
                "notebooklm_save_chat_to_note completed",
                notebook_id=notebook_id,
                saved=saved,
            )
            return result

        except ValueError as e:
            logger.error(
                "notebooklm_save_chat_to_note failed: validation error",
                error=str(e),
            )
            return {"error": str(e), "error_type": "ValueError"}

        except NotebookLMError as e:
            logger.error(
                "notebooklm_save_chat_to_note failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "error": e.message,
                "error_type": type(e).__name__,
                "context": e.context,
            }

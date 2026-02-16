"""ChatService for NotebookLM AI chat operations.

This module provides ``ChatService``, which orchestrates Playwright
browser operations for sending chat queries, retrieving responses via
clipboard copy, managing chat settings, and clearing chat history.

Architecture
------------
The service receives a ``NotebookLMBrowserManager`` via dependency injection
and uses ``SelectorManager`` for resilient element lookup with fallback
selector chains.

Each operation:
1. Creates a new browser page from the shared context.
2. Navigates to the target notebook.
3. Interacts with the chat UI (input query, wait for response, copy).
4. Extracts data from the clipboard or page DOM.
5. Returns typed Pydantic models.
6. Closes the page in a ``finally`` block.

Response Extraction Strategy
----------------------------
NotebookLM renders AI responses as rich HTML in a ProseMirror editor,
making direct DOM scraping fragile. Instead, we use the **clipboard copy**
button (``aria-label="モデルの回答をクリップボードにコピー"``) to capture
the Markdown-formatted response reliably.

Examples
--------
>>> from notebooklm.browser import NotebookLMBrowserManager
>>> from notebooklm.services.chat import ChatService
>>>
>>> async with NotebookLMBrowserManager() as manager:
...     service = ChatService(manager)
...     response = await service.chat("abc-123", "What are the key findings?")
...     print(response.answer)

See Also
--------
notebooklm.browser.manager : Browser lifecycle management.
notebooklm.browser.helpers : Page operation helpers.
notebooklm.selectors : CSS selector management.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from notebooklm.browser.helpers import (
    click_with_fallback,
    navigate_to_notebook,
    wait_for_element,
)
from notebooklm.constants import (
    CHAT_RESPONSE_TIMEOUT_MS,
    DEFAULT_ELEMENT_TIMEOUT_MS,
    GENERATION_POLL_INTERVAL_SECONDS,
)
from notebooklm.errors import ChatError
from notebooklm.selectors import SelectorManager
from notebooklm.types import ChatHistory, ChatResponse
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from notebooklm.browser.manager import NotebookLMBrowserManager

logger = get_logger(__name__)


class ChatService:
    """Service for NotebookLM AI chat operations.

    Provides methods for sending chat queries, retrieving AI responses,
    configuring chat settings, and managing chat history via Playwright
    browser automation.

    Parameters
    ----------
    browser_manager : NotebookLMBrowserManager
        Initialized browser manager for page creation.

    Attributes
    ----------
    _browser_manager : NotebookLMBrowserManager
        The injected browser manager.
    _selectors : SelectorManager
        Selector registry for UI element lookup.

    Examples
    --------
    >>> async with NotebookLMBrowserManager() as manager:
    ...     service = ChatService(manager)
    ...     response = await service.chat("abc-123", "What are the key findings?")
    ...     print(response.answer)
    """

    def __init__(self, browser_manager: NotebookLMBrowserManager) -> None:
        self._browser_manager = browser_manager
        self._selectors = SelectorManager()

        logger.debug("ChatService initialized")

    async def chat(
        self,
        notebook_id: str,
        question: str,
    ) -> ChatResponse:
        """Send a chat query and retrieve the AI response.

        Navigates to the notebook page, types the question into the
        chat input, sends it, waits for the AI response, and copies
        the response text via the clipboard copy button.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        question : str
            The question to ask. Must not be empty.

        Returns
        -------
        ChatResponse
            The AI-generated response with citations and follow-ups.

        Raises
        ------
        ValueError
            If ``notebook_id`` or ``question`` is empty.
        ChatError
            If the chat interaction fails at any step.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> response = await service.chat("abc-123", "What are the key findings?")
        >>> print(response.answer)
        'The key findings include...'
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not question.strip():
            raise ValueError("question must not be empty")

        logger.info(
            "Sending chat query",
            notebook_id=notebook_id,
            question_length=len(question),
        )

        page = await self._browser_manager.new_page()
        try:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Type the question into the chat input
            chat_input_selectors = self._selectors.get_selector_strings(
                "chat_query_input"
            )
            chat_input = await wait_for_element(
                page,
                chat_input_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )
            await chat_input.fill(question)

            # Click the send button
            send_selectors = self._selectors.get_selector_strings("chat_send_button")
            await click_with_fallback(
                page,
                send_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for the AI response to appear
            await self._wait_for_response(page)

            # Copy response via clipboard
            answer = await self._copy_response_via_clipboard(page)

            # Extract suggested follow-up questions
            suggested_followups = await self._extract_suggested_followups(page)

            logger.info(
                "Chat response received",
                notebook_id=notebook_id,
                answer_length=len(answer),
                followup_count=len(suggested_followups),
            )

            return ChatResponse(
                notebook_id=notebook_id,
                question=question,
                answer=answer,
                citations=[],
                suggested_followups=suggested_followups,
            )

        except ValueError:
            raise
        except ChatError:
            raise
        except Exception as e:
            raise ChatError(
                f"Chat interaction failed: {e}",
                context={
                    "notebook_id": notebook_id,
                    "question": question,
                    "error": str(e),
                },
            ) from e
        finally:
            await page.close()

    async def get_chat_history(
        self,
        notebook_id: str,
    ) -> ChatHistory:
        """Get the chat history for a notebook.

        Navigates to the notebook page and extracts the visible
        chat messages from the conversation panel.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.

        Returns
        -------
        ChatHistory
            The chat conversation history.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty.
        ChatError
            If the history retrieval fails.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> history = await service.get_chat_history("abc-123")
        >>> print(history.total_messages)
        5
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        logger.info("Getting chat history", notebook_id=notebook_id)

        page = await self._browser_manager.new_page()
        try:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Wait for chat panel to load
            await page.wait_for_load_state("networkidle")

            # Count the copy buttons to determine message count
            copy_button_selectors = self._selectors.get_selector_strings(
                "chat_copy_response_button"
            )
            selector = (
                copy_button_selectors[0]
                if copy_button_selectors
                else 'button[aria-label="モデルの回答をクリップボードにコピー"]'
            )
            copy_buttons = await page.locator(selector).count()

            logger.info(
                "Chat history retrieved",
                notebook_id=notebook_id,
                message_count=copy_buttons,
            )

            return ChatHistory(
                notebook_id=notebook_id,
                messages=[],
                total_messages=copy_buttons,
            )

        except ValueError:
            raise
        except Exception as e:
            if isinstance(e, ChatError):
                raise
            raise ChatError(
                f"Failed to get chat history: {e}",
                context={
                    "notebook_id": notebook_id,
                    "error": str(e),
                },
            ) from e
        finally:
            await page.close()

    async def clear_chat_history(
        self,
        notebook_id: str,
    ) -> bool:
        """Clear the chat history for a notebook.

        Opens the chat options menu and clicks the "Clear chat history"
        menu item.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.

        Returns
        -------
        bool
            True if the history was cleared successfully.

        Raises
        ------
        ValueError
            If ``notebook_id`` is empty.
        ChatError
            If the clear operation fails.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> cleared = await service.clear_chat_history("abc-123")
        >>> print(cleared)
        True
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")

        logger.info("Clearing chat history", notebook_id=notebook_id)

        page = await self._browser_manager.new_page()
        try:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Click the chat options menu button
            options_selectors = self._selectors.get_selector_strings(
                "chat_options_menu_button"
            )
            await click_with_fallback(
                page,
                options_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Small delay for menu animation
            await asyncio.sleep(0.5)

            # Click "Clear chat history" menu item
            clear_selectors = self._selectors.get_selector_strings(
                "chat_clear_history_menuitem"
            )
            await click_with_fallback(
                page,
                clear_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for UI to update
            await asyncio.sleep(1.0)

            logger.info(
                "Chat history cleared",
                notebook_id=notebook_id,
            )
            return True

        except ValueError:
            raise
        except Exception as e:
            if isinstance(e, ChatError):
                raise
            raise ChatError(
                f"Failed to clear chat history: {e}",
                context={
                    "notebook_id": notebook_id,
                    "error": str(e),
                },
            ) from e
        finally:
            await page.close()

    async def configure_chat(
        self,
        notebook_id: str,
        system_prompt: str,
    ) -> bool:
        """Configure chat settings for a notebook.

        Opens the chat settings dialog, enters the system prompt,
        and saves the configuration.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        system_prompt : str
            System prompt to configure for the chat. Must not be empty.

        Returns
        -------
        bool
            True if the settings were saved successfully.

        Raises
        ------
        ValueError
            If ``notebook_id`` or ``system_prompt`` is empty.
        ChatError
            If the configuration fails.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> configured = await service.configure_chat(
        ...     "abc-123",
        ...     "Answer concisely in Japanese",
        ... )
        >>> print(configured)
        True
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not system_prompt.strip():
            raise ValueError("system_prompt must not be empty")

        logger.info(
            "Configuring chat settings",
            notebook_id=notebook_id,
            prompt_length=len(system_prompt),
        )

        page = await self._browser_manager.new_page()
        try:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Click the settings button
            settings_selectors = self._selectors.get_selector_strings(
                "chat_settings_button"
            )
            await click_with_fallback(
                page,
                settings_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for settings dialog to open
            await asyncio.sleep(0.5)

            # Find the settings text input and fill it
            # The settings dialog uses a textbox for the system prompt
            settings_input = await wait_for_element(
                page,
                ['[role="textbox"]', "textarea"],
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )
            await settings_input.fill(system_prompt)

            # Click save button
            save_selectors = self._selectors.get_selector_strings(
                "chat_settings_save_button"
            )
            await click_with_fallback(
                page,
                save_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for settings to be applied
            await asyncio.sleep(1.0)

            logger.info(
                "Chat settings configured",
                notebook_id=notebook_id,
            )
            return True

        except ValueError:
            raise
        except Exception as e:
            if isinstance(e, ChatError):
                raise
            raise ChatError(
                f"Failed to configure chat: {e}",
                context={
                    "notebook_id": notebook_id,
                    "system_prompt_length": len(system_prompt),
                    "error": str(e),
                },
            ) from e
        finally:
            await page.close()

    async def save_response_to_note(
        self,
        notebook_id: str,
        question: str,
    ) -> bool:
        """Send a chat query and save the response to a note.

        Sends the question, waits for the response, then clicks
        the "Save to note" button on the latest response.

        Parameters
        ----------
        notebook_id : str
            UUID of the target notebook. Must not be empty.
        question : str
            The question to ask. Must not be empty.

        Returns
        -------
        bool
            True if the response was saved to a note.

        Raises
        ------
        ValueError
            If ``notebook_id`` or ``question`` is empty.
        ChatError
            If the save operation fails.
        SessionExpiredError
            If the browser session has expired.

        Examples
        --------
        >>> saved = await service.save_response_to_note(
        ...     "abc-123",
        ...     "Summarize the key findings",
        ... )
        >>> print(saved)
        True
        """
        if not notebook_id.strip():
            raise ValueError("notebook_id must not be empty")
        if not question.strip():
            raise ValueError("question must not be empty")

        logger.info(
            "Sending chat query and saving to note",
            notebook_id=notebook_id,
            question_length=len(question),
        )

        page = await self._browser_manager.new_page()
        try:
            # Navigate to the notebook
            await navigate_to_notebook(page, notebook_id)

            # Type the question
            chat_input_selectors = self._selectors.get_selector_strings(
                "chat_query_input"
            )
            chat_input = await wait_for_element(
                page,
                chat_input_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )
            await chat_input.fill(question)

            # Send the question
            send_selectors = self._selectors.get_selector_strings("chat_send_button")
            await click_with_fallback(
                page,
                send_selectors,
                timeout_ms=DEFAULT_ELEMENT_TIMEOUT_MS,
            )

            # Wait for response
            await self._wait_for_response(page)

            # Click "Save to note" button on the latest response
            save_selectors = self._selectors.get_selector_strings(
                "chat_save_to_note_button"
            )
            # Get all save buttons and click the last one (latest response)
            selector = (
                save_selectors[0]
                if save_selectors
                else 'button[aria-label="メッセージをメモに保存"]'
            )
            save_buttons = page.locator(selector)
            count = await save_buttons.count()

            if count > 0:
                await save_buttons.nth(count - 1).click()
                await asyncio.sleep(1.0)

                logger.info(
                    "Response saved to note",
                    notebook_id=notebook_id,
                )
                return True

            logger.warning(
                "Save to note button not found",
                notebook_id=notebook_id,
            )
            return False

        except ValueError:
            raise
        except Exception as e:
            if isinstance(e, ChatError):
                raise
            raise ChatError(
                f"Failed to save response to note: {e}",
                context={
                    "notebook_id": notebook_id,
                    "question": question,
                    "error": str(e),
                },
            ) from e
        finally:
            await page.close()

    # ---- Private helpers ----

    async def _wait_for_response(self, page: Any) -> None:
        """Wait for the AI response to appear in the chat.

        Polls for the appearance of a copy response button, which
        indicates that the AI has finished generating its response.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.

        Raises
        ------
        ChatError
            If the response does not appear within the timeout.
        """
        copy_selectors = self._selectors.get_selector_strings(
            "chat_copy_response_button"
        )
        selector = (
            copy_selectors[0]
            if copy_selectors
            else 'button[aria-label="モデルの回答をクリップボードにコピー"]'
        )

        elapsed_ms = 0
        poll_interval_ms = int(GENERATION_POLL_INTERVAL_SECONDS * 1000)

        while elapsed_ms < CHAT_RESPONSE_TIMEOUT_MS:
            count = await page.locator(selector).count()
            if count > 0:
                logger.debug(
                    "AI response detected",
                    elapsed_ms=elapsed_ms,
                    copy_button_count=count,
                )
                return

            await asyncio.sleep(GENERATION_POLL_INTERVAL_SECONDS)
            elapsed_ms += poll_interval_ms

        raise ChatError(
            f"AI response not received within {CHAT_RESPONSE_TIMEOUT_MS}ms",
            context={
                "timeout_ms": CHAT_RESPONSE_TIMEOUT_MS,
                "elapsed_ms": elapsed_ms,
            },
        )

    async def _copy_response_via_clipboard(self, page: Any) -> str:
        """Copy the latest AI response text via the clipboard button.

        Clicks the copy button on the most recent response and reads
        the clipboard content via ``page.evaluate()``.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.

        Returns
        -------
        str
            The copied response text in Markdown format.
        """
        copy_selectors = self._selectors.get_selector_strings(
            "chat_copy_response_button"
        )
        selector = (
            copy_selectors[0]
            if copy_selectors
            else 'button[aria-label="モデルの回答をクリップボードにコピー"]'
        )

        # Click the last copy button (most recent response)
        copy_buttons = page.locator(selector)
        count = await copy_buttons.count()

        if count == 0:
            logger.warning("No copy response button found")
            return ""

        await copy_buttons.nth(count - 1).click()

        # Small delay for clipboard write
        await asyncio.sleep(0.5)

        # Read clipboard content via Clipboard API
        try:
            clipboard_text: str = await page.evaluate("navigator.clipboard.readText()")
            return clipboard_text.strip() if clipboard_text else ""
        except Exception as e:
            logger.warning(
                "Clipboard read failed, falling back to DOM extraction",
                error=str(e),
            )
            # Fallback: try to extract text from the response element
            return await self._extract_response_from_dom(page)

    async def _extract_response_from_dom(self, page: Any) -> str:
        """Extract the latest response text directly from the DOM.

        Fallback method when clipboard access is unavailable.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.

        Returns
        -------
        str
            The extracted response text, or empty string if not found.
        """
        # Try to find the last response message element
        response_locator = page.locator(
            ".chat-message-model, .response-content, [data-role='model']"
        )
        count = await response_locator.count()

        if count > 0:
            text = await response_locator.nth(count - 1).inner_text()
            return text.strip() if text else ""

        logger.warning("No response element found in DOM")
        return ""

    async def _extract_suggested_followups(self, page: Any) -> list[str]:
        """Extract suggested follow-up questions from the chat panel.

        Parameters
        ----------
        page : Any
            Playwright page object positioned on a notebook page.

        Returns
        -------
        list[str]
            List of suggested follow-up question strings.
        """
        followup_locator = page.locator(
            ".suggested-question, .followup-chip, [data-type='suggested-followup']"
        )
        elements = await followup_locator.all()

        followups: list[str] = []
        for element in elements:
            text = await element.inner_text()
            text = text.strip() if text else ""
            if text:
                followups.append(text)

        return followups


__all__ = [
    "ChatService",
]

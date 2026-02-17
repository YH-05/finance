"""Custom exception classes for the notebooklm package.

This module provides a hierarchy of exception classes for handling
various error conditions when automating Google NotebookLM via Playwright.

All exceptions include:
- Error messages with context
- Optional context dictionary for additional details

Exception Hierarchy
-------------------
NotebookLMError (base)
    AuthenticationError (login/session failures)
    NavigationError (page navigation failures)
    ElementNotFoundError (UI element lookup failures)
    BrowserTimeoutError (operation timeout failures)
    SessionExpiredError (expired authentication session)
    SourceAddError (source addition failures)
    ChatError (AI chat failures)
    StudioGenerationError (Studio content generation failures)
"""

from typing import Any

from utils_core.logging import get_logger

logger = get_logger(__name__)


class NotebookLMError(Exception):
    """Base exception for all notebooklm package errors.

    All custom exceptions in this package inherit from this class,
    providing a consistent interface for error handling.

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context about the error.

    Attributes
    ----------
    message : str
        The error message.
    context : dict[str, Any]
        Additional error context.

    Examples
    --------
    >>> try:
    ...     raise NotebookLMError(
    ...         "Failed to create notebook",
    ...         context={"title": "My Notebook", "step": "title_input"},
    ...     )
    ... except NotebookLMError as e:
    ...     print(e.context)
    {'title': 'My Notebook', 'step': 'title_input'}
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}


class AuthenticationError(NotebookLMError):
    """Exception raised when authentication with Google fails.

    This exception is raised when:
    - Google login cannot be completed
    - OAuth consent cannot be granted
    - Session file is corrupted or invalid

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., login_url, session_file).

    Examples
    --------
    >>> raise AuthenticationError(
    ...     "Google login failed",
    ...     context={"login_url": "https://accounts.google.com", "attempt": 2},
    ... )
    """


class NavigationError(NotebookLMError):
    """Exception raised when page navigation fails.

    This exception is raised when:
    - A NotebookLM page cannot be loaded
    - A redirect leads to an unexpected URL
    - The target notebook or resource does not exist

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., target_url, current_url, notebook_id).

    Examples
    --------
    >>> raise NavigationError(
    ...     "Failed to navigate to notebook",
    ...     context={
    ...         "notebook_id": "abc-123",
    ...         "target_url": "https://notebooklm.google.com/notebook/abc-123",
    ...     },
    ... )
    """


class ElementNotFoundError(NotebookLMError):
    """Exception raised when a UI element cannot be found on the page.

    This exception is raised when:
    - A CSS selector does not match any element
    - An ARIA role/label combination finds no element
    - A fallback selector chain is exhausted without finding the element

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., selector, fallback_selectors, page_url).

    Examples
    --------
    >>> raise ElementNotFoundError(
    ...     "Create notebook button not found",
    ...     context={
    ...         "selector": 'button[ref="e78"]',
    ...         "fallback_selectors": ['button[ref="e135"]'],
    ...         "page_url": "https://notebooklm.google.com",
    ...     },
    ... )
    """


class BrowserTimeoutError(NotebookLMError):
    """Exception raised when a browser operation times out.

    This exception is raised when:
    - Page load exceeds the configured timeout
    - An element does not appear within the wait timeout
    - A long-running operation (e.g., Audio Overview generation) exceeds its timeout

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., operation, timeout_ms, elapsed_ms).

    Examples
    --------
    >>> raise BrowserTimeoutError(
    ...     "Audio Overview generation timed out after 600000ms",
    ...     context={
    ...         "operation": "audio_overview_generation",
    ...         "timeout_ms": 600000,
    ...         "notebook_id": "abc-123",
    ...     },
    ... )
    """


class SessionExpiredError(NotebookLMError):
    """Exception raised when the Google authentication session has expired.

    This exception is raised when:
    - The stored session cookies are no longer valid
    - Google redirects to a login page during an operation
    - The session file's cookies have passed their expiration time

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., session_file, last_used, redirect_url).

    Examples
    --------
    >>> raise SessionExpiredError(
    ...     "Session expired, re-authentication required",
    ...     context={
    ...         "session_file": ".notebooklm-session.json",
    ...         "last_used": "2026-02-15T10:00:00Z",
    ...     },
    ... )
    """


class SourceAddError(NotebookLMError):
    """Exception raised when adding a source to a notebook fails.

    This exception is raised when:
    - Text source insertion fails
    - URL source cannot be fetched or added
    - File upload fails or the file format is unsupported
    - Google Drive source selection fails

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., source_type, notebook_id, source_url).

    Examples
    --------
    >>> raise SourceAddError(
    ...     "Failed to add URL source: paywall detected",
    ...     context={
    ...         "source_type": "url",
    ...         "notebook_id": "abc-123",
    ...         "source_url": "https://example.com/article",
    ...     },
    ... )
    """


class ChatError(NotebookLMError):
    """Exception raised when AI chat interaction fails.

    This exception is raised when:
    - The chat input field cannot be found
    - The AI response is not generated within the timeout
    - The chat message cannot be submitted

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., notebook_id, question, step).

    Examples
    --------
    >>> raise ChatError(
    ...     "AI response not received within timeout",
    ...     context={
    ...         "notebook_id": "abc-123",
    ...         "question": "What are the key findings?",
    ...         "timeout_ms": 30000,
    ...     },
    ... )
    """


class StudioGenerationError(NotebookLMError):
    """Exception raised when Studio content generation fails.

    This exception is raised when:
    - A Studio content type (report, infographic, slides, data table)
      cannot be generated
    - The generation times out
    - The generated content cannot be extracted or downloaded

    Parameters
    ----------
    message : str
        Human-readable error message.
    context : dict[str, Any] | None
        Additional context (e.g., content_type, notebook_id, generation_time_seconds).

    Examples
    --------
    >>> raise StudioGenerationError(
    ...     "Slide generation timed out after 600 seconds",
    ...     context={
    ...         "content_type": "slides",
    ...         "notebook_id": "abc-123",
    ...         "timeout_seconds": 600,
    ...     },
    ... )
    """


__all__ = [
    "AuthenticationError",
    "BrowserTimeoutError",
    "ChatError",
    "ElementNotFoundError",
    "NavigationError",
    "NotebookLMError",
    "SessionExpiredError",
    "SourceAddError",
    "StudioGenerationError",
]

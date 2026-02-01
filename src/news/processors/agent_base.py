"""Base class for AI processors using Claude Agent SDK.

This module provides the AgentProcessor abstract base class that integrates
with Claude Agent SDK for AI processing of news articles (summarization,
classification, tagging, etc.).

Examples
--------
>>> class SummarizerProcessor(AgentProcessor):
...     @property
...     def processor_name(self) -> str:
...         return "claude_summarizer"
...
...     @property
...     def processor_type(self) -> ProcessorType:
...         return ProcessorType.SUMMARIZER
...
...     def _build_prompt(self, article: Article) -> str:
...         return f"Summarize this article: {article.title}"
...
...     def _parse_response(self, response: str, article: Article) -> dict:
...         return {"summary_ja": response}
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from utils_core.logging import get_logger

from ..core.article import Article  # noqa: TC001
from ..core.errors import NewsError
from ..core.processor import ProcessorType  # noqa: TC001

# AIDEV-NOTE: Lazy import for claude_agent_sdk to allow mocking in tests
# Import at module level for easier patching
_claude_agent_sdk: Any = None

logger = get_logger(__name__, module="agent_processor")


class AgentProcessorError(NewsError):
    """Exception raised when AI processor execution fails.

    This exception is raised for errors that occur during Claude Agent SDK
    execution, including SDK errors, timeout errors, and response parsing errors.

    Parameters
    ----------
    message : str
        Human-readable error message.
    processor_name : str
        Name of the processor that raised the error.
    cause : Exception | None, optional
        Original exception that caused this error.

    Attributes
    ----------
    processor_name : str
        Name of the processor that raised the error.
    cause : Exception | None
        Original exception that caused this error.

    Examples
    --------
    >>> error = AgentProcessorError(
    ...     message="Failed to parse response",
    ...     processor_name="claude_summarizer",
    ... )
    >>> error.processor_name
    'claude_summarizer'
    """

    def __init__(
        self,
        message: str,
        processor_name: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize AgentProcessorError with processor information."""
        super().__init__(message)
        self.processor_name = processor_name
        self.cause = cause

        logger.debug(
            "AgentProcessorError created",
            message=message,
            processor_name=processor_name,
            has_cause=cause is not None,
        )


class SDKNotInstalledError(AgentProcessorError):
    """Exception raised when Claude Agent SDK is not installed.

    This exception is raised when attempting to use AgentProcessor without
    the claude-agent-sdk package installed.

    Examples
    --------
    >>> error = SDKNotInstalledError()
    >>> "install" in str(error).lower()
    True
    """

    def __init__(self) -> None:
        """Initialize SDKNotInstalledError with installation hint."""
        message = (
            "Claude Agent SDK is not installed. "
            "Please install it with: uv add claude-agent-sdk"
        )
        super().__init__(
            message=message,
            processor_name="unknown",
        )


class AgentProcessor(ABC):
    """Abstract base class for AI processors using Claude Agent SDK.

    This class provides the foundation for AI-powered processing of news
    articles using Claude Agent SDK. Subclasses must implement the abstract
    methods to define processor-specific behavior.

    Subclasses must implement:
    - processor_name: Property returning the processor's name
    - processor_type: Property returning the ProcessorType
    - _build_prompt: Method to build the prompt for the AI
    - _parse_response: Method to parse the AI response

    Notes
    -----
    - This class implements the ProcessorProtocol interface.
    - Processors should return new Article instances with updated fields.
    - Errors during processing are wrapped in AgentProcessorError.

    Examples
    --------
    >>> class MySummarizer(AgentProcessor):
    ...     @property
    ...     def processor_name(self) -> str:
    ...         return "my_summarizer"
    ...
    ...     @property
    ...     def processor_type(self) -> ProcessorType:
    ...         return ProcessorType.SUMMARIZER
    ...
    ...     def _build_prompt(self, article: Article) -> str:
    ...         return f"Summarize: {article.title}"
    ...
    ...     def _parse_response(self, response: str, article: Article) -> dict:
    ...         return {"summary_ja": response}
    """

    @property
    @abstractmethod
    def processor_name(self) -> str:
        """Name of the AI processor.

        Returns
        -------
        str
            Human-readable name identifying this processor.
        """
        ...

    @property
    @abstractmethod
    def processor_type(self) -> ProcessorType:
        """Type of the AI processor.

        Returns
        -------
        ProcessorType
            The ProcessorType enum value for this processor.
        """
        ...

    @abstractmethod
    def _build_prompt(self, article: Article) -> str:
        """Build the prompt to send to the AI.

        Parameters
        ----------
        article : Article
            The article to process.

        Returns
        -------
        str
            The prompt string to send to Claude Agent SDK.
        """
        ...

    @abstractmethod
    def _parse_response(self, response: str, article: Article) -> dict[str, Any]:
        """Parse the AI response into article update fields.

        Parameters
        ----------
        response : str
            The raw response from Claude Agent SDK.
        article : Article
            The original article being processed.

        Returns
        -------
        dict[str, Any]
            Dictionary of fields to update on the article.

        Raises
        ------
        AgentProcessorError
            If the response cannot be parsed.
        """
        ...

    def _article_to_json(self, article: Article) -> str:
        """Convert an Article to JSON string for AI processing.

        Parameters
        ----------
        article : Article
            The article to convert.

        Returns
        -------
        str
            JSON string representation of the article.

        Examples
        --------
        >>> processor = MyProcessor()
        >>> json_str = processor._article_to_json(article)
        >>> data = json.loads(json_str)
        >>> "title" in data
        True
        """
        return article.model_dump_json(indent=2)

    def _get_sdk(self) -> Any:
        """Get the Claude Agent SDK module.

        Returns
        -------
        Any
            The claude_agent_sdk module.

        Raises
        ------
        SDKNotInstalledError
            If claude-agent-sdk is not installed.
        """
        import sys

        # Check if claude_agent_sdk module is explicitly set to None (mocked)
        if (
            "claude_agent_sdk" in sys.modules
            and sys.modules["claude_agent_sdk"] is None
        ):
            raise SDKNotInstalledError()

        # Use the module-level variable if it's been set (for testing)
        if _claude_agent_sdk is not None:
            return _claude_agent_sdk

        try:
            import claude_agent_sdk as sdk  # type: ignore[import-not-found]

            return sdk
        except ImportError as e:
            raise SDKNotInstalledError() from e

    def _check_sdk_available(self) -> None:
        """Check if Claude Agent SDK is available.

        Raises
        ------
        SDKNotInstalledError
            If claude-agent-sdk is not installed.
        """
        self._get_sdk()

    async def _execute_query(self, prompt: str) -> str:
        """Execute a query against Claude Agent SDK.

        Parameters
        ----------
        prompt : str
            The prompt to send to the AI.

        Returns
        -------
        str
            The AI response text.

        Raises
        ------
        AgentProcessorError
            If the query fails or times out.
        """
        sdk = self._get_sdk()

        logger.debug(
            "Executing query",
            processor_name=self.processor_name,
            prompt_length=len(prompt),
        )

        try:
            response_parts: list[str] = []
            async for message in sdk.query(prompt=prompt):
                if (
                    hasattr(message, "type")
                    and message.type == "text"
                    and hasattr(message, "content")
                    and message.content
                ):
                    response_parts.append(message.content)

            response = "".join(response_parts)
            logger.debug(
                "Query completed",
                processor_name=self.processor_name,
                response_length=len(response),
            )
            return response

        except asyncio.TimeoutError as e:
            logger.error(
                "Query timeout",
                processor_name=self.processor_name,
                error=str(e),
            )
            raise AgentProcessorError(
                message=f"Query timeout for processor {self.processor_name}",
                processor_name=self.processor_name,
                cause=e,
            ) from e

        except Exception as e:
            logger.error(
                "Query execution failed",
                processor_name=self.processor_name,
                error=str(e),
                exc_info=True,
            )
            raise AgentProcessorError(
                message=f"Agent execution failed: {e}",
                processor_name=self.processor_name,
                cause=e,
            ) from e

    def process(self, article: Article) -> Article:
        """Process a single article.

        Parameters
        ----------
        article : Article
            The article to process.

        Returns
        -------
        Article
            A new Article instance with updated fields.

        Raises
        ------
        SDKNotInstalledError
            If Claude Agent SDK is not installed.
        AgentProcessorError
            If processing fails.

        Notes
        -----
        - The original article is not modified.
        - This method runs the async query synchronously.

        Examples
        --------
        >>> processor = MySummarizer()
        >>> result = processor.process(article)
        >>> result.summary_ja is not None
        True
        """
        logger.info(
            "Processing article",
            processor_name=self.processor_name,
            article_url=str(article.url),
            article_title=article.title[:50] + "..."
            if len(article.title) > 50
            else article.title,
        )

        # Check SDK availability
        self._check_sdk_available()

        # Build prompt
        prompt = self._build_prompt(article)

        # Execute query
        try:
            response = asyncio.get_event_loop().run_until_complete(
                self._execute_query(prompt)
            )
        except RuntimeError:
            # No event loop running, create a new one
            response = asyncio.run(self._execute_query(prompt))

        # Parse response
        try:
            updates = self._parse_response(response, article)
        except AgentProcessorError:
            raise
        except Exception as e:
            logger.error(
                "Response parsing failed",
                processor_name=self.processor_name,
                error=str(e),
            )
            raise AgentProcessorError(
                message=f"Failed to parse response: {e}",
                processor_name=self.processor_name,
                cause=e,
            ) from e

        # Create new article with updates
        result = article.model_copy(update=updates)

        logger.info(
            "Article processed",
            processor_name=self.processor_name,
            article_url=str(article.url),
            updates=list(updates.keys()),
        )

        return result

    def process_batch(self, articles: list[Article]) -> list[Article]:
        """Process multiple articles.

        Parameters
        ----------
        articles : list[Article]
            List of articles to process.

        Returns
        -------
        list[Article]
            List of processed Article instances in the same order.

        Notes
        -----
        - If `articles` is empty, returns an empty list.
        - Each article is processed independently.
        - Results are in the same order as input articles.

        Examples
        --------
        >>> processor = MySummarizer()
        >>> results = processor.process_batch([article1, article2])
        >>> len(results)
        2
        """
        if not articles:
            return []

        logger.info(
            "Processing batch",
            processor_name=self.processor_name,
            batch_size=len(articles),
        )

        results: list[Article] = []
        for article in articles:
            result = self.process(article)
            results.append(result)

        logger.info(
            "Batch processing completed",
            processor_name=self.processor_name,
            processed_count=len(results),
        )

        return results


__all__ = [
    "AgentProcessor",
    "AgentProcessorError",
    "SDKNotInstalledError",
]

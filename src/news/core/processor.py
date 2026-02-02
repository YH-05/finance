"""AI processor protocol for the news package.

This module defines the ProcessorProtocol, an abstract interface for AI processing
(summarization, classification, tagging, etc.) of news articles.

Examples
--------
>>> class SummarizerProcessor:
...     @property
...     def processor_name(self) -> str:
...         return "summarizer"
...
...     @property
...     def processor_type(self) -> ProcessorType:
...         return ProcessorType.SUMMARIZER
...
...     def process(self, article: Article) -> Article:
...         # Implementation here
...         ...
...
...     def process_batch(self, articles: list[Article]) -> list[Article]:
...         # Implementation here
...         ...
"""

from enum import Enum
from typing import Protocol, runtime_checkable

from utils_core.logging import get_logger

from .article import Article

logger = get_logger(__name__, module="processor")


class ProcessorType(str, Enum):
    """Processor type enumeration for AI processing.

    Represents the type of AI processing to be applied to news articles.

    Attributes
    ----------
    SUMMARIZER : str
        Summary generation processor.
    CLASSIFIER : str
        Category classification processor.
    TAGGER : str
        Tag extraction processor.
    """

    SUMMARIZER = "summarizer"
    CLASSIFIER = "classifier"
    TAGGER = "tagger"


@runtime_checkable
class ProcessorProtocol(Protocol):
    """Protocol for AI processing of news articles.

    This protocol defines the interface that all AI processors must implement.
    It provides a unified way to process news articles with various AI tasks
    (summarization, classification, tagging, etc.).

    Attributes
    ----------
    processor_name : str
        Human-readable name of the processor (e.g., "openai_summarizer").
    processor_type : ProcessorType
        Type of the processor from the ProcessorType enum.

    Methods
    -------
    process(article)
        Process a single article.
    process_batch(articles)
        Process multiple articles.

    Notes
    -----
    - This is a `Protocol` class, so implementations don't need to
      explicitly inherit from it.
    - The `@runtime_checkable` decorator enables `isinstance()` checks.
    - Implementations should handle errors gracefully and may raise
      exceptions for critical failures.
    - Processors should return a new Article with updated fields,
      not modify the original article.

    Examples
    --------
    Creating a custom processor:

    >>> class MyProcessor:
    ...     @property
    ...     def processor_name(self) -> str:
    ...         return "my_processor"
    ...
    ...     @property
    ...     def processor_type(self) -> ProcessorType:
    ...         return ProcessorType.SUMMARIZER
    ...
    ...     def process(self, article: Article) -> Article:
    ...         # Process a single article
    ...         return article.model_copy(update={"summary_ja": "..."})
    ...
    ...     def process_batch(self, articles: list[Article]) -> list[Article]:
    ...         return [self.process(a) for a in articles]

    Checking if an object implements the protocol:

    >>> isinstance(MyProcessor(), ProcessorProtocol)
    True
    """

    @property
    def processor_name(self) -> str:
        """Name of the AI processor.

        Returns
        -------
        str
            Human-readable name identifying this processor.
            Examples: "openai_summarizer", "gemini_classifier", "llama_tagger".

        Notes
        -----
        This name is used for logging and identifying the processor
        in processing pipelines.
        """
        ...

    @property
    def processor_type(self) -> ProcessorType:
        """Type of the AI processor.

        Returns
        -------
        ProcessorType
            The ProcessorType enum value for this processor.

        Notes
        -----
        This type is used to categorize the processor
        (summarizer, classifier, tagger, etc.).
        """
        ...

    def process(self, article: Article) -> Article:
        """Process a single article.

        Parameters
        ----------
        article : Article
            The article to process.

        Returns
        -------
        Article
            A new Article instance with updated fields based on the processing.
            The original article should not be modified.

        Notes
        -----
        - Implementations should return a new Article with updated fields
          using `article.model_copy(update={...})`.
        - For summarizers: update `summary_ja` field.
        - For classifiers: update `category` field.
        - For taggers: update `tags` field.
        - Implementations may raise exceptions for critical failures.

        Examples
        --------
        >>> processor = SummarizerProcessor()
        >>> result = processor.process(article)
        >>> result.summary_ja is not None
        True
        """
        ...

    def process_batch(self, articles: list[Article]) -> list[Article]:
        """Process multiple articles.

        Parameters
        ----------
        articles : list[Article]
            List of articles to process.

        Returns
        -------
        list[Article]
            List of processed Article instances, one per input article.
            Results are in the same order as the input articles.

        Notes
        -----
        - If `articles` is empty, returns an empty list.
        - Each article is processed independently; a failure for one
          article may or may not affect others depending on implementation.
        - Implementations may choose to process articles in parallel
          or sequentially.
        - For batch API calls (e.g., OpenAI batch), implementations
          should optimize for efficiency.

        Examples
        --------
        >>> processor = SummarizerProcessor()
        >>> results = processor.process_batch([article1, article2, article3])
        >>> len(results)
        3
        >>> all(r.summary_ja is not None for r in results)
        True
        """
        ...


# Export all public symbols
__all__ = [
    "ProcessorProtocol",
    "ProcessorType",
]

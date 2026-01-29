"""Base extractor abstract class for article body extraction.

This module provides the abstract base class for all article extractors.
Extractors are responsible for fetching the main body text from article URLs.

Examples
--------
>>> from news.extractors.base import BaseExtractor
>>> from news.models import CollectedArticle, ExtractedArticle, ExtractionStatus
>>>
>>> class TrafilaturaExtractor(BaseExtractor):
...     @property
...     def extractor_name(self) -> str:
...         return "trafilatura"
...
...     async def extract(
...         self,
...         article: CollectedArticle,
...     ) -> ExtractedArticle:
...         # Fetch and extract article body
...         return ExtractedArticle(
...             collected=article,
...             body_text="Extracted content...",
...             extraction_status=ExtractionStatus.SUCCESS,
...             extraction_method=self.extractor_name,
...         )
"""

import asyncio
from abc import ABC, abstractmethod

from news.models import CollectedArticle, ExtractedArticle


class BaseExtractor(ABC):
    """Abstract base class for article body extractors.

    This class defines the interface for extractors that fetch the main body
    text from article URLs. Concrete implementations must provide:

    1. An `extractor_name` property returning the name of the extractor
    2. An `extract()` method that fetches and returns the extracted article

    The `extract_batch()` method is provided as a concrete implementation
    that uses semaphore-based concurrency control to extract multiple
    articles in parallel.

    Attributes
    ----------
    extractor_name : str
        The name of this extractor (abstract property).

    Methods
    -------
    extract(article)
        Extract the body text from a single article (abstract method).
    extract_batch(articles, concurrency=5)
        Extract body text from multiple articles in parallel.

    Notes
    -----
    - All extractors must be async-compatible
    - The `extract_batch()` method uses `asyncio.Semaphore` to limit concurrency
    - Default concurrency is 5 to avoid overwhelming target servers

    Examples
    --------
    >>> class MyExtractor(BaseExtractor):
    ...     @property
    ...     def extractor_name(self) -> str:
    ...         return "my_extractor"
    ...
    ...     async def extract(
    ...         self,
    ...         article: CollectedArticle,
    ...     ) -> ExtractedArticle:
    ...         # Fetch article content and extract body
    ...         return ExtractedArticle(
    ...             collected=article,
    ...             body_text="...",
    ...             extraction_status=ExtractionStatus.SUCCESS,
    ...             extraction_method=self.extractor_name,
    ...         )
    ...
    >>> extractor = MyExtractor()
    >>> extractor.extractor_name
    'my_extractor'
    """

    @property
    @abstractmethod
    def extractor_name(self) -> str:
        """Return the name of this extractor.

        Returns
        -------
        str
            The name of the extractor (e.g., "trafilatura", "newspaper3k").

        Examples
        --------
        >>> extractor.extractor_name
        'trafilatura'
        """

    @abstractmethod
    async def extract(self, article: CollectedArticle) -> ExtractedArticle:
        """Extract the body text from a single article.

        Parameters
        ----------
        article : CollectedArticle
            The collected article to extract body text from.

        Returns
        -------
        ExtractedArticle
            The article with extracted body text and extraction status.

        Notes
        -----
        - The method should handle extraction errors gracefully
        - If extraction fails, return ExtractedArticle with appropriate status
          (FAILED, PAYWALL, or TIMEOUT) and error_message

        Examples
        --------
        >>> from news.models import ExtractionStatus
        >>> result = await extractor.extract(article)
        >>> result.extraction_status
        <ExtractionStatus.SUCCESS: 'success'>
        >>> result.body_text[:50]
        'The Federal Reserve announced today that...'
        """

    async def extract_batch(
        self,
        articles: list[CollectedArticle],
        concurrency: int = 5,
    ) -> list[ExtractedArticle]:
        """Extract body text from multiple articles in parallel.

        Uses asyncio.Semaphore to limit the number of concurrent extractions,
        preventing overwhelming the target servers while maintaining efficiency.

        Parameters
        ----------
        articles : list[CollectedArticle]
            List of collected articles to extract body text from.
        concurrency : int, optional
            Maximum number of concurrent extractions. Default is 5.

        Returns
        -------
        list[ExtractedArticle]
            List of extracted articles in the same order as input.

        Notes
        -----
        - Order of results matches order of input articles
        - Uses asyncio.gather to run extractions concurrently
        - The semaphore ensures at most `concurrency` extractions run at once

        Examples
        --------
        >>> articles = [article1, article2, article3]
        >>> results = await extractor.extract_batch(articles, concurrency=3)
        >>> len(results)
        3
        >>> all(isinstance(r, ExtractedArticle) for r in results)
        True
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def extract_with_semaphore(article: CollectedArticle) -> ExtractedArticle:
            async with semaphore:
                return await self.extract(article)

        tasks = [extract_with_semaphore(article) for article in articles]
        return list(await asyncio.gather(*tasks))


__all__ = ["BaseExtractor"]

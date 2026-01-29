"""Extractors package for article body text extraction.

This package provides extractors for fetching and extracting the main body
text from news article URLs. Extractors handle the conversion from a
CollectedArticle (with just URL and metadata) to an ExtractedArticle
(with the full article body text).

Available Extractors
--------------------
BaseExtractor
    Abstract base class for all extractors.
TrafilaturaExtractor
    Trafilatura-based extractor that wraps ArticleExtractor.

Examples
--------
>>> from news.extractors import TrafilaturaExtractor
>>> from news.models import CollectedArticle, ExtractionStatus
>>>
>>> extractor = TrafilaturaExtractor()
>>> result = await extractor.extract(article)
>>> result.extraction_status
<ExtractionStatus.SUCCESS: 'success'>
"""

from news.extractors.base import BaseExtractor
from news.extractors.trafilatura import TrafilaturaExtractor

__all__ = ["BaseExtractor", "TrafilaturaExtractor"]

"""Extractors package for article body text extraction.

This package provides extractors for fetching and extracting the main body
text from news article URLs. Extractors handle the conversion from a
CollectedArticle (with just URL and metadata) to an ExtractedArticle
(with the full article body text).

Examples
--------
>>> from news.extractors.base import BaseExtractor
>>> from news.models import CollectedArticle, ExtractedArticle
>>>
>>> class MyExtractor(BaseExtractor):
...     @property
...     def extractor_name(self) -> str:
...         return "my_extractor"
...
...     async def extract(self, article: CollectedArticle) -> ExtractedArticle:
...         # Implementation here
...         pass
"""

from news.extractors.base import BaseExtractor

__all__ = ["BaseExtractor"]

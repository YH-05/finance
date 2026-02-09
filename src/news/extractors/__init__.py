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
PlaywrightExtractor
    Playwright-based extractor for JS-rendered pages (optional dependency).
DomainRateLimiter
    Per-domain rate limiter with jitter and session-fixed User-Agent.

Examples
--------
>>> from news.extractors import TrafilaturaExtractor
>>> from news.models import CollectedArticle, ExtractionStatus
>>>
>>> extractor = TrafilaturaExtractor()
>>> result = await extractor.extract(article)
>>> result.extraction_status
<ExtractionStatus.SUCCESS: 'success'>

>>> # For JS-rendered pages (requires playwright optional dependency)
>>> from news.extractors import PlaywrightExtractor
>>> async with PlaywrightExtractor(config) as extractor:
...     result = await extractor.extract(article)
"""

from news.extractors.base import BaseExtractor
from news.extractors.playwright import PlaywrightExtractor
from news.extractors.rate_limiter import DomainRateLimiter
from news.extractors.trafilatura import TrafilaturaExtractor

__all__ = [
    "BaseExtractor",
    "DomainRateLimiter",
    "PlaywrightExtractor",
    "TrafilaturaExtractor",
]

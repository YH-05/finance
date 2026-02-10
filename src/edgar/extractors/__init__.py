"""Extractors subpackage for SEC EDGAR filing data.

This subpackage provides extractor classes for parsing and extracting
structured data from SEC EDGAR filings.

Public API
----------
SectionExtractor
    Extract section-level text from filings (Item 1, Item 1A, etc.)
TextExtractor
    Extract clean text and Markdown from Filing objects
"""

from .section import SectionExtractor
from .text import TextExtractor

__all__ = [
    "SectionExtractor",
    "TextExtractor",
]
